import React from 'react';
import clsx from 'clsx';

export interface Tag {
    label: string;
    color?: 'default' | 'green' | 'amber' | 'red' | 'blue' | 'purple' | 'accent';
    icon?: React.ReactNode;
}

interface TagsRowProps {
    tags: Tag[];
    maxVisible?: number;
    size?: 'sm' | 'md';
    variant?: 'colorful' | 'monochrome';
    onTagClick?: (tag: Tag) => void;
    className?: string;
}

// Colorful style - each color is distinct
const COLOR_MAP_COLORFUL = {
    default: 'bg-gray-800 text-gray-300 border-gray-700 hover:bg-gray-700',
    green: 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/30',
    amber: 'bg-amber-500/20 text-amber-400 border-amber-500/30 hover:bg-amber-500/30',
    red: 'bg-red-500/20 text-red-400 border-red-500/30 hover:bg-red-500/30',
    blue: 'bg-blue-500/20 text-blue-400 border-blue-500/30 hover:bg-blue-500/30',
    purple: 'bg-purple-500/20 text-purple-400 border-purple-500/30 hover:bg-purple-500/30',
    accent: 'bg-accent/20 text-accent border-accent/30 hover:bg-accent/30',
};

// Monochrome style - subtle, professional, less saturated
const COLOR_MAP_MONOCHROME = {
    default: 'bg-white/5 text-gray-400 border-white/10 hover:bg-white/10',
    green: 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10',
    amber: 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10',
    red: 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10',
    blue: 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10',
    purple: 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10',
    accent: 'bg-white/5 text-gray-300 border-white/10 hover:bg-white/10',
};

const SIZE_MAP = {
    sm: 'text-[8px] px-1.5 py-0.5',
    md: 'text-[10px] px-2 py-1',
};

/**
 * TagsRow - A horizontal row of tag/badge chips.
 * Perfect for displaying project categories, certifications, or status labels.
 * 
 * Variants:
 * - colorful: Each tag has its distinct color (default)
 * - monochrome: All tags are subtle gray/white for a professional look
 */
export function TagsRow({
    tags,
    maxVisible = 5,
    size = 'sm',
    variant = 'colorful',
    onTagClick,
    className,
}: TagsRowProps) {
    const visibleTags = tags.slice(0, maxVisible);
    const hiddenCount = tags.length - maxVisible;
    const colorMap = variant === 'monochrome' ? COLOR_MAP_MONOCHROME : COLOR_MAP_COLORFUL;

    if (tags.length === 0) {
        return null;
    }

    const handleTagClick = (e: React.MouseEvent, tag: Tag) => {
        e.stopPropagation();
        if (onTagClick) {
            onTagClick(tag);
        }
    };

    return (
        <div className={clsx("flex flex-wrap gap-1", className)}>
            {visibleTags.map((tag, i) => (
                <span
                    key={i}
                    className={clsx(
                        "inline-flex items-center gap-1 rounded border font-bold uppercase tracking-wide transition-colors",
                        colorMap[tag.color || 'default'],
                        SIZE_MAP[size],
                        onTagClick && "cursor-pointer"
                    )}
                    onClick={(e) => handleTagClick(e, tag)}
                >
                    {tag.icon}
                    {tag.label}
                </span>
            ))}
            {hiddenCount > 0 && (
                <span className={clsx(
                    "inline-flex items-center rounded border font-mono transition-colors",
                    colorMap.default,
                    SIZE_MAP[size]
                )}>
                    +{hiddenCount}
                </span>
            )}
        </div>
    );
}

export default TagsRow;
