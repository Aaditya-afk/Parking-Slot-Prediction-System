import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Gauge, Send, MessageSquare } from 'lucide-react';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';
import smartparkApi from '@/services/smartparkAPI';

export default function Feedback() {
  const [rating, setRating] = useState(0);
  const [hoverRating, setHoverRating] = useState(0);
  const [feedbackType, setFeedbackType] = useState('');
  const [comment, setComment] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (submitting) return;

    if (rating === 0) {
      toast.error('Please select a rating');
      return;
    }
    if (!feedbackType) {
      toast.error('Please select feedback category');
      return;
    }
    if (!comment.trim()) {
      toast.error('Please enter your feedback');
      return;
    }

    try {
      setSubmitting(true);
      const res = await smartparkApi.submitFeedback({
        user_name: 'Guest User',
        user_email: 'guest@example.com',
        rating,
        category: feedbackType as any,
        message: comment.trim(),
      });
      if (res?.success) {
        toast.success('✓ Feedback submitted');
        setRating(0);
        setFeedbackType('');
        setComment('');
      } else {
        toast.error(res?.detail || 'Failed to submit feedback');
      }
    } catch (err: any) {
      toast.error(err?.message || 'Failed to submit feedback');
    } finally {
      setSubmitting(false);
    }
  };

  const ratingLabels = [
    { value: 1, label: 'CRITICAL', color: 'text-destructive' },
    { value: 2, label: 'POOR', color: 'text-warning' },
    { value: 3, label: 'AVERAGE', color: 'text-muted-foreground' },
    { value: 4, label: 'GOOD', color: 'text-success' },
    { value: 5, label: 'EXCELLENT', color: 'text-primary' },
  ];

  return (
    <div className="min-h-screen">
      <div className="container mx-auto px-4 py-8 max-w-3xl animate-fade-in">
        <div className="space-y-4 mb-8">
          <div className="flex items-center gap-3">
            <div className="p-3 rounded-full bg-gradient-neon-green shadow-glow-green">
              <MessageSquare className="h-8 w-8 text-success-foreground" />
            </div>
            <div>
              <h1 className="font-orbitron text-4xl font-bold text-success tracking-wider">
                SHARE FEEDBACK
              </h1>
              <p className="font-exo text-muted-foreground">Help us improve SmartPark system</p>
            </div>
          </div>
        </div>

        <Card className="glass-card border-2 border-primary/30 p-8 shadow-elevated-neon">
          {/* Animated background */}
          <div className="absolute inset-0 hud-grid opacity-5 rounded-xl" />

          <form onSubmit={handleSubmit} className="relative space-y-8">
            {/* Rating - Speedometer Style */}
            <div className="space-y-6">
              <Label className="font-orbitron text-lg font-semibold uppercase tracking-wider text-primary">
                Rate Your Experience
              </Label>
              
              {/* Speedometer dials */}
              <div className="grid grid-cols-5 gap-4 py-6">
                {ratingLabels.map((item) => (
                  <button
                    key={item.value}
                    type="button"
                    onClick={() => setRating(item.value)}
                    onMouseEnter={() => setHoverRating(item.value)}
                    onMouseLeave={() => setHoverRating(0)}
                    className={cn(
                      "flex flex-col items-center gap-3 p-4 rounded-xl transition-all duration-300 border-2",
                      (hoverRating || rating) >= item.value
                        ? 'glass-card border-primary shadow-glow-cyan scale-105'
                        : 'border-primary/20 hover:border-primary/40'
                    )}
                  >
                    <div className="relative">
                      <Gauge 
                        className={cn(
                          "h-12 w-12 transition-all duration-300",
                          (hoverRating || rating) >= item.value
                            ? item.color
                            : 'text-muted-foreground'
                        )}
                        style={{
                          transform: `rotate(${-90 + (item.value * 36)}deg)`
                        }}
                      />
                      <div className={cn(
                        "absolute inset-0 rounded-full blur-xl transition-opacity duration-300",
                        (hoverRating || rating) >= item.value ? 'opacity-30' : 'opacity-0',
                        item.value === 5 && 'bg-primary',
                        item.value === 4 && 'bg-success',
                        item.value === 3 && 'bg-muted-foreground',
                        item.value === 2 && 'bg-warning',
                        item.value === 1 && 'bg-destructive'
                      )} />
                    </div>
                    <span className={cn(
                      "font-orbitron text-xs font-bold tracking-wider transition-colors",
                      (hoverRating || rating) >= item.value
                        ? item.color
                        : 'text-muted-foreground'
                    )}>
                      {item.label}
                    </span>
                  </button>
                ))}
              </div>

              {rating > 0 && (
                <div className="p-4 rounded-lg glass-card border border-primary/30">
                  <p className="font-exo text-center text-primary">
                    {ratingLabels[rating - 1].label} - {
                      rating === 1 ? 'Critical issues reported' :
                      rating === 2 ? 'Needs significant improvement' :
                      rating === 3 ? 'Meets basic expectations' :
                      rating === 4 ? 'Exceeds expectations' :
                      'Outstanding performance!'
                    }
                  </p>
                </div>
              )}
            </div>

            {/* Feedback Type - Gear Selector Style */}
            <div className="space-y-3">
              <Label htmlFor="feedback-type" className="font-orbitron text-base font-semibold uppercase tracking-wider text-primary">
                Feedback Category
              </Label>
              <Select value={feedbackType} onValueChange={setFeedbackType}>
                <SelectTrigger 
                  id="feedback-type"
                  className="glass-card border-2 border-primary/30 hover:border-primary font-exo h-12"
                >
                  <SelectValue placeholder="SELECT CATEGORY" />
                </SelectTrigger>
                <SelectContent className="glass-card border-2 border-primary/30">
                  <SelectItem value="complaint" className="font-orbitron">COMPLAINT</SelectItem>
                  <SelectItem value="suggestion" className="font-orbitron">SUGGESTION</SelectItem>
                  <SelectItem value="general" className="font-orbitron">GENERAL</SelectItem>
                </SelectContent>
              </Select>
            </div>

            {/* Comment - Terminal Style */}
            <div className="space-y-3">
              <Label htmlFor="comment" className="font-orbitron text-base font-semibold uppercase tracking-wider text-primary">
                Your Message
              </Label>
              <Textarea
                id="comment"
                placeholder="Enter your feedback here..."
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                rows={6}
                className="glass-card border-2 border-primary/30 focus:border-primary font-exo resize-none terminal-text"
              />
              <div className="flex justify-between items-center">
                <p className="font-exo text-xs text-muted-foreground">
                  {comment.length}/1000 characters
                </p>
                <div className={cn(
                  "px-2 py-1 rounded text-xs font-orbitron",
                  comment.length > 900 ? 'bg-destructive/20 text-destructive' :
                  comment.length > 700 ? 'bg-warning/20 text-warning' :
                  'bg-success/20 text-success'
                )}>
                  {comment.length > 900 ? 'MAX' : comment.length > 700 ? 'HIGH' : 'OK'}
                </div>
              </div>
            </div>

            {/* Submit Button - Ignition Style */}
            <Button 
              type="submit" 
              className="w-full h-14 engine-start-btn font-orbitron text-lg tracking-wider bg-gradient-neon-cyan border-2 border-primary shadow-glow-cyan"
              size="lg"
              disabled={submitting}
            >
              <Send className="h-5 w-5 mr-3" />
              {submitting ? 'SENDING…' : 'TRANSMIT FEEDBACK'}
            </Button>
          </form>
        </Card>

        {/* Info Card - Dashboard Info Panel */}
        <Card className="glass-card border-2 border-success/30 p-6 mt-6 shadow-glow-green">
          <h3 className="font-orbitron font-semibold uppercase tracking-wider text-success mb-3">
            Why Feedback Matters
          </h3>
          <ul className="space-y-2 font-exo text-sm text-muted-foreground">
            <li className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-success" />
              Real-time issue detection and resolution
            </li>
            <li className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-success" />
              Drives next-generation feature development
            </li>
            <li className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-success" />
              Enhances user experience for all drivers
            </li>
            <li className="flex items-center gap-2">
              <div className="w-1 h-1 rounded-full bg-success" />
              Validates system performance metrics
            </li>
          </ul>
        </Card>
      </div>
    </div>
  );
}
