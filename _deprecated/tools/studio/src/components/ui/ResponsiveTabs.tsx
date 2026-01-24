import React from 'react';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import type { LucideIcon } from 'lucide-react';

export interface TabItem {
    id: string;
    label: string;
    icon?: LucideIcon;
    count?: number;
}

interface ResponsiveTabsProps {
    items: TabItem[];
    activeId: string;
    onChange: (id: string) => void;
    variant?: 'pills' | 'underline' | 'cards';
    className?: string;
}

export function ResponsiveTabs({ items, activeId, onChange, variant = 'pills', className }: ResponsiveTabsProps) {
    return (
        <div className={clsx("flex flex-wrap gap-2", className)}>
            {items.map((item) => {
                const isActive = activeId === item.id;
                const Icon = item.icon;

                return (
                    <button
                        key={item.id}
                        onClick={() => onChange(item.id)}
                        className={clsx(
                            "relative flex items-center gap-2 px-3 py-1.5 text-sm font-bold uppercase transition-all rounded-md group overflow-hidden",

                            // Variant: Pills (Default)
                            variant === 'pills' && (
                                isActive
                                    ? "bg-accent text-black shadow-lg shadow-accent/20"
                                    : "bg-white/5 text-gray-400 hover:text-white hover:bg-white/10"
                            ),

                            // Variant: Underline
                            variant === 'underline' && (
                                isActive
                                    ? "text-accent"
                                    : "text-gray-400 hover:text-white"
                            )
                        )}
                    >
                        {/* Underline Indicator */}
                        {variant === 'underline' && isActive && (
                            <motion.div
                                layoutId="activeTabUnderline"
                                className="absolute bottom-0 left-0 right-0 h-0.5 bg-accent"
                            />
                        )}

                        {Icon && <Icon size={16} className={clsx("shrink-0", isActive ? "opacity-100" : "opacity-70 group-hover:opacity-100")} />}

                        <span className="whitespace-nowrap">{item.label}</span>

                        {item.count !== undefined && (
                            <span className={clsx(
                                "text-[10px] px-1.5 py-0.5 rounded-full ml-1",
                                isActive ? "bg-black/20 text-black/80" : "bg-black/40 text-gray-500"
                            )}>
                                {item.count}
                            </span>
                        )}
                    </button>
                );
            })}
        </div>
    );
}
