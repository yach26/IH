export function ProgressBar({ 
  label, 
  current, 
  target, 
  colorClass = 'bg-primary' 
}: { 
  label: string; 
  current: number; 
  target: number; 
  colorClass?: string 
}) {
  const percentage = Math.min(100, Math.max(0, (current / target) * 100));
  
  return (
    <div className="flex items-center space-x-4 w-full">
      <span className="w-6 font-semibold text-foreground">{label}</span>
      <div className="flex-1 h-4 bg-surface-hover rounded-full overflow-hidden border border-border flex">
        <div 
          className={`h-full ${colorClass} transition-all duration-500`} 
          style={{ width: `${percentage}%` }}
        />
      </div>
      <span className="w-16 text-xs text-muted text-right">{current} / {target}</span>
    </div>
  );
}
