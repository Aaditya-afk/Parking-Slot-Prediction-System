/**
 * System Status Card Component
 * Displays real-time system health and Arduino connection status
 */

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { 
  Shield, 
  Database, 
  Cpu, 
  Wifi, 
  AlertTriangle, 
  CheckCircle, 
  XCircle,
  RefreshCw
} from 'lucide-react';
import { cn } from '@/lib/utils';
import { useSystemStatus, useHealth } from '@/hooks/useSmartPark';

interface SystemStatusCardProps {
  className?: string;
}

export const SystemStatusCard = ({ className }: SystemStatusCardProps) => {
  const { data: systemStatus, isLoading: statusLoading, refetch: refetchStatus } = useSystemStatus();
  const { data: health, isLoading: healthLoading } = useHealth();

  const isLoading = statusLoading || healthLoading;

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircle className="h-4 w-4 text-green-400" />;
      case 'warning':
        return <AlertTriangle className="h-4 w-4 text-yellow-400" />;
      case 'critical':
      case 'error':
        return <XCircle className="h-4 w-4 text-red-400" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'text-green-400 border-green-500/30 bg-green-500/10';
      case 'warning':
        return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
      case 'critical':
      case 'error':
        return 'text-red-400 border-red-500/30 bg-red-500/10';
      default:
        return 'text-gray-400 border-gray-500/30 bg-gray-500/10';
    }
  };

  if (isLoading) {
    return (
      <Card className={cn("glass-card border-2 p-4 animate-pulse", className)}>
        <div className="space-y-3">
          <div className="h-4 bg-muted/20 rounded" />
          <div className="h-3 bg-muted/20 rounded w-3/4" />
          <div className="h-3 bg-muted/20 rounded w-1/2" />
        </div>
      </Card>
    );
  }

  const overallStatus = systemStatus?.overall_status || 'unknown';

  return (
    <Card className={cn(
      "glass-card border-2 p-4 transition-all duration-300",
      getStatusColor(overallStatus),
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <Shield className="h-5 w-5 text-primary" />
          <h3 className="font-semibold">System Status</h3>
        </div>
        
        <div className="flex items-center gap-2">
          <Badge variant="outline" className={getStatusColor(overallStatus)}>
            {getStatusIcon(overallStatus)}
            <span className="ml-1">{overallStatus.toUpperCase()}</span>
          </Badge>
          
          <Button
            variant="ghost"
            size="sm"
            onClick={() => refetchStatus()}
            className="h-8 w-8 p-0"
          >
            <RefreshCw className="h-3 w-3" />
          </Button>
        </div>
      </div>

      {/* Component Status */}
      <div className="space-y-3">
        {/* Database */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Database className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Database</span>
          </div>
          {getStatusIcon(systemStatus?.components?.database || 'unknown')}
        </div>

        {/* Sensors */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Cpu className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Sensors</span>
          </div>
          {getStatusIcon(systemStatus?.components?.sensors || 'unknown')}
        </div>

        {/* Arduino Connection */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Wifi className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">Arduino</span>
          </div>
          {health?.serial_connected ? (
            <CheckCircle className="h-4 w-4 text-green-400" />
          ) : (
            <XCircle className="h-4 w-4 text-red-400" />
          )}
        </div>
      </div>

      {/* Metrics */}
      {systemStatus?.metrics && (
        <div className="mt-4 pt-3 border-t border-border/50">
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-muted-foreground">Sensor Events</span>
              <div className="font-medium">{systemStatus.metrics.recent_sensor_events}</div>
            </div>
            
            <div>
              <span className="text-muted-foreground">Errors</span>
              <div className="font-medium">{systemStatus.metrics.recent_errors}</div>
            </div>
            
            <div>
              <span className="text-muted-foreground">WebSockets</span>
              <div className="font-medium">{health?.active_websockets || 0}</div>
            </div>
            
            <div>
              <span className="text-muted-foreground">Uptime</span>
              <div className="font-medium">{systemStatus.metrics.uptime_hours}h</div>
            </div>
          </div>
        </div>
      )}

      {/* Last Check */}
      <div className="mt-3 pt-2 border-t border-border/50">
        <div className="text-xs text-muted-foreground">
          Last checked: {systemStatus?.checked_at ? 
            new Date(systemStatus.checked_at).toLocaleTimeString() : 
            'Unknown'
          }
        </div>
      </div>

      {/* HUD decoration */}
      <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary animate-pulse opacity-60" />
    </Card>
  );
};

export default SystemStatusCard;
