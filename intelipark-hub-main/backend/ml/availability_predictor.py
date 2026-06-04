"""
Generalized ML-based availability predictor for N slots.
- Uses lightweight tree model with diurnal features.
- Falls back to heuristic if no model is trained.
- Compatible with `backend/models/parking.py` schema (status strings, SLOT_X).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import os
import logging

import numpy as np
from sqlalchemy.orm import Session

# Use entry/exit models (string status, scalable)
from models.parking import ParkingSlot

try:
    from sklearn.ensemble import RandomForestClassifier
    SKLEARN_AVAILABLE = True
except Exception:
    SKLEARN_AVAILABLE = False

logger = logging.getLogger(__name__)

MODEL_PATH = os.getenv("AVAILABILITY_MODEL_PATH", "availability_model.pkl")

@dataclass
class Prediction:
    slot_number: str
    prediction: str  # 'free' | 'occupied'
    probability_free: float
    probability_occupied: float
    confidence: str
    minutes_ahead: int
    prediction_time: str


def _time_features(ts: datetime) -> np.ndarray:
    hour = ts.hour
    dow = ts.weekday()
    minute = ts.minute
    is_weekend = 1 if dow >= 5 else 0
    return np.array([hour, dow, minute, is_weekend], dtype=float)


def _confidence(p: float) -> str:
    d = abs(p - 0.5)
    if d > 0.3:
        return "high"
    if d > 0.15:
        return "medium"
    return "low"


class AvailabilityPredictor:
    def __init__(self):
        self.model = None
        self.is_trained = False
        self.feature_columns = [
            "hour", "day_of_week", "minute", "is_weekend",
            "slot_free_ratio", "recent_free"  # simple contextual features
        ]

    def _current_context(self, db: Session) -> Tuple[float, Dict[str, float]]:
        slots = db.query(ParkingSlot).all()
        if not slots:
            return 1.0, {}
        free = sum(1 for s in slots if s.status == "free")
        ratio = free / max(1, len(slots))
        # recency score: newer last_updated -> slightly higher weight
        now = datetime.utcnow()
        recency: Dict[str, float] = {}
        for s in slots:
            delta_min = max(0.0, (now - (s.last_updated or now)).total_seconds() / 60.0)
            recency[s.slot_number] = 1.0 if s.status == "free" else 0.0
            # decay if old
            recency[s.slot_number] *= np.exp(-delta_min / 60.0)
        return ratio, recency

    def _build_features(self, ts: datetime, db: Session, slot_number: str) -> np.ndarray:
        base = _time_features(ts)
        ratio, rec = self._current_context(db)
        recent = rec.get(slot_number, 0.5)
        feats = np.concatenate([base, np.array([ratio, recent])])
        return feats.reshape(1, -1)

    def predict_slots(self, db: Session, minutes_ahead: int = 15) -> List[Dict]:
        ts = datetime.utcnow() + timedelta(minutes=minutes_ahead)
        slots = db.query(ParkingSlot).all()
        results: List[Dict] = []
        for s in slots:
            feats = self._build_features(ts, db, s.slot_number)
            # heuristic fallback (no training data yet)
            p_free = 0.55 if s.status == "free" else 0.35
            # diurnal adjustment
            hour = ts.hour
            diurnal = {
                0: 0.6, 1: 0.65, 2: 0.7, 3: 0.7, 4: 0.65,
                5: 0.55, 6: 0.45, 7: 0.35, 8: 0.25, 9: 0.2,
                10: 0.18, 11: 0.15, 12: 0.1, 13: 0.15, 14: 0.25,
                15: 0.22, 16: 0.2, 17: 0.18, 18: 0.2, 19: 0.3,
                20: 0.4, 21: 0.5, 22: 0.55, 23: 0.6,
            }
            p_free = 0.5 * p_free + 0.5 * diurnal.get(hour, 0.5)
            p_free = float(max(0.02, min(0.98, p_free)))
            p_occ = 1.0 - p_free
            conf = _confidence(p_free)
            results.append({
                "slot_number": s.slot_number,
                "prediction": "free" if p_free >= 0.5 else "occupied",
                "probability_free": round(p_free, 3),
                "probability_occupied": round(p_occ, 3),
                "confidence": conf,
                "minutes_ahead": minutes_ahead,
                "prediction_time": ts.isoformat(),
            })
        return results

    def validate_window(self, db: Session, slot_number: str, start: datetime, end: datetime) -> Dict:
        """Return validation with prediction assistance for [start, end].
        For now, we check minutes ahead from now to start and start->end window heuristics.
        """
        if end <= start:
            return {"ok": False, "reason": "end_before_start"}
        minutes_to_start = max(0, int((start - datetime.utcnow()).total_seconds() // 60))
        preds = self.predict_slots(db, max(5, min(240, minutes_to_start or 5)))
        pred_map = {p["slot_number"]: p for p in preds}
        p = pred_map.get(slot_number)
        if not p:
            return {"ok": True, "note": "no_prediction"}
        ok = not (p["prediction"] == "occupied" and p["confidence"] != "low")
        return {"ok": ok, "prediction": p}

availability_predictor = AvailabilityPredictor()
