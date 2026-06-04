import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { BarChart3, PieChart, TrendingUp, Clock, Activity } from 'lucide-react';

interface AnalyticsData {
  current_stats: {
    total: number;
    available: number;
    occupied: number;
    reserved: number;
    occupancy_rate: number;
  };
  hourly_occupancy: Array<{ hour: number; occupancy: number; available: number }>;
  average_duration: number;
  peak_hours: number[];
}

export default function Analytics() {
  const [analytics, setAnalytics] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const res = await fetch('http://localhost:8000/api/analytics');
        const data = await res.json();
        if (data.success) {
          setAnalytics(data.data);
        }
      } catch (error) {
        console.error('Error fetching analytics:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchAnalytics();
    const interval = setInterval(fetchAnalytics, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  if (loading || !analytics) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <Activity className="h-16 w-16 mx-auto text-primary animate-pulse mb-4" />
          <p className="font-orbitron text-xl">Loading Analytics...</p>
        </div>
      </div>
    );
  }

  const currentHour = new Date().getHours();
  const currentOccupancy = analytics.hourly_occupancy.find(h => h.hour === currentHour);

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-full bg-gradient-neon-cyan shadow-glow-cyan">
            <BarChart3 className="h-8 w-8 text-primary-foreground" />
          </div>
          <div>
            <h1 className="font-orbitron text-4xl font-bold neon-cyan tracking-wider">
              ANALYTICS DASHBOARD
            </h1>
            <p className="font-exo text-muted-foreground">Real-time parking insights</p>
          </div>
        </div>

        {/* Current Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <Card className="glass-card border-2 border-success/50 p-4">
            <div className="text-sm text-muted-foreground mb-1">Available</div>
            <div className="font-orbitron text-3xl font-bold text-success">
              {analytics.current_stats.available}
            </div>
          </Card>
          <Card className="glass-card border-2 border-destructive/50 p-4">
            <div className="text-sm text-muted-foreground mb-1">Occupied</div>
            <div className="font-orbitron text-3xl font-bold text-destructive">
              {analytics.current_stats.occupied}
            </div>
          </Card>
          <Card className="glass-card border-2 border-warning/50 p-4">
            <div className="text-sm text-muted-foreground mb-1">Reserved</div>
            <div className="font-orbitron text-3xl font-bold text-warning">
              {analytics.current_stats.reserved}
            </div>
          </Card>
          <Card className="glass-card border-2 border-primary/50 p-4">
            <div className="text-sm text-muted-foreground mb-1">Occupancy Rate</div>
            <div className="font-orbitron text-3xl font-bold text-primary">
              {analytics.current_stats.occupancy_rate}%
            </div>
          </Card>
        </div>

        {/* Pie Chart - Distribution */}
        <Card className="glass-card border-2 border-primary/30 p-6">
          <div className="flex items-center gap-2 mb-6">
            <PieChart className="h-6 w-6 text-primary" />
            <h2 className="font-orbitron text-2xl font-bold">Slot Distribution</h2>
          </div>
          
          <div className="flex items-center justify-center gap-8">
            <div className="relative w-64 h-64">
              <svg viewBox="0 0 100 100" className="transform -rotate-90">
                {/* Available - Green */}
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="hsl(var(--success))"
                  strokeWidth="20"
                  strokeDasharray={`${(analytics.current_stats.available / 80) * 251.2} 251.2`}
                  opacity="0.8"
                />
                {/* Occupied - Red */}
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="hsl(var(--destructive))"
                  strokeWidth="20"
                  strokeDasharray={`${(analytics.current_stats.occupied / 80) * 251.2} 251.2`}
                  strokeDashoffset={`-${(analytics.current_stats.available / 80) * 251.2}`}
                  opacity="0.8"
                />
                {/* Reserved - Yellow */}
                <circle
                  cx="50"
                  cy="50"
                  r="40"
                  fill="none"
                  stroke="hsl(var(--warning))"
                  strokeWidth="20"
                  strokeDasharray={`${(analytics.current_stats.reserved / 80) * 251.2} 251.2`}
                  strokeDashoffset={`-${((analytics.current_stats.available + analytics.current_stats.occupied) / 80) * 251.2}`}
                  opacity="0.8"
                />
              </svg>
              <div className="absolute inset-0 flex items-center justify-center">
                <div className="text-center">
                  <div className="font-orbitron text-4xl font-bold text-primary">80</div>
                  <div className="text-sm text-muted-foreground">Total Slots</div>
                </div>
              </div>
            </div>

            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-success"></div>
                <span className="font-exo">Available: {analytics.current_stats.available}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-destructive"></div>
                <span className="font-exo">Occupied: {analytics.current_stats.occupied}</span>
              </div>
              <div className="flex items-center gap-3">
                <div className="w-4 h-4 rounded bg-warning"></div>
                <span className="font-exo">Reserved: {analytics.current_stats.reserved}</span>
              </div>
            </div>
          </div>
        </Card>

        {/* Hourly Occupancy Chart */}
        <Card className="glass-card border-2 border-primary/30 p-6">
          <div className="flex items-center gap-2 mb-6">
            <TrendingUp className="h-6 w-6 text-primary" />
            <h2 className="font-orbitron text-2xl font-bold">24-Hour Occupancy Trend</h2>
          </div>
          
          <div className="relative h-64">
            <div className="absolute inset-0 flex items-end justify-between gap-1">
              {analytics.hourly_occupancy.map((data) => {
                const height = (data.occupancy / 80) * 100;
                const isCurrentHour = data.hour === currentHour;
                
                return (
                  <div key={data.hour} className="flex-1 flex flex-col items-center gap-1">
                    <div 
                      className={`w-full rounded-t transition-all ${
                        isCurrentHour ? 'bg-primary shadow-glow-cyan' : 'bg-primary/50'
                      }`}
                      style={{ height: `${height}%` }}
                    >
                      {isCurrentHour && (
                        <div className="text-xs font-bold text-center text-primary-foreground mt-1">
                          {data.occupancy}
                        </div>
                      )}
                    </div>
                    <div className={`text-xs ${isCurrentHour ? 'text-primary font-bold' : 'text-muted-foreground'}`}>
                      {data.hour}h
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </Card>

        {/* Key Metrics */}
        <div className="grid md:grid-cols-2 gap-4">
          <Card className="glass-card border-2 border-primary/30 p-6">
            <div className="flex items-center gap-3 mb-4">
              <Clock className="h-6 w-6 text-primary" />
              <h3 className="font-orbitron text-xl font-bold">Average Duration</h3>
            </div>
            <div className="text-center">
              <div className="font-orbitron text-5xl font-bold text-primary mb-2">
                {analytics.average_duration}
              </div>
              <div className="text-muted-foreground">minutes per parking session</div>
            </div>
          </Card>

          <Card className="glass-card border-2 border-primary/30 p-6">
            <div className="flex items-center gap-3 mb-4">
              <Activity className="h-6 w-6 text-primary" />
              <h3 className="font-orbitron text-xl font-bold">Peak Hours</h3>
            </div>
            <div className="flex flex-wrap gap-2 justify-center">
              {analytics.peak_hours.map((hour) => (
                <div 
                  key={hour}
                  className="px-4 py-2 rounded bg-primary/20 border border-primary/30"
                >
                  <span className="font-orbitron font-bold text-primary">{hour}:00</span>
                </div>
              ))}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
}
