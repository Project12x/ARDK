import React from 'react';
import clsx from 'clsx';

interface CardProps extends React.HTMLAttributes<HTMLDivElement> {
    title?: string;
    action?: React.ReactNode;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(({ className, title, action, children, ...props }, ref) => {
    return (
        <div ref={ref} className={clsx("border border-border bg-surface p-4 relative group", className)} {...props}>
            {/* Decorative corners */}
            <div className="absolute top-0 left-0 w-2 h-2 border-t border-l border-white opacity-20" />
            <div className="absolute top-0 right-0 w-2 h-2 border-t border-r border-white opacity-20" />
            <div className="absolute bottom-0 left-0 w-2 h-2 border-b border-l border-white opacity-20" />
            <div className="absolute bottom-0 right-0 w-2 h-2 border-b border-r border-white opacity-20" />

            {(title || action) && (
                <div className="flex justify-between items-center mb-4 border-b border-white/5 pb-2">
                    {title && <h3 className="text-sm font-bold text-gray-400 uppercase tracking-widest">{title}</h3>}
                    {action}
                </div>
            )}
            {children}
        </div>
    );
});

Card.displayName = 'Card';
