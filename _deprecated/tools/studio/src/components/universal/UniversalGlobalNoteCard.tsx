/**
 * UniversalGlobalNoteCard
 * Card for displaying global notes with pinned status.
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
    GripVertical, Settings, Save, X, StickyNote, Pin, Trash2
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { GlobalNote } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    content: z.string(),
    category: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// PROPS
// ============================================================================

interface UniversalGlobalNoteCardProps {
    entity: UniversalEntity<GlobalNote>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalGlobalNoteCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
}: UniversalGlobalNoteCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveNote = useLiveQuery(
        () => db.global_notes.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const note = liveNote || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (note) {
            reset({
                title: note.title || '',
                content: note.content || '',
                category: note.category || '',
            });
        }
    }, [note, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-note-${note.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: note },
            entityType: 'note',
            id: note.id,
            title: note.title,
            metadata: { category: note.category, pinned: note.pinned },
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
            await db.global_notes.update(note.id!, {
                title: data.title,
                content: data.content,
                category: data.category || undefined,
                updated_at: new Date(),
            });
            toast.success('Note updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update');
        }
    };

    // Toggle pin
    const handleTogglePin = async () => {
        try {
            await db.global_notes.update(note.id!, { pinned: !note.pinned });
            toast.success(note.pinned ? 'Unpinned' : 'Pinned');
        } catch (err) {
            toast.error('Failed to update');
        }
    };

    // Delete
    const handleDelete = async () => {
        if (confirm('Delete this note?')) {
            try {
                await db.global_notes.delete(note.id!);
                toast.success('Note deleted');
            } catch (err) {
                toast.error('Failed to delete');
            }
        }
    };

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-amber-500/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-amber-400 uppercase tracking-wider">Edit Note</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />
                    <Input label="Category" {...register('category')} placeholder="e.g. Work, Personal" />

                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Content</label>
                        <textarea
                            {...register('content')}
                            rows={4}
                            className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-amber-500 resize-none"
                        />
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
                note.pinned ? 'border-amber-500/50 bg-amber-950/10' : 'border-white/10',
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

            {/* Pin indicator */}
            {note.pinned && (
                <Pin size={12} className="absolute top-2 left-2 text-amber-400" />
            )}

            {/* Icon + Category */}
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1.5 rounded', note.pinned ? 'bg-amber-500/20' : 'bg-white/10')}>
                    <StickyNote size={14} className={note.pinned ? 'text-amber-400' : 'text-gray-400'} />
                </div>
                {note.category && (
                    <span className="text-[10px] text-gray-500 bg-white/5 px-1.5 rounded">
                        {note.category}
                    </span>
                )}
            </div>

            {/* Title */}
            <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 mb-2">
                {note.title}
            </h3>

            {/* Preview Content */}
            {note.content && (
                <p className="text-xs text-gray-500 line-clamp-3">
                    {note.content.substring(0, 150)}
                </p>
            )}

            {/* Action Buttons */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); handleTogglePin(); }}
                    className={clsx('p-1.5 rounded transition-colors', note.pinned ? 'bg-amber-500/20 text-amber-400' : 'bg-white/10 text-gray-400 hover:text-amber-400')}
                    title={note.pinned ? 'Unpin' : 'Pin'}
                >
                    <Pin size={12} />
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
