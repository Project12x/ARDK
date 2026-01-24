/**
 * UniversalEntityLinkCard
 * Card for displaying relationships between entities.
 * Read-only card for relationship visualization, compatible with Transporter DnD.
 */

import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import clsx from 'clsx';
import {
    GripVertical, ArrowRight, Ban, Lock, ArrowDownToLine,
    Link as LinkIcon, GitBranch, GitMerge, Trash2
} from 'lucide-react';
import { toast } from 'sonner';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { EntityLink } from '../../lib/db';
import { db } from '../../lib/db';

// ============================================================================
// CONFIG
// ============================================================================

const RELATIONSHIP_CONFIG: Record<string, { icon: typeof LinkIcon; color: string; bg: string; label: string }> = {
    'blocks': { icon: Ban, color: 'text-red-400', bg: 'bg-red-500/20', label: 'Blocks' },
    'blocked-by': { icon: Lock, color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Blocked By' },
    'depends-on': { icon: ArrowDownToLine, color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Depends On' },
    'related': { icon: LinkIcon, color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Related' },
    'child-of': { icon: GitBranch, color: 'text-cyan-400', bg: 'bg-cyan-500/20', label: 'Child Of' },
    'parent-of': { icon: GitMerge, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Parent Of' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalEntityLinkCardProps {
    entity: UniversalEntity<EntityLink>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onDelete?: () => void;
    /** Labels for source and target entities (for display) */
    sourceLabel?: string;
    targetLabel?: string;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalEntityLinkCard({
    entity,
    dragOrigin = 'grid',
    onClick,
    onDelete,
    sourceLabel,
    targetLabel,
}: UniversalEntityLinkCardProps) {
    const link = entity.data;

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-link-${link.id}`,
        data: {
            type: 'universal-card',
            entity: entity,
            entityType: 'link',
            id: link.id,
            title: `${link.source_type}:${link.source_id} → ${link.target_type}:${link.target_id}`,
            metadata: { relationship: link.relationship },
            origin: dragOrigin
        } as UniversalDragPayload & { entityType: string; id: number; title: string; metadata: any },
    });

    const style = {
        transform: CSS.Translate.toString(transform),
        zIndex: isDragging ? 999 : undefined,
    };

    // Delete handler
    const handleDelete = async () => {
        if (confirm('Delete this relationship?')) {
            try {
                await db.entity_links.delete(link.id!);
                toast.success('Relationship removed');
                if (onDelete) onDelete();
            } catch (err) {
                toast.error('Failed to delete');
            }
        }
    };

    const config = RELATIONSHIP_CONFIG[link.relationship] || RELATIONSHIP_CONFIG.related;
    const RelIcon = config.icon;

    return (
        <div
            ref={setNodeRef}
            style={style}
            onClick={onClick}
            className={clsx(
                'group relative bg-surface border rounded-lg transition-all p-3',
                isDragging && 'opacity-30 scale-95',
                'border-white/10 hover:border-accent/50 hover:shadow-lg'
            )}
        >
            {/* Drag Handle */}
            <div
                {...listeners}
                {...attributes}
                className="absolute top-2 right-2 p-1 rounded cursor-grab active:cursor-grabbing text-gray-600 hover:text-white hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                title="Drag to Transporter"
            >
                <GripVertical size={14} />
            </div>

            {/* Relationship Type Badge */}
            <div className="flex items-center gap-2 mb-3">
                <div className={clsx('p-1.5 rounded', config.bg)}>
                    <RelIcon size={14} className={config.color} />
                </div>
                <span className={clsx('text-xs font-bold uppercase', config.color)}>
                    {config.label}
                </span>
            </div>

            {/* Source → Target Display */}
            <div className="flex items-center gap-2 text-sm">
                {/* Source */}
                <div className="flex-1 bg-black/40 rounded px-2 py-1.5 border border-white/10">
                    <div className="text-[10px] text-gray-500 uppercase font-mono">{link.source_type}</div>
                    <div className="text-white font-medium truncate">
                        {sourceLabel || `#${link.source_id}`}
                    </div>
                </div>

                {/* Arrow */}
                <ArrowRight size={16} className="text-gray-600 flex-shrink-0" />

                {/* Target */}
                <div className="flex-1 bg-black/40 rounded px-2 py-1.5 border border-white/10">
                    <div className="text-[10px] text-gray-500 uppercase font-mono">{link.target_type}</div>
                    <div className="text-white font-medium truncate">
                        {targetLabel || `#${link.target_id}`}
                    </div>
                </div>
            </div>

            {/* Timestamp */}
            <div className="mt-2 text-[10px] text-gray-500 font-mono">
                Created {new Date(link.created_at).toLocaleDateString()}
            </div>

            {/* Delete Button */}
            <button
                onClick={(e) => { e.stopPropagation(); handleDelete(); }}
                className="absolute bottom-2 right-2 p-1.5 rounded bg-red-500/20 text-red-400 hover:text-red-300 hover:bg-red-500/30 opacity-0 group-hover:opacity-100 transition-all"
                title="Delete Relationship"
            >
                <Trash2 size={12} />
            </button>
        </div>
    );
}
