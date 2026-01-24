import React from 'react';
import clsx from 'clsx';

interface LEDBarProps {
    value: number;
    max?: number;
    segments?: number;
    color?: 'green' | 'amber' | 'red' | 'blue' | 'accent';
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
    label?: string;
    className?: string;
}

const COLOR_MAP = {
    green: { active: 'bg-emerald-500 shadow-[0_0_4px_rgba(16,185,129,0.6)]', inactive: 'bg-emerald-900/30' },
    amber: { active: 'bg-amber-500 shadow-[0_0_4px_rgba(245,158,11,0.6)]', inactive: 'bg-amber-900/30' },
    red: { active: 'bg-red-500 shadow-[0_0_4px_rgba(239,68,68,0.6)]', inactive: 'bg-red-900/30' },
    blue: { active: 'bg-blue-500 shadow-[0_0_4px_rgba(59,130,246,0.6)]', inactive: 'bg-blue-900/30' },
    accent: { active: 'bg-accent shadow-[0_0_4px_rgba(var(--accent-rgb),0.6)]', inactive: 'bg-accent/20' },
};

const SIZE_MAP = {
    sm: 'h-1.5 gap-[1px]',
    md: 'h-2.5 gap-[2px]',
    lg: 'h-4 gap-[3px]',
};

/**
 * LEDBar - A segmented LED-style progress bar component.
 * Inspired by hardware status indicators and retro computing displays.
 */
export function LEDBar({
    value,
    max = 10,
    segments = 10,
    color = 'green',
    size = 'md',
    showLabel = false,
    label,
    className,
}: LEDBarProps) {
    const filledSegments = Math.round((value / max) * segments);
    const colors = COLOR_MAP[color];
    const sizeClasses = SIZE_MAP[size];

    return (
        <div className={clsx("flex flex-col gap-1", className)}>
            {showLabel && (
                <div className="flex justify-between items-center text-[9px] text-gray-400 uppercase font-bold">
                    <span>{label || 'Progress'}</span>
                    <span className="font-mono">{value}/{max}</span>
                </div>
            )}
            <div className={clsx("flex w-full", sizeClasses)}>
                {Array.from({ length: segments }).map((_, i) => (
                    <div
                        key={i}
                        className={clsx(
                            "flex-1 rounded-[1px] transition-all duration-150",
                            i < filledSegments ? colors.active : colors.inactive
                        )}
                    />
                ))}
            </div>
        </div>
    );
}

export default LEDBar;
