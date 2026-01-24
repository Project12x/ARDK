import React from 'react';
import { ChevronRight, Home } from 'lucide-react';
import { NavLink } from 'react-router-dom';
import clsx from 'clsx';

export interface BreadcrumbItem {
    label: string;
    to?: string;
    icon?: any;
}

interface UniversalBreadcrumbsProps {
    items: BreadcrumbItem[];
    className?: string;
}

/**
 * UniversalBreadcrumbs
 * 
 * Standardized breadcrumb navigation.
 * Automatically handles home icon and separators.
 */
export function UniversalBreadcrumbs({ items, className }: UniversalBreadcrumbsProps) {
    return (
        <div className={clsx("flex items-center gap-1.5 text-xs font-mono uppercase tracking-wider text-gray-500", className)}>
            <NavLink to="/" className="hover:text-white transition-colors flex items-center">
                <Home size={12} />
            </NavLink>

            {items.map((item, index) => (
                <div key={index} className="flex items-center gap-1.5">
                    <ChevronRight size={10} className="opacity-50" />
                    {item.to ? (
                        <NavLink
                            to={item.to}
                            className="hover:text-accent transition-colors flex items-center gap-1"
                        >
                            {item.icon && <item.icon size={12} />}
                            {item.label}
                        </NavLink>
                    ) : (
                        <span className="text-gray-300 font-bold flex items-center gap-1">
                            {item.icon && <item.icon size={12} />}
                            {item.label}
                        </span>
                    )}
                </div>
            ))}
        </div>
    );
}
