/**
 * UniversalInventoryCard
 * A specialized card for displaying InventoryItem entities in the Universal system.
 * Consumes UniversalEntity<InventoryItem> and provides full visual fidelity + edit mode.
 */

import { useState, useEffect } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { useLiveQuery } from 'dexie-react-hooks';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Package, Wrench, Droplet, Settings, Save, X, Printer, MapPin, DollarSign } from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

import type { UniversalEntity } from '../../lib/universal/types';
import type { InventoryItem } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    name: z.string().min(1, 'Name required'),
    quantity: z.preprocess(
        (val) => (val === '' || val === null || isNaN(Number(val)) ? 0 : Number(val)),
        z.number().min(0)
    ),
    units: z.string().optional(),
    category: z.string().optional(),
    domain: z.string().optional(),
    location: z.string().optional(),
    unit_cost: z.preprocess(
        (val) => (val === '' || val === null || isNaN(Number(val)) ? undefined : Number(val)),
        z.number().optional()
    ),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// PROPS
// ============================================================================

interface UniversalInventoryCardProps {
    entity: UniversalEntity<InventoryItem>;
    layoutMode?: 'grid' | 'list';
    onClick?: () => void;
    onPrint?: (item: InventoryItem) => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalInventoryCard({
    entity: initialEntity,
    layoutMode = 'grid',
    onClick,
    onPrint,
}: UniversalInventoryCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query for reactive updates
    const liveItem = useLiveQuery(
        () => db.inventory.get(Number(initialEntity.id)),
        [initialEntity.id]
    );

    const item = liveItem || initialEntity.data;

    // Form setup - at top level, always called
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<EditFormData>({
        resolver: zodResolver(editSchema),
        defaultValues: {
            name: '',
            quantity: 0,
            units: '',
            category: '',
            domain: '',
            location: '',
            unit_cost: undefined,
        },
    });

    // Reset form when entering edit mode or when item changes
    useEffect(() => {
        if (item) {
            reset({
                name: item.name || '',
                quantity: item.quantity || 0,
                units: item.units || '',
                category: item.category || '',
                domain: item.domain || '',
                location: item.location || '',
                unit_cost: item.unit_cost || undefined,
            });
        }
    }, [item, isEditing, reset]);

    // Draggable setup with flattened fields for Layout.tsx
    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: initialEntity.urn,
        data: {
            type: 'universal-card',
            entityType: 'inventory',
            id: initialEntity.id,
            title: item.name,
            metadata: {
                quantity: item.quantity,
                category: item.category,
                location: item.location,
            },
            entity: { ...initialEntity, data: item },
        },
    });

    // Form submit
    const onSubmit = async (data: EditFormData) => {
        try {
            await db.inventory.update(Number(initialEntity.id), {
                name: data.name,
                quantity: data.quantity,
                units: data.units || undefined,
                category: data.category || undefined,
                domain: data.domain || undefined,
                location: data.location || undefined,
                unit_cost: data.unit_cost || undefined,
                updated_at: new Date(),
            });
            toast.success('Inventory updated');
            setIsEditing(false);
        } catch (error) {
            console.error('Failed to update inventory:', error);
            toast.error('Failed to save');
        }
    };

    // Icon based on type
    const TypeIcon = item.type === 'tool' ? Wrench : item.type === 'consumable' ? Droplet : Package;

    // Stock status
    const isLowStock = item.quantity <= (item.min_stock || 0);
    const isOutOfStock = item.quantity <= 0;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-lg p-4 shadow-xl z-10 animate-in fade-in zoom-in-95">
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="flex items-center justify-between mb-2">
                        <h3 className="text-sm font-bold text-accent flex items-center gap-2">
                            <TypeIcon size={14} /> Edit Item
                        </h3>
                        <button type="button" onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                            <X size={16} />
                        </button>
                    </div>

                    <Input label="Name" {...register('name')} error={errors.name?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Quantity" type="number" {...register('quantity', { valueAsNumber: true })} />
                        <Input label="Units" placeholder="pcs, ml, kg" {...register('units')} />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Kingdom" {...register('domain')} />
                        <Input label="Phylum" {...register('category')} />
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Location" {...register('location')} />
                        <Input label="Unit Cost ($)" type="number" step="0.01" {...register('unit_cost', { valueAsNumber: true })} />
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
            onClick={onClick}
            className={clsx(
                'group relative bg-surface border rounded-lg transition-all',
                isDragging && 'opacity-30 scale-95',
                isOutOfStock ? 'border-red-500/50' : isLowStock ? 'border-amber-500/50' : 'border-white/10',
                'hover:border-accent/50 hover:shadow-lg hover:-translate-y-0.5',
                layoutMode === 'list' ? 'flex items-center gap-4 p-3' : 'p-4 min-h-[120px]'
            )}
        >
            {/* Drag Handle - ONLY THIS has drag listeners */}
            <div
                {...listeners}
                {...attributes}
                className="absolute top-2 right-12 p-1 rounded cursor-grab active:cursor-grabbing text-gray-600 hover:text-white hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                title="Drag to reorder"
            >
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <circle cx="9" cy="5" r="1" /><circle cx="9" cy="12" r="1" /><circle cx="9" cy="19" r="1" />
                    <circle cx="15" cy="5" r="1" /><circle cx="15" cy="12" r="1" /><circle cx="15" cy="19" r="1" />
                </svg>
            </div>

            {/* Type Badge */}
            <div className={clsx(
                'absolute top-2 left-2 p-1.5 rounded-md',
                item.type === 'tool' ? 'bg-purple-500/20 text-purple-400' :
                    item.type === 'consumable' ? 'bg-cyan-500/20 text-cyan-400' :
                        'bg-accent/20 text-accent'
            )}>
                <TypeIcon size={14} />
            </div>

            {/* Quantity */}
            <div className="absolute top-2 right-2 text-right">
                <span className={clsx(
                    'block font-mono font-bold text-xl leading-none',
                    isOutOfStock ? 'text-red-500' : isLowStock ? 'text-amber-500' : 'text-accent'
                )}>
                    {item.quantity}
                </span>
                {item.units && (
                    <span className="block text-[9px] text-gray-500 uppercase font-mono">{item.units}</span>
                )}
            </div>

            {/* Content */}
            <div className={clsx('mt-8', layoutMode === 'list' && 'mt-0 flex-1')}>
                <h4 className="font-bold text-white text-sm leading-tight pr-12 mb-2">{item.name}</h4>

                {/* Taxonomy */}
                {(item.domain || item.category) && (
                    <div className="text-[10px] text-gray-500 mb-2">
                        {item.domain && <span className="text-accent">{item.domain}</span>}
                        {item.domain && item.category && <span className="mx-1">›</span>}
                        {item.category && <span>{item.category}</span>}
                    </div>
                )}

                {/* Location */}
                {item.location && (
                    <div className="flex items-center gap-1 text-[10px] text-gray-500">
                        <MapPin size={10} />
                        <span>{item.location}</span>
                    </div>
                )}

                {/* Cost */}
                {item.unit_cost && (
                    <div className="flex items-center gap-1 text-[10px] text-gray-400 mt-1">
                        <DollarSign size={10} />
                        <span>${(item.unit_cost * item.quantity).toFixed(2)} total</span>
                    </div>
                )}
            </div>

            {/* Action Buttons (hover) */}
            <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                <button
                    onClick={(e) => { e.stopPropagation(); setIsEditing(true); }}
                    className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                    title="Edit"
                >
                    <Settings size={12} />
                </button>
                {onPrint && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onPrint(item); }}
                        className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                        title="Print Label"
                    >
                        <Printer size={12} />
                    </button>
                )}
            </div>
        </div>
    );
}
