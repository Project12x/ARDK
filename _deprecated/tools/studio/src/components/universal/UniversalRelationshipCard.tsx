/**
 * UniversalRelationshipCard
 * Displays relationships between entities.
 */

import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, ArrowRight, Ban, Link, FolderUp, HeartHandshake, Trash2 } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { RelationshipEntry } from '../../lib/universal/adapters/relationshipAdapter';
import { RELATIONSHIP_CONFIG } from '../../lib/universal/adapters/relationshipAdapter';

interface UniversalRelationshipCardProps {
    entity: UniversalEntity<RelationshipEntry>;
    onClick?: () => void;
    onDelete?: () => void;
    className?: string;
}

const REL_ICONS: Record<string, typeof Link> = {
    'blocks': Ban,
    'depends_on': ArrowRight,
    'related': Link,
    'parent': FolderUp,
    'supports': HeartHandshake,
};

export function UniversalRelationshipCard({ entity, onClick, onDelete, className }: UniversalRelationshipCardProps) {
    const rel = entity.data;
    const config = RELATIONSHIP_CONFIG[rel.relationship] || RELATIONSHIP_CONFIG['custom'];
    const RelIcon = REL_ICONS[rel.relationship] || Link;

    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'list' }
    });

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-black/40 hover:border-white/20 transition-all",
                isDragging && "opacity-50 scale-95",
                className
            )}
        >
            {/* Drag Handle */}
            <div
                {...attributes}
                {...listeners}
                className="absolute top-2 right-8 p-1 rounded cursor-grab text-gray-500 hover:text-white opacity-0 group-hover:opacity-100"
            >
                <GripVertical size={14} />
            </div>

            {/* Delete Button */}
            {onDelete && (
                <button
                    onClick={(e) => { e.stopPropagation(); onDelete(); }}
                    className="absolute top-2 right-2 p-1 rounded text-gray-500 hover:text-red-500 opacity-0 group-hover:opacity-100"
                >
                    <Trash2 size={14} />
                </button>
            )}

            {/* Source */}
            <div className="flex-1 min-w-0">
                <div className="text-[10px] text-gray-500 uppercase">{rel.source_type}</div>
                <div className="text-sm font-medium text-white truncate">
                    {rel.source_title || `#${rel.source_id}`}
                </div>
            </div>

            {/* Relationship */}
            <div className={clsx("flex flex-col items-center gap-1", config.color)}>
                <RelIcon size={16} />
                <span className="text-[9px] font-bold uppercase">{config.verb}</span>
            </div>

            {/* Target */}
            <div className="flex-1 min-w-0 text-right">
                <div className="text-[10px] text-gray-500 uppercase">{rel.target_type}</div>
                <div className="text-sm font-medium text-white truncate">
                    {rel.target_title || `#${rel.target_id}`}
                </div>
            </div>
        </div>
    );
}
