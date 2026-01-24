/**
 * UniversalSongCard
 * A specialized card for displaying Song entities in the Universal system.
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
    GripVertical, Settings, Save, X, Music, Play, Pause, Mic, Radio,
    Disc, Check, Clock, Hash
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Song } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    status: z.enum(['draft', 'idea', 'demo', 'recording', 'mixing', 'mastering', 'released']),
    bpm: z.preprocess(val => (val === '' || val === null ? undefined : Number(val)), z.number().optional()),
    key: z.string().optional(),
    duration: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const STATUS_CONFIG = {
    'idea': { icon: Music, color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Idea' },
    'draft': { icon: Music, color: 'text-gray-400', bg: 'bg-gray-500/20', label: 'Draft' },
    'demo': { icon: Mic, color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Demo' },
    'recording': { icon: Radio, color: 'text-blue-400', bg: 'bg-blue-500/20', label: 'Recording' },
    'mixing': { icon: Disc, color: 'text-cyan-400', bg: 'bg-cyan-500/20', label: 'Mixing' },
    'mastering': { icon: Disc, color: 'text-pink-400', bg: 'bg-pink-500/20', label: 'Mastering' },
    'released': { icon: Check, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Released' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalSongCardProps {
    entity: UniversalEntity<Song>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onPlay?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalSongCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    onPlay,
}: UniversalSongCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveSong = useLiveQuery(
        () => db.songs.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const song = liveSong || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema) as any,
    });

    useEffect(() => {
        if (song) {
            reset({
                title: song.title || '',
                status: song.status || 'draft',
                bpm: song.bpm,
                key: song.key || '',
                duration: song.duration || '',
            });
        }
    }, [song, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-song-${song.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: song },
            entityType: 'song',
            id: song.id,
            title: song.title,
            metadata: { status: song.status, bpm: song.bpm, key: song.key },
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
            await db.songs.update(song.id!, {
                title: data.title,
                status: data.status,
                bpm: data.bpm,
                key: data.key || undefined,
                duration: data.duration || undefined,
                updated_at: new Date(),
            });
            toast.success('Song updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update song');
        }
    };

    const statusConfig = STATUS_CONFIG[song.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.draft;
    const StatusIcon = statusConfig.icon;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-purple-500/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-purple-400 uppercase tracking-wider">Edit Song</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Status</label>
                            <select {...register('status')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-purple-500">
                                <option value="idea">Idea</option>
                                <option value="draft">Draft</option>
                                <option value="demo">Demo</option>
                                <option value="recording">Recording</option>
                                <option value="mixing">Mixing</option>
                                <option value="mastering">Mastering</option>
                                <option value="released">Released</option>
                            </select>
                        </div>
                        <Input label="Key" {...register('key')} placeholder="e.g. Am" />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="BPM" type="number" {...register('bpm')} placeholder="120" />
                        <Input label="Duration" {...register('duration')} placeholder="3:45" />
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
                song.status === 'released' ? 'border-green-500/50' : 'border-purple-500/30',
                'hover:border-purple-500/60 hover:shadow-lg hover:-translate-y-0.5'
            )}
        >
            {/* Cover Art / Placeholder */}
            <div className="h-24 bg-gradient-to-br from-purple-900/50 to-black relative overflow-hidden">
                {song.cover_art_url || song.thumbnail_url ? (
                    <img src={song.cover_art_url || song.thumbnail_url} alt={song.title} className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <Music size={32} className="text-purple-700" />
                    </div>
                )}

                {/* Play Button */}
                {onPlay && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onPlay(); }}
                        className="absolute bottom-2 left-2 p-2 rounded-full bg-purple-500 text-white opacity-0 group-hover:opacity-100 transition-opacity hover:bg-purple-400"
                    >
                        <Play size={16} fill="white" />
                    </button>
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
                <div className={clsx('absolute bottom-2 right-2 px-2 py-0.5 rounded-full text-[10px] font-bold', statusConfig.bg, statusConfig.color)}>
                    {statusConfig.label}
                </div>
            </div>

            {/* Content */}
            <div className="p-3">
                <h3 className="font-semibold text-white text-sm leading-tight line-clamp-1">{song.title}</h3>

                {/* Meta Row */}
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    {song.duration && (
                        <span className="flex items-center gap-1">
                            <Clock size={10} /> {song.duration}
                        </span>
                    )}
                    {song.bpm && (
                        <span className="flex items-center gap-1">
                            <Hash size={10} /> {song.bpm} BPM
                        </span>
                    )}
                    {song.key && (
                        <span className="px-1.5 py-0.5 rounded bg-white/5">{song.key}</span>
                    )}
                </div>

                {/* Tags */}
                {song.tags && song.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mt-2">
                        {song.tags.slice(0, 3).map((tag, i) => (
                            <span key={i} className="text-[10px] px-1.5 py-0.5 rounded bg-purple-500/20 text-purple-400">{tag}</span>
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
