import * as React from 'react';
import { useEffect, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { DoorOpen, DoorClosed, Wifi } from 'lucide-react';
import smartparkApi from '@/services/smartparkAPI';

type GateState = 'open' | 'closed' | 'moving' | 'error' | 'unknown';

export const GateWidget: React.FC = () => {
  const [gateState, setGateState] = useState<GateState>('unknown');
  const [lastEvent, setLastEvent] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  // Connect to WebSocket and listen to gate events
  useEffect(() => {
    const ws = smartparkApi.connectWebSocket((data) => {
      if (data.type === 'gate_event') {
        const action = (data.data?.action || '').toLowerCase();
        const status = (data.data?.status || '').toLowerCase();
        setLastEvent(`${action} (${status})`);
        if (status === 'success') {
          setGateState(action === 'open' ? 'open' : 'closed');
        } else if (status === 'failed') {
          setGateState('error');
        }
        setBusy(false);
      }
    });

    wsRef.current = ws;
    setConnected(!!ws);

    return () => {
      if (wsRef.current) wsRef.current.close();
    };
  }, []);

  const openGate = async () => {
    try {
      setBusy(true);
      setGateState('moving');
      await smartparkApi.openGate();
    } catch (e) {
      setBusy(false);
      setGateState('error');
    }
  };

  const closeGate = async () => {
    try {
      setBusy(true);
      setGateState('moving');
      await smartparkApi.closeGate();
    } catch (e) {
      setBusy(false);
      setGateState('error');
    }
  };

  const StatusIcon = gateState === 'open' ? DoorOpen : gateState === 'closed' ? DoorClosed : Wifi;

  return (
    <Card className="glass-card border-2 border-primary/30 p-5">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <div className="p-3 rounded-full bg-gradient-neon-cyan shadow-glow-cyan">
            <StatusIcon className="h-6 w-6 text-primary-foreground" />
          </div>
          <div>
            <h3 className="font-orbitron text-lg font-bold neon-cyan">Gate Control</h3>
            <p className="font-exo text-sm text-muted-foreground">
              Status: {gateState.toUpperCase()} {lastEvent ? `• Last: ${lastEvent}` : ''}
            </p>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs font-exo text-muted-foreground">{connected ? 'LIVE' : 'OFFLINE'}</span>
        </div>
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3">
        <Button onClick={openGate} disabled={busy} className="bg-green-500 hover:bg-green-600 text-white">
          Open Gate
        </Button>
        <Button onClick={closeGate} disabled={busy} variant="outline">
          Close Gate
        </Button>
      </div>
    </Card>
  );
};

export default GateWidget;
