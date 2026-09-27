import { ReactNode } from 'react';

type BadgeVariant = 'success' | 'warning' | 'error' | 'neutral' | 'primary';

export function Badge({ children, variant = 'neutral', className = '' }: { children: ReactNode; variant?: BadgeVariant; className?: string }) {
  const variants = {
    success: 'bg-green-100 text-green-800 border-green-200',
    warning: 'bg-orange-100 text-orange-800 border-orange-200',
    error: 'bg-red-100 text-red-800 border-red-200',
    primary: 'bg-primary/10 text-primary border-primary/20',
    neutral: 'bg-slate-100 text-slate-800 border-slate-200',
  };
  
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold border ${variants[variant]} ${className}`}>
      {children}
    </span>
  );
}
