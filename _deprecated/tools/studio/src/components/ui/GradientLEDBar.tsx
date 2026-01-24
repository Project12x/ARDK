import React from 'react';
import clsx from 'clsx';

interface GradientLEDBarProps {
    value: number;
    max?: number;
    segments?: number;
    gradient?: 'red' | 'blue' | 'green' | 'amber' | 'accent' | 'priority' | 'impact';
    size?: 'sm' | 'md' | 'lg';
    label?: string;
    showValue?: boolean;
    onChange?: (newValue: number) => void;
    interactive?: boolean;
    className?: string;
}

// Gradient presets for common use cases
const GRADIENT_PRESETS = {
    red: ['#fecaca', '#f87171', '#ef4444', '#dc2626', '#b91c1c'],
    blue: ['#bfdbfe', '#60a5fa', '#3b82f6', '#2563eb', '#1d4ed8'],
    green: ['#bbf7d0', '#4ade80', '#22c55e', '#16a34a', '#15803d'],
    amber: ['#fef3c7', '#fcd34d', '#f59e0b', '#d97706', '#b45309'],
    accent: ['rgba(255,107,0,0.3)', 'rgba(255,107,0,0.5)', 'rgba(255,107,0,0.7)', 'rgba(255,107,0,0.85)', 'rgba(255,107,0,1)'],
    // Priority: Low (green) -> High (red)
    priority: ['#22c55e', '#84cc16', '#eab308', '#f97316', '#ef4444'],
    // Impact: Low (blue) -> High (magenta)
    impact: ['#60a5fa', '#818cf8', '#a855f7', '#d946ef', '#ec4899'],
};

const SIZE_MAP = {
    sm: 'h-2 gap-[2px]',
    md: 'h-3 gap-[3px]',
    lg: 'h-4 gap-[4px]',
};

/**
 * GradientLEDBar - An enhanced LED bar with per-segment gradient colors.
 * Perfect for Priority/Impact bars that transition from low to high intensity.
 * Supports click-to-set interactivity when onChange is provided.
 */
export function GradientLEDBar({
    value,
    max = 5,
    segments = 5,
    gradient = 'priority',
    size = 'md',
    label,
    showValue = false,
    onChange,
    interactive = true,
    className,
}: GradientLEDBarProps) {
    const [hoverIndex, setHoverIndex] = React.useState<number | null>(null);
    const filledSegments = Math.round((value / max) * segments);
    const colors = GRADIENT_PRESETS[gradient];
    const sizeClasses = SIZE_MAP[size];
    const isInteractive = interactive && onChange;

    const handleClick = (index: number) => {
        if (onChange) {
            // Calculate the value based on clicked segment
            const newValue = Math.round(((index + 1) / segments) * max);
            onChange(newValue);
        }
    };

    return (
        <div className={clsx("flex flex-col gap-1", className)}>
            {(label || showValue) && (
                <div className="flex justify-between items-center text-[9px] text-gray-400 uppercase font-bold">
                    {label && <span>{label}</span>}
                    {showValue && <span className="font-mono">{value}/{max}</span>}
                </div>
            )}
            <div
                className={clsx("flex w-full", sizeClasses, isInteractive && "cursor-pointer")}
                onMouseLeave={() => setHoverIndex(null)}
            >
                {Array.from({ length: segments }).map((_, i) => {
                    const isActive = i < filledSegments;
                    const isHovered = hoverIndex !== null && i <= hoverIndex;
                    const showActive = isInteractive ? (isHovered || (hoverIndex === null && isActive)) : isActive;
                    const segmentColor = showActive ? colors[Math.min(i, colors.length - 1)] : 'rgba(255,255,255,0.08)';
                    const glowColor = showActive ? colors[Math.min(i, colors.length - 1)] : 'transparent';

                    return (
                        <div
                            key={i}
                            className={clsx(
                                "flex-1 rounded-[2px] transition-all duration-150",
                                showActive && "shadow-[0_0_4px_var(--glow-color)]",
                                isInteractive && "hover:scale-110"
                            )}
                            style={{
                                backgroundColor: segmentColor,
                                '--glow-color': glowColor,
                            } as React.CSSProperties}
                            onClick={(e) => {
                                e.stopPropagation();
                                handleClick(i);
                            }}
                            onMouseEnter={() => isInteractive && setHoverIndex(i)}
                        />
                    );
                })}
            </div>
        </div>
    );
}

export default GradientLEDBar;
