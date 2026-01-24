import React from 'react';
import clsx from 'clsx';
import { differenceInDays, differenceInHours, differenceInMinutes, isPast } from 'date-fns';

interface CountdownTimerProps {
    targetDate: Date | string | null | undefined;
    label?: string;
    size?: 'sm' | 'md' | 'lg';
    showLabel?: boolean;
    className?: string;
}

const SIZE_MAP = {
    sm: { container: 'gap-1', unit: 'text-xs', label: 'text-[8px]' },
    md: { container: 'gap-2', unit: 'text-lg', label: 'text-[9px]' },
    lg: { container: 'gap-3', unit: 'text-2xl', label: 'text-[10px]' },
};

/**
 * CountdownTimer - Displays time remaining until a target date.
 * Shows days, hours, and minutes in a clean format.
 */
export function CountdownTimer({
    targetDate,
    label = 'DEADLINE',
    size = 'md',
    showLabel = true,
    className,
}: CountdownTimerProps) {
    const [timeLeft, setTimeLeft] = React.useState({ days: 0, hours: 0, minutes: 0 });
    const [isOverdue, setIsOverdue] = React.useState(false);

    React.useEffect(() => {
        if (!targetDate) return;

        const target = typeof targetDate === 'string' ? new Date(targetDate) : targetDate;

        const updateCountdown = () => {
            const now = new Date();

            if (isPast(target)) {
                setIsOverdue(true);
                const days = Math.abs(differenceInDays(now, target));
                const hours = Math.abs(differenceInHours(now, target)) % 24;
                const minutes = Math.abs(differenceInMinutes(now, target)) % 60;
                setTimeLeft({ days, hours, minutes });
            } else {
                setIsOverdue(false);
                const days = differenceInDays(target, now);
                const hours = differenceInHours(target, now) % 24;
                const minutes = differenceInMinutes(target, now) % 60;
                setTimeLeft({ days, hours, minutes });
            }
        };

        updateCountdown();
        const interval = setInterval(updateCountdown, 60000); // Update every minute

        return () => clearInterval(interval);
    }, [targetDate]);

    if (!targetDate) {
        return (
            <div className={clsx("text-gray-600 text-[9px] italic", className)}>
                No deadline
            </div>
        );
    }

    const sizeClasses = SIZE_MAP[size];

    return (
        <div className={clsx("flex flex-col", className)}>
            {showLabel && (
                <span className={clsx(
                    "uppercase font-bold tracking-wide mb-1",
                    sizeClasses.label,
                    isOverdue ? "text-red-400" : "text-gray-500"
                )}>
                    {isOverdue ? 'OVERDUE' : label}
                </span>
            )}
            <div className={clsx("flex items-end", sizeClasses.container)}>
                <div className="flex items-baseline gap-0.5">
                    <span className={clsx("font-bold font-mono", sizeClasses.unit, isOverdue ? "text-red-400" : "text-white")}>
                        {timeLeft.days}
                    </span>
                    <span className={clsx("uppercase font-bold", sizeClasses.label, "text-gray-500")}>d</span>
                </div>
                <div className="flex items-baseline gap-0.5">
                    <span className={clsx("font-bold font-mono", sizeClasses.unit, isOverdue ? "text-red-400" : "text-white")}>
                        {timeLeft.hours}
                    </span>
                    <span className={clsx("uppercase font-bold", sizeClasses.label, "text-gray-500")}>h</span>
                </div>
                <div className="flex items-baseline gap-0.5">
                    <span className={clsx("font-bold font-mono", sizeClasses.unit, isOverdue ? "text-red-400" : "text-white")}>
                        {timeLeft.minutes}
                    </span>
                    <span className={clsx("uppercase font-bold", sizeClasses.label, "text-gray-500")}>m</span>
                </div>
            </div>
        </div>
    );
}

export default CountdownTimer;
