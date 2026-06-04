import { useEffect, useMemo, useState } from 'react';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Input } from '@/components/ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import smartparkApi from '@/services/smartparkAPI';

export type BookingType = 'immediate' | 'scheduled' | 'hourly' | 'daily';

interface Props {
  open: boolean;
  slotNumber: string | null;
  onClose: () => void;
  onBooked: (result: any) => void;
}

export default function BookingModal({ open, slotNumber, onClose, onBooked }: Props) {
  const [bookingType, setBookingType] = useState<BookingType>('immediate');
  const [start, setStart] = useState<string>('');
  const [end, setEnd] = useState<string>('');
  const [durationMinutes, setDurationMinutes] = useState<number>(60);
  const [checking, setChecking] = useState(false);
  const [available, setAvailable] = useState<null | boolean>(null);
  const [mlInfo, setMlInfo] = useState<any>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Helpers to work with local datetime for <input type="datetime-local">
  const pad = (n: number) => String(n).padStart(2, '0');
  const formatLocal = (d: Date) => `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  const addMinutesLocal = (d: Date, m: number) => new Date(d.getTime() + m * 60000);

  useEffect(() => {
    if (!open) return;
    setAvailable(null);
    setError(null);
    const now = new Date();
    setStart(formatLocal(addMinutesLocal(now, 5)));
    setEnd(formatLocal(addMinutesLocal(now, 65)));
    setDurationMinutes(60);
    setBookingType('immediate');
  }, [open]);

  // When type switches to scheduled, seed sensible future times
  useEffect(() => {
    if (!open) return;
    if (bookingType === 'scheduled') {
      const now = new Date();
      const s = addMinutesLocal(now, 15);
      const e = addMinutesLocal(s, durationMinutes);
      setStart(formatLocal(s));
      setEnd(formatLocal(e));
      setAvailable(null);
    }
  }, [bookingType, durationMinutes, open]);

  // Keep end >= start for scheduled
  useEffect(() => {
    if (!open || bookingType !== 'scheduled') return;
    const s = new Date(start);
    const e = new Date(end);
    if (!isNaN(s.getTime()) && !isNaN(e.getTime()) && e <= s) {
      const e2 = addMinutesLocal(s, Math.max(15, durationMinutes));
      setEnd(formatLocal(e2));
    }
  }, [start, end, bookingType, durationMinutes, open]);

  const canCheck = useMemo(() => !!slotNumber && ((bookingType === 'scheduled' && start && end) || bookingType !== 'scheduled'), [bookingType, slotNumber, start, end]);
  const canSubmit = useMemo(() => {
    if (!slotNumber) return false;
    if (bookingType !== 'scheduled') return true;
    const now = new Date();
    const s = new Date(start);
    const e = new Date(end);
    if (isNaN(s.getTime()) || isNaN(e.getTime())) return false;
    return s > now && e > s; // must be in future and valid window
  }, [bookingType, slotNumber, start, end]);

  const handleCheck = async () => {
    if (!slotNumber) return;
    setChecking(true);
    setError(null);
    try {
      const startISO = bookingType === 'immediate'
        ? new Date().toISOString()
        : (start ? new Date(start).toISOString() : new Date().toISOString());
      const endISO = bookingType === 'immediate'
        ? new Date(Date.now() + durationMinutes * 60000).toISOString()
        : (end ? new Date(end).toISOString() : new Date(Date.now() + durationMinutes * 60000).toISOString());
      const res = await smartparkApi.checkAvailability(slotNumber, startISO, endISO);
      setAvailable(res?.available ?? null);
      setMlInfo(res?.ml ?? null);
    } catch (e: any) {
      setError(e?.message || 'Failed to check availability');
    } finally {
      setChecking(false);
    }
  };

  const handleConfirm = async () => {
    if (!slotNumber) return;
    setSubmitting(true);
    setError(null);
    try {
      const payload: any = {
        slot_number: slotNumber,
        booking_type: bookingType,
        user_name: 'Guest User',
        user_email: 'guest@example.com',
      };
      
      if (bookingType === 'immediate' || bookingType === 'hourly' || bookingType === 'daily') {
        payload.duration_minutes = durationMinutes;
        if (bookingType !== 'immediate') {
          // Convert datetime-local (local tz) to ISO (UTC)
          const startDate = new Date(start);
          if (isNaN(startDate.getTime())) {
            throw new Error('Invalid start time');
          }
          payload.start_time = startDate.toISOString();
        }
      } else {
        // Scheduled booking - validate both times
        const startDate = new Date(start); // interpret as local
        const endDate = new Date(end);
        
        if (isNaN(startDate.getTime())) {
          throw new Error('Invalid start time');
        }
        if (isNaN(endDate.getTime())) {
          throw new Error('Invalid end time');
        }
        
        payload.start_time = startDate.toISOString();
        payload.end_time = endDate.toISOString();
      }
      
      console.log('📤 Sending booking payload:', payload);
      const result = await smartparkApi.createAdvancedBooking(payload);
      onBooked(result);
      onClose();
    } catch (e: any) {
      console.error('❌ Booking error:', e);
      setError(e?.message || 'Failed to create booking');
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) onClose(); }}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>New Booking {slotNumber ? `for ${slotNumber}` : ''}</DialogTitle>
        </DialogHeader>

        <div className="space-y-4">
          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>Booking Type</Label>
              <Select value={bookingType} onValueChange={(v) => setBookingType(v as BookingType)}>
                <SelectTrigger><SelectValue placeholder="Select" /></SelectTrigger>
                <SelectContent>
                  <SelectItem value="immediate">Immediate</SelectItem>
                  <SelectItem value="scheduled">Scheduled</SelectItem>
                  <SelectItem value="hourly">Hourly</SelectItem>
                  <SelectItem value="daily">Daily</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div>
              <Label>Duration (minutes)</Label>
              <Input type="number" min={15} max={1440} value={durationMinutes} onChange={(e) => setDurationMinutes(parseInt(e.target.value || '60', 10))} disabled={bookingType === 'scheduled'} />
            </div>
          </div>

          <div className="grid grid-cols-2 gap-3">
            <div>
              <Label>{bookingType === 'immediate' ? 'Start time' : 'Start time'}</Label>
              <Input type="datetime-local" value={start} onChange={(e) => setStart(e.target.value)} disabled={bookingType === 'immediate'} />
            </div>
            <div>
              <Label>End time</Label>
              <Input type="datetime-local" value={end} onChange={(e) => setEnd(e.target.value)} disabled={bookingType !== 'scheduled'} />
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button variant="outline" onClick={handleCheck} disabled={!canCheck || checking}>
              {checking ? 'Checking…' : 'Check Availability'}
            </Button>
            {available === true && <Badge className="bg-green-600">Available</Badge>}
            {available === false && <Badge className="bg-red-600">Unavailable</Badge>}
            {mlInfo?.prediction && (
              <Badge variant="secondary">ML: {mlInfo.prediction} ({mlInfo.confidence})</Badge>
            )}
          </div>

          {bookingType === 'scheduled' && (
            <div className="text-xs text-muted-foreground">
              Start must be in the future. End must be after start.
            </div>
          )}
          {error && <div className="text-sm text-red-500">{error}</div>}

          <div className="flex justify-end gap-2 pt-2">
            <Button variant="outline" onClick={onClose}>Cancel</Button>
            <Button onClick={handleConfirm} disabled={submitting || !canSubmit}>{submitting ? 'Booking…' : 'Confirm Booking'}</Button>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
