import type { UniversalAction } from '../../lib/universal/types';
import { UniversalButton } from './UniversalButton';
import clsx from 'clsx';

interface UniversalActionBarProps {
    actions: UniversalAction[];
    onActionClick?: (actionId: string) => void;
    className?: string;
    direction?: 'horizontal' | 'vertical';
    size?: 'sm' | 'md' | 'lg' | 'icon';
    variant?: 'default' | 'toolbar' | 'ghost';
}

export function UniversalActionBar({
    actions,
    onActionClick,
    className,
    direction = 'horizontal',
    size = 'md',
    variant = 'default'
}: UniversalActionBarProps) {
    if (!actions.length) return null;

    const containerClasses = clsx(
        "flex gap-2",
        direction === 'vertical' ? "flex-col" : "items-center",
        variant === 'toolbar' && "bg-black/40 backdrop-blur border border-white/10 p-1.5 rounded-xl",
        className
    );

    return (
        <div className={containerClasses}>
            {actions.map((action, index) => (
                <UniversalButton
                    key={action.id || index}
                    action={action}
                    onClick={() => {
                        action.action?.();
                        if (action.id) onActionClick?.(action.id);
                    }}
                    size={size}
                    // If toolbar variant, force ghost unless action specifies otherwise
                    variant={variant === 'toolbar' && !action.variant ? 'ghost' : action.variant}
                />
            ))}
        </div>
    );
}
