import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type PurchaseItem, type Vendor } from '../lib/db';
import {
    ShoppingCart,
    Plus,
    Truck,
    Package,
    CheckCircle,
    AlertCircle,
    ExternalLink,
    Trash2,
    MoreHorizontal,
    DollarSign,
    Filter
} from 'lucide-react';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import clsx from 'clsx';
// import { useAutoAnimate } from '@formkit/auto-animate/react'; // Conflict with DnD usually
import { toast } from 'sonner';
import { DndContext, DragOverlay, useDraggable, useDroppable, type DragStartEvent, type DragEndEvent } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { createPortal } from 'react-dom';
import { useMemo } from 'react';

export function PurchaseQueuePage() {
    const items = useLiveQuery(() => db.purchase_items.toArray());
    const vendors = useLiveQuery(() => db.vendors.toArray());

    // Group items by status
    const planned = items?.filter(i => i.status === 'planned') || [];
    const ordered = items?.filter(i => i.status === 'ordered') || [];
    const shipped = items?.filter(i => i.status === 'shipped') || [];
    const arrived = items?.filter(i => i.status === 'arrived') || [];

    const [isCreating, setIsCreating] = useState(false);

    const [activeId, setActiveId] = useState<number | null>(null);

    // Calculate totals
    const calculateTotal = (list: PurchaseItem[]) => {
        return list.reduce((sum, item) => {
            const cost = item.actual_unit_cost || item.estimated_unit_cost || 0;
            return sum + (cost * item.quantity_needed);
        }, 0);
    };

    const handleDragStart = (event: DragStartEvent) => {
        setActiveId(Number(event.active.id));
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;
        setActiveId(null);

        if (!over) return;

        const itemId = Number(active.id);
        const newStatus = over.id as PurchaseItem['status'];

        if (newStatus) {
            await db.purchase_items.update(itemId, {
                status: newStatus,
                updated_at: new Date()
            });
        }
    };

    const activeItem = useMemo(() => items?.find(i => i.id === activeId), [items, activeId]);

    return (
        <div className="flex flex-col h-full bg-black text-white overflow-hidden">
            {/* Header Removed for Integration into InventoryPage */}
            <div className="flex justify-end p-4 border-b border-white/10">
                <Button onClick={() => setIsCreating(true)} className="bg-accent text-black font-bold">
                    <Plus size={18} className="mr-2" /> Add Item
                </Button>
            </div>

            {/* Kanban Board */}
            <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
                <div className="flex-1 overflow-x-auto p-6">
                    <div className="flex gap-6 min-w-max h-full">
                        <KanbanColumn
                            id="planned"
                            title="Planned"
                            items={planned}
                            color="border-gray-500"
                            icon={<ShoppingCart size={16} />}
                            total={calculateTotal(planned)}
                            vendors={vendors}
                        />
                        <KanbanColumn
                            id="ordered"
                            title="Ordered"
                            items={ordered}
                            color="border-yellow-500"
                            icon={<Truck size={16} />}
                            total={calculateTotal(ordered)}
                            vendors={vendors}
                        />
                        <KanbanColumn
                            id="shipped"
                            title="Shipped"
                            items={shipped}
                            color="border-blue-500"
                            icon={<Package size={16} />}
                            total={calculateTotal(shipped)}
                            vendors={vendors}
                        />
                        <KanbanColumn
                            id="arrived"
                            title="Arrived"
                            items={arrived}
                            color="border-green-500"
                            icon={<CheckCircle size={16} />}
                            total={calculateTotal(arrived)}
                            vendors={vendors}
                        />
                    </div>
                </div>

                {createPortal(
                    <DragOverlay>
                        {activeItem ? (
                            <div className="w-[300px] opacity-90 rotate-2 cursor-grabbing">
                                <PurchaseItemCard item={activeItem} vendors={vendors || []} isOverlay />
                            </div>
                        ) : null}
                    </DragOverlay>,
                    document.body
                )}
            </DndContext>

            {isCreating && <CreatePurchaseItemModal onClose={() => setIsCreating(false)} vendors={vendors || []} />}
        </div>
    );
}

function KanbanColumn({ id, title, items, color, icon, total, vendors }: any) {
    const { setNodeRef } = useDroppable({ id });

    return (
        <div ref={setNodeRef} className="w-[350px] flex flex-col h-full bg-white/5 rounded-xl border border-white/10">
            {/* Header */}
            <div className={clsx("p-4 border-t-4 bg-white/5 rounded-t-xl flex justify-between items-start", color)}>
                <div>
                    <div className="flex items-center gap-2 font-bold uppercase tracking-wider text-sm mb-1">
                        {icon} {title} <span className="text-gray-500">({items.length})</span>
                    </div>
                    <div className="text-xs font-mono text-gray-400">
                        Total: ${total.toFixed(2)}
                    </div>
                </div>
            </div>

            {/* List */}
            <div className="flex-1 overflow-y-auto p-3 space-y-3">
                {items.map((item: PurchaseItem) => (
                    <PurchaseItemCard key={item.id} item={item} vendors={vendors} />
                ))}
            </div>
        </div>
    );
}

