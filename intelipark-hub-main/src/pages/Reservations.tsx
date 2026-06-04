import { useEffect, useMemo, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import smartparkApi from '@/services/smartparkAPI';
import { QrCode, Calendar, Clock, MapPin, CheckCircle2, XCircle, Zap, RefreshCcw } from 'lucide-react';

interface AdvReservation {
  id: number;
  slot_number: string | null;
  start_time: string | null;
  end_time: string | null;
  status: 'active' | 'completed' | 'cancelled' | string;
  user_name?: string;
  user_email?: string;
}

function formatDT(iso?: string | null) {
  if (!iso) return '-';
  try { return new Date(iso).toLocaleString(); } catch { return iso; }
}

function msRemaining(endISO?: string | null) {
  if (!endISO) return 0;
  const end = new Date(endISO).getTime();
  const now = Date.now();
  return Math.max(0, end - now);
}

function fmtRemaining(ms: number) {
  const totalSec = Math.floor(ms / 1000);
  const h = Math.floor(totalSec / 3600);
  const m = Math.floor((totalSec % 3600) / 60);
  const s = totalSec % 60;
  if (h > 0) return `${h}h ${m}m ${s}s`;
  if (m > 0) return `${m}m ${s}s`;
  return `${s}s`;
}

export default function Reservations() {
  const [reservations, setReservations] = useState<AdvReservation[]>([]);
  const [loading, setLoading] = useState(false);
  const [tick, setTick] = useState(0);

  const refresh = async () => {
    setLoading(true);
    try {
      const rows = await smartparkApi.getAdvancedReservations(200);
      setReservations(rows || []);
    } catch (e) {
      console.error('refresh reservations failed', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { refresh(); }, []);
  // simple 1s tick for countdowns
  useEffect(() => {
    const t = setInterval(() => setTick((v) => (v + 1) % 1_000_000), 1000);
    return () => clearInterval(t);
  }, []);

  const activeReservations = useMemo(() => reservations.filter((r) => r.status === 'active'), [reservations, tick]);
  const pastReservations = useMemo(() => reservations.filter((r) => r.status !== 'active'), [reservations]);

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'active':
        return <Badge className="bg-gradient-neon-green border border-success/30 font-orbitron tracking-wider">{status.toUpperCase()}</Badge>;
      case 'completed':
        return <Badge variant="secondary" className="font-orbitron tracking-wider">{status.toUpperCase()}</Badge>;
      case 'cancelled':
        return <Badge className="bg-gradient-neon-red border border-destructive/30 font-orbitron tracking-wider">{status.toUpperCase()}</Badge>;
      default:
        return <Badge variant="outline" className="font-orbitron tracking-wider">{status.toUpperCase()}</Badge>;
    }
  };

  const onExtend = async (r: AdvReservation, minutes = 30) => {
    if (!r.end_time) return;
    const newEnd = new Date(new Date(r.end_time).getTime() + minutes * 60000).toISOString();
    const ok = await smartparkApi.modifyAdvancedReservation(r.id, { end_time: newEnd });
    if (ok) await refresh();
  };

  const onCancel = async (r: AdvReservation) => {
    const ok = await smartparkApi.cancelAdvancedReservation(r.id);
    if (ok) await refresh();
  };

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-8 animate-fade-in">
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-gradient-neon-cyan shadow-glow-cyan">
              <Calendar className="h-8 w-8 text-primary-foreground" />
            </div>
            <div className="flex-1 flex items-center justify-between">
              <div>
                <h1 className="font-orbitron text-4xl font-bold neon-cyan tracking-wider">MY RESERVATIONS</h1>
                <p className="font-exo text-muted-foreground">Manage your parking bookings</p>
              </div>
              <Button onClick={refresh} variant="outline" size="sm" className="font-orbitron tracking-wider border-2 border-primary/40 hover:border-primary">
                <RefreshCcw className="h-4 w-4 mr-2" /> Refresh
              </Button>
            </div>
          </div>
        </div>

        {/* Active Reservations */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="font-orbitron text-2xl font-semibold text-primary uppercase tracking-wider">Active Bookings</h2>
            <Button size="sm" className="engine-start-btn font-orbitron tracking-wider bg-gradient-neon-cyan border-2 border-primary shadow-glow-cyan">
              <Zap className="h-4 w-4 mr-2" /> NEW BOOKING
            </Button>
          </div>

          {loading ? (
            <Card className="glass-card border-2 border-primary/30 p-12 text-center">
              <p className="font-exo text-muted-foreground">Loading reservations...</p>
            </Card>
          ) : activeReservations.length === 0 ? (
            <Card className="glass-card border-2 border-primary/30 p-12 text-center">
              <p className="font-exo text-muted-foreground mb-6 text-lg">No active reservations</p>
              <Button className="engine-start-btn font-orbitron tracking-wider bg-gradient-neon-cyan border-2 border-primary shadow-glow-cyan">
                <Zap className="h-4 w-4 mr-2" /> RESERVE A SLOT
              </Button>
            </Card>
          ) : (
            <div className="grid md:grid-cols-2 gap-4">
              {activeReservations.map((reservation) => {
                const remain = msRemaining(reservation.end_time);
                return (
                  <Card key={reservation.id} className="glass-card border-2 border-primary/30 p-6 space-y-5 hover:border-primary hover:shadow-elevated-neon transition-all">
                    <div className="flex items-start justify-between">
                      <div className="space-y-2">
                        <h3 className="font-orbitron text-2xl font-bold neon-cyan">{reservation.slot_number || 'SLOT ?'}</h3>
                        <div className="flex items-center gap-2 text-sm font-exo text-muted-foreground">
                          <MapPin className="h-4 w-4 text-primary" />
                          <span>IoT Smart Parking System</span>
                        </div>
                      </div>
                      {getStatusBadge(reservation.status)}
                    </div>

                    {/* Time Info */}
                    <div className="space-y-3 p-4 rounded-lg glass-card border border-primary/20">
                      <div className="flex items-center gap-3">
                        <Clock className="h-5 w-5 text-success animate-neon-flicker" />
                        <div className="flex-1">
                          <p className="font-exo text-xs text-muted-foreground uppercase tracking-wider">Start Time</p>
                          <p className="font-orbitron text-sm text-primary">{formatDT(reservation.start_time)}</p>
                        </div>
                      </div>
                      <div className="h-px bg-primary/20" />
                      <div className="flex items-center gap-3">
                        <Clock className="h-5 w-5 text-warning animate-neon-flicker" />
                        <div className="flex-1">
                          <p className="font-exo text-xs text-muted-foreground uppercase tracking-wider">End Time</p>
                          <p className="font-orbitron text-sm text-primary">{formatDT(reservation.end_time)}</p>
                        </div>
                        <div className="font-mono text-xs text-primary/80">{fmtRemaining(remain)}</div>
                      </div>
                    </div>

                    {/* QR placeholder */}
                    <div className="relative p-8 rounded-lg glass-card border-2 border-primary/50 bg-gradient-to-br from-primary/10 to-primary/5">
                      <div className="absolute inset-0 hud-grid opacity-10 rounded-lg" />
                      <div className="relative text-center space-y-3">
                        <div className="inline-block p-4 rounded-lg bg-background/80 backdrop-blur-sm">
                          <QrCode className="h-32 w-32 mx-auto text-primary animate-pulse-glow" />
                        </div>
                        <p className="font-mono text-xs text-primary/80 tracking-wider">RES-{reservation.id}</p>
                        <p className="font-exo text-xs text-muted-foreground">Scan at gate entrance</p>
                      </div>
                    </div>

                    {/* Actions */}
                    <div className="flex gap-3">
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 font-orbitron tracking-wide border-2 border-success/30 hover:border-success hover:bg-success/10 hover:shadow-glow-green"
                        onClick={() => onExtend(reservation, 30)}
                      >
                        <CheckCircle2 className="h-4 w-4 mr-2" /> EXTEND 30m
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        className="flex-1 font-orbitron tracking-wide border-2 border-destructive/30 hover:border-destructive hover:bg-destructive/10 hover:shadow-glow-red"
                        onClick={() => onCancel(reservation)}
                      >
                        <XCircle className="h-4 w-4 mr-2" /> CANCEL
                      </Button>
                    </div>
                  </Card>
                );
              })}
            </div>
          )}
        </div>

        {/* Past Reservations */}
        <div className="space-y-4">
          <h2 className="font-orbitron text-2xl font-semibold text-primary uppercase tracking-wider">Booking History</h2>
          {pastReservations.length === 0 ? (
            <Card className="glass-card border-2 border-primary/30 p-8 text-center">
              <p className="font-exo text-muted-foreground">No past reservations</p>
            </Card>
          ) : (
            <div className="space-y-3">
              {pastReservations.map((reservation) => (
                <Card key={reservation.id} className="glass-card border-2 border-primary/20 p-5 hover:border-primary/40 transition-all">
                  <div className="flex items-center justify-between flex-wrap gap-4">
                    <div className="flex items-center gap-4">
                      <div className="p-3 rounded-lg glass-card border border-primary/30">
                        <Calendar className="h-6 w-6 text-primary" />
                      </div>
                      <div>
                        <p className="font-orbitron font-semibold text-lg neon-cyan">{reservation.slot_number || 'SLOT ?'}</p>
                        <p className="font-exo text-sm text-muted-foreground">
                          {formatDT(reservation.start_time)}  {formatDT(reservation.end_time)}
                        </p>
                      </div>
                    </div>
                    {getStatusBadge(reservation.status)}
                  </div>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
