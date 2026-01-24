/**
 * UniversalActivityCard
 * Displays activity/timeline entries for tracking changes across entities.
 */

import { formatDistanceToNow } from 'date-fns';
import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, Activity, Edit, Plus, Trash2, Link, CheckCircle, MessageSquare, Upload, RefreshCw } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { ActivityEntry } from '../../lib/universal/adapters/activityAdapter';
import { ACTIVITY_ACTION_CONFIG } from '../../lib/universal/adapters/activityAdapter';

interface UniversalActivityCardProps {
    entity: UniversalEntity<ActivityEntry>;
    onClick?: () => void;
    className?: string;
}

const ACTION_ICONS: Record<string, typeof Activity> = {
    'create': Plus,
    'update': Edit,
    'delete': Trash2,
    'link': Link,
    'complete': CheckCircle,
    'comment': MessageSquare,
    'upload': Upload,
    'sync': RefreshCw,
};

export function UniversalActivityCard({ entity, onClick, className }: UniversalActivityCardProps) {
    const activity = entity.data;
    const config = ACTIVITY_ACTION_CONFIG[activity.action] || ACTIVITY_ACTION_CONFIG['update'];
    const ActionIcon = ACTION_ICONS[activity.action] || Activity;

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'list' }
    });

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative flex items-start gap-3 p-3 rounded-lg border border-white/5 bg-black/40 hover:border-white/20 transition-all",
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

            {/* Action Icon */}
            <div className={clsx("p-2 rounded-lg bg-white/5", config.color)}>
                <ActionIcon size={16} />
            </div>

            {/* Content */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className={clsx("text-[10px] font-bold uppercase", config.color)}>
                        {config.label}
                    </span>
                    <span className="text-[10px] text-gray-500">
                        {activity.entity_type}
                    </span>
                </div>
                <h4 className="text-sm font-medium text-white truncate">
                    {activity.entity_title}
                </h4>
                <div className="flex items-center gap-2 mt-1 text-[10px] text-gray-500">
                    {activity.actor && <span>{activity.actor}</span>}
                    <span>•</span>
                    <span>{formatDistanceToNow(new Date(activity.created_at), { addSuffix: true })}</span>
                </div>
            </div>
        </div>
    );
}
