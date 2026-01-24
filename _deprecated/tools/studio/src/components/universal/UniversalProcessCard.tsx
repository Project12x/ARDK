/**
 * UniversalProcessCard
 * Displays multi-step processes/workflows with progress.
 */

import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, Workflow, CheckCircle, Circle, PlayCircle, PauseCircle } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { ProcessEntry } from '../../lib/universal/adapters/processAdapter';

interface UniversalProcessCardProps {
    entity: UniversalEntity<ProcessEntry>;
    onClick?: () => void;
    className?: string;
}

const STATUS_ICONS: Record<string, typeof Workflow> = {
    'active': PlayCircle,
    'paused': PauseCircle,
    'completed': CheckCircle,
    'draft': Circle,
};

export function UniversalProcessCard({ entity, onClick, className }: UniversalProcessCardProps) {
    const process = entity.data;
    const progress = entity.progress || 0;
    const StatusIcon = STATUS_ICONS[process.status] || Workflow;

    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'grid' }
    });

    const statusColor = {
        'active': 'text-blue-500',
        'paused': 'text-yellow-500',
        'completed': 'text-green-500',
        'failed': 'text-red-500',
        'draft': 'text-gray-500',
    }[process.status] || 'text-gray-500';

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative p-4 rounded-xl border border-white/5 bg-black/40 hover:border-white/20 transition-all",
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
            <div className="flex items-center gap-2 mb-3">
                <StatusIcon size={16} className={statusColor} />
                <h3 className="text-sm font-bold text-white truncate">{process.name}</h3>
            </div>

            {/* Progress Bar */}
            <div className="mb-3">
                <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                    <span>{entity.metadata?.completedSteps}/{process.steps.length} steps</span>
                    <span>{progress}%</span>
                </div>
                <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-accent transition-all rounded-full"
                        style={{ width: `${progress}%` }}
                    />
                </div>
            </div>

            {/* Steps Overview */}
            <div className="flex gap-1">
                {process.steps.slice(0, 6).map((step, i) => (
                    <div
                        key={step.id}
                        className={clsx(
                            "flex-1 h-1.5 rounded-full",
                            step.status === 'completed' ? 'bg-green-500' :
                                step.status === 'in_progress' ? 'bg-blue-500' :
                                    'bg-white/10'
                        )}
                        title={step.title}
                    />
                ))}
                {process.steps.length > 6 && (
                    <span className="text-[10px] text-gray-500">+{process.steps.length - 6}</span>
                )}
            </div>

            {/* Category */}
            {process.category && (
                <div className="mt-3 text-[10px] text-gray-500 uppercase">
                    {process.category}
                </div>
            )}
        </div>
    );
}
