import React, { useState, useEffect } from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

export interface AsyncBadgeProps {
    /** URL to open on click */
    url?: string;
    /** Function to fetch data, returns object with label/status */
    fetcher?: () => Promise<{ label?: string; count?: number; status?: string; color?: string; tooltip?: string }>;
    /** Static label if no fetcher */
    label?: string;
    /** Icon component */
    icon?: React.ElementType;
    /** Base color class or hex */
    color?: string;
    /** Custom class name */
    className?: string;
}

export function AsyncBadge({
    url,
    fetcher,
    label,
    icon: Icon,
    color, // fallback color
    className
}: AsyncBadgeProps) {
    const [data, setData] = useState<{ label?: string; count?: number; status?: string; color?: string; tooltip?: string } | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);

    // Fetch on hover or mount if desired. For now, let's fetch on hover to save bandwidth, 
    // or we can implement a "fetch on visible" strategy later. 
    // Creating a dedicated hook for "lazy fetch" would be ideal.
    // For simplicity parity with ProjectCard, we'll fetch on mouse enter.

    const handleMouseEnter = async () => {
        if (!fetcher || data || loading || error) return;
        setLoading(true);
        try {
            const result = await fetcher();
            setData(result);
        } catch (e) {
            console.error(e);
            setError(true);
        } finally {
            setLoading(false);
        }
    };

    const displayLabel = data?.label || (data?.count !== undefined ? data.count : label);
    const displayColor = data?.color || color;
    const tooltip = data?.tooltip || (url ? `Open ${url}` : undefined);

    // Determine styles based on state
    // Active/Success/Fresh usually gets a glow or brighter color
    // We'll simplisticly map "status" if provided to some styles, else use default.

    // Default style (gray/ghost)
    let styleClasses = "border-white/20 text-white bg-white/10 hover:bg-white/20";

    // Dynamic style overrides
    const isSuccess = data?.status === 'success' || data?.status === 'active';
    const isError = error || data?.status === 'error';

    if (isSuccess || (displayColor === 'green')) {
        styleClasses = "border-green-500/50 text-green-400 bg-green-900/20";
    } else if (isError) {
        styleClasses = "border-red-500/50 text-red-400 bg-red-900/20";
    }

    const content = (
        <div
            className={clsx(
                "px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1 transition-colors relative group select-none",
                styleClasses,
                url ? "cursor-pointer" : "cursor-default",
                className
            )}
            onMouseEnter={handleMouseEnter}
            title={tooltip}
        >
            {loading ? (
                <Loader2 size={10} className="animate-spin" />
            ) : (
                Icon && <Icon size={10} />
            )}

            <span>{loading ? '...' : displayLabel}</span>

            {/* Tooltip Popup (optional, can be controlled by TooltipProvider instead) */}
            {data?.tooltip && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-black border border-white/20 shadow-xl rounded whitespace-nowrap hidden group-hover:block z-50 pointer-events-none">
                    {data.tooltip}
                </div>
            )}
        </div>
    );

    if (url) {
        return (
            <a href={url} target="_blank" rel="noopener noreferrer" onClick={(e) => e.stopPropagation()} className="no-underline">
                {content}
            </a>
        );
    }

    return content;
}
