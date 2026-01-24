/**
 * UniversalGoalCard
 * A specialized card for displaying Goal entities in the Universal system.
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
    GripVertical, Settings, Save, X, Star, Calendar, BarChart2, Target,
    CheckCircle, PlayCircle, Pause, XCircle
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Goal } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    level: z.enum(['vision', 'year', 'quarter', 'objective']),
    status: z.enum(['active', 'achieved', 'paused', 'abandoned']),
    progress: z.preprocess(
        val => (val === '' || val === null ? 0 : Number(val)),
        z.number().min(0).max(100)
    ),
    target_date: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const STATUS_CONFIG = {
    'active': { icon: PlayCircle, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    'achieved': { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20' },
    'paused': { icon: Pause, color: 'text-amber-400', bg: 'bg-amber-500/20' },
    'abandoned': { icon: XCircle, color: 'text-gray-400', bg: 'bg-gray-500/20' },
};

const LEVEL_CONFIG = {
    'vision': { icon: Star, color: 'text-purple-400', label: '🌟 Vision' },
    'year': { icon: Calendar, color: 'text-blue-400', label: '📅 Annual' },
    'quarter': { icon: BarChart2, color: 'text-green-400', label: '📊 Quarterly' },
    'objective': { icon: Target, color: 'text-amber-400', label: '🎯 Objective' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalGoalCardProps {
    entity: UniversalEntity<Goal>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalGoalCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
}: UniversalGoalCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query for reactive updates
    const liveGoal = useLiveQuery(
        () => db.goals.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const goal = liveGoal || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
        defaultValues: {
            title: '',
            level: 'objective',
            status: 'active',
            progress: 0,
            target_date: '',
        },
    });

    // Reset form
    useEffect(() => {
        if (goal) {
            reset({
                title: goal.title || '',
                level: goal.level || 'objective',
                status: goal.status || 'active',
                progress: goal.progress || 0,
                target_date: goal.target_date ? new Date(goal.target_date).toISOString().split('T')[0] : '',
            });
        }
    }, [goal, isEditing, reset]);

    // DND - Transporter compatible
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-goal-${goal.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: goal },
            entityType: 'goal',
            id: goal.id,
            title: goal.title,
            metadata: {
                status: goal.status,
                level: goal.level,
                progress: goal.progress,
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
            await db.goals.update(goal.id!, {
                title: data.title,
                level: data.level,
                status: data.status,
                progress: data.progress,
                target_date: data.target_date ? new Date(data.target_date) : undefined,
                updated_at: new Date(),
            });
            toast.success('Goal updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update goal');
            console.error(err);
        }
    };

    // Configs
    const statusConfig = STATUS_CONFIG[goal.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.active;
    const levelConfig = LEVEL_CONFIG[goal.level as keyof typeof LEVEL_CONFIG] || LEVEL_CONFIG.objective;
    const StatusIcon = statusConfig.icon;
    const LevelIcon = levelConfig.icon;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-purple-500/50 rounded-xl p-4 shadow-xl z-10 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider">Edit Goal</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Level</label>
                            <select
                                {...register('level')}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                            >
                                <option value="vision">Vision</option>
                                <option value="year">Annual Goal</option>
                                <option value="quarter">Quarterly Goal</option>
                                <option value="objective">Objective</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Status</label>
                            <select
                                {...register('status')}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500"
                            >
                                <option value="active">Active</option>
                                <option value="achieved">Achieved</option>
                                <option value="paused">Paused</option>
                                <option value="abandoned">Abandoned</option>
                            </select>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Progress (%)" type="number" {...register('progress')} min={0} max={100} />
                        <Input label="Target Date" type="date" {...register('target_date')} />
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
                'group relative bg-surface border rounded-lg transition-all p-4',
                isDragging && 'opacity-30 scale-95',
                goal.status === 'achieved' ? 'border-green-500/50' :
                    goal.status === 'paused' ? 'border-amber-500/50' :
                        goal.status === 'abandoned' ? 'border-gray-500/50' : 'border-purple-500/30',
                'hover:border-purple-500/60 hover:shadow-lg hover:-translate-y-0.5'
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

            {/* Level Badge */}
            <div className="flex items-center gap-2 mb-2">
                <span className={clsx('text-xs font-bold px-2 py-0.5 rounded', levelConfig.color, 'bg-white/5')}>
                    {levelConfig.label}
                </span>
                <div className={clsx('p-1 rounded', statusConfig.bg)}>
                    <StatusIcon size={12} className={statusConfig.color} />
                </div>
            </div>

            {/* Title */}
            <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 mb-3">
                {goal.title}
            </h3>

            {/* Progress Bar */}
            <div className="relative h-2 bg-white/10 rounded-full overflow-hidden mb-2">
                <div
                    className={clsx(
                        'absolute inset-y-0 left-0 rounded-full transition-all',
                        goal.status === 'achieved' ? 'bg-green-500' :
                            goal.status === 'paused' ? 'bg-amber-500' : 'bg-purple-500'
                    )}
                    style={{ width: `${goal.progress || 0}%` }}
                />
            </div>
            <div className="flex justify-between text-xs text-gray-500">
                <span>{goal.progress || 0}%</span>
                {goal.target_date && (
                    <span className="flex items-center gap-1">
                        <Calendar size={10} /> {new Date(goal.target_date).toLocaleDateString()}
                    </span>
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
