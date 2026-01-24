/**
 * UniversalVendorCard
 * Card for vendor/supplier display.
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
    GripVertical, Settings, Save, X, Store, ExternalLink, Zap, Globe
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Vendor } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    name: z.string().min(1, 'Name required'),
    website: z.string().optional(),
    api_integration: z.enum(['none', 'octopart', 'digikey']),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// PROPS
// ============================================================================

interface UniversalVendorCardProps {
    entity: UniversalEntity<Vendor>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalVendorCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
}: UniversalVendorCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveVendor = useLiveQuery(
        () => db.vendors.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const vendor = liveVendor || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
    });

    useEffect(() => {
        if (vendor) {
            reset({
                name: vendor.name || '',
                website: vendor.website || '',
                api_integration: vendor.api_integration || 'none',
            });
        }
    }, [vendor, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-vendor-${vendor.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: vendor },
            entityType: 'vendor',
            id: vendor.id,
            title: vendor.name,
            metadata: { api_integration: vendor.api_integration },
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
            await db.vendors.update(vendor.id!, {
                name: data.name,
                website: data.website || undefined,
                api_integration: data.api_integration,
            });
            toast.success('Vendor updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update');
        }
    };

    const hasApi = vendor.api_integration && vendor.api_integration !== 'none';

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-green-500/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-green-400 uppercase tracking-wider">Edit Vendor</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Name" {...register('name')} error={errors.name?.message} />
                    <Input label="Website" {...register('website')} placeholder="https://..." />

                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">API Integration</label>
                        <select {...register('api_integration')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-green-500">
                            <option value="none">None</option>
                            <option value="octopart">Octopart</option>
                            <option value="digikey">Digi-Key</option>
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
                'group relative bg-surface border rounded-lg transition-all p-4',
                isDragging && 'opacity-30 scale-95',
                'border-white/10 hover:border-green-500/50 hover:shadow-lg hover:-translate-y-0.5'
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

            {/* Icon + API Badge */}
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1.5 rounded', hasApi ? 'bg-green-500/20' : 'bg-white/10')}>
                    <Store size={14} className={hasApi ? 'text-green-400' : 'text-gray-400'} />
                </div>
                {hasApi && (
                    <span className="text-[10px] text-green-400 bg-green-500/20 px-1.5 py-0.5 rounded flex items-center gap-1">
                        <Zap size={10} /> {vendor.api_integration}
                    </span>
                )}
            </div>

            {/* Name */}
            <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 mb-2">
                {vendor.name}
            </h3>

            {/* Website */}
            {vendor.website && (
                <a
                    href={vendor.website}
                    target="_blank"
                    rel="noopener"
                    onClick={e => e.stopPropagation()}
                    className="text-xs text-gray-500 hover:text-blue-400 flex items-center gap-1 truncate"
                >
                    <Globe size={10} />
                    {vendor.website.replace(/^https?:\/\/(www\.)?/, '')}
                    <ExternalLink size={10} className="ml-1 flex-shrink-0" />
                </a>
            )}

            {/* Edit Button */}
            <button
                onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                className="absolute bottom-2 right-2 p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 opacity-0 group-hover:opacity-100 transition-all"
                title="Edit"
            >
                <Settings size={12} />
            </button>
        </div>
    );
}
