import React from 'react';
import clsx from 'clsx';
import { motion } from 'framer-motion';

export interface TabItem {
    id: string;
    label: string;
    icon?: any;
    count?: number;
}

interface UniversalTabsProps {
    tabs: TabItem[];
    activeTab: string;
    onChange: (tabId: string) => void;
    className?: string;
    variant?: 'line' | 'pill' | 'square-pill';
}

/**
 * UniversalTabs
 * 
 * Standardized tab navigation for Universal Pages.
 * Features an animated underline and hover effects.
 * 
 * Variants:
 * - 'line': Minimalist, text with animated underline (Default)
 * - 'pill': Segmented control / button style
 */
export function UniversalTabs({ tabs, activeTab, onChange, className, variant = 'line' }: UniversalTabsProps) {
    if (variant === 'pill' || variant === 'square-pill') {
        const isSquare = variant === 'square-pill';
        return (
            <div className={clsx(
                "flex flex-wrap items-center gap-1 p-1 bg-white/5 border border-white/5",
                isSquare ? "rounded-none" : "rounded-lg",
                className
            )}>
                {tabs.map((tab) => {
                    const isActive = activeTab === tab.id;
                    return (
                        <button
                            key={tab.id}
                            onClick={() => onChange(tab.id)}
                            className={clsx(
                                "relative px-3 py-1.5 text-xs font-bold tracking-wide uppercase transition-all flex items-center gap-2 shrink-0 user-select-none",
                                isSquare ? "rounded-none" : "rounded-md",
                                isActive
                                    ? "bg-accent text-back shadow-sm"
                                    : "text-gray-400 hover:text-foreground hover:bg-white/5"
                            )}
                        >
                            {tab.icon && <tab.icon size={14} className={isActive ? "text-black" : "text-gray-400"} />}
                            <span>{tab.label}</span>
                            {tab.count !== undefined && (
                                <span className={clsx(
                                    "text-[9px] px-1.5 py-0.5 rounded-full",
                                    isActive ? "bg-black/20 text-black" : "bg-white/10 text-gray-500"
                                )}>
                                    {tab.count}
                                </span>
                            )}
                        </button>
                    );
                })}
            </div>
        );
    }

    // Default: 'line' variant
    return (
        <div className={clsx("flex flex-wrap items-center gap-x-4 gap-y-2 sm:gap-x-6 border-b border-transparent", className)}>
            {tabs.map((tab) => {
                const isActive = activeTab === tab.id;
                return (
                    <button
                        key={tab.id}
                        onClick={() => onChange(tab.id)}
                        className={clsx(
                            "relative pb-3 text-sm font-mono tracking-wide uppercase transition-colors flex items-center gap-2 shrink-0 user-select-none",
                            isActive ? "text-accent font-bold" : "text-gray-500 hover:text-foreground"
                        )}
                    >
                        {tab.icon && <tab.icon size={14} />}
                        <span>{tab.label}</span>
                        {tab.count !== undefined && (
                            <span className={clsx(
                                "text-[10px] px-1.5 rounded-full",
                                isActive ? "bg-accent/20 text-accent" : "bg-white/10 text-gray-500"
                            )}>
                                {tab.count}
                            </span>
                        )}

                        {/* Animated Underline */}
                        {isActive && (
                            <motion.div
                                layoutId="activeTabUnderline"
                                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent shadow-[0_0_10px_rgba(var(--accent-rgb),0.5)]"
                                initial={false}
                                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                            />
                        )}
                    </button>
                );
            })}
        </div>
    );
}
