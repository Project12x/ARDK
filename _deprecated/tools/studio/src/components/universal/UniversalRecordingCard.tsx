/**
 * UniversalRecordingCard
 * A specialized card for displaying Recording entities in the Universal system.
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
    GripVertical, Settings, Save, X, Mic, Voicemail, AudioWaveform, Crown,
    Play, Clock, FileAudio, Music
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Recording } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    title: z.string().min(1, 'Title required'),
    type: z.enum(['demo', 'voice_memo', 'stem', 'master']),
    duration: z.string().optional(),
    notes: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const TYPE_CONFIG = {
    'demo': { icon: Mic, color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Demo' },
    'voice_memo': { icon: Voicemail, color: 'text-purple-400', bg: 'bg-purple-500/20', label: 'Voice Memo' },
    'stem': { icon: AudioWaveform, color: 'text-cyan-400', bg: 'bg-cyan-500/20', label: 'Stem' },
    'master': { icon: Crown, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Master' },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalRecordingCardProps {
    entity: UniversalEntity<Recording>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onPlay?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalRecordingCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
    onPlay,
}: UniversalRecordingCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveRecording = useLiveQuery(
        () => db.recordings.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const recording = liveRecording || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (recording) {
            reset({
                title: recording.title || '',
                type: recording.type || 'demo',
                duration: recording.duration || '',
                notes: recording.notes || '',
            });
        }
    }, [recording, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-recording-${recording.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: recording },
            entityType: 'recording',
            id: recording.id,
            title: recording.title,
            metadata: { type: recording.type, duration: recording.duration },
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
            await db.recordings.update(recording.id!, {
                title: data.title,
                type: data.type,
                duration: data.duration || undefined,
                notes: data.notes || undefined,
            });
            toast.success('Recording updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update recording');
        }
    };

    const typeConfig = TYPE_CONFIG[recording.type as keyof typeof TYPE_CONFIG] || TYPE_CONFIG.demo;
    const TypeIcon = typeConfig.icon;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-accent uppercase tracking-wider">Edit Recording</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Title" {...register('title')} error={errors.title?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Type</label>
                            <select {...register('type')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent">
                                <option value="demo">Demo</option>
                                <option value="voice_memo">Voice Memo</option>
                                <option value="stem">Stem</option>
                                <option value="master">Master</option>
                            </select>
                        </div>
                        <Input label="Duration" {...register('duration')} placeholder="e.g. 2:45" />
                    </div>

                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Notes</label>
                        <textarea
                            {...register('notes')}
                            rows={2}
                            className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent resize-none"
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
                recording.type === 'master' ? 'border-green-500/50' : 'border-white/10',
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

            {/* Type Badge & Play */}
            <div className="flex items-center gap-3 mb-3">
                <div className={clsx('p-2 rounded-lg', typeConfig.bg)}>
                    <TypeIcon size={20} className={typeConfig.color} />
                </div>
                <div className="flex-1">
                    <span className={clsx('text-xs font-bold', typeConfig.color)}>{typeConfig.label}</span>
                </div>
                {onPlay && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onPlay(); }}
                        className="p-2 rounded-full bg-accent/20 text-accent hover:bg-accent hover:text-black transition-colors"
                    >
                        <Play size={16} fill="currentColor" />
                    </button>
                )}
            </div>

            {/* Title */}
            <h3 className="font-semibold text-white text-sm leading-tight line-clamp-1">{recording.title}</h3>

            {/* Meta */}
            <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                {recording.duration && (
                    <span className="flex items-center gap-1">
                        <Clock size={10} /> {recording.duration}
                    </span>
                )}
                {recording.filename && (
                    <span className="flex items-center gap-1 truncate">
                        <FileAudio size={10} /> {recording.filename}
                    </span>
                )}
            </div>

            {/* Notes */}
            {recording.notes && (
                <p className="mt-2 text-xs text-gray-500 line-clamp-2 italic">{recording.notes}</p>
            )}

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
