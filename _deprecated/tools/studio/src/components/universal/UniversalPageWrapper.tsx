import React from 'react';
import clsx from 'clsx';

interface UniversalPageWrapperProps {
    children: React.ReactNode;
    title?: string;
    actions?: React.ReactNode;
    className?: string;
}

/**
 * UniversalPageWrapper
 * 
 * A standardized container for full-screen pages that need to sit within
 * the application layout but manage their own internal structure.
 * 
 * Provides:
 * - Consistent Padding / Margins
 * - Standardized Header Area
 * - Scrollable Content Area
 */
export function UniversalPageWrapper({ children, title, actions, className }: UniversalPageWrapperProps) {
    return (
        <div className={clsx("flex flex-col h-full w-full overflow-hidden bg-black/50 backdrop-blur-sm", className)}>
            {/* Standard Header */}
            {(title || actions) && (
                <div className="flex justify-between items-center p-6 border-b border-white/10 shrink-0">
                    {title && <h1 className="text-2xl font-black text-white uppercase tracking-tight">{title}</h1>}
                    <div className="flex items-center gap-2">
                        {actions}
                    </div>
                </div>
            )}

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-6 relative">
                {children}
            </div>
        </div>
    );
}
