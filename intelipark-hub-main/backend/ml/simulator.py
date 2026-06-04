"""
SmartPark Data Simulator (software-only mode)
- Backfills historical parking slot logs
- Generates live occupancy changes
- Designed to work with FastAPI DB session from database_entry_exit
"""
from __future__ import annotations

import os
import random
from datetime import datetime, timedelta
from typing import Dict, List

from sqlalchemy.orm import Session

# Use entry_exit models (status string based)
from ..models.parking import ParkingSlot, SystemLog

# Configuration via env
SIM_HISTORY_DAYS = int(os.getenv("SIM_HISTORY_DAYS", "30"))
SIM_LIVE_INTERVAL_SECONDS = int(os.getenv("SIM_LIVE_INTERVAL_SECONDS", "15"))
TOTAL_SLOTS = int(os.getenv("TOTAL_PARKING_SLOTS", "3"))

# Diurnal occupancy profile (0..1 expected occupancy rate by hour)
DIURNAL = {
    0: 0.15, 1: 0.1, 2: 0.08, 3: 0.08, 4: 0.1,
    5: 0.15, 6: 0.25, 7: 0.35, 8: 0.55, 9: 0.65,
    10: 0.7, 11: 0.75, 12: 0.8, 13: 0.75, 14: 0.6,
    15: 0.65, 16: 0.7, 17: 0.8, 18: 0.85, 19: 0.7,
    20: 0.5, 21: 0.4, 22: 0.3, 23: 0.2,
}

SLOT_WEIGHTS = {
    "SLOT_1": 1.1,  # near entry, fills earlier
    "SLOT_2": 1.0,
    "SLOT_3": 0.9,  # empties sooner on average
}


def ensure_slots(db: Session):
    existing = db.query(ParkingSlot).count()
    if existing == 0:
        for i in range(1, TOTAL_SLOTS + 1):
            db.add(ParkingSlot(slot_number=f"SLOT_{i}", status="free"))
        db.commit()


def _expected_rate(dt: datetime) -> float:
    base = DIURNAL.get(dt.hour, 0.5)
    # weekend lighter
    if dt.weekday() >= 5:
        base *= 0.7
    return max(0.0, min(0.95, base))


def generate_state_snapshot(dt: datetime) -> Dict[str, str]:
    """Return dict slot_number -> status ('free'|'occupied')."""
    rate = _expected_rate(dt)
    states: Dict[str, str] = {}
    for i in range(1, TOTAL_SLOTS + 1):
        slot_id = f"SLOT_{i}"
        w = SLOT_WEIGHTS.get(slot_id, 1.0)
        p_occ = max(0.0, min(0.98, rate * w + random.uniform(-0.1, 0.1)))
        states[slot_id] = "occupied" if random.random() < p_occ else "free"
    return states


def backfill_history(db: Session, days: int = SIM_HISTORY_DAYS, step_minutes: int = 5) -> int:
    """Backfill slot states every step_minutes for last `days`. Overwrites current states to last snapshot."""
    ensure_slots(db)
    now = datetime.utcnow()
    start = now - timedelta(days=days)
    t = start
    written = 0

    while t <= now:
        snapshot = generate_state_snapshot(t)
        for slot_num, state in snapshot.items():
            slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == slot_num).first()
            if slot is None:
                slot = ParkingSlot(slot_number=slot_num, status=state)
                db.add(slot)
            else:
                slot.status = state
                slot.last_updated = t
            written += 1
        if written % 300 == 0:
            db.commit()
        t += timedelta(minutes=step_minutes)

    db.add(SystemLog(level="INFO", component="simulator", message=f"Backfilled {written} slot states over {days}d"))
    db.commit()
    return written


def tick_once(db: Session) -> Dict[str, str]:
    """Generate one live tick and persist current states."""
    ensure_slots(db)
    dt = datetime.utcnow()
    snapshot = generate_state_snapshot(dt)
    for slot_num, state in snapshot.items():
        slot = db.query(ParkingSlot).filter(ParkingSlot.slot_number == slot_num).first()
        if slot is None:
            db.add(ParkingSlot(slot_number=slot_num, status=state))
        else:
            slot.status = state
            slot.last_updated = dt
    db.commit()
    return snapshot
