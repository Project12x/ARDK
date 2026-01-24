/**
 * UniversalLogCard
 * Card for displaying changelog/log entries.
 * Read-only card for history display, compatible with Transporter DnD.
 */

import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import clsx from 'clsx';
import { GripVertical, History, GitCommit, Bot } from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Log } from '../../lib/db';

// ============================================================================
// PROPS
// ============================================================================

interface UniversalLogCardProps {
    entity: UniversalEntity<Log>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalLogCard({
    entity,
    dragOrigin = 'grid',
    onClick,
}: UniversalLogCardProps) {
    const log = entity.data;

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-log-${log.id}`,
        data: {
            type: 'universal-card',
            entity: entity,
            entityType: 'log',
            id: log.id,
            title: log.summary,
            metadata: { version: log.version, type: log.type },
            origin: dragOrigin
        } as UniversalDragPayload & { entityType: string; id: number; title: string; metadata: any },
    });

    const style = {
        transform: CSS.Translate.toString(transform),
        zIndex: isDragging ? 999 : undefined,
    };

    const isAuto = log.type === 'auto';
    const TypeIcon = isAuto ? Bot : GitCommit;

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

            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1 rounded', isAuto ? 'bg-gray-500/20' : 'bg-blue-500/20')}>
                    <TypeIcon size={12} className={isAuto ? 'text-gray-400' : 'text-blue-400'} />
                </div>
                <span className="text-xs font-bold text-accent font-mono">
                    {log.version}
                </span>
                <span className={clsx(
                    'text-[10px] px-1.5 py-0.5 rounded uppercase font-mono',
                    isAuto ? 'bg-gray-500/20 text-gray-400' : 'bg-blue-500/20 text-blue-400'
                )}>
                    {log.type}
                </span>
            </div>

            {/* Summary */}
            <p className="text-sm text-gray-300 line-clamp-2">
                {log.summary}
            </p>

            {/* Timestamp */}
            <div className="mt-2 text-[10px] text-gray-500 font-mono flex items-center gap-1">
                <History size={10} />
                {(() => {
                    const d = new Date(log.date);
                    return isNaN(d.getTime()) ? 'Invalid date' : d.toLocaleString();
                })()}
            </div>
        </div>
    );
}
