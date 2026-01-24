/**
 * UniversalRoutineCard
 * A specialized card for displaying Routine entities in the Universal system.
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
    GripVertical, Settings, Save, X, RefreshCw, Check, AlertTriangle,
    Calendar, Clock, Tag
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Routine } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    frequency: z.enum(['daily', 'weekly', 'biweekly', 'monthly', 'quarterly', 'yearly']),
    category: z.string().optional(),
    season: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const FREQUENCY_CONFIG = {
    'daily': { label: 'Daily', color: 'text-red-400' },
    'weekly': { label: 'Weekly', color: 'text-orange-400' },
    'biweekly': { label: 'Biweekly', color: 'text-amber-400' },
    'monthly': { label: 'Monthly', color: 'text-blue-400' },
    'quarterly': { label: 'Quarterly', color: 'text-purple-400' },
    'yearly': { label: 'Yearly', color: 'text-green-400' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalRoutineCardProps {
    entity: UniversalEntity<Routine>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onComplete?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalRoutineCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    onComplete,
}: UniversalRoutineCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveRoutine = useLiveQuery(
        () => db.routines.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const routine = liveRoutine || initialEntity.data;

    // Computed
    const isOverdue = routine.next_due && new Date(routine.next_due) < new Date();
    const isDueToday = routine.next_due &&
        new Date(routine.next_due).toDateString() === new Date().toDateString();

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (routine) {
            reset({
                title: routine.title || '',
                frequency: routine.frequency || 'weekly',
                category: routine.category || '',
                season: routine.season || '',
            });
        }
    }, [routine, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-routine-${routine.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: routine },
            entityType: 'routine',
            id: routine.id,
            title: routine.title,
            metadata: { frequency: routine.frequency, category: routine.category, next_due: routine.next_due },
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
            await db.routines.update(routine.id!, {
                title: data.title,
                frequency: data.frequency,
                category: data.category || undefined,
                season: data.season || undefined,
            });
            toast.success('Routine updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update routine');
        }
    };

    // Mark as complete
    const handleComplete = async () => {
        try {
            const nextDue = calculateNextDue(routine.frequency);
            await db.routines.update(routine.id!, {
                last_completed: new Date(),
                next_due: nextDue,
            });
            toast.success('Routine completed!');
            if (onComplete) onComplete();
        } catch (err) {
            toast.error('Failed to complete routine');
        }
    };

    const freqConfig = FREQUENCY_CONFIG[routine.frequency as keyof typeof FREQUENCY_CONFIG] || FREQUENCY_CONFIG.weekly;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-accent uppercase tracking-wider">Edit Routine</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Frequency</label>
                            <select {...register('frequency')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent">
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="biweekly">Biweekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="quarterly">Quarterly</option>
                                <option value="yearly">Yearly</option>
                            </select>
                        </div>
                        <Input label="Category" {...register('category')} placeholder="e.g. Maintenance" />
                    </div>

                    <Input label="Season (optional)" {...register('season')} placeholder="e.g. winter" />

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
                isOverdue ? 'border-red-500/50 bg-red-950/20' :
                    isDueToday ? 'border-amber-500/50' : 'border-white/10',
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
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1.5 rounded', isOverdue ? 'bg-red-500/20' : 'bg-blue-500/20')}>
                    {isOverdue ? (
                        <AlertTriangle size={14} className="text-red-400" />
                    ) : (
                        <RefreshCw size={14} className="text-blue-400" />
                    )}
                </div>
                <span className={clsx('text-xs font-bold', freqConfig.color)}>
                    {freqConfig.label}
                </span>
                {routine.season && (
                    <span className="text-[10px] text-gray-500 bg-white/5 px-1.5 rounded">
                        {routine.season}
                    </span>
                )}
            </div>

            {/* Title */}
            <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 mb-2">
                {routine.title}
            </h3>

            {/* Meta Row */}
            <div className="flex items-center gap-3 text-xs text-gray-500">
                {routine.next_due && (
                    <span className={clsx('flex items-center gap-1', isOverdue && 'text-red-400')}>
                        <Calendar size={10} />
                        {isOverdue ? 'Overdue: ' : 'Due: '}
                        {new Date(routine.next_due).toLocaleDateString()}
                    </span>
                )}
                {routine.last_completed && (
                    <span className="flex items-center gap-1">
                        <Clock size={10} />
                        Last: {new Date(routine.last_completed).toLocaleDateString()}
                    </span>
                )}
            </div>

            {/* Category */}
            {routine.category && (
                <div className="mt-2">
                    <span className="flex items-center gap-1 text-[10px] text-gray-500 bg-white/5 px-1.5 py-0.5 rounded w-fit">
                        <Tag size={10} /> {routine.category}
                    </span>
                </div>
            )}

            {/* Action Buttons */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); handleComplete(); }}
                    className="p-1.5 rounded bg-green-500/20 text-green-400 hover:text-green-300 hover:bg-green-500/30 transition-colors"
                    title="Mark Complete"
                >
                    <Check size={12} />
                </button>
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

// Helper to calculate next due date based on frequency
function calculateNextDue(frequency: string): Date {
    const now = new Date();
    switch (frequency) {
        case 'daily': return new Date(now.setDate(now.getDate() + 1));
        case 'weekly': return new Date(now.setDate(now.getDate() + 7));
        case 'biweekly': return new Date(now.setDate(now.getDate() + 14));
        case 'monthly': return new Date(now.setMonth(now.getMonth() + 1));
        case 'quarterly': return new Date(now.setMonth(now.getMonth() + 3));
        case 'yearly': return new Date(now.setFullYear(now.getFullYear() + 1));
        default: return new Date(now.setDate(now.getDate() + 7));
    }
}
