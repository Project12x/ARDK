/**
 * UniversalReminderCard
 * Card for reminder display with complete action.
 * Compatible with Transporter DnD and Universal Card system.
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
    GripVertical, Settings, Save, X, Bell, Check, Trash2
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Reminder } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    content: z.string().min(1, 'Content required'),
    priority: z.number().min(1).max(5),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const PRIORITY_COLORS: Record<number, string> = {
    1: 'text-gray-400',
    2: 'text-blue-400',
    3: 'text-amber-400',
    4: 'text-orange-400',
    5: 'text-red-400',
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalReminderCardProps {
    entity: UniversalEntity<Reminder>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onComplete?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalReminderCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    onComplete,
}: UniversalReminderCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveReminder = useLiveQuery(
        () => db.reminders.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const reminder = liveReminder || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (reminder) {
            reset({
                content: reminder.content || '',
                priority: reminder.priority || 2,
            });
        }
    }, [reminder, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-reminder-${reminder.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: reminder },
            entityType: 'reminder',
            id: reminder.id,
            title: reminder.content,
            metadata: { priority: reminder.priority, is_completed: reminder.is_completed },
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
            await db.reminders.update(reminder.id!, {
                content: data.content,
                priority: data.priority,
            });
            toast.success('Reminder updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update');
        }
    };

    // Complete
    const handleComplete = async () => {
        try {
            await db.reminders.update(reminder.id!, { is_completed: !reminder.is_completed });
            toast.success(reminder.is_completed ? 'Unmarked' : 'Completed!');
            if (onComplete) onComplete();
        } catch (err) {
            toast.error('Failed to update');
        }
    };

    // Delete
    const handleDelete = async () => {
        if (confirm('Delete this reminder?')) {
            try {
                await db.reminders.delete(reminder.id!);
                toast.success('Deleted');
            } catch (err) {
                toast.error('Failed to delete');
            }
        }
    };

    const priorityColor = PRIORITY_COLORS[reminder.priority] || PRIORITY_COLORS[2];

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-amber-500/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">Edit Reminder</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Content</label>
                        <textarea
                            {...register('content')}
                            rows={2}
                            className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 resize-none"
                        />
                        {errors.content && <span className="text-xs text-red-500">{errors.content.message}</span>}
                    </div>

                    <Input label="Priority (1-5)" type="number" {...register('priority', { valueAsNumber: true })} />

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
                reminder.is_completed ? 'border-green-500/30 opacity-60' : 'border-white/10',
                'hover:border-amber-500/50 hover:shadow-lg hover:-translate-y-0.5'
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

            {/* Header */}
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1.5 rounded', reminder.is_completed ? 'bg-green-500/20' : 'bg-amber-500/20')}>
                    {reminder.is_completed ? (
                        <Check size={14} className="text-green-400" />
                    ) : (
                        <Bell size={14} className={priorityColor} />
                    )}
                </div>
                <span className={clsx('text-xs font-bold', priorityColor)}>
                    P{reminder.priority}
                </span>
                {reminder.is_completed && (
                    <span className="text-[10px] text-green-400 bg-green-500/20 px-1.5 rounded">
                        Done
                    </span>
                )}
            </div>

            {/* Content */}
            <p className={clsx(
                'text-sm line-clamp-3',
                reminder.is_completed ? 'text-gray-500 line-through' : 'text-white'
            )}>
                {reminder.content}
            </p>

            {/* Action Buttons */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); handleComplete(); }}
                    className={clsx(
                        'p-1.5 rounded transition-colors',
                        reminder.is_completed
                            ? 'bg-gray-500/20 text-gray-400'
                            : 'bg-green-500/20 text-green-400 hover:text-green-300'
                    )}
                    title={reminder.is_completed ? 'Undo' : 'Complete'}
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
                <button
                    onClick={(e) => { e.stopPropagation(); handleDelete(); }}
                    className="p-1.5 rounded bg-red-500/20 text-red-400 hover:text-red-300 hover:bg-red-500/30 transition-colors"
                    title="Delete"
                >
                    <Trash2 size={12} />
                </button>
            </div>
        </div>
    );
}
