/**
 * Real-time Connection Indicator Component
 * Shows WebSocket connection status with futuristic HUD styling
 */

import { useEffect, useState } from 'react';
import { Wifi, WifiOff, Activity } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useRealtimeSlots } from '@/hooks/useSmartPark';

interface RealtimeIndicatorProps {
  className?: string;
  showLabel?: boolean;
}

export const RealtimeIndicator = ({ className, showLabel = true }: RealtimeIndicatorProps) => {
  const { isConnected } = useRealtimeSlots();
  const [pulseCount, setPulseCount] = useState(0);

  // Pulse animation for connected state
  useEffect(() => {
    if (!isConnected) return;

    const interval = setInterval(() => {
      setPulseCount(prev => prev + 1);
    }, 2000);

    return () => clearInterval(interval);
  }, [isConnected]);

  return (
    <div className={cn(
      "flex items-center gap-2 px-3 py-1.5 rounded-lg border transition-all duration-300",
      isConnected 
        ? "bg-green-500/10 border-green-500/30 text-green-400" 
        : "bg-red-500/10 border-red-500/30 text-red-400",
      className
    )}>
      {/* Connection Icon */}
      <div className="relative">
        {isConnected ? (
          <>
            <Wifi className="h-4 w-4" />
            {/* Pulse rings for connected state */}
            <div 
              key={pulseCount}
              className="absolute inset-0 rounded-full border-2 border-green-400 animate-ping opacity-75"
            />
          </>
        ) : (
          <WifiOff className="h-4 w-4" />
        )}
      </div>

      {/* Status Text */}
      {showLabel && (
        <span className="text-xs font-medium">
          {isConnected ? 'LIVE' : 'OFFLINE'}
        </span>
      )}

      {/* Activity Indicator */}
      {isConnected && (
        <Activity className="h-3 w-3 animate-pulse" />
      )}
    </div>
  );
};

export default RealtimeIndicator;
