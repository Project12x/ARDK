import clsx from 'clsx';

interface ProgressBarProps {
    value: number;
    max?: number;
    label?: string;
    gradient?: string;
    size?: 'sm' | 'md';
    showValue?: boolean;
    compact?: boolean;
    onClick?: (value: number) => void;
}

export function ProgressBar({
    value,
    max = 5,
    label,
    gradient = 'from-accent to-orange-400',
    size = 'md',
    showValue = false,
    compact = false,
    onClick
}: ProgressBarProps) {
    const percentage = Math.min((value / max) * 100, 100);

    const handleClick = (e: React.MouseEvent<HTMLDivElement>) => {
        if (!onClick) return;
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const newValue = Math.ceil((x / rect.width) * max);
        onClick(Math.min(Math.max(newValue, 1), max));
    };

    return (
        <div className={clsx(
            "flex items-center",
            compact ? "gap-1.5" : "gap-3 w-full"
        )}>
            {label && (
                <span className={clsx(
                    "font-semibold text-gray-500 uppercase tracking-wider shrink-0",
                    compact ? "text-[9px]" : size === 'sm' ? 'text-[10px] w-14' : 'text-xs w-16'
                )}>
                    {label}
                </span>
            )}
            <div
                className={clsx(
                    "bg-white/5 rounded-full overflow-hidden relative",
                    compact ? "w-14 h-1.5" : "flex-1",
                    !compact && (size === 'sm' ? 'h-2.5' : 'h-3'),
                    onClick && 'cursor-pointer hover:bg-white/10 transition-colors'
                )}
                onClick={handleClick}
            >
                {/* Animated gradient fill */}
                <div
                    className={clsx(
                        "h-full rounded-full bg-gradient-to-r transition-all duration-300 ease-out",
                        gradient
                    )}
                    style={{ width: `${percentage}%` }}
                />
                {/* Subtle glow effect */}
                {!compact && (
                    <div
                        className={clsx(
                            "absolute inset-0 rounded-full bg-gradient-to-r opacity-50 blur-sm",
                            gradient
                        )}
                        style={{ width: `${percentage}%` }}
                    />
                )}
            </div>
            {showValue && (
                <span className={clsx(
                    "font-mono text-gray-400 shrink-0",
                    compact ? "text-[9px]" : size === 'sm' ? 'text-[10px]' : 'text-xs'
                )}>
                    {value}/{max}
                </span>
            )}
        </div>
    );
}
