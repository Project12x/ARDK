import clsx from 'clsx';
import type { UniversalAction } from '../../lib/universal/types';
import { Loader2 } from 'lucide-react';

interface UniversalButtonProps {
    action?: UniversalAction; // Can be driven by data object
    onClick?: () => void;
    label?: string;
    icon?: any;
    variant?: UniversalAction['variant'];
    disabled?: boolean;
    loading?: boolean;
    className?: string;
    size?: 'sm' | 'md' | 'lg' | 'icon';
    title?: string;
}

export function UniversalButton({
    action,
    onClick,
    label,
    icon: Icon,
    variant = 'primary',
    disabled,
    loading,
    className,
    size = 'md',
    title
}: UniversalButtonProps) {

    // Resolve props from Action object if provided
    const resolvedLabel = label || action?.label;
    const ResolvedIcon = Icon || action?.icon;
    const resolvedOnClick = onClick || action?.action;
    const resolvedVariant = variant || action?.variant || 'primary';
    const resolvedDisabled = disabled || action?.disabled;
    const resolvedTitle = title || action?.tooltip;

    const baseStyles = "inline-flex items-center justify-center rounded-lg font-mono tracking-wide transition-all duration-200 focus:outline-none focus:ring-2 focus:ring-accent/50 disabled:opacity-50 disabled:cursor-not-allowed";

    const variants = {
        primary: "bg-accent text-black hover:bg-white font-bold shadow-lg shadow-accent/20 hover:shadow-accent/40",
        secondary: "bg-white/10 text-white hover:bg-white/20 border border-white/5",
        ghost: "text-gray-400 hover:text-white hover:bg-white/5",
        outline: "border border-white/20 text-gray-300 hover:border-white hover:text-white hover:bg-white/5",
        danger: "bg-red-500/10 text-red-500 border border-red-500/20 hover:bg-red-500/20 hover:border-red-500/50"
    };

    const sizes = {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 text-sm",
        lg: "h-12 px-6 text-base",
        icon: "h-10 w-10 p-2"
    };

    return (
        <button
            onClick={resolvedOnClick}
            disabled={resolvedDisabled || loading}
            className={clsx(
                baseStyles,
                variants[resolvedVariant],
                sizes[size],
                className
            )}
            title={resolvedTitle}
        >
            {loading ? (
                <Loader2 size={16} className="animate-spin" />
            ) : (
                <>
                    {ResolvedIcon && (
                        <ResolvedIcon
                            size={size === 'sm' ? 14 : 18}
                            className={clsx(resolvedLabel ? "mr-2" : "")}
                        />
                    )}
                    {resolvedLabel}
                </>
            )}
        </button>
    );
}
