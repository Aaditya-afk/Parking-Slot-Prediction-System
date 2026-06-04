import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, MapPin, Timer, Zap, CheckCircle, AlertCircle } from 'lucide-react';

interface SlotWithTimerProps {
  slot: {
    slot_id: number;
    status: 'available' | 'occupied' | 'reserved' | 'maintenance';
    zone: string;
    expected_free_time?: string;
    timer_remaining?: number;
    predicted_free_in?: number;
    prediction_confidence?: number;
    user_set_duration?: number;
  };
  onClick?: () => void;
  onBook?: (slotId: number, duration: number) => void;
  onFree?: (slotId: number) => void;
}

export function SlotWithTimer({ slot, onClick, onBook, onFree }: SlotWithTimerProps) {
  const [timeLeft, setTimeLeft] = useState<string>('');
  const [showBookModal, setShowBookModal] = useState(false);
  const [selectedDuration, setSelectedDuration] = useState(30);

  // Live countdown timer
  useEffect(() => {
    if (slot.status === 'occupied' && slot.timer_remaining) {
      const interval = setInterval(() => {
        const remaining = slot.timer_remaining || 0;
        const minutes = Math.floor(remaining / 60);
        const seconds = remaining % 60;
        setTimeLeft(`${minutes}m ${seconds}s`);
      }, 1000);

      return () => clearInterval(interval);
    } else {
      setTimeLeft('');
    }
  }, [slot.timer_remaining, slot.status]);

  const getStatusColor = () => {
    switch (slot.status) {
      case 'available': return 'border-success bg-success/10 hover:bg-success/20';
      case 'occupied': return 'border-destructive bg-destructive/10';
      case 'reserved': return 'border-warning bg-warning/10';
      default: return 'border-muted bg-muted/10';
    }
  };

  const getStatusIcon = () => {
    switch (slot.status) {
      case 'available': return <CheckCircle className="h-6 w-6 text-success" />;
      case 'occupied': return <Clock className="h-6 w-6 text-destructive animate-pulse" />;
      case 'reserved': return <Timer className="h-6 w-6 text-warning" />;
      default: return <AlertCircle className="h-6 w-6 text-muted" />;
    }
  };

  const handleBook = () => {
    if (onBook) {
      onBook(slot.slot_id, selectedDuration);
      setShowBookModal(false);
    }
  };

  return (
    <>
      <Card 
        className={`glass-card border-2 ${getStatusColor()} p-4 space-y-3 transition-all cursor-pointer`}
        onClick={onClick}
      >
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {getStatusIcon()}
            <div>
              <h3 className="font-orbitron font-bold text-sm">SLOT_{slot.slot_id}</h3>
              <div className="flex items-center gap-1 text-xs text-muted-foreground">
                <MapPin className="h-3 w-3" />
                <span>Zone {slot.zone}</span>
              </div>
            </div>
          </div>
          <Badge className={`font-orbitron text-xs ${
            slot.status === 'available' ? 'bg-success' :
            slot.status === 'occupied' ? 'bg-destructive' :
            slot.status === 'reserved' ? 'bg-warning' : 'bg-muted'
          }`}>
            {slot.status.toUpperCase()}
          </Badge>
        </div>

        {/* Live Countdown Timer */}
        {slot.status === 'occupied' && timeLeft && (
          <div className="flex items-center justify-center gap-2 p-2 rounded bg-destructive/20 border border-destructive/30">
            <Timer className="h-4 w-4 text-destructive animate-pulse" />
            <div className="text-center">
              <div className="font-mono text-lg font-bold text-destructive">{timeLeft}</div>
              <div className="text-xs text-muted-foreground">Time Left</div>
            </div>
          </div>
        )}

        {/* Expected Free Time */}
        {slot.status === 'occupied' && slot.expected_free_time && (
          <div className="text-xs text-center p-2 rounded bg-background/50">
            <span className="text-muted-foreground">Free at: </span>
            <span className="font-bold text-primary">
              {new Date(slot.expected_free_time).toLocaleTimeString('en-US', { 
                hour: '2-digit', 
                minute: '2-digit' 
              })}
            </span>
          </div>
        )}

        {/* ML Prediction */}
        {slot.predicted_free_in !== undefined && slot.predicted_free_in > 0 && (
          <div className="text-xs text-center p-2 rounded bg-primary/10 border border-primary/30">
            <div className="flex items-center justify-center gap-1">
              <Zap className="h-3 w-3 text-primary" />
              <span className="text-muted-foreground">Predicted free in: </span>
              <span className="font-bold text-primary">{slot.predicted_free_in}m</span>
            </div>
            {slot.prediction_confidence && (
              <div className="text-xs text-muted-foreground mt-1">
                Confidence: {Math.round(slot.prediction_confidence * 100)}%
              </div>
            )}
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
          {slot.status === 'available' && (
            <Button 
              size="sm" 
              className="flex-1 font-orbitron text-xs bg-success hover:bg-success/90"
              onClick={() => setShowBookModal(true)}
            >
              <Zap className="h-3 w-3 mr-1" />
              BOOK
            </Button>
          )}
          {slot.status === 'occupied' && onFree && (
            <Button 
              size="sm" 
              variant="outline"
              className="flex-1 font-orbitron text-xs border-destructive text-destructive hover:bg-destructive/10"
              onClick={() => onFree(slot.slot_id)}
            >
              FREE UP
            </Button>
          )}
        </div>
      </Card>

      {/* Booking Modal */}
      {showBookModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50" onClick={() => setShowBookModal(false)}>
          <Card className="glass-card border-2 border-primary/50 p-6 max-w-md w-full m-4" onClick={(e) => e.stopPropagation()}>
            <h3 className="font-orbitron text-xl font-bold mb-4">Book SLOT_{slot.slot_id}</h3>
            
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium mb-2 block">How long will you park?</label>
                <div className="grid grid-cols-3 gap-2">
                  {[15, 30, 45, 60, 90, 120].map((duration) => (
                    <Button
                      key={duration}
                      size="sm"
                      variant={selectedDuration === duration ? "default" : "outline"}
                      onClick={() => setSelectedDuration(duration)}
                      className="font-orbitron"
                    >
                      {duration}m
                    </Button>
                  ))}
                </div>
              </div>

              <div className="p-3 rounded bg-primary/10 border border-primary/30">
                <div className="text-sm text-muted-foreground">Expected free at:</div>
                <div className="font-bold text-primary">
                  {new Date(Date.now() + selectedDuration * 60000).toLocaleTimeString('en-US', {
                    hour: '2-digit',
                    minute: '2-digit'
                  })}
                </div>
              </div>

              <div className="flex gap-2">
                <Button variant="outline" className="flex-1" onClick={() => setShowBookModal(false)}>
                  Cancel
                </Button>
                <Button className="flex-1 bg-success hover:bg-success/90" onClick={handleBook}>
                  Confirm Booking
                </Button>
              </div>
            </div>
          </Card>
        </div>
      )}
    </>
  );
}
