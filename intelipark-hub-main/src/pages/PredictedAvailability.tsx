import { useEffect, useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Zap, Clock, TrendingUp, RefreshCw, Brain, MapPin } from 'lucide-react';

interface Prediction {
  slot_id: number;
  predicted_free_in: number;
  confidence: number;
  status: string;
}

interface Recommendation {
  slot_id: number;
  zone: string;
  free_in_minutes: number;
  confidence: number;
}

export default function PredictedAvailability() {
  const [predictions, setPredictions] = useState<Prediction[]>([]);
  const [recommendations, setRecommendations] = useState<Recommendation[]>([]);
  const [loading, setLoading] = useState(false);

  const fetchPredictions = async () => {
    setLoading(true);
    try {
      const [predRes, recRes] = await Promise.all([
        fetch('http://localhost:8000/api/predictions'),
        fetch('http://localhost:8000/api/recommendations')
      ]);

      const predData = await predRes.json();
      const recData = await recRes.json();

      if (predData.success) {
        // Filter to show only slots predicted to be free soon
        const soonFree = predData.data.predictions.filter(
          (p: Prediction) => p.predicted_free_in > 0 && p.predicted_free_in <= 30
        );
        setPredictions(soonFree);
      }

      if (recData.success) {
        setRecommendations(recData.data.soon_available || []);
      }
    } catch (error) {
      console.error('Error fetching predictions:', error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchPredictions();
    const interval = setInterval(fetchPredictions, 10000); // Refresh every 10s
    return () => clearInterval(interval);
  }, []);

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.8) return 'text-success';
    if (confidence >= 0.6) return 'text-warning';
    return 'text-muted-foreground';
  };

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 space-y-6 animate-fade-in">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-gradient-neon-cyan shadow-glow-cyan">
              <Brain className="h-8 w-8 text-primary-foreground" />
            </div>
            <div>
              <h1 className="font-orbitron text-4xl font-bold neon-cyan tracking-wider">
                PREDICTED AVAILABILITY
              </h1>
              <p className="font-exo text-muted-foreground">AI-powered slot predictions</p>
            </div>
          </div>
          <Button 
            onClick={fetchPredictions} 
            disabled={loading}
            className="font-orbitron tracking-wide"
          >
            <RefreshCw className={`h-4 w-4 mr-2 ${loading ? 'animate-spin' : ''}`} />
            REFRESH
          </Button>
        </div>

        {/* Smart Recommendations */}
        {recommendations.length > 0 && (
          <Card className="glass-card border-2 border-success/50 p-6 space-y-4">
            <div className="flex items-center gap-2">
              <TrendingUp className="h-6 w-6 text-success animate-pulse" />
              <h2 className="font-orbitron text-2xl font-bold text-success">
                SLOTS FREEING SOON
              </h2>
            </div>
            <p className="font-exo text-muted-foreground">
              These slots will be available shortly. Reserve them in advance!
            </p>
            
            <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
              {recommendations.map((rec) => (
                <Card key={rec.slot_id} className="glass-card border border-success/30 p-4 space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="font-orbitron font-bold text-lg text-success">
                      SLOT_{rec.slot_id}
                    </h3>
                    <Badge className="bg-success/20 text-success border-success/30">
                      Zone {rec.zone}
                    </Badge>
                  </div>
                  
                  <div className="flex items-center justify-center gap-2 p-3 rounded bg-success/10 border border-success/20">
                    <Clock className="h-5 w-5 text-success" />
                    <div className="text-center">
                      <div className="font-mono text-2xl font-bold text-success">
                        {rec.free_in_minutes}m
                      </div>
                      <div className="text-xs text-muted-foreground">Until Free</div>
                    </div>
                  </div>

                  <div className="text-center text-sm">
                    <span className="text-muted-foreground">Confidence: </span>
                    <span className={`font-bold ${getConfidenceColor(rec.confidence)}`}>
                      {Math.round(rec.confidence * 100)}%
                    </span>
                  </div>

                  <Button size="sm" className="w-full font-orbitron bg-success hover:bg-success/90">
                    <Zap className="h-4 w-4 mr-2" />
                    RESERVE NOW
                  </Button>
                </Card>
              ))}
            </div>
          </Card>
        )}

        {/* All Predictions */}
        <Card className="glass-card border-2 border-primary/30 p-6 space-y-4">
          <h2 className="font-orbitron text-2xl font-bold neon-cyan">
            ALL PREDICTIONS (Next 30 Minutes)
          </h2>
          
          {predictions.length === 0 ? (
            <div className="text-center py-12">
              <Brain className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
              <p className="font-exo text-muted-foreground">
                No slots predicted to be free in the next 30 minutes
              </p>
            </div>
          ) : (
            <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
              {predictions.map((pred) => (
                <Card key={pred.slot_id} className="glass-card border border-primary/30 p-4 space-y-2">
                  <div className="flex items-center justify-between">
                    <h4 className="font-orbitron font-bold">SLOT_{pred.slot_id}</h4>
                    <Badge variant="outline" className="text-xs">
                      {pred.status}
                    </Badge>
                  </div>
                  
                  <div className="text-center p-2 rounded bg-primary/10">
                    <div className="text-sm text-muted-foreground">Free in</div>
                    <div className="font-mono text-xl font-bold text-primary">
                      ~{pred.predicted_free_in}m
                    </div>
                  </div>

                  <div className="text-xs text-center">
                    <span className={`font-bold ${getConfidenceColor(pred.confidence)}`}>
                      {Math.round(pred.confidence * 100)}% confidence
                    </span>
                  </div>
                </Card>
              ))}
            </div>
          )}
        </Card>

        {/* How It Works */}
        <Card className="glass-card border-2 border-primary/30 p-6">
          <h3 className="font-orbitron text-xl font-bold mb-4">How Predictions Work</h3>
          <div className="grid md:grid-cols-3 gap-4">
            <div className="space-y-2">
              <div className="p-3 rounded-full bg-primary/20 w-fit">
                <Brain className="h-6 w-6 text-primary" />
              </div>
              <h4 className="font-orbitron font-semibold">ML Analysis</h4>
              <p className="text-sm text-muted-foreground">
                Our AI analyzes historical patterns, time of day, and current occupancy
              </p>
            </div>
            <div className="space-y-2">
              <div className="p-3 rounded-full bg-primary/20 w-fit">
                <Clock className="h-6 w-6 text-primary" />
              </div>
              <h4 className="font-orbitron font-semibold">Real-Time Data</h4>
              <p className="text-sm text-muted-foreground">
                Live countdown timers provide accurate availability predictions
              </p>
            </div>
            <div className="space-y-2">
              <div className="p-3 rounded-full bg-primary/20 w-fit">
                <TrendingUp className="h-6 w-6 text-primary" />
              </div>
              <h4 className="font-orbitron font-semibold">Smart Recommendations</h4>
              <p className="text-sm text-muted-foreground">
                Get notified about slots freeing soon so you can plan ahead
              </p>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
