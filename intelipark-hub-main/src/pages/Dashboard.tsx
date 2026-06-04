import { StatsCard } from '@/components/StatsCard';
import { SlotCard } from '@/components/SlotCard';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Car, Zap, Clock, Activity, ArrowRight, Calendar, MessageSquare, Target } from 'lucide-react';
import { useRealtimeParking } from '@/hooks/useRealtimeParking';
import { GateWidget } from '@/components/GateWidget';
import { useNavigate } from 'react-router-dom';

export default function Dashboard() {
  const navigate = useNavigate();
  const { parkingData, isConnected, refresh } = useRealtimeParking();
  const totalSlots = parkingData?.totalSlots ?? 80;
  const availableSlots = parkingData?.availableSlots ?? 0;
  const occupiedSlots = parkingData?.occupiedSlots ?? 0;
  const reservedSlots = parkingData?.reservedSlots ?? 0;
  const occupancyRate = parkingData?.occupancyRate ?? 0;
  const recentSlots = (parkingData?.slots ?? []).slice(0, 6);

  const stats = [
    {
      title: 'Total Slots',
      value: totalSlots,
      icon: Car,
      trend: { value: 5, isPositive: true }
    },
    {
      title: 'Available Now',
      value: availableSlots,
      icon: Zap,
      trend: { value: 12, isPositive: true }
    },
    {
      title: 'Reserved',
      value: reservedSlots,
      icon: Clock,
      trend: { value: 3, isPositive: false }
    },
    {
      title: 'Occupancy Rate',
      value: `${occupancyRate}%`,
      icon: Activity,
      trend: { value: 8, isPositive: false }
    }
  ];

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-8 animate-fade-in">
        {/* Hero HUD Display */}
        <div className="relative overflow-hidden rounded-2xl glass-card border-2 border-primary/50 p-8 shadow-elevated-neon">
          {/* Animated HUD Grid Background */}
          <div className="absolute inset-0 hud-grid opacity-20" />
          
          {/* Radar circles */}
          <div className="absolute top-1/2 right-10 -translate-y-1/2">
            <div className="relative w-32 h-32">
              <div className="absolute inset-0 rounded-full border-2 border-primary/30" />
              <div className="absolute inset-2 rounded-full border-2 border-primary/20" />
              <div className="absolute inset-4 rounded-full border-2 border-primary/10" />
              <div className="absolute inset-0 rounded-full border-t-2 border-primary animate-[spin_4s_linear_infinite]" />
            </div>
          </div>

          <div className="relative z-10 space-y-6 max-w-3xl">
            {/* Title with neon effect */}
            <div className="space-y-2">
              <div className="flex items-center gap-3">
                <Target className="h-8 w-8 text-primary" />
                <h1 className="font-orbitron font-black text-5xl md:text-6xl text-primary tracking-wider">
                  SMARTPARK
                </h1>
              </div>
              <p className="font-exo text-lg md:text-xl text-primary-glow/80 tracking-wide">
                Real-time IoT Parking Management System
              </p>
            </div>

            {/* Quick stats bar */}
            <div className="flex flex-wrap gap-6 items-center">
              <div className="flex items-baseline gap-2">
                <span className="font-orbitron text-4xl font-bold text-success">{availableSlots}</span>
                <span className="font-exo text-sm text-white/90 uppercase tracking-wider">spots free</span>
              </div>
              <div className="w-px h-8 bg-primary/30" />
              <div className="flex items-baseline gap-2">
                <span className="font-orbitron text-4xl font-bold text-primary">{totalSlots}</span>
                <span className="font-exo text-sm text-white/90 uppercase tracking-wider">total capacity</span>
              </div>
            </div>

            {/* Action buttons - Engine start style */}
            <div className="flex flex-wrap gap-4">
              <Button 
                size="lg" 
                onClick={() => navigate('/slots')}
                className="engine-start-btn font-orbitron tracking-wider bg-gradient-neon-cyan border-2 border-primary hover:border-primary-glow text-primary-foreground shadow-glow-cyan"
              >
                <Zap className="mr-2 h-5 w-5" />
                FIND PARKING
                <ArrowRight className="ml-2 h-5 w-5" />
              </Button>
              
              <Button 
                size="lg" 
                variant="outline"
                onClick={() => navigate('/reservations')}
                className="font-orbitron tracking-wider border-2 border-primary/50 hover:border-primary hover:bg-primary/10 hover:shadow-glow-cyan"
              >
                <Calendar className="mr-2 h-5 w-5" />
                MY BOOKINGS
              </Button>
            </div>
          </div>
        </div>

        {/* Stats Grid - Digital Odometer Style */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {stats.map((stat, index) => (
            <div key={stat.title} className="animate-fade-in" style={{ animationDelay: `${index * 100}ms` }}>
              <StatsCard {...stat} />
            </div>
          ))}
        </div>

        {/* Gate Control Widget */}
        <GateWidget />

        {/* Live Status Section */}
        <Card className="glass-card border-2 border-primary/30 p-6 space-y-6 shadow-elevated-neon">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="font-orbitron text-2xl font-bold neon-cyan tracking-wider mb-2">
                LIVE PARKING STATUS
              </h2>
              <p className="font-exo text-muted-foreground">SmartPark IoT Lot</p>
            </div>
            
            {/* Live indicator */}
            <div className="flex items-center gap-3 px-4 py-2 rounded-full glass-card border border-success/30">
              <div className="relative">
                <div className="w-3 h-3 bg-success rounded-full animate-pulse-glow" />
                <div className="absolute inset-0 w-3 h-3 bg-success rounded-full animate-radar-ping" />
              </div>
              <span className="font-orbitron text-sm font-medium text-success uppercase tracking-wider">
                {isConnected ? 'Live Updates' : 'Offline'}
              </span>
            </div>
          </div>

          {/* Slots Grid */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            {recentSlots.map((slot, index) => (
              <div key={slot.id} style={{ animationDelay: `${index * 50}ms` }}>
                <SlotCard 
                  slot={slot} 
                  onClick={slot.status === 'available' ? () => navigate('/slots') : undefined}
                />
              </div>
            ))}
          </div>

          <Button 
            variant="outline" 
            className="w-full font-orbitron tracking-wider border-2 border-primary/30 hover:border-primary hover:bg-primary/10 hover:shadow-glow-cyan"
            onClick={() => navigate('/slots')}
          >
            VIEW ALL SLOTS
            <ArrowRight className="ml-2 h-4 w-4" />
          </Button>
        </Card>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-2 gap-4">
          <Card 
            className="glass-card-hover p-6 space-y-4 cursor-pointer border-2 border-primary/30" 
            onClick={() => navigate('/reservations')}
          >
            <div className="p-3 rounded-full bg-gradient-neon-cyan w-fit shadow-glow-cyan">
              <Calendar className="h-8 w-8 text-primary-foreground" />
            </div>
            <h3 className="font-orbitron text-xl font-bold neon-cyan">RESERVE SLOT</h3>
            <p className="font-exo text-muted-foreground">
              Book your parking spot in advance with QR confirmation
            </p>
          </Card>
          
          <Card 
            className="glass-card-hover p-6 space-y-4 cursor-pointer border-2 border-primary/30" 
            onClick={() => navigate('/feedback')}
          >
            <div className="p-3 rounded-full bg-gradient-neon-green w-fit shadow-glow-green">
              <MessageSquare className="h-8 w-8 text-success-foreground" />
            </div>
            <h3 className="font-orbitron text-xl font-bold text-success">SHARE FEEDBACK</h3>
            <p className="font-exo text-muted-foreground">
              Help us improve by sharing your experience
            </p>
          </Card>
        </div>
      </div>
    </div>
  );
}
