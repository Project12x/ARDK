/**
 * UniversalTemplateCard
 * Displays reusable entity templates.
 */

import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, FileCode2, Copy, Star } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { TemplateEntry } from '../../lib/universal/adapters/templateAdapter';

interface UniversalTemplateCardProps {
    entity: UniversalEntity<TemplateEntry>;
    onClick?: () => void;
    onUse?: () => void;
    className?: string;
}

export function UniversalTemplateCard({ entity, onClick, onUse, className }: UniversalTemplateCardProps) {
    const template = entity.data;

    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'grid' }
    });

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative p-4 rounded-xl border border-white/5 bg-black/40 hover:border-white/20 transition-all",
                template.is_system && "border-purple-500/20",
                isDragging && "opacity-50 scale-95",
                className
            )}
        >
            {/* Drag Handle */}
            <div
                {...attributes}
                {...listeners}
                className="absolute top-2 right-2 p-1 rounded cursor-grab text-gray-500 hover:text-white opacity-0 group-hover:opacity-100"
            >
                <GripVertical size={14} />
            </div>

            {/* Preview Image */}
            {template.preview_url ? (
                <div className="w-full h-24 rounded-lg overflow-hidden mb-3 bg-white/5">
                    <img
                        src={template.preview_url}
                        alt={template.name}
                        className="w-full h-full object-cover"
                    />
                </div>
            ) : (
                <div className="w-full h-24 rounded-lg mb-3 bg-white/5 flex items-center justify-center">
                    <FileCode2 size={32} className="text-gray-600" />
                </div>
            )}

            {/* Header */}
            <div className="flex items-center gap-2 mb-1">
                {template.is_system && <Star size={12} className="text-purple-500" />}
                <h3 className="text-sm font-bold text-white truncate">{template.name}</h3>
            </div>

            {/* Subtitle */}
            <div className="text-[10px] text-gray-500 mb-2">
                Creates {template.entity_type}
            </div>

            {/* Description */}
            {template.description && (
                <p className="text-xs text-gray-400 line-clamp-2 mb-3">
                    {template.description}
                </p>
            )}

            {/* Use Button */}
            {onUse && (
                <button
                    onClick={(e) => { e.stopPropagation(); onUse(); }}
                    className="w-full flex items-center justify-center gap-2 py-2 rounded-lg bg-accent/20 text-accent hover:bg-accent/30 transition-colors text-xs font-medium"
                >
                    <Copy size={14} />
                    Use Template
                </button>
            )}

            {/* Usage Count */}
            {template.usage_count !== undefined && template.usage_count > 0 && (
                <div className="mt-2 text-[10px] text-gray-500 text-center">
                    Used {template.usage_count} times
                </div>
            )}
        </div>
    );
}
