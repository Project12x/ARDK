import React, { type ReactNode } from 'react';
import clsx from 'clsx';
import { motion } from 'framer-motion';

export interface UniversalPageProps {
    /** Page Title (Displayed in Header) */
    title?: string;
    /** Optional subtitle or breadcrumb text */
    subtitle?: string;
    /** Primary Action Buttons (Top Right) */
    actions?: ReactNode;
    /** Explicit Breadcrumbs component slot */
    breadcrumbs?: ReactNode;
    /** Tabs component slot (UniversalTabs) */
    tabs?: ReactNode;
    /** Main Content */
    children: ReactNode;
    /** Class name for the root container */
    className?: string;
    /** If true, removes default padding from content area */
    noPadding?: boolean;
    /** Optional sidebar (Right side panel) */
    complementarySidebar?: ReactNode;
}

/**
 * UniversalPage
 * 
 * The standardized V2 Layout for all pages.
 * Provides a consistent Header, Action Bar, Tabs area, and scrollable Content.
 * 
 * Usage:
 * <UniversalPage title="Projects" actions={<Button>New</Button>}>
 *    <Content />
 * </UniversalPage>
 */
export function UniversalPage({
    title,
    subtitle,
    actions,
    breadcrumbs,
    tabs,
    children,
    className,
    noPadding = false,
    complementarySidebar
}: UniversalPageProps) {
    return (
        <div className={clsx("flex flex-col h-full w-full overflow-hidden bg-background relative", className)}>
            {/* --- HEADER SECTION --- */}
            {(title || actions || tabs || breadcrumbs) && (
                <div className="shrink-0 flex flex-col border-b border-border bg-black/20 backdrop-blur-sm z-10">

                    {/* Top Row: Title & Actions */}
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between px-4 sm:px-6 py-4 gap-4 sm:gap-0">
                        <div className="flex flex-col gap-0.5">
                            {breadcrumbs && <div className="mb-1">{breadcrumbs}</div>}
                            {title && (
                                <h1 className="text-xl sm:text-2xl font-black text-foreground uppercase tracking-tight leading-none truncate">
                                    {title}
                                </h1>
                            )}
                            {subtitle && (
                                <div className="text-xs sm:text-sm font-mono text-gray-400 truncate">
                                    {subtitle}
                                </div>
                            )}
                        </div>
                        {actions && (
                            <div className="flex items-center gap-2 self-end sm:self-auto">
                                {actions}
                            </div>
                        )}
                    </div>

                    {/* Bottom Row: Tabs */}
                    {tabs && (
                        <div className="px-6 pb-0">
                            {tabs}
                        </div>
                    )}
                </div>
            )}

            {/* --- BODY SECTION --- */}
            <div className="flex-1 flex overflow-hidden relative">

                {/* Main Content Area */}
                <main className={clsx(
                    "flex-1 overflow-y-auto custom-scrollbar relative",
                    !noPadding && "p-4 sm:p-6"
                )}>
                    {children}
                </main>

                {/* Optional Right Sidebar - Hidden on mobile, fixed width on desktop */}
                {complementarySidebar && (
                    <aside className="hidden lg:block w-80 shrink-0 border-l border-border bg-black/10 overflow-y-auto custom-scrollbar">
                        {complementarySidebar}
                    </aside>
                )}
            </div>
        </div>
    );
}
