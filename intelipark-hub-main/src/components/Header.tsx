import { useNavigate, useLocation } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Gauge, LayoutDashboard, Car, Calendar, MessageSquare, Settings } from 'lucide-react';
import { cn } from '@/lib/utils';

export function Header() {
  const navigate = useNavigate();
  const location = useLocation();

  const navItems = [
    { path: '/', label: 'Dashboard', icon: Gauge },
    { path: '/slots', label: 'Parking', icon: Car },
    { path: '/reservations', label: 'Bookings', icon: Calendar },
    { path: '/feedback', label: 'Feedback', icon: MessageSquare },
    { path: '/admin', label: 'Admin', icon: Settings },
  ];

  return (
    <header className="sticky top-0 z-50 w-full border-b border-primary/20 bg-card/80 backdrop-blur-xl shadow-elevated-neon">
      <div className="container flex h-20 items-center justify-between px-6">
        {/* Logo - Luxury Car Badge Style */}
        <div 
          className="flex items-center gap-3 cursor-pointer group"
          onClick={() => navigate('/')}
        >
          <div className="relative">
            {/* Outer red glow ring */}
            <div className="absolute inset-0 rounded-full bg-gradient-neon-red opacity-20 blur-xl group-hover:opacity-40 transition-all duration-300" />
            
            {/* Badge */}
            <div className="relative p-3 rounded-full bg-primary/10 border-2 border-primary/40 shadow-glow-red group-hover:border-primary transition-all duration-300 ambient-red">
              <Gauge className="h-7 w-7 text-primary group-hover:rotate-12 transition-transform duration-300" />
            </div>
          </div>
          
          <div className="flex flex-col">
            <span className="font-orbitron font-black text-2xl text-primary neon-red tracking-[0.2em] uppercase">
              SMARTPARK
            </span>
            <span className="font-exo text-[10px] text-muted-foreground tracking-[0.15em] uppercase">
              IOT PARKING SYSTEM
            </span>
          </div>
        </div>

        {/* Navigation - Desktop */}
        <nav className="hidden md:flex items-center gap-3">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = location.pathname === item.path;
            return (
              <Button
                key={item.path}
                variant="ghost"
                size="sm"
                onClick={() => navigate(item.path)}
                className={cn(
                  'relative font-orbitron font-bold transition-all duration-300 tracking-wider uppercase text-xs px-5 py-2.5 rounded-lg',
                  isActive 
                    ? 'bg-gradient-to-r from-blue-600 to-cyan-500 text-white border-2 border-cyan-400/50 shadow-lg shadow-cyan-500/50' 
                    : 'border border-border/40 text-foreground/70 hover:border-cyan-400/40 hover:bg-cyan-500/10 hover:text-white'
                )}
              >
                <Icon className={cn(
                  "h-4 w-4 mr-2 transition-transform duration-300",
                  isActive && "animate-pulse"
                )} />
                <span>{item.label}</span>
              </Button>
            );
          })}
        </nav>

        {/* Mobile Menu Button */}
        <Button 
          variant="outline" 
          size="sm" 
          className="md:hidden border border-primary/40 hover:border-primary hover:bg-primary/10 text-primary"
        >
          <span className="font-orbitron text-xs tracking-wider uppercase">MENU</span>
        </Button>
      </div>
    </header>
  );
}
