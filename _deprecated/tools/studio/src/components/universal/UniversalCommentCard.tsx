/**
 * UniversalCommentCard
 * Displays comments attached to any entity.
 */

import { formatDistanceToNow } from 'date-fns';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, MessageSquare, Pin, Reply } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { CommentEntry } from '../../lib/universal/adapters/commentAdapter';

interface UniversalCommentCardProps {
    entity: UniversalEntity<CommentEntry>;
    onClick?: () => void;
    className?: string;
}

export function UniversalCommentCard({ entity, onClick, className }: UniversalCommentCardProps) {
    const comment = entity.data;

    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'list' }
    });

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative p-3 rounded-lg border border-white/5 bg-black/40 hover:border-white/20 transition-all",
                comment.is_pinned && "border-yellow-500/30",
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

            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
                <MessageSquare size={14} className="text-gray-500" />
                <span className="text-sm font-medium text-white">{comment.author || 'Anonymous'}</span>
                {comment.is_pinned && <Pin size={12} className="text-yellow-500" />}
                {comment.reply_to_id && <Reply size={12} className="text-gray-500" />}
            </div>

            {/* Content */}
            <p className="text-sm text-gray-300 line-clamp-3">
                {comment.content}
            </p>

            {/* Footer */}
            <div className="flex items-center justify-between mt-2 text-[10px] text-gray-500">
                <span>{comment.parent_type} #{comment.parent_id}</span>
                <span>{formatDistanceToNow(new Date(comment.created_at), { addSuffix: true })}</span>
            </div>

            {/* Reactions */}
            {comment.reactions && Object.keys(comment.reactions).length > 0 && (
                <div className="flex gap-1 mt-2">
                    {Object.entries(comment.reactions).map(([emoji, count]) => (
                        <span key={emoji} className="text-xs px-1.5 py-0.5 rounded bg-white/5">
                            {emoji} {count}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}
