import { useMemo, useState } from 'react';
import { SlotCard } from '@/components/SlotCard';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useRealtimeParking } from '@/hooks/useRealtimeParking';
import { Filter, MapPin, Radar } from 'lucide-react';
import { SlotStatus } from '@/types/parking';
import BookingModal from '@/components/BookingModal';
import { SlotTimerModal } from '@/components/SlotTimerModal';

export default function Slots() {
  const [filterStatus, setFilterStatus] = useState<SlotStatus | 'all'>('all');
  const { parkingData, refresh, releaseSlot: releaseSlotApi } = useRealtimeParking();
  const lotAddress = 'IoT Smart Parking System';
  const slots = (parkingData?.slots ?? []) as Array<{ id: string; status: SlotStatus } & any>;
  const [bookingSlot, setBookingSlot] = useState<string | null>(null);
  const [selectedSlot, setSelectedSlot] = useState<any>(null);
  const [page, setPage] = useState(1);
  const pageSize = 20;

  const filteredSlots = useMemo(() => (
    filterStatus === 'all' ? slots : slots.filter(slot => slot.status === filterStatus)
  ), [slots, filterStatus]);

  const totalPages = Math.max(1, Math.ceil(filteredSlots.length / pageSize));
  const currentPage = Math.min(page, totalPages);
  const startIdx = (currentPage - 1) * pageSize;
  const endIdx = startIdx + pageSize;
  const pageSlots = filteredSlots.slice(startIdx, endIdx);

  const statusCounts = {
    all: slots.length,
    available: slots.filter(s => s.status === 'available').length,
    occupied: slots.filter(s => s.status === 'occupied').length,
    reserved: slots.filter(s => s.status === 'reserved').length,
    maintenance: slots.filter(s => s.status === 'maintenance').length,
  };

  const handleSlotClick = (slot: any) => {
    // Only allow clicking on available slots
    if (slot.status === 'available') {
      setBookingSlot(slot.slotNumber);
    }
    // Occupied, reserved, and maintenance slots are not clickable
  };

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-6 animate-fade-in">
        {/* Header with HUD styling */}
        <div className="space-y-4">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-primary/10 border-2 border-primary/40 ambient-red">
              <Radar className="h-8 w-8 text-primary animate-[spin_4s_linear_infinite]" />
            </div>
            <div>
              <h1 className="font-orbitron text-4xl font-extrabold text-primary neon-red tracking-[0.15em] uppercase">
                PARKING SLOTS
              </h1>
              <div className="flex items-center gap-2 text-muted-foreground font-exo tracking-wide">
                <MapPin className="h-4 w-4" />
                <span>{lotAddress}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Filters - Cockpit Control Panel Style */}
        <Card className="glass-card border border-primary/20 bg-card/50 backdrop-blur-lg shadow-neon-card p-5">
          <div className="flex items-center gap-4 flex-wrap">
            <div className="flex items-center gap-2">
              <Filter className="h-5 w-5 text-primary animate-pulse-glow" />
              <span className="font-orbitron text-sm font-bold uppercase tracking-[0.1em]">
                Filter Status:
              </span>
            </div>
            <div className="flex gap-2 flex-wrap">
              <Button
                variant={filterStatus === 'all' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('all')}
                className={
                  filterStatus === 'all'
                    ? 'font-orbitron tracking-wide bg-secondary/30 border-2 border-secondary hover:border-destructive/50'
                    : 'font-orbitron tracking-wide border-2 border-muted-foreground/30 hover:border-muted-foreground'
                }
              >
                ALL
                <Badge variant="secondary" className="ml-2 font-orbitron">
                  {statusCounts.all}
                </Badge>
              </Button>
              <Button
                variant={filterStatus === 'available' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('available')}
                className={
                  filterStatus === 'available'
                    ? 'font-orbitron tracking-wide bg-gradient-neon-green border-2 border-success shadow-glow-green'
                    : 'font-orbitron tracking-wide border-2 border-success/30 hover:border-success hover:shadow-glow-green'
                }
              >
                AVAILABLE
                <Badge variant="secondary" className="ml-2 font-orbitron">
                  {statusCounts.available}
                </Badge>
              </Button>
              <Button
                variant={filterStatus === 'occupied' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('occupied')}
                className={
                  filterStatus === 'occupied'
                    ? 'font-orbitron tracking-wide bg-gradient-neon-red border-2 border-destructive shadow-glow-red'
                    : 'font-orbitron tracking-wide border-2 border-destructive/30 hover:border-destructive hover:shadow-glow-red'
                }
              >
                OCCUPIED
                <Badge variant="secondary" className="ml-2 font-orbitron">
                  {statusCounts.occupied}
                </Badge>
              </Button>
              <Button
                variant={filterStatus === 'reserved' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('reserved')}
                className={
                  filterStatus === 'reserved'
                    ? 'font-orbitron tracking-wide bg-gradient-neon-amber border-2 border-warning shadow-glow-amber'
                    : 'font-orbitron tracking-wide border-2 border-warning/30 hover:border-warning hover:shadow-glow-amber'
                }
              >
                RESERVED
                <Badge variant="secondary" className="ml-2 font-orbitron">
                  {statusCounts.reserved}
                </Badge>
              </Button>
              <Button
                variant={filterStatus === 'maintenance' ? 'default' : 'outline'}
                size="sm"
                onClick={() => setFilterStatus('maintenance')}
                className="font-orbitron tracking-wide border-2 border-muted-foreground/30 hover:border-muted-foreground"
              >
                MAINTENANCE
                <Badge variant="secondary" className="ml-2 font-orbitron">
                  {statusCounts.maintenance}
                </Badge>
              </Button>
            </div>
          </div>
        </Card>

        {/* Slot Grid - Parking Layout */}
        <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-4">
          {pageSlots.map((slot, index) => (
            <div 
              key={slot.id} 
              className="animate-fade-in"
              style={{ animationDelay: `${index * 30}ms` }}
            >
              <SlotCard 
                slot={slot} 
                onClick={() => handleSlotClick(slot)} 
              />
            </div>
          ))}
        </div>

        {/* Pagination Controls */}
        <div className="flex items-center justify-between mt-2">
          <div className="text-sm font-exo text-muted-foreground">
            Showing {Math.min(filteredSlots.length, endIdx)} of {filteredSlots.length} slots
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={currentPage <= 1}
              className="font-orbitron tracking-wide"
            >
              Prev
            </Button>
            <span className="text-sm font-exo">
              Page {currentPage} / {totalPages}
            </span>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={currentPage >= totalPages}
              className="font-orbitron tracking-wide"
            >
              Next
            </Button>
          </div>
        </div>

        {filteredSlots.length === 0 && (
          <Card className="glass-card border border-primary/20 bg-card/50 backdrop-blur-lg shadow-neon-card p-12 text-center">
            <p className="font-exo text-muted-foreground text-lg tracking-wide">
              No slots found with the selected filter
            </p>
          </Card>
        )}

        {/* Legend - Infotainment Style */}
        <Card className="glass-card border border-primary/20 bg-card/50 backdrop-blur-lg shadow-neon-card p-6">
          <h3 className="font-orbitron font-bold uppercase tracking-[0.15em] mb-4 text-primary text-sm">
            System Legend
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="flex items-center gap-3 p-3 rounded-lg glass-card border border-success/30">
              <div className="w-6 h-6 rounded bg-gradient-neon-green shadow-glow-green" />
              <div>
                <p className="font-orbitron text-sm font-semibold text-success">AVAILABLE</p>
                <p className="font-exo text-xs text-muted-foreground">Ready to reserve</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg glass-card border border-destructive/30">
              <div className="w-6 h-6 rounded bg-gradient-neon-red shadow-glow-red" />
              <div>
                <p className="font-orbitron text-sm font-semibold text-destructive">OCCUPIED</p>
                <p className="font-exo text-xs text-muted-foreground">Currently in use</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg glass-card border border-warning/30">
              <div className="w-6 h-6 rounded bg-gradient-neon-amber shadow-glow-amber" />
              <div>
                <p className="font-orbitron text-sm font-semibold text-warning">RESERVED</p>
                <p className="font-exo text-xs text-muted-foreground">Booked by user</p>
              </div>
            </div>
            <div className="flex items-center gap-3 p-3 rounded-lg glass-card border border-muted-foreground/20">
              <div className="w-6 h-6 rounded bg-muted" />
              <div>
                <p className="font-orbitron text-sm font-semibold text-muted-foreground">MAINTENANCE</p>
                <p className="font-exo text-xs text-muted-foreground">Under repair</p>
              </div>
            </div>
          </div>
        </Card>

        {/* Booking Modal */}
        <BookingModal
          open={!!bookingSlot}
          slotNumber={bookingSlot}
          onClose={() => setBookingSlot(null)}
          onBooked={() => { setBookingSlot(null); refresh(); }}
        />

        {/* Timer Modal for occupied/reserved */}
        <SlotTimerModal
          open={!!selectedSlot}
          slot={selectedSlot}
          onClose={() => setSelectedSlot(null)}
          onReserve={(slotId) => {
            // Optional: wire an auto-reserve workflow here
            setSelectedSlot(null);
          }}
          onAutoFree={async (slotId) => {
            try {
              await releaseSlotApi(undefined, slotId);
            } catch (e) {
              // ignore errors; UI will refresh regardless
            } finally {
              setSelectedSlot((prev: any) => prev ? { ...prev, status: 'available' } : prev);
              refresh();
            }
          }}
        />
      </div>
    </div>
  );
}
