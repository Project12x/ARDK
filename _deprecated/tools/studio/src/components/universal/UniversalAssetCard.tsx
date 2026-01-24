/**
 * UniversalAssetCard
 * A specialized card for displaying Asset entities in the Universal system.
 * Inherits DnD from UniversalCard pattern for Transporter compatibility.
 */

import { useState, useEffect } from 'react';
import { useUniversalDnd } from '../../lib/universal/useUniversalDnd';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useLiveQuery } from 'dexie-react-hooks';
import clsx from 'clsx';
import { toast } from 'sonner';
import {
    GripVertical, Settings, Save, X, CheckCircle, AlertTriangle, Wrench, Archive,
    Monitor, Zap, Camera, Volume2, Box, MapPin, Image as ImageIcon
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { Asset } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    name: z.string().min(1, 'Name required'),
    category: z.string().min(1, 'Category required'),
    status: z.enum(['active', 'maintenance', 'broken', 'retired']),
    location: z.string().optional(),
    make: z.string().optional(),
    model: z.string().optional(),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// STATUS CONFIG
// ============================================================================

const STATUS_CONFIG = {
    'active': { icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/20', label: 'Active' },
    'maintenance': { icon: Wrench, color: 'text-amber-400', bg: 'bg-amber-500/20', label: 'Maintenance' },
    'broken': { icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/20', label: 'Broken' },
    'retired': { icon: Archive, color: 'text-gray-400', bg: 'bg-gray-500/20', label: 'Retired' },
};

const CATEGORY_ICONS: Record<string, typeof Box> = {
    'computer': Monitor,
    'test equipment': Zap,
    'audio': Volume2,
    'camera': Camera,
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalAssetCardProps {
    entity: UniversalEntity<Asset>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalAssetCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
}: UniversalAssetCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query for reactive updates
    const liveAsset = useLiveQuery(
        () => db.assets.get(initialEntity.data.id!),
        [initialEntity.data.id]
    );
    const asset = liveAsset || initialEntity.data;

    // Form setup
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
        defaultValues: {
            name: '',
            category: '',
            status: 'active',
            location: '',
            make: '',
            model: '',
        },
    });

    // Reset form when asset changes or edit mode opens
    useEffect(() => {
        if (asset) {
            reset({
                name: asset.name || '',
                category: asset.category || '',
                status: asset.status || 'active',
                location: asset.location || '',
                make: asset.make || '',
                model: asset.model || '',
            });
        }
    }, [asset, isEditing, reset]);

    // DND Setup
    const { attributes, listeners, setNodeRef, isDragging } = useUniversalDnd(initialEntity, dragOrigin, isEditing);

    // Form submit

    // Form submit
    const onSubmit = async (data: EditFormData) => {
        try {
            await db.assets.update(asset.id!, {
                name: data.name,
                category: data.category,
                status: data.status,
                location: data.location || undefined,
                make: data.make || undefined,
                model: data.model || undefined,
                updated_at: new Date(),
            });
            toast.success('Asset updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update asset');
            console.error(err);
        }
    };

    // Status config
    const statusConfig = STATUS_CONFIG[asset.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.active;
    const StatusIcon = statusConfig.icon;

    // Category icon
    const CategoryIcon = CATEGORY_ICONS[asset.category?.toLowerCase()] || Box;

    // Thumbnail
    const thumbnail = asset.images?.[0];

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-10 animate-in fade-in zoom-in-95">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-accent uppercase tracking-wider">Edit Asset</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Name" {...register('name')} error={errors.name?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Category" {...register('category')} error={errors.category?.message} />
                        <div>
                            <label className="block text-xs text-gray-500 mb-1.5">Status</label>
                            <select
                                {...register('status')}
                                className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                            >
                                <option value="active">Active</option>
                                <option value="maintenance">Maintenance</option>
                                <option value="broken">Broken</option>
                                <option value="retired">Retired</option>
                            </select>
                        </div>
                    </div>

                    <Input label="Location" {...register('location')} placeholder="e.g. Workshop" />

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Make" {...register('make')} placeholder="e.g. Fluke" />
                        <Input label="Model" {...register('model')} placeholder="e.g. 87V" />
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
            {...listeners}
            {...attributes}
            onClick={onClick}
            className={clsx(
                'group relative bg-surface border rounded-lg transition-all overflow-hidden',
                isDragging && 'opacity-30 scale-95',
                asset.status === 'broken' ? 'border-red-500/50' :
                    asset.status === 'maintenance' ? 'border-amber-500/50' :
                        asset.status === 'retired' ? 'border-gray-500/50' : 'border-white/10',
                'hover:border-accent/50 hover:shadow-lg hover:-translate-y-0.5'
            )}
        >
            {/* Thumbnail / Placeholder */}
            < div className="h-24 bg-black/50 relative overflow-hidden" >
                {
                    thumbnail ? (
                        <img src={thumbnail} alt={asset.name} className="w-full h-full object-cover" />
                    ) : (
                        <div className="w-full h-full flex items-center justify-center">
                            <CategoryIcon size={32} className="text-gray-700" />
                        </div >
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
                <div className={clsx('absolute bottom-2 left-2 px-2 py-1 rounded-md text-xs font-bold flex items-center gap-1', statusConfig.bg)}>
                    <StatusIcon size={12} className={statusConfig.color} />
                    <span className={statusConfig.color}>{statusConfig.label}</span>
                </div>
            </div >

            {/* Content */}
            < div className="p-3" >
                <h3 className="font-semibold text-white text-sm leading-tight line-clamp-1">
                    {asset.name}
                </h3>

                {
                    (asset.make || asset.model) && (
                        <span className="text-xs text-gray-500 block mt-0.5">
                            {[asset.make, asset.model].filter(Boolean).join(' ')}
                        </span>
                    )
                }

                {/* Meta Row */}
                <div className="flex items-center gap-3 mt-2 text-xs text-gray-500">
                    <span className="flex items-center gap-1 px-1.5 py-0.5 rounded bg-white/5">
                        <CategoryIcon size={12} /> {asset.category}
                    </span>
                    {asset.location && (
                        <span className="flex items-center gap-1">
                            <MapPin size={12} /> {asset.location}
                        </span>
                    )}
                </div>
            </div >

            {/* Action Buttons */}
            < div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity" >
                <button
                    onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                    className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                    title="Edit"
                >
                    <Settings size={12} />
                </button>
            </div >
        </div >
    );
}
