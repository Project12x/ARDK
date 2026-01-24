/**
 * UniversalLibraryCard
 * A specialized card for displaying LibraryItem entities in the Universal system.
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
    GripVertical, Settings, Save, X, FileText, Book, Image as ImageIcon,
    Disc, Film, Archive, Download, Trash2, Eye
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { LibraryItem } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    category: z.enum(['bookshelf', 'records', 'photos', 'vhs', 'junk']),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const TYPE_ICONS: Record<string, typeof FileText> = {
    'pdf': FileText,
    'text': FileText,
    'ebook': Book,
    'image': ImageIcon,
    'audio': Disc,
    'video': Film,
    'other': Archive,
};

const TYPE_COLORS: Record<string, string> = {
    'pdf': 'text-red-400',
    'text': 'text-gray-400',
    'ebook': 'text-amber-400',
    'image': 'text-green-400',
    'audio': 'text-pink-400',
    'video': 'text-cyan-400',
    'other': 'text-blue-400',
};

const CATEGORY_CONFIG: Record<string, { label: string; bg: string }> = {
    'bookshelf': { label: 'Bookshelf', bg: 'bg-amber-500/20' },
    'records': { label: 'Records', bg: 'bg-pink-500/20' },
    'photos': { label: 'Photos', bg: 'bg-green-500/20' },
    'vhs': { label: 'VHS', bg: 'bg-cyan-500/20' },
    'junk': { label: 'Junk', bg: 'bg-gray-500/20' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalLibraryCardProps {
    entity: UniversalEntity<LibraryItem>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onPreview?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalLibraryCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    onPreview,
}: UniversalLibraryCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveItem = useLiveQuery(
        () => db.library_items.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const item = liveItem || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (item) {
            reset({
                title: item.title || '',
                category: (item.category as any) || 'junk',
            });
        }
    }, [item, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-library-${item.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: item },
            entityType: 'library',
            id: item.id,
            title: item.title,
            metadata: { type: item.type, category: item.category },
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
            await db.library_items.update(item.id!, {
                title: data.title,
                category: data.category,
            });
            toast.success('Library item updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update item');
        }
    };

    // Download handler
    const handleDownload = () => {
        if (item.content) {
            const link = document.createElement('a');
            link.href = item.content;
            link.download = item.title;
            link.click();
        }
    };

    // Delete handler
    const handleDelete = async () => {
        if (confirm('Delete this library item?')) {
            try {
                await db.library_items.delete(item.id!);
                toast.success('Item deleted');
            } catch (err) {
                toast.error('Failed to delete');
            }
        }
    };

    const TypeIcon = TYPE_ICONS[item.type] || Archive;
    const typeColor = TYPE_COLORS[item.type] || 'text-blue-400';
    const categoryConfig = CATEGORY_CONFIG[item.category || 'junk'] || CATEGORY_CONFIG.junk;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-indigo-500/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-indigo-400 uppercase tracking-wider">Edit Library Item</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />

                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Category</label>
                        <select {...register('category')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-indigo-500">
                            <option value="bookshelf">📚 Bookshelf</option>
                            <option value="records">💿 Records</option>
                            <option value="photos">📷 Photos</option>
                            <option value="vhs">📼 VHS</option>
                            <option value="junk">📦 Junk Drawer</option>
                        </select>
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
                'group relative bg-surface border rounded-lg transition-all overflow-hidden',
                isDragging && 'opacity-30 scale-95',
                'border-white/10 hover:border-indigo-500/50 hover:shadow-lg hover:-translate-y-0.5'
            )}
        >
            {/* Thumbnail / Preview */}
            <div className="aspect-[3/4] bg-black/60 relative overflow-hidden flex items-center justify-center">
                {item.type === 'image' && item.content ? (
                    <img src={item.content} alt={item.title} className="w-full h-full object-cover" />
                ) : (
                    <TypeIcon size={48} className={clsx(typeColor, 'opacity-60')} />
                )}

                {/* Drag Handle */}
                <div
                    {...listeners}
                    {...attributes}
                    className="absolute top-2 right-2 p-1.5 rounded cursor-grab active:cursor-grabbing bg-black/50 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity z-10"
                    title="Drag to Transporter"
                >
                    <GripVertical size={14} />
                </div>

                {/* Category Badge */}
                <div className={clsx('absolute top-2 left-2 px-2 py-0.5 rounded-full text-[10px] font-bold text-white', categoryConfig.bg)}>
                    {categoryConfig.label}
                </div>

                {/* Type Badge */}
                <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/70 text-[10px] font-mono text-gray-400 uppercase">
                    {item.type}
                </div>

                {/* Preview Button */}
                {(item.type === 'image' || item.type === 'pdf') && onPreview && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onPreview(); }}
                        className="absolute bottom-2 left-2 p-1.5 rounded bg-white/10 text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"
                    >
                        <Eye size={14} />
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="p-3">
                <h3 className="font-semibold text-white text-xs leading-tight line-clamp-2" title={item.title}>
                    {item.title}
                </h3>

                {item.file_size && (
                    <div className="mt-1 text-[10px] text-gray-500 font-mono">
                        {(item.file_size / 1024).toFixed(0)} KB
                    </div>
                )}
            </div>

            {/* Action Buttons */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                {item.content && (
                    <button
                        onClick={(e) => { e.stopPropagation(); handleDownload(); }}
                        className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                        title="Download"
                    >
                        <Download size={12} />
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
