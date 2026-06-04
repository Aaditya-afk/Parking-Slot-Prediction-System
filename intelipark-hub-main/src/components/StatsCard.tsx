import { Card } from '@/components/ui/card';
import { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useEffect, useState } from 'react';

interface StatsCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  className?: string;
}

export function StatsCard({ title, value, icon: Icon, trend, className }: StatsCardProps) {
  const [displayValue, setDisplayValue] = useState(0);
  const numericValue = typeof value === 'string' ? parseFloat(value) : value;

  // Odometer counter animation
  useEffect(() => {
    if (typeof numericValue === 'number' && !isNaN(numericValue)) {
      let start = 0;
      const end = numericValue;
      const duration = 1500;
      const increment = end / (duration / 16);

      const timer = setInterval(() => {
        start += increment;
        if (start >= end) {
          setDisplayValue(end);
          clearInterval(timer);
        } else {
          setDisplayValue(Math.floor(start));
        }
      }, 16);

      return () => clearInterval(timer);
    }
  }, [numericValue]);

  return (
    <Card className={cn(
      'glass-card-hover relative overflow-hidden group bg-card/50 border border-primary/20 backdrop-blur-lg shadow-neon-card',
      className
    )}>
      {/* Subtle inner glow */}
      <div className="absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-transparent opacity-50" />
      
      <div className="relative p-6 flex items-center justify-between">
        <div className="space-y-3 flex-1">
          {/* Title - Uppercase Gauge Style */}
          <p className="text-[10px] font-orbitron uppercase tracking-[0.15em] text-foreground/60 font-bold">
            {title}
          </p>
          
          {/* Value - Digital Gauge Number */}
          <div className="flex items-baseline gap-2">
            <p className="text-5xl font-orbitron font-black text-primary transition-all duration-300 group-hover:scale-105">
              {typeof value === 'string' && value.includes('%') 
                ? value 
                : displayValue
              }
            </p>
          </div>
          
          {/* Trend Indicator - Refined */}
          {trend && (
            <div className={cn(
              'flex items-center gap-1.5 text-xs font-orbitron font-semibold px-3 py-1 rounded-md w-fit tracking-wider',
              trend.isPositive 
                ? 'bg-success/15 text-success border border-success/40' 
                : 'bg-primary/15 text-primary border border-primary/40'
            )}>
              <span className="text-sm">{trend.isPositive ? '↑' : '↓'}</span>
              <span>{Math.abs(trend.value)}%</span>
            </div>
          )}
        </div>
        
        {/* Icon without glow */}
        <div className="relative">
          {/* Icon container */}
          <div className="relative p-3 rounded-xl bg-primary/10 border border-primary/30 group-hover:border-primary/50 transition-all duration-300">
            <Icon className="h-6 w-6 text-primary group-hover:scale-110 transition-transform duration-300" />
          </div>
        </div>
      </div>

      {/* Bottom accent line with glow */}
      <div className="absolute bottom-0 left-0 right-0 h-[2px] bg-gradient-to-r from-transparent via-primary to-transparent opacity-50 group-hover:opacity-100 transition-all duration-300" />
    </Card>
  );
}
