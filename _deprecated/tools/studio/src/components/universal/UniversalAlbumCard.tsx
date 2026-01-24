/**
 * UniversalAlbumCard
 * A specialized card for displaying Album entities in the Universal system.
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
    GripVertical, Settings, Save, X, Disc, Play, Calendar, User, Music
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Album } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    artist: z.string().optional(),
    status: z.enum(['planned', 'in-progress', 'released']),
    release_date: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const STATUS_CONFIG = {
    'planned': { color: 'text-gray-400', bg: 'bg-gray-500/20', label: 'Planned' },
    'in-progress': { color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'In Progress' },
    'released': { color: 'text-green-400', bg: 'bg-green-500/20', label: 'Released' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalAlbumCardProps {
    entity: UniversalEntity<Album>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    trackCount?: number;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalAlbumCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    trackCount = 0,
}: UniversalAlbumCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveAlbum = useLiveQuery(
        () => db.albums.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const album = liveAlbum || initialEntity.data;

    // Get track count
    const tracks = useLiveQuery(
        () => db.songs.where('album_id').equals(album.id!).count(),
        [album.id]
    );

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (album) {
            reset({
                title: album.title || '',
                artist: album.artist || '',
                status: album.status || 'planned',
                release_date: album.release_date ? new Date(album.release_date).toISOString().split('T')[0] : '',
            });
        }
    }, [album, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-album-${album.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: album },
            entityType: 'album',
            id: album.id,
            title: album.title,
            metadata: { status: album.status, artist: album.artist },
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
            await db.albums.update(album.id!, {
                title: data.title,
                artist: data.artist || undefined,
                status: data.status,
                release_date: data.release_date ? new Date(data.release_date) : undefined,
                updated_at: new Date(),
            });
            toast.success('Album updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update album');
        }
    };

    const statusConfig = STATUS_CONFIG[album.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.planned;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-accent uppercase tracking-wider">Edit Album</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />
                    <Input label="Artist" {...register('artist')} placeholder="Artist name" />

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Status</label>
                            <select {...register('status')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent">
                                <option value="planned">Planned</option>
                                <option value="in-progress">In Progress</option>
                                <option value="released">Released</option>
                            </select>
                        </div>
                        <Input label="Release Date" type="date" {...register('release_date')} />
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
                album.status === 'released' ? 'border-green-500/50' : 'border-white/10',
                'hover:border-accent/50 hover:shadow-lg hover:-translate-y-0.5'
            )}
        >
            {/* Cover Art */}
            <div className="aspect-square bg-gradient-to-br from-gray-800 to-black relative overflow-hidden">
                {album.cover_art_url ? (
                    <img src={album.cover_art_url} alt={album.title} className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <Disc size={48} className="text-gray-700" />
                    </div>
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

                {/* Status Badge */}
                <div className={clsx('absolute top-2 left-2 px-2 py-0.5 rounded-full text-[10px] font-bold', statusConfig.bg, statusConfig.color)}>
                    {statusConfig.label}
                </div>

                {/* Track Count */}
                <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded-full bg-black/70 text-white text-[10px] font-bold flex items-center gap-1">
                    <Music size={10} /> {tracks || trackCount} tracks
                </div>
            </div>

            {/* Content */}
            <div className="p-3">
                <h3 className="font-semibold text-white text-sm leading-tight line-clamp-1">{album.title}</h3>

                {album.artist && (
                    <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                        <User size={10} /> {album.artist}
                    </div>
                )}

                {album.release_date && (
                    <div className="flex items-center gap-1 mt-1 text-xs text-gray-500">
                        <Calendar size={10} /> {new Date(album.release_date).toLocaleDateString()}
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
