import { ButtonHTMLAttributes, ReactNode } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'outline' | 'ghost';
  children: ReactNode;
}

export function Button({ variant = 'primary', className = '', children, ...props }: ButtonProps) {
  const baseStyle = 'inline-flex items-center justify-center px-4 py-2 rounded-lg font-medium transition-colors shadow-sm focus:outline-none';
  const variants = {
    primary: 'bg-primary text-white hover:bg-primary-hover border border-transparent',
    secondary: 'bg-surface-hover text-foreground hover:bg-slate-200 border border-transparent',
    outline: 'bg-surface text-foreground border border-border hover:bg-surface-hover',
    ghost: 'bg-transparent text-muted hover:text-foreground hover:bg-surface-hover shadow-none',
  };

  return (
    <button className={`${baseStyle} ${variants[variant]} ${className}`} {...props}>
      {children}
    </button>
  );
}
