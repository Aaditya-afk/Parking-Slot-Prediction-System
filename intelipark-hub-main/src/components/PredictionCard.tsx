/**
 * ML Prediction Card Component
 * Displays AI-powered parking availability predictions
 */

import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Progress } from '@/components/ui/progress';
import { Brain, TrendingUp, Clock, Zap } from 'lucide-react';
import { cn } from '@/lib/utils';
import type { ForecastResponse } from '@/lib/api';

interface PredictionCardProps {
  prediction: ForecastResponse & {
    slot?: any;
    predictedStatus?: 'likely_free' | 'likely_occupied' | 'uncertain';
    confidenceColor?: string;
  };
  className?: string;
}

export const PredictionCard = ({ prediction, className }: PredictionCardProps) => {
  const probabilityPercent = Math.round(prediction.probability_free * 100);
  
  const getStatusColor = () => {
    if (prediction.probability_free > 0.7) return 'text-green-400 border-green-500/30 bg-green-500/10';
    if (prediction.probability_free < 0.3) return 'text-red-400 border-red-500/30 bg-red-500/10';
    return 'text-yellow-400 border-yellow-500/30 bg-yellow-500/10';
  };

  const getStatusText = () => {
    if (prediction.probability_free > 0.7) return 'Likely Free';
    if (prediction.probability_free < 0.3) return 'Likely Occupied';
    return 'Uncertain';
  };

  const getConfidenceIcon = () => {
    switch (prediction.confidence) {
      case 'high': return <TrendingUp className="h-3 w-3" />;
      case 'medium': return <Clock className="h-3 w-3" />;
      case 'low': return <Zap className="h-3 w-3" />;
      default: return null;
    }
  };

  return (
    <Card className={cn(
      "glass-card border-2 hover:border-primary/50 transition-all duration-300 p-4",
      getStatusColor(),
      className
    )}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <Brain className="h-4 w-4 text-primary" />
          <span className="font-semibold text-sm">{prediction.slot_label}</span>
        </div>
        
        <Badge variant="outline" className={cn("text-xs", prediction.confidenceColor)}>
          {getConfidenceIcon()}
          <span className="ml-1">{prediction.confidence.toUpperCase()}</span>
        </Badge>
      </div>

      {/* Prediction Status */}
      <div className="mb-3">
        <div className="flex items-center justify-between mb-1">
          <span className="text-xs text-muted-foreground">
            In {prediction.horizon_minutes} minutes
          </span>
          <span className="text-xs font-medium">
            {getStatusText()}
          </span>
        </div>
        
        {/* Probability Bar */}
        <Progress 
          value={probabilityPercent} 
          className="h-2 bg-muted/20"
        />
        
        <div className="flex justify-between mt-1">
          <span className="text-xs text-muted-foreground">Occupied</span>
          <span className="text-xs font-medium">{probabilityPercent}% Free</span>
          <span className="text-xs text-muted-foreground">Free</span>
        </div>
      </div>

      {/* Prediction Details */}
      <div className="space-y-1 text-xs text-muted-foreground">
        <div className="flex justify-between">
          <span>Confidence:</span>
          <span className={prediction.confidenceColor}>
            {prediction.confidence}
          </span>
        </div>
        
        <div className="flex justify-between">
          <span>Generated:</span>
          <span>{new Date(prediction.generated_at).toLocaleTimeString()}</span>
        </div>
      </div>

      {/* HUD-style decoration */}
      <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-primary animate-pulse opacity-60" />
    </Card>
  );
};

export default PredictionCard;
