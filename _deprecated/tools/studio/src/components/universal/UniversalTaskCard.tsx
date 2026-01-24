/**
 * UniversalTaskCard
 * A specialized card for displaying ProjectTask entities in the Universal system.
 * Inherits DnD from UniversalCard pattern for Transporter compatibility.
 */

import { useState, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLiveQuery } from 'dexie-react-hooks';
import clsx from 'clsx';
import { toast } from 'sonner';
import {
    GripVertical, Settings, Save, X, Circle, CheckCircle, PlayCircle, AlertCircle,
    Calendar, Clock, Zap, Flag, AlertTriangle
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { ProjectTask } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    status: z.enum(['pending', 'in-progress', 'completed', 'blocked']),
    priority: z.preprocess(
        val => (val === '' || val === null ? 3 : Number(val)),
        z.number().min(1).max(5)
    ),
    phase: z.string().optional(),
    estimated_time: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// STATUS CONFIG
// ============================================================================

const STATUS_CONFIG = {
    'pending': { icon: Circle, color: 'text-gray-400', bg: 'bg-gray-500/20' },
    'in-progress': { icon: PlayCircle, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    'completed': { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20' },
    'blocked': { icon: AlertCircle, color: 'text-red-400', bg: 'bg-red-500/20' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalTaskCardProps {
    entity: UniversalEntity<ProjectTask>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalTaskCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
}: UniversalTaskCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query for reactive updates
    const liveTask = useLiveQuery(
        () => db.project_tasks.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const task = liveTask || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
        defaultValues: {
            title: '',
            status: 'pending',
            priority: 3,
            phase: '',
            estimated_time: '',
        },
    });

    // Reset form when task changes or edit mode opens
    useEffect(() => {
        if (task) {
            reset({
                title: task.title || '',
                status: task.status || 'pending',
                priority: task.priority || 3,
                phase: task.phase || '',
                estimated_time: task.estimated_time || '',
            });
        }
    }, [task, isEditing, reset]);

    // DND - Transporter compatible
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-task-${task.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: task },
            entityType: 'task',
            id: task.id,
            title: task.title,
            metadata: {
                status: task.status,
                priority: task.priority,
                phase: task.phase,
            },
            origin: dragOrigin
        } as UniversalDragPayload & { entityType: string; id: number; title: string; metadata: any },
        disabled: isEditing
    });

    const style = {
        transform: CSS.Translate.toString(transform),
        zIndex: isDragging ? 999 : undefined,
    };

    // Form submit
    const onSubmit = async (data: EditFormData) => {
        try {
            await db.project_tasks.update(task.id!, {
                title: data.title,
                status: data.status,
                priority: data.priority as 1 | 2 | 3 | 4 | 5,
                phase: data.phase || undefined,
                estimated_time: data.estimated_time || undefined,
            });
            toast.success('Task updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update task');
            console.error(err);
        }
    };

    // Status config
    const statusConfig = STATUS_CONFIG[task.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.pending;
    const StatusIcon = statusConfig.icon;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-10 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-accent uppercase tracking-wider">Edit Task</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Status</label>
                            <select
                                {...register('status')}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                            >
                                <option value="pending">Pending</option>
                                <option value="in-progress">In Progress</option>
                                <option value="completed">Completed</option>
                                <option value="blocked">Blocked</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Priority</label>
                            <select
                                {...register('priority')}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                            >
                                <option value="1">1 - Lowest</option>
                                <option value="2">2 - Low</option>
                                <option value="3">3 - Medium</option>
                                <option value="4">4 - High</option>
                                <option value="5">5 - Critical</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Phase" {...register('phase')} placeholder="e.g. Planning" />
                        <Input label="Estimated Time" {...register('estimated_time')} placeholder="e.g. 2h" />
                    </div>

                    <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                        <Button type="button" variant="ghost" size="sm" onClick={() => setIsEditing(false)}>Cancel</Button>
                        <Button type="submit" size="sm" disabled={isSubmitting}>
                            <Save size={14} className="mr-1" /> Save
                        </Button>
                    </div>
                </form>
            </div>
        );
    }

    // ========================================================================
    // VIEW MODE
    // ========================================================================

    return (
        <div
            ref={setNodeRef}
            style={style}
            onClick={onClick}
            className={clsx(
                'group relative bg-surface border rounded-lg transition-all p-4 min-h-[100px]',
                isDragging && 'opacity-30 scale-95',
                task.status === 'blocked' ? 'border-red-500/50' :
                    task.status === 'completed' ? 'border-green-500/50' :
                        task.is_high_priority ? 'border-amber-500/50' : 'border-white/10',
                'hover:border-accent/50 hover:shadow-lg hover:-translate-y-0.5'
            )}
        >
            {/* Drag Handle */}
            <div
                {...listeners}
                {...attributes}
                className="absolute top-2 right-12 p-1 rounded cursor-grab active:cursor-grabbing text-gray-600 hover:text-white hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                title="Drag to Transporter"
            >
                <GripVertical size={14} />
            </div>

            {/* Status Badge */}
            <div className={clsx('absolute top-2 left-2 p-1.5 rounded-md', statusConfig.bg)}>
                <StatusIcon size={14} className={statusConfig.color} />
            </div>

            {/* Priority Flag */}
            {(task.is_high_priority || task.priority >= 4) && (
                <div className="absolute top-2 left-10 p-1.5 rounded-md bg-amber-500/20">
                    <Flag size={14} className="text-amber-400" />
                </div>
            )}

            {/* Content */}
            <div className="mt-8">
                <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2">
                    {task.title}
                </h3>

                {task.phase && (
                    <span className="text-xs text-gray-500 mt-1 block">
                        Phase: {task.phase}
                    </span>
                )}

                {/* Meta Row */}
                <div className="flex items-center gap-3 mt-3 text-xs text-gray-500">
                    {task.estimated_time && (
                        <span className="flex items-center gap-1">
                            <Clock size={12} /> {task.estimated_time}
                        </span>
                    )}
                    {task.scheduled_date && (
                        <span className="flex items-center gap-1">
                            <Calendar size={12} /> {new Date(task.scheduled_date).toLocaleDateString()}
                        </span>
                    )}
                    {task.energy_level && (
                        <span className="flex items-center gap-1">
                            <Zap size={12} className={
                                task.energy_level === 'high' ? 'text-red-400' :
                                    task.energy_level === 'medium' ? 'text-amber-400' : 'text-green-400'
                            } />
                            {task.energy_level}
                        </span>
                    )}
                </div>

                {/* Caution Flags */}
                {task.caution_flags && task.caution_flags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                        {task.caution_flags.map((flag, i) => (
                            <span key={i} className="flex items-center gap-1 text-[10px] px-1.5 py-0.5 rounded bg-amber-500/20 text-amber-400">
                                <AlertTriangle size={10} /> {flag}
                            </span>
                        ))}
                    </div>
                )}
            </div>

            {/* Action Buttons */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                    className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                    title="Edit"
                >
                    <Settings size={12} />
                </button>
            </div>
        </div>
    );
}
