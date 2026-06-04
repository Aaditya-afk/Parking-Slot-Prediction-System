import { ParkingSlot } from '@/types/parking';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Car, Clock, Wrench, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';

interface SlotCardProps {
  slot: ParkingSlot;
  onClick?: () => void;
}

export function SlotCard({ slot, onClick }: SlotCardProps) {
  const getStatusConfig = () => {
    switch (slot.status) {
      case 'available':
        return {
          icon: Zap,
          label: 'AVAILABLE',
          cardClass: 'border-success/40 bg-success/5 hover:border-success hover:shadow-glow-green',
          iconClass: 'text-success',
          glowClass: 'shadow-glow-green',
          badgeClass: 'bg-gradient-neon-green text-success-foreground border-success/30',
        };
      case 'occupied':
        return {
          icon: Car,
          label: 'OCCUPIED',
          cardClass: 'border-destructive/50 bg-destructive/5',
          iconClass: 'text-destructive',
          glowClass: 'shadow-glow-red',
          badgeClass: 'bg-gradient-neon-red text-destructive-foreground border-destructive/30',
        };
      case 'reserved':
        return {
          icon: Clock,
          label: 'RESERVED',
          cardClass: 'border-warning/50 bg-warning/5',
          iconClass: 'text-warning',
          glowClass: 'shadow-glow-amber',
          badgeClass: 'bg-gradient-neon-amber text-warning-foreground border-warning/30',
        };
      case 'maintenance':
        return {
          icon: Wrench,
          label: 'MAINTENANCE',
          cardClass: 'border-muted-foreground/30 bg-muted/5',
          iconClass: 'text-muted-foreground',
          glowClass: '',
          badgeClass: 'bg-muted text-muted-foreground border-muted-foreground/30',
        };
    }
  };

  const config = getStatusConfig();
  const StatusIcon = config.icon;
  // Only available slots are clickable
  const isClickable = !!onClick && slot.status === 'available';

  return (
    <Card
      className={cn(
        'relative overflow-hidden transition-all duration-300 border-2 backdrop-blur-sm',
        config.cardClass,
        isClickable && 'cursor-pointer hover:scale-105 headlight-glow',
        'animate-fade-in glass-card'
      )}
      onClick={isClickable ? onClick : undefined}
    >
      {/* Animated background grid for available slots */}
      {slot.status === 'available' && (
        <div className="absolute inset-0 opacity-30 hud-grid" />
      )}

      <div className="relative p-5 flex flex-col items-center justify-center space-y-3">
        {/* Icon with glow effect */}
        <div className={cn(
          "relative p-3 rounded-full border-2 transition-all duration-300",
          config.cardClass,
          config.glowClass
        )}>
          <StatusIcon className={cn("h-8 w-8", config.iconClass)} />
          
          {/* Animated pulse for available slots */}
          {slot.status === 'available' && (
            <div className="absolute inset-0 rounded-full border-2 border-success animate-radar-ping" />
          )}
        </div>

        {/* Slot Number - Odometer Style */}
        <div className="text-center space-y-1">
          <p className="font-orbitron font-bold text-xl tracking-wider text-primary">
            {slot.slotNumber}
          </p>
          <Badge className={cn(
            "text-[10px] font-orbitron tracking-widest border-2",
            config.badgeClass
          )}>
            {config.label}
          </Badge>
        </div>
        
        {/* Prediction Timer */}
        {slot.predictedFreeInMinutes !== undefined && slot.predictedFreeInMinutes > 0 && (
          <div
            className={cn(
              "flex items-center gap-1.5 px-2 py-1 rounded-full border",
              slot.status === 'occupied' && 'bg-destructive/10 border-destructive/30',
              slot.status === 'reserved' && 'bg-warning/10 border-warning/30',
              slot.status === 'available' && 'bg-success/10 border-success/30'
            )}
          >
            <Clock
              className={cn(
                "h-3 w-3 animate-neon-flicker",
                slot.status === 'occupied' && 'text-destructive',
                slot.status === 'reserved' && 'text-white',
                slot.status === 'available' && 'text-success'
              )}
            />
            <span
              className={cn(
                "text-xs font-exo",
                slot.status === 'occupied' && 'text-destructive',
                slot.status === 'reserved' && 'text-white',
                slot.status === 'available' && 'text-success'
              )}
            >
              ~{slot.predictedFreeInMinutes}min
            </span>
          </div>
        )}
      </div>
      {/* Reserved Until Info */}
      {slot.status === 'reserved' && slot.reservedUntil && (
        <div className="absolute top-2 right-2 px-2 py-1 rounded bg-warning/20 border border-warning/30 backdrop-blur-sm">
          <div className="text-[10px] font-exo text-white">
            Until {new Date(slot.reservedUntil).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
          </div>
        </div>
      )}

      {/* Car animation overlay for occupied */}
      {slot.status === 'occupied' && (
        <div className="absolute bottom-0 left-0 right-0 h-1 bg-gradient-neon-red opacity-50 animate-pulse-glow" />
      )}
    </Card>
  );
}
