import React from 'react';
import clsx from 'clsx';

interface MiniLinkMapProps {
    links?: { id: string | number; label: string; type?: 'blocker' | 'related' }[];
    maxVisible?: number;
    className?: string;
}

/**
 * MiniLinkMap - A compact visualization of linked projects/entities.
 * Displays a small node graph showing connections.
 */
export function MiniLinkMap({
    links = [],
    maxVisible = 3,
    className,
}: MiniLinkMapProps) {
    const visibleLinks = links.slice(0, maxVisible);
    const hasMore = links.length > maxVisible;

    // If no links, show placeholder
    if (links.length === 0) {
        return (
            <div className={clsx("flex items-center justify-center text-[9px] text-gray-600 italic", className)}>
                No links
            </div>
        );
    }

    return (
        <div className={clsx("flex items-center gap-2", className)}>
            {/* Center Node (current project) */}
            <div className="relative flex items-center justify-center">
                <div className="w-3 h-3 rounded-full bg-accent shadow-[0_0_6px_rgba(255,107,0,0.6)]" />

                {/* Connection Lines */}
                <svg className="absolute w-12 h-8" style={{ left: 6 }}>
                    {visibleLinks.map((_, i) => {
                        const yOffset = (i - (visibleLinks.length - 1) / 2) * 10;
                        return (
                            <line
                                key={i}
                                x1={0}
                                y1={16}
                                x2={40}
                                y2={16 + yOffset}
                                stroke={visibleLinks[i]?.type === 'blocker' ? '#ef4444' : '#3b82f6'}
                                strokeWidth={1}
                                strokeDasharray={visibleLinks[i]?.type === 'blocker' ? 'none' : '2,2'}
                                opacity={0.6}
                            />
                        );
                    })}
                </svg>
            </div>

            {/* Linked Nodes */}
            <div className="flex flex-col gap-1 ml-10">
                {visibleLinks.map((link, i) => (
                    <div
                        key={link.id}
                        className="flex items-center gap-1.5"
                    >
                        <div className={clsx(
                            "w-2 h-2 rounded-full",
                            link.type === 'blocker' ? "bg-red-500" : "bg-blue-500"
                        )} />
                        <span className="text-[8px] text-gray-400 font-mono truncate max-w-[60px]">
                            {link.label}
                        </span>
                    </div>
                ))}
                {hasMore && (
                    <span className="text-[8px] text-gray-500">+{links.length - maxVisible} more</span>
                )}
            </div>
        </div>
    );
}

export default MiniLinkMap;
