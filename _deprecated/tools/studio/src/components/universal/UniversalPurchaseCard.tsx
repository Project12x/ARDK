/**
 * UniversalPurchaseCard
 * Card for purchase/order tracking with progress indicators.
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
    GripVertical, Settings, Save, X, ShoppingCart, Package, Truck,
    PackageCheck, CheckCircle, ExternalLink, DollarSign
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload } from '../../lib/universal/types';
import type { PurchaseItem } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// SCHEMA
// ============================================================================

const editSchema = z.object({
    name: z.string().min(1, 'Name required'),
    quantity_needed: z.number().min(1),
    status: z.enum(['planned', 'ordered', 'shipped', 'arrived', 'installed']),
    priority: z.number().min(1).max(5),
});

type EditFormData = z.infer<typeof editSchema>;

// ============================================================================
// CONFIG
// ============================================================================

const STATUS_CONFIG = {
    'planned': { icon: ShoppingCart, color: 'text-gray-400', bg: 'bg-gray-500/20', progress: 0 },
    'ordered': { icon: Package, color: 'text-blue-400', bg: 'bg-blue-500/20', progress: 25 },
    'shipped': { icon: Truck, color: 'text-purple-400', bg: 'bg-purple-500/20', progress: 50 },
    'arrived': { icon: PackageCheck, color: 'text-green-400', bg: 'bg-green-500/20', progress: 75 },
    'installed': { icon: CheckCircle, color: 'text-emerald-400', bg: 'bg-emerald-500/20', progress: 100 },
};

// ============================================================================
// PROPS
// ============================================================================

interface UniversalPurchaseCardProps {
    entity: UniversalEntity<PurchaseItem>;
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalPurchaseCard({
    entity: initialEntity,
    dragOrigin = 'grid',
    onClick,
}: UniversalPurchaseCardProps) {
    const [isEditing, setIsEditing] = useState(false);

    // Live query
    const liveItem = useLiveQuery(
        () => db.purchase_items.get(initialEntity.data.id!),
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
                name: item.name || '',
                quantity_needed: item.quantity_needed || 1,
                status: item.status || 'planned',
                priority: item.priority || 3,
            });
        }
    }, [item, isEditing, reset]);

    // DND
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-purchase-${item.id}`,
        data: {
            type: 'universal-card',
            entity: { ...initialEntity, data: item },
            entityType: 'purchase',
            id: item.id,
            title: item.name,
            metadata: { status: item.status, priority: item.priority },
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
            await db.purchase_items.update(item.id!, {
                name: data.name,
                quantity_needed: data.quantity_needed,
                status: data.status,
                priority: data.priority,
                updated_at: new Date(),
            });
            toast.success('Purchase updated');
            setIsEditing(false);
        } catch (err) {
            toast.error('Failed to update');
        }
    };

    const statusConfig = STATUS_CONFIG[item.status as keyof typeof STATUS_CONFIG] || STATUS_CONFIG.planned;
    const StatusIcon = statusConfig.icon;

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-blue-500/50 rounded-xl p-4 shadow-xl z-10">
                <div className="flex items-center justify-between mb-4">
                    <h3 className="text-sm font-bold text-blue-400 uppercase tracking-wider">Edit Purchase</h3>
                    <button onClick={() => setIsEditing(false)} className="text-gray-500 hover:text-white">
                        <X size={16} />
                    </button>
                </div>

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input label="Name" {...register('name')} error={errors.name?.message} />

                    <div className="grid grid-cols-2 gap-3">
                        <Input label="Quantity" type="number" {...register('quantity_needed', { valueAsNumber: true })} />
                        <Input label="Priority (1-5)" type="number" {...register('priority', { valueAsNumber: true })} />
                    </div>

                    <div>
                        <label className="block text-xs text-gray-500 mb-1.5">Status</label>
                        <select {...register('status')} className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
                            <option value="planned">🛒 Planned</option>
                            <option value="ordered">📦 Ordered</option>
                            <option value="shipped">🚚 Shipped</option>
                            <option value="arrived">📬 Arrived</option>
                            <option value="installed">✅ Installed</option>
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
                'group relative bg-surface border rounded-lg transition-all p-4 overflow-hidden',
                isDragging && 'opacity-30 scale-95',
                'border-white/10 hover:border-blue-500/50 hover:shadow-lg hover:-translate-y-0.5'
            )}
        >
            {/* Progress Bar */}
            <div className="absolute top-0 left-0 right-0 h-1 bg-white/5">
                <div
                    className={clsx('h-full transition-all', statusConfig.bg)}
                    style={{ width: `${statusConfig.progress}%` }}
                />
            </div>

            {/* Drag Handle */}
            <div
                {...listeners}
                {...attributes}
                className="absolute top-3 right-12 p-1 rounded cursor-grab active:cursor-grabbing text-gray-600 hover:text-white hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity z-10"
                title="Drag to Transporter"
            >
                <GripVertical size={14} />
            </div>

            {/* Status Badge */}
            <div className="flex items-center gap-2 mb-2">
                <div className={clsx('p-1.5 rounded', statusConfig.bg)}>
                    <StatusIcon size={14} className={statusConfig.color} />
                </div>
                <span className={clsx('text-xs font-bold uppercase', statusConfig.color)}>
                    {item.status}
                </span>
                <span className="text-[10px] text-gray-500 ml-auto">
                    P{item.priority}
                </span>
            </div>

            {/* Title */}
            <h3 className="font-semibold text-white text-sm leading-tight line-clamp-2 mb-2">
                {item.name}
            </h3>

            {/* Meta */}
            <div className="flex items-center gap-3 text-xs text-gray-500">
                <span>{item.quantity_needed}× needed</span>
                {item.estimated_unit_cost && (
                    <span className="flex items-center gap-1">
                        <DollarSign size={10} />
                        {item.estimated_unit_cost.toFixed(2)}
                    </span>
                )}
            </div>

            {/* Tracking / URL */}
            {(item.tracking_number || item.url) && (
                <div className="mt-2 pt-2 border-t border-white/5">
                    {item.tracking_number && (
                        <span className="text-[10px] text-gray-500 font-mono">
                            #{item.tracking_number}
                        </span>
                    )}
                    {item.url && (
                        <a
                            href={item.url}
                            target="_blank"
                            rel="noopener"
                            className="ml-2 text-blue-400 hover:text-blue-300"
                            onClick={e => e.stopPropagation()}
                        >
                            <ExternalLink size={10} />
                        </a>
                    )}
                </div>
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
