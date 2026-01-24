/**
 * UniversalInboxCard
 * A specialized card for displaying InboxItem entities in the Universal system.
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
    GripVertical, Settings, Save, X, Inbox, StickyNote, Link, Lightbulb,
    CheckSquare, File, CheckCircle, Clock, Trash2
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { InboxItem } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    content: z.string().min(1, 'Content required'),
    type: z.enum(['note', 'link', 'idea', 'task', 'file']),
    suggested_action: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const TYPE_CONFIG = {
    'note': { icon: StickyNote, color: 'text-blue-400', bg: 'bg-blue-500/20' },
    'link': { icon: Link, color: 'text-green-400', bg: 'bg-green-500/20' },
    'idea': { icon: Lightbulb, color: 'text-amber-400', bg: 'bg-amber-500/20' },
    'task': { icon: CheckSquare, color: 'text-purple-400', bg: 'bg-purple-500/20' },
    'file': { icon: File, color: 'text-gray-400', bg: 'bg-gray-500/20' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalInboxCardProps {
    entity: UniversalEntity<InboxItem>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onTriage?: (item: InboxItem) => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalInboxCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    onTriage,
}: UniversalInboxCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query for reactive updates
    const liveItem = useLiveQuery(
        () => db.inbox_items.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const item = liveItem || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
        defaultValues: {
            content: '',
            type: 'note',
            suggested_action: '',
        },
    });

    // Reset form
    useEffect(() => {
        if (item) {
            reset({
                content: item.content || '',
                type: (item.type as any) || 'note',
                suggested_action: item.suggested_action || '',
            });
        }
    }, [item, isEditing, reset]);

    // DND - Transporter compatible
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-inbox-${item.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: item },
            entityType: 'inbox',
            id: item.id,
            title: item.content?.substring(0, 50) || 'Inbox Item',
            metadata: {
                type: item.type,
                triaged: !!item.triaged_at,
                suggested_action: item.suggested_action,
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
            await db.inbox_items.update(item.id!, {
                content: data.content,
                type: data.type,
                suggested_action: data.suggested_action || undefined,
            });
            toast.success('Inbox item updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update item');
            console.error(err);
        }
    };

    // Mark as triaged
    const handleTriage = async () => {
        try {
            await db.inbox_items.update(item.id!, {
                triaged_at: new Date(),
            });
            toast.success('Item triaged');
            if (onTriage) onTriage(item);
        } catch (err) {
            toast.error('Failed to triage item');
        }
    };

    // Delete
    const handleDelete = async () => {
        try {
            await db.inbox_items.delete(item.id!);
            toast.success('Item deleted');
        } catch (err) {
            toast.error('Failed to delete item');
        }
    };

    // Config
    const typeConfig = TYPE_CONFIG[item.type as keyof typeof TYPE_CONFIG] || TYPE_CONFIG.note;
    const TypeIcon = typeConfig.icon;
    const isTriaged = !!item.triaged_at;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-10 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-accent uppercase tracking-wider">Edit Inbox Item</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Content</label>
                        <textarea
                            {...register('content')}
                            rows={3}
                            className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent resize-none"
                        />
                        {errors.content && <span className="text-xs text-red-500">{errors.content.message}</span>}
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Type</label>
                            <select
                                {...register('type')}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                            >
                                <option value="note">Note</option>
                                <option value="link">Link</option>
                                <option value="idea">Idea</option>
                                <option value="task">Task</option>
                                <option value="file">File</option>
                            </select>
                        </div>
                        <Input label="Suggested Action" {...register('suggested_action')} placeholder="e.g. Create task" />
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
                isTriaged ? 'border-green-500/30 opacity-60' : 'border-white/10',
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

            {/* Type & Status Badges */}
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1.5 rounded', typeConfig.bg)}>
                    <TypeIcon size={14} className={typeConfig.color} />
                </div>
                {isTriaged ? (
                    <span className="flex items-center gap-1 text-[10px] text-green-400">
                        <CheckCircle size={10} /> Triaged
                    </span>
                ) : (
                    <span className="flex items-center gap-1 text-[10px] text-amber-400">
                        <Clock size={10} /> Pending
                    </span>
                )}
            </div>

            {/* Content Preview */}
            <p className="text-sm text-white line-clamp-3 leading-relaxed">
                {item.content}
            </p>

            {/* Suggested Action */}
            {item.suggested_action && (
                <div className="mt-2 text-xs text-gray-500 italic">
                    💡 {item.suggested_action}
                </div>
            )}

            {/* Timestamp */}
            <div className="mt-2 text-[10px] text-gray-600">
                {new Date(item.created_at).toLocaleString()}
            </div>

            {/* Action Buttons */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {!isTriaged && (
                    <button
                        onClick={(e) => { e.stopPropagation(); handleTriage(); }}
                        className="p-1.5 rounded bg-green-500/20 text-green-400 hover:text-green-300 hover:bg-green-500/30 transition-colors"
                        title="Mark as Triaged"
                    >
                        <CheckCircle size={12} />
                    </button>
                )}
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
