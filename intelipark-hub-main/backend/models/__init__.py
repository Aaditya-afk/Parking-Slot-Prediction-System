"""Models package - exports all database models"""

from .slots import ParkingSlot as Slot, SlotLog, Base
from .reservations import Reservation, GateLog

# Create a dummy SensorLog and SystemLog for backward compatibility
class SensorLog:
    """Placeholder for sensor logs"""
    pass

class SystemLog:
    """Placeholder for system logs"""
    pass

__all__ = ['Slot', 'SlotLog', 'Reservation', 'GateLog', 'SensorLog', 'SystemLog', 'Base']
