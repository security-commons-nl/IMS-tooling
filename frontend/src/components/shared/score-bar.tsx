import clsx from 'clsx';

interface ScoreBarProps {
  value: number;
  label: string;
  size?: 'sm' | 'md';
}

export function ScoreBar({ value, label, size = 'md' }: ScoreBarProps) {
  const clamped = Math.max(0, Math.min(100, value));

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-1.5">
        <span
          className={clsx(
            'font-medium text-neutral-800',
            size === 'sm' ? 'text-xs' : 'text-sm',
          )}
        >
          {label}
        </span>
        <span
          className={clsx(
            'font-semibold text-neutral-900',
            size === 'sm' ? 'text-xs' : 'text-sm',
          )}
        >
          {Math.round(clamped)}%
        </span>
      </div>
      <div
        className={clsx(
          'w-full rounded-full bg-neutral-100',
          size === 'sm' ? 'h-1.5' : 'h-2.5',
        )}
      >
        <div
          className={clsx(
            'rounded-full bg-primary-600 transition-all duration-300',
            size === 'sm' ? 'h-1.5' : 'h-2.5',
          )}
          style={{ width: `${clamped}%` }}
        />
      </div>
    </div>
  );
}
