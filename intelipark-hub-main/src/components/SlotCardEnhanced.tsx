import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Clock, MapPin, Zap, Timer, CheckCircle } from 'lucide-react';

interface SlotCardEnhancedProps {
  slot: {
    slot_id: number;
    status: 'available' | 'occupied' | 'reserved' | 'maintenance';
    zone: string;
    expected_free_time?: string;
    reserved_until?: string;
    prediction_confidence?: number;
    occupied_duration?: number;
  };
  onReserve?: (slotId: number) => void;
  onOccupy?: (slotId: number) => void;
  onFree?: (slotId: number) => void;
}

export function SlotCardEnhanced({ slot, onReserve, onOccupy, onFree }: SlotCardEnhancedProps) {
  const [countdown, setCountdown] = useState<string>('');
  const [tick, setTick] = useState(0);

  // Countdown timer
  useEffect(() => {
    const timer = setInterval(() => setTick(t => t + 1), 1000);
    return () => clearInterval(timer);
  }, []);

  useEffect(() => {
    const targetTime = slot.status === 'occupied' 
      ? slot.expected_free_time 
      : slot.status === 'reserved' 
      ? slot.reserved_until 
      : null;

    if (targetTime) {
      const remaining = new Date(targetTime).getTime() - Date.now();
      if (remaining > 0) {
        const minutes = Math.floor(remaining / 60000);
        const seconds = Math.floor((remaining % 60000) / 1000);
        setCountdown(`${minutes}m ${seconds}s`);
      } else {
        setCountdown('Expired');
      }
    }
  }, [tick, slot]);

  const getStatusColor = () => {
    switch (slot.status) {
      case 'available': return 'border-success bg-success/10';
      case 'occupied': return 'border-destructive bg-destructive/10';
      case 'reserved': return 'border-warning bg-warning/10';
      case 'maintenance': return 'border-muted bg-muted/10';
      default: return 'border-primary/30';
    }
  };

  const getStatusIcon = () => {
    switch (slot.status) {
      case 'available': return <CheckCircle className="h-8 w-8 text-success" />;
      case 'occupied': return <Clock className="h-8 w-8 text-destructive" />;
      case 'reserved': return <Timer className="h-8 w-8 text-warning" />;
      default: return <Zap className="h-8 w-8 text-muted" />;
    }
  };

  return (
    <Card className={`glass-card border-2 ${getStatusColor()} p-4 space-y-3 hover:shadow-elevated-neon transition-all`}>
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          {getStatusIcon()}
          <div>
            <h3 className="font-orbitron font-bold text-lg">SLOT_{slot.slot_id}</h3>
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

      {/* Countdown Timer */}
      {(slot.status === 'occupied' || slot.status === 'reserved') && countdown && (
        <div className="flex items-center justify-center gap-2 p-2 rounded bg-background/50">
          <Clock className="h-4 w-4 text-primary animate-pulse" />
          <span className="font-mono text-sm font-bold text-primary">
            {slot.status === 'occupied' ? 'Free in: ' : 'Expires in: '}
            {countdown}
          </span>
        </div>
      )}

      {/* ML Prediction */}
      {slot.prediction_confidence && slot.status === 'occupied' && (
        <div className="text-xs text-center p-2 rounded bg-primary/10 border border-primary/30">
          <span className="text-muted-foreground">Predicted availability: </span>
          <span className="font-bold text-primary">{Math.round(slot.prediction_confidence * 100)}%</span>
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {slot.status === 'available' && onReserve && (
          <Button 
            size="sm" 
            className="flex-1 font-orbitron text-xs"
            onClick={() => onReserve(slot.slot_id)}
          >
            <Timer className="h-3 w-3 mr-1" />
            RESERVE
          </Button>
        )}
        {slot.status === 'available' && onOccupy && (
          <Button 
            size="sm" 
            variant="outline"
            className="flex-1 font-orbitron text-xs"
            onClick={() => onOccupy(slot.slot_id)}
          >
            OCCUPY
          </Button>
        )}
        {(slot.status === 'occupied' || slot.status === 'reserved') && onFree && (
          <Button 
            size="sm" 
            variant="destructive"
            className="flex-1 font-orbitron text-xs"
            onClick={() => onFree(slot.slot_id)}
          >
            FREE UP
          </Button>
        )}
      </div>
    </Card>
  );
}
