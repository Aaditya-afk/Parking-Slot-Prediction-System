import { useEffect, useRef, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, Timer, Calendar, MapPin, Bell } from 'lucide-react';

interface SlotTimerModalProps {
  open: boolean;
  onClose: () => void;
  slot: {
    slot_id?: number;
    slotNumber?: string;
    status: string;
    expected_free_time?: string;
    timer_remaining?: number;
    zone?: string;
    user_set_duration?: number;
    occupied_at?: string;
  } | null;
  onReserve?: (slotId: number) => void;
  onAutoFree?: (slotId: number) => void;
}

export function SlotTimerModal({ open, onClose, slot, onReserve, onAutoFree }: SlotTimerModalProps) {
  const [countdown, setCountdown] = useState<string>('');
  const [tick, setTick] = useState(0);
  const [secondsLeft, setSecondsLeft] = useState<number | null>(null);
  const [firedAutoFree, setFiredAutoFree] = useState(false);
  const targetTsRef = useRef<number | null>(null);

  // Debug: Log slot data when modal opens
  useEffect(() => {
    if (open && slot) {
      console.log('🎯 Modal opened with slot:', {
        slotNumber: slot.slotNumber,
        status: slot.status,
        timer_remaining: slot.timer_remaining,
        expected_free_time: slot.expected_free_time,
        occupied_at: slot.occupied_at,
        user_set_duration: slot.user_set_duration,
        fullSlot: slot
      });
    }
  }, [open, slot]);

  // Update countdown every second
  useEffect(() => {
    if (!open || !slot) return;

    const timer = setInterval(() => {
      setTick(t => t + 1);
    }, 1000);

    return () => clearInterval(timer);
  }, [open, slot]);

  // Establish a single target timestamp when the modal opens or slot changes
  useEffect(() => {
    targetTsRef.current = null;
    setSecondsLeft(null);
    setCountdown('');
    if (!slot) return;
    // Priority: expected_free_time > timer_remaining > occupied_at + user_set_duration
    if (slot.expected_free_time) {
      targetTsRef.current = new Date(slot.expected_free_time).getTime();
      return;
    }
    if (typeof slot.timer_remaining === 'number') {
      targetTsRef.current = Date.now() + Math.max(0, slot.timer_remaining) * 1000;
      return;
    }
    if (slot.occupied_at && slot.user_set_duration) {
      targetTsRef.current = new Date(slot.occupied_at).getTime() + slot.user_set_duration * 60000;
      return;
    }
  }, [open, slot?.slot_id, slot?.slotNumber]);

  // Tick: compute remaining from target timestamp so the timer doesn't reset
  useEffect(() => {
    if (!targetTsRef.current) {
      setCountdown('');
      setSecondsLeft(null);
      return;
    }
    const now = Date.now();
    const remainingMs = Math.max(0, targetTsRef.current - now);
    const hours = Math.floor(remainingMs / 3600000);
    const minutes = Math.floor((remainingMs % 3600000) / 60000);
    const seconds = Math.floor((remainingMs % 60000) / 1000);
    if (remainingMs <= 0) {
      setCountdown('0s'); // Show 0s instead of 'Available Now' to keep timer display
      setSecondsLeft(0);
    } else {
      if (hours > 0) setCountdown(`${hours}h ${minutes}m ${seconds}s`);
      else if (minutes > 0) setCountdown(`${minutes}m ${seconds}s`);
      else setCountdown(`${seconds}s`);
      setSecondsLeft(Math.floor(remainingMs / 1000));
    }
  }, [tick]);

  // Auto-free when countdown hits zero (once)
  useEffect(() => {
    if (!open || !slot) return;
    const sid = slot.slot_id || parseInt(slot.slotNumber?.replace('SLOT_', '') || '0');
    if (!sid) return;
    if (secondsLeft === 0 && !firedAutoFree) {
      setFiredAutoFree(true);
      onAutoFree?.(sid);
    }
  }, [secondsLeft, firedAutoFree, open, slot, onAutoFree]);

  // Reset internal flags when slot changes or modal re-opens
  useEffect(() => {
    setFiredAutoFree(false);
  }, [open, slot?.slot_id, slot?.slotNumber]);

  // If nothing to show, render nothing
  if (!slot) return null;

  const slotId = slot.slot_id || parseInt(slot.slotNumber?.replace('SLOT_', '') || '0');
  const slotName = slot.slotNumber || (slot.slot_id ? `SLOT_${slot.slot_id}` : 'SLOT');
  const expectedFreeTime = slot.expected_free_time 
    ? new Date(slot.expected_free_time).toLocaleTimeString('en-US', {
        hour: '2-digit',
        minute: '2-digit',
        hour12: true,
      })
    : null;

  const getStatusColor = () => {
    switch (slot?.status) {
      case 'occupied': return 'bg-destructive';
      case 'reserved': return 'bg-warning';
      case 'available': return 'bg-success';
      case 'free': return 'bg-success'; // Backend uses 'free' not 'available'
      default: return 'bg-muted';
    }
  };
  
  const getStatusLabel = () => {
    switch (slot?.status) {
      case 'occupied': return 'OCCUPIED';
      case 'reserved': return 'RESERVED';
      case 'available': return 'AVAILABLE';
      case 'free': return 'AVAILABLE'; // Backend uses 'free' not 'available'
      default: return slot?.status?.toUpperCase() || 'UNKNOWN';
    }
  };

  return (
    <Dialog open={open} onOpenChange={onClose}>
      <DialogContent className="glass-card border-2 border-primary/50 max-w-md">
        <DialogHeader>
          <DialogTitle className="font-orbitron text-2xl flex items-center gap-3">
            <div className="p-2 rounded-full bg-primary/20">
              <Timer className="h-6 w-6 text-primary" />
            </div>
            {slotName}
          </DialogTitle>
        </DialogHeader>

        <div className="space-y-4 mt-4">
          {/* Status Badge */}
          <div className="flex items-center justify-between">
            <span className="text-sm text-muted-foreground">Current Status:</span>
            <Badge className={`${getStatusColor()} font-orbitron tracking-wider`}>
              {getStatusLabel()}
            </Badge>
          </div>

          {/* Zone Info */}
          {slot.zone && (
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Zone:</span>
              <div className="flex items-center gap-2">
                <MapPin className="h-4 w-4 text-primary" />
                <span className="font-orbitron font-bold text-primary">Zone {slot.zone}</span>
              </div>
            </div>
          )}

          {/* Occupied Slot - Show timer or no ETA message */}
          {slot.status === 'occupied' && (
            <>
              {!countdown && (
                <div className="p-6 rounded-lg bg-background/50 border-2 border-primary/20 text-center">
                  <div className="text-sm text-muted-foreground mb-2">ETA not available from server</div>
                  <div className="text-xs text-muted-foreground">We will update this as soon as predictions or booking info arrives.</div>
                </div>
              )}

              {countdown && (
                <div className="p-6 rounded-lg bg-gradient-to-br from-destructive/20 to-destructive/5 border-2 border-destructive/30">
                  <div className="text-center space-y-3">
                    <div className="flex items-center justify-center gap-2">
                      <Clock className="h-6 w-6 text-destructive animate-pulse" />
                      <span className="text-sm font-medium text-muted-foreground">
                        Available In:
                      </span>
                    </div>
                    
                    <div className="font-mono text-5xl font-bold text-destructive animate-pulse">
                      {countdown}
                    </div>

                    {expectedFreeTime && (
                      <div className="pt-3 border-t border-destructive/20">
                        <div className="flex items-center justify-center gap-2 text-sm">
                          <Calendar className="h-4 w-4 text-muted-foreground" />
                          <span className="text-muted-foreground">Expected free at:</span>
                          <span className="font-bold text-primary">{expectedFreeTime}</span>
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}

          {/* Reserved Slot Info */}
          {slot.status === 'reserved' && countdown && (
            <div className="p-6 rounded-lg bg-gradient-to-br from-warning/20 to-warning/5 border-2 border-warning/30">
              <div className="text-center space-y-3">
                <div className="flex items-center justify-center gap-2">
                  <Bell className="h-6 w-6 text-warning" />
                  <span className="text-sm font-medium text-muted-foreground">
                    Reservation Expires In:
                  </span>
                </div>
                
                <div className="font-mono text-4xl font-bold text-warning">
                  {countdown}
                </div>
              </div>
            </div>
          )}

          {/* Available Slot */}
          {(slot.status === 'available' || slot.status === 'free') && (
            <div className="p-6 rounded-lg bg-gradient-to-br from-success/20 to-success/5 border-2 border-success/30 text-center">
              <div className="flex items-center justify-center gap-2 mb-2">
                <Clock className="h-6 w-6 text-success" />
                <span className="text-lg font-bold text-success">Available Now!</span>
              </div>
              <p className="text-sm text-muted-foreground">This slot is ready to book</p>
            </div>
          )}

          {/* Duration Info */}
          {slot.user_set_duration && slot.status === 'occupied' && (
            <div className="flex items-center justify-between p-3 rounded bg-background/50">
              <span className="text-sm text-muted-foreground">Parking Duration:</span>
              <span className="font-bold text-primary">{slot.user_set_duration} minutes</span>
            </div>
          )}

          {/* Action Buttons */}
          <div className="flex gap-3 pt-4">
            {slot.status === 'occupied' && onReserve && countdown !== 'Available Now' && (
              <Button 
                className="flex-1 font-orbitron bg-warning hover:bg-warning/90"
                onClick={() => {
                  onReserve(slotId);
                  onClose();
                }}
              >
                <Bell className="h-4 w-4 mr-2" />
                RESERVE WHEN FREE
              </Button>
            )}
            
            <Button 
              variant="outline" 
              className="flex-1 font-orbitron"
              onClick={onClose}
            >
              CLOSE
            </Button>
          </div>

          {/* Info Message */}
          {slot.status === 'occupied' && (
            <div className="text-xs text-center text-muted-foreground p-3 rounded bg-primary/5">
              💡 This slot will automatically become available when the timer reaches zero
            </div>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