function PurchaseItemCard({ item, vendors, isOverlay }: { item: PurchaseItem, vendors: Vendor[], isOverlay?: boolean }) {
    const vendor = vendors?.find(v => v.id === item.vendor_id);

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: item.id!,
        disabled: false
    });

    const style = transform ? {
        transform: CSS.Translate.toString(transform),
    } : undefined;

    const updateStatus = async (newStatus: PurchaseItem['status']) => {
        await db.purchase_items.update(item.id!, {
            status: newStatus,
            updated_at: new Date()
        });
    };

    const handleDelete = async () => {
        if (confirm('Delete this item?')) {
            await db.purchase_items.delete(item.id!);
        }
    };

    if (isOverlay) {
        return (
            <Card className="p-3 bg-neutral-900 border-white/20 shadow-2xl">
                <div className="flex justify-between items-start mb-2">
                    <div className="font-bold text-sm text-white leading-tight">
                        {item.name}
                    </div>
                </div>
                <div className="flex justify-between items-center text-xs text-gray-500 mb-2">
                    <div>Qty: <span className="text-white">{item.quantity_needed}</span></div>
                </div>
            </Card>
        )
    }

    return (
        <div ref={setNodeRef} style={style} {...listeners} {...attributes} className={clsx("touch-none", isDragging && "opacity-50 grayscale")}>
            <Card className="p-3 bg-neutral-900 border-white/10 hover:border-white/20 transition-all group cursor-grab active:cursor-grabbing">
                <div className="flex justify-between items-start mb-2">
                    <div className="font-bold text-sm text-white leading-tight">
                        {item.name}
                    </div>
                    <div className="opacity-0 group-hover:opacity-100 transition-opacity">
                        <button onClick={handleDelete} className="text-gray-600 hover:text-red-400"><Trash2 size={12} /></button>
                    </div>
                </div>

                <div className="flex justify-between items-center text-xs text-gray-500 mb-2">
                    <div>Qty: <span className="text-white">{item.quantity_needed}</span></div>
                    {item.estimated_unit_cost && (
                        <div>Est: <span className="text-white">${item.estimated_unit_cost}</span></div>
                    )}
                </div>

                {vendor && (
                    <div className="text-[10px] uppercase font-bold tracking-wider text-accent mb-3 flex items-center gap-1">
                        {vendor.name}
                        {item.url && <a href={item.url} target="_blank" rel="noreferrer"><ExternalLink size={8} /></a>}
                    </div>
                )}

                {/* Actions */}
                <div className="grid grid-cols-2 gap-2 mt-auto">
                    {item.status === 'planned' && (
                        <Button size="sm" variant="outline" className="h-6 text-[10px]" onClick={() => updateStatus('ordered')}>
                            Mark Ordered
                        </Button>
                    )}
                    {item.status === 'ordered' && (
                        <Button size="sm" variant="outline" className="h-6 text-[10px]" onClick={() => updateStatus('shipped')}>
                            Mark Shipped
                        </Button>
                    )}
                    {item.status === 'shipped' && (
                        <Button size="sm" variant="outline" className="h-6 text-[10px]" onClick={() => updateStatus('arrived')}>
                            Mark Arrived
                        </Button>
                    )}
                    {item.status === 'arrived' && (
                        <Button size="sm" variant="outline" className="h-6 text-[10px]" onClick={() => updateStatus('installed')}>
                            Mark Installed
                        </Button>
                    )}
                </div>
            </Card>
        </div>
    );
}

function CreatePurchaseItemModal({ onClose, vendors }: { onClose: () => void, vendors: Vendor[] }) {
    const [name, setName] = useState('');
    const [qty, setQty] = useState(1);
    const [estCost, setEstCost] = useState('');
    const [vendorId, setVendorId] = useState<number | ''>('');
    const [link, setLink] = useState('');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await db.purchase_items.add({
            name,
            quantity_needed: qty,
            status: 'planned',
            priority: 3,
            vendor_id: vendorId === '' ? undefined : vendorId,
            estimated_unit_cost: estCost ? parseFloat(estCost) : undefined,
            url: link,
            created_at: new Date(),
            updated_at: new Date()
        });
        toast.success("Added to purchase queue");
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-neutral-900 border border-white/20 rounded-xl w-full max-w-md p-6">
                <h2 className="text-xl font-bold text-white mb-6">Add Purchase Item</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="text-xs uppercase font-bold text-gray-500">Item Name</label>
                        <input value={name} onChange={e => setName(e.target.value)} className="w-full bg-black border border-white/10 rounded p-2 text-white" autoFocus required />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="text-xs uppercase font-bold text-gray-500">Quantity</label>
                            <input type="number" value={qty} onChange={e => setQty(parseInt(e.target.value))} className="w-full bg-black border border-white/10 rounded p-2 text-white" required min="1" />
                        </div>
                        <div>
                            <label className="text-xs uppercase font-bold text-gray-500">Est. Cost ($)</label>
                            <input type="number" step="0.01" value={estCost} onChange={e => setEstCost(e.target.value)} className="w-full bg-black border border-white/10 rounded p-2 text-white" />
                        </div>
                    </div>
                    <div>
                        <label className="text-xs uppercase font-bold text-gray-500">Vendor</label>
                        <select value={vendorId} onChange={e => setVendorId(Number(e.target.value))} className="w-full bg-black border border-white/10 rounded p-2 text-white">
                            <option value="">Select Vendor...</option>
                            {vendors.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
                        </select>
                    </div>
                    <div>
                        <label className="text-xs uppercase font-bold text-gray-500">Link / URL</label>
                        <input value={link} onChange={e => setLink(e.target.value)} className="w-full bg-black border border-white/10 rounded p-2 text-white" placeholder="https://..." />
                    </div>
                    <div className="flex justify-end gap-3 mt-6">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                        <Button type="submit" disabled={!name}>Add Item</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
