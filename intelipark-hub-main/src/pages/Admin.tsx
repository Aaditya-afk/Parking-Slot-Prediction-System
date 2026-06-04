import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Activity, Star, MessageSquare, AlertTriangle, TrendingUp, Settings, Terminal } from 'lucide-react';
import { StatsCard } from '@/components/StatsCard';
import smartparkApi from '@/services/smartparkAPI';

export default function Admin() {
  const [summary, setSummary] = useState<any | null>(null);
  const [feedback, setFeedback] = useState<any[]>([]);
  const [recent, setRecent] = useState<any[]>([]);
  const [slots, setSlots] = useState<any[]>([]);
  const activeReservations = summary?.data?.active_bookings ?? 0;
  const totalFeedback = summary?.data?.total_feedback ?? 0;
  const averageRating = Number(summary?.data?.average_rating ?? 0);
  const totalSlots = slots.length;
  const freeSlots = slots.filter((s: any) => s.status === 'available').length;

  useEffect(() => {
    let mounted = true;
    const load = async () => {
      try {
        const [s, flist, r, sl] = await Promise.all([
          smartparkApi.getAdminSummary().catch(() => null),
          smartparkApi.getFeedbackList({ limit: 50 }).catch(() => ({ success: false, data: [] })),
          smartparkApi.getRecentReservations(20).catch(() => ({ success: false, data: [] })),
          smartparkApi.getSlots().catch(() => ({ slots: [] })),
        ]);
        if (!mounted) return;
        if (s?.success) setSummary(s);
        if (flist?.success) setFeedback(flist.data);
        if (r?.success) setRecent(r.data);
        if (sl?.slots) setSlots(sl.slots);
      } catch {}
    };
    load();
    const id = setInterval(load, 30000);
  }, []);

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-8 animate-fade-in">
        {/* Brand Header / Nav Context */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-primary/10 border-2 border-primary/40 ambient-red">
              <Settings className="h-7 w-7 text-primary" />
            </div>
            <div>
              <h1 className="font-orbitron text-2xl font-extrabold tracking-[0.2em] text-primary neon-red uppercase">SMARTPARK</h1>
              <p className="text-xs text-muted-foreground tracking-wide">Real-time IoT Parking Management System</p>
            </div>
          </div>
        </div>

        {/* Hero Section - Luxury Car Dashboard */}
        <Card className="glass-card border border-primary/20 bg-card/60 backdrop-blur-xl shadow-elevated-neon">
          <div className="p-6 md:p-10 grid grid-cols-1 md:grid-cols-2 gap-8 items-center">
            <div className="space-y-4">
              <h2 className="font-orbitron text-4xl md:text-5xl font-black tracking-[0.15em] text-primary uppercase">
                SMARTPARK
              </h2>
              <p className="text-sm text-foreground/70 tracking-wide font-medium">Real-time IoT Parking Management System</p>
              <div className="flex items-end gap-4 mt-6">
                <span className="font-orbitron text-6xl md:text-7xl font-black text-primary">{freeSlots}</span>
                <span className="font-exo text-xl md:text-2xl text-foreground/80 tracking-wider uppercase pb-2">SPOTS FREE</span>
              </div>
              <div className="flex gap-4 pt-4">
                <button className="px-6 py-3 rounded-lg border-2 border-primary/60 text-foreground bg-secondary hover:bg-secondary/80 transition-all electric-pulse font-orbitron tracking-wider uppercase text-sm">
                  ⚡ FIND PARKING
                </button>
                <button className="px-6 py-3 rounded-lg border border-border/50 text-foreground/90 bg-muted/20 hover:bg-muted/30 transition-all font-orbitron tracking-wider uppercase text-sm">
                  MY BOOKINGS
                </button>
              </div>
            </div>
            <div className="relative h-48 md:h-64 w-full rounded-2xl overflow-hidden border border-primary/30">
              <img 
                src="/red-sports-car.png" 
                alt="Red Sports Car"
                className="absolute inset-0 w-full h-full object-cover object-center"
                style={{
                  filter: 'contrast(1.1) saturate(1.2) brightness(0.95)'
                }}
              />
              {/* Soft red glow beneath car */}
              <div className="absolute inset-0 bg-gradient-to-t from-primary/15 via-transparent to-transparent pointer-events-none" />
              <div className="absolute inset-0 bg-gradient-to-l from-black/30 via-transparent to-transparent pointer-events-none" />
            </div>
          </div>
        </Card>

        {/* Metrics Cards Row - Digital Gauge Style */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
          <StatsCard
            title="TOTAL SLOTS"
            value={totalSlots}
            icon={Activity}
            trend={{ value: 5, isPositive: true }}
          />
          <StatsCard
            title="AVAILABLE NOW"
            value={freeSlots}
            icon={MessageSquare}
            trend={{ value: 13, isPositive: true }}
          />
          <StatsCard
            title="RESERVED"
            value={slots.filter((s: any) => s.status === 'reserved').length}
            icon={Star}
            trend={{ value: 3, isPositive: false }}
          />
          <StatsCard
            title="OCCUPANCY RATE"
            value={`${((slots.filter((s: any) => s.status === 'occupied').length / (totalSlots || 1)) * 100).toFixed(1)}%`}
            icon={TrendingUp}
            trend={{ value: 8, isPositive: false }}
          />
        </div>

        {/* Gate Control Bar - Luxury Style */}
        <Card className="glass-card border border-primary/20 bg-card/40 backdrop-blur-lg shadow-neon-card">
          <div className="flex items-center justify-between p-5">
            <div className="flex items-center gap-4">
              <div className="h-10 w-10 rounded-lg bg-primary/10 border border-primary/30 flex items-center justify-center">
                <span className="h-4 w-4 rounded-full bg-primary inline-block animate-pulse" />
              </div>
              <div>
                <p className="font-orbitron tracking-[0.1em] uppercase text-sm font-bold">Gate Control</p>
                <p className="text-xs text-muted-foreground tracking-wide">Status: UNKNOWN</p>
              </div>
            </div>
            <div className="flex items-center gap-2 text-xs text-success font-orbitron tracking-wider">
              <span className="h-2.5 w-2.5 rounded-full bg-success inline-block animate-pulse" /> LIVE
            </div>
          </div>
        </Card>

        {/* Tabs - Diagnostic Interface */}
        <Tabs defaultValue="slots" className="space-y-6">
          <TabsList className="grid w-full grid-cols-3 h-14 glass-card border-2 border-destructive/30">
            <TabsTrigger 
              value="slots"
              className="font-orbitron tracking-wider data-[state=active]:bg-gradient-neon-red data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow-red"
            >
              SLOT STATUS
            </TabsTrigger>
            <TabsTrigger 
              value="reservations"
              className="font-orbitron tracking-wider data-[state=active]:bg-gradient-neon-red data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow-red"
            >
              BOOKINGS
            </TabsTrigger>
            <TabsTrigger 
              value="feedback"
              className="font-orbitron tracking-wider data-[state=active]:bg-gradient-neon-red data-[state=active]:text-primary-foreground data-[state=active]:shadow-glow-red"
            >
              FEEDBACK
            </TabsTrigger>
          </TabsList>

          {/* Slots Tab - Realtime Monitoring */}
          <TabsContent value="slots" className="space-y-4">
            <Card className="glass-card border-2 border-primary/30 p-6">
              <div className="flex items-center gap-3 mb-6">
                <Terminal className="h-6 w-6 text-primary animate-pulse-glow" />
                <h3 className="font-orbitron text-xl font-semibold uppercase tracking-wider text-primary">
                  Real-time Sensor Monitoring
                </h3>
              </div>
              
              <div className="space-y-2">
                {slots.slice(0, 10).map((slot: any) => (
                  <div 
                    key={slot.id} 
                    className="flex items-center justify-between p-4 rounded-lg glass-card border border-primary/20 hover:border-primary/40 transition-all terminal-text"
                  >
                    <div className="flex items-center gap-4">
                      <div className={`w-3 h-3 rounded-full shadow-lg ${
                        slot.status === 'available' ? 'bg-success shadow-glow-green animate-pulse-glow' :
                        slot.status === 'occupied' ? 'bg-destructive shadow-glow-red animate-pulse-glow' :
                        slot.status === 'reserved' ? 'bg-warning shadow-glow-amber animate-pulse-glow' :
                        'bg-muted-foreground'
                      }`} />
                      <span className="font-orbitron font-medium">{slot.slotNumber}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <Badge className={
                        slot.status === 'available' ? 'bg-gradient-neon-green border border-success/30' :
                        slot.status === 'occupied' ? 'bg-gradient-neon-red border border-destructive/30' :
                        slot.status === 'reserved' ? 'bg-gradient-neon-amber border border-warning/30' :
                        'bg-muted border border-muted-foreground/30'
                      }>
                        <span className="font-orbitron text-xs tracking-wider">
                          {slot.status.toUpperCase()}
                        </span>
                      </Badge>
                      <span className="font-mono text-xs text-muted-foreground">
                        {slot.lastUpdated ? new Date(slot.lastUpdated).toLocaleTimeString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Reservations Tab - Logbook */}
          <TabsContent value="reservations" className="space-y-4">
            <Card className="glass-card border-2 border-primary/30 p-6">
              <h3 className="font-orbitron text-xl font-semibold uppercase tracking-wider text-primary mb-6">
                Recent Reservations
              </h3>
              <div className="space-y-3">
                {recent.map((reservation: any) => (
                  <div key={reservation.id} className="p-5 rounded-lg glass-card border border-primary/20 hover:border-primary/40 transition-all">
                    <div className="flex items-start justify-between mb-3">
                      <div>
                        <p className="font-orbitron font-semibold text-lg neon-cyan">
                          {reservation.slot_number}
                        </p>
                        <p className="font-mono text-sm text-muted-foreground terminal-text">
                          USER: {reservation.user_name}
                        </p>
                      </div>
                      <Badge className={
                        reservation.status === 'active' ? 'bg-gradient-neon-green border border-success/30' :
                        reservation.status === 'completed' ? 'bg-muted border border-muted-foreground/30' :
                        reservation.status === 'reserved' ? 'bg-gradient-neon-amber border border-warning/30' :
                        'bg-gradient-neon-red border border-destructive/30'
                      }>
                        <span className="font-orbitron text-xs tracking-wider">
                          {reservation.status.toUpperCase()}
                        </span>
                      </Badge>
                    </div>
                    <div className="space-y-1 font-mono text-xs text-muted-foreground terminal-text">
                      <p>START: {reservation.start_time ? new Date(reservation.start_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</p>
                      <p>END: {reservation.end_time ? new Date(reservation.end_time).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</p>
                      <p>CREATED: {reservation.created_at ? new Date(reservation.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}</p>
                    </div>
                  </div>
                ))}
              </div>
            </Card>
          </TabsContent>

          {/* Feedback Tab - Analytics Dashboard */}
          <TabsContent value="feedback" className="space-y-4">
            <Card className="glass-card border-2 border-primary/30 p-6">
              <div className="flex items-center justify-between mb-6">
                <h3 className="font-orbitron text-xl font-semibold uppercase tracking-wider text-primary">
                  User Feedback Analytics
                </h3>
                <div className="flex items-center gap-3 p-3 rounded-full glass-card border border-warning/30">
                  <Star className="h-6 w-6 text-warning animate-neon-flicker" />
                  <div>
                    <span className="font-orbitron text-2xl font-bold text-warning">
                      {averageRating.toFixed(1)}
                    </span>
                    <span className="font-exo text-xs text-muted-foreground ml-2">AVG</span>
                  </div>
                </div>
              </div>
              
              <div className="space-y-4">
                {feedback.map((fb: any) => (
                  <div key={fb.id} className="p-5 rounded-lg glass-card border border-primary/20 hover:border-primary/40 transition-all">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        {/* Rating bars - fuel gauge style */}
                        <div className="flex gap-1">
                          {[...Array(5)].map((_, i) => (
                            <div
                              key={i}
                              className={`w-2 h-8 rounded-full ${
                                i < fb.rating
                                  ? fb.rating >= 4 ? 'bg-gradient-neon-green shadow-glow-green' :
                                    fb.rating === 3 ? 'bg-gradient-neon-amber shadow-glow-amber' :
                                    'bg-gradient-neon-red shadow-glow-red'
                                  : 'bg-muted'
                              }`}
                            />
                          ))}
                        </div>
                        <Badge className={
                          fb.category === 'complaint' ? 'bg-gradient-neon-red border border-destructive/30' :
                          fb.category === 'suggestion' ? 'bg-gradient-neon-cyan border border-primary/30' :
                          'bg-muted border border-muted-foreground/30'
                        }>
                          <span className="font-orbitron text-xs tracking-wider">
                            {String(fb.category || 'GENERAL').toUpperCase()}
                          </span>
                        </Badge>
                      </div>
                      <span className="font-mono text-xs text-muted-foreground">
                        {fb.created_at ? new Date(fb.created_at).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata' }) : ''}
                      </span>
                    </div>
                    <p className="font-exo text-sm mb-2">{fb.message}</p>
                    <p className="font-mono text-xs text-muted-foreground terminal-text">
                      USER: {fb.user_name}
                    </p>
                  </div>
                ))}
              </div>
            </Card>

            {/* Alerts - Warning Panel */}
            <Card className="glass-card border-2 border-warning/50 p-6 shadow-glow-amber">
              <div className="flex items-start gap-4">
                <AlertTriangle className="h-6 w-6 text-warning shrink-0 mt-1 animate-pulse-glow" />
                <div>
                  <h4 className="font-orbitron font-semibold uppercase tracking-wider text-warning mb-2">
                    Action Required
                  </h4>
                  <p className="font-exo text-sm text-muted-foreground">
                    1 complaint detected regarding slot A-07 sensor malfunction. Maintenance dispatch recommended.
                  </p>
                </div>
              </div>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
