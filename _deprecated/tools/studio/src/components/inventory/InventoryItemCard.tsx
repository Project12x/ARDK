import { useState, useEffect } from 'react';
import { db, type InventoryItem } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Trash2, Save, Ruler, Printer } from 'lucide-react';
import clsx from 'clsx';
import { UniversalCard } from '../ui/UniversalCard';

export function InventoryItemCard({ item, onPrint }: { item: InventoryItem, onPrint?: (item: InventoryItem) => void }) {
    const [isEditing, setIsEditing] = useState(false);

    // Edit Form State - Quantity is string to allow empty state
    const [form, setForm] = useState({
        name: item.name,
        quantity: String(item.quantity),
        units: item.units || '',
        category: item.category,
        domain: item.domain || '',
        location: item.location || '',
        cost: item.unit_cost ? String(item.unit_cost) : '',
        totalCost: (item.unit_cost && item.quantity) ? String((item.unit_cost * item.quantity).toFixed(2)) : '',
        url: item.datasheet_url || '',
        type: item.type || 'part' // Add Type to Edit
    });

    // Reset form when item prop updates (external change)
    useEffect(() => {
        setForm({
            name: item.name,
            quantity: String(item.quantity),
            units: item.units || '',
            category: item.category,
            domain: item.domain || '',
            location: item.location || '',
            cost: item.unit_cost ? String(item.unit_cost) : '',
            totalCost: (item.unit_cost && item.quantity) ? String((item.unit_cost * item.quantity).toFixed(2)) : '',
            url: item.datasheet_url || '',
            type: item.type || 'part'
        });
    }, [item.id, item.name, item.quantity, item.unit_cost, item.units, item.category, item.domain, item.location, item.type, item.datasheet_url]);

    // Cost Calculation Logic
    const updateCosts = (type: 'unit' | 'total' | 'qty', value: string) => {
        const numVal = parseFloat(value);
        if (isNaN(numVal) && value !== '') { // Allow empty but not invalid
            setForm(prev => ({ ...prev, [type === 'qty' ? 'quantity' : type === 'unit' ? 'cost' : 'totalCost']: value }));
            return;
        }

        const newForm = { ...form };

        if (type === 'qty') {
            newForm.quantity = value;
            // Qty changed: Update Total, keep Unit Cost constant
            if (newForm.cost && value !== '') {
                newForm.totalCost = (parseFloat(newForm.cost) * numVal).toFixed(2);
            } else if (value === '') {
                newForm.totalCost = '';
            }
        } else if (type === 'unit') {
            newForm.cost = value;
            // Unit changed: Update Total
            if (newForm.quantity && value !== '') {
                newForm.totalCost = (numVal * parseFloat(newForm.quantity)).toFixed(2);
            } else if (value === '') {
                newForm.totalCost = '';
            }
        } else if (type === 'total') {
            newForm.totalCost = value;
            // Total changed: Update Unit Cost
            if (newForm.quantity && parseFloat(newForm.quantity) !== 0 && value !== '') {
                newForm.cost = (numVal / parseFloat(newForm.quantity)).toFixed(4); // Higher precision for unit
            } else if (value === '') {
                newForm.cost = '';
            }
        }
        setForm(newForm);
    };

    const handleSave = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!item.id) return;

        await db.inventory.update(item.id, {
            name: form.name,
            quantity: form.quantity === '' ? 0 : Number(form.quantity),
            units: form.units,
            category: form.category,
            domain: form.domain,
            location: form.location,
            unit_cost: form.cost ? Number(form.cost) : undefined,
            datasheet_url: form.url,
            type: form.type as any
        });
        setIsEditing(false);
    };

    const handleDelete = async () => {
        if (confirm('Permanently delete this item?')) {
            await db.inventory.delete(item.id!);
        }
    };

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 p-4 shadow-xl z-10 relative animate-in fade-in zoom-in-95" onClick={e => e.stopPropagation()}>
                <div className="space-y-3">
                    <Input label="Name" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} autoFocus className="font-bold" />

                    <div className="grid grid-cols-2 gap-2">
                        <div className="col-span-2">
                            <label className="text-[10px] uppercase text-gray-500 font-bold block mb-1">Type</label>
                            <div className="flex border border-white/20 rounded-sm overflow-hidden">
                                <button type="button" onClick={() => setForm({ ...form, type: 'part' })} className={clsx("flex-1 text-xs py-1 font-bold", form.type === 'part' ? "bg-accent text-black" : "bg-black text-gray-500")}>PART</button>
                                <button type="button" onClick={() => setForm({ ...form, type: 'tool' })} className={clsx("flex-1 text-xs py-1 font-bold", form.type === 'tool' ? "bg-accent text-black" : "bg-black text-gray-500")}>TOOL</button>
                            </div>
                        </div>

                        <div className="col-span-2 grid grid-cols-2 gap-2">
                            <Input label="Kingdom" value={form.domain} onChange={e => setForm({ ...form, domain: e.target.value })} />
                            <Input label="Phylum" value={form.category} onChange={e => setForm({ ...form, category: e.target.value })} />
                        </div>

                        <Input label="Qty" value={form.quantity} onChange={e => updateCosts('qty', e.target.value)} />
                        <Input label="Units" value={form.units} onChange={e => setForm({ ...form, units: e.target.value })} />

                        <Input label="Unit Cost ($)" value={form.cost} type="number" onChange={e => updateCosts('unit', e.target.value)} />
                        <Input label="Total Value ($)" value={form.totalCost} type="number" onChange={e => updateCosts('total', e.target.value)} />

                        <div className="col-span-2">
                            <Input label="Loc" value={form.location} onChange={e => setForm({ ...form, location: e.target.value })} />
                        </div>
                    </div>

                    <div className="flex justify-between pt-2 border-t border-white/10 mt-2">
                        <Button size="sm" variant="ghost" className="text-red-500 hover:bg-red-900/20 h-7" onClick={async (e) => { e.stopPropagation(); await handleDelete(); }}><Trash2 size={12} /></Button>
                        <div className="flex gap-2">
                            <Button size="sm" variant="ghost" onClick={() => setIsEditing(false)} className="h-7 text-xs">Cancel</Button>
                            <Button size="sm" onClick={handleSave} className="h-7 text-xs bg-accent text-black hover:bg-white"><Save size={12} className="mr-1" /> Save</Button>
                        </div>
                    </div>
                </div>
            </div>
        )
    }

    return (
        <UniversalCard
            entityType="inventory-item"
            entityId={item.id!}
            title={item.name}
            metadata={{
                quantity: item.quantity,
                units: item.units,
                category: item.category,
                domain: item.domain,
                status: item.type || 'part'
            }}
            onClick={() => setIsEditing(true)}
            // Explicitly don't pass DELETE here to UniversalCard to prevent double delete buttons,
            // or pass it if you want the UniversalCard standard delete button.
            // Let's stick to the card's visual style for now.
            className={clsx(
                "bg-black border-white/10 p-3 hover:border-accent/50 hover:shadow-[0_0_15px_rgba(59,130,246,0.1)] flex flex-col justify-between min-h-[100px] hover:translate-y-[-2px] transition-all",
            )}
        >
            <div className="flex justify-between items-start mb-2 group h-full">
                <h4 className="font-bold text-gray-200 leading-tight pr-8 break-words text-sm">{item.name}</h4>
                <div className="absolute top-3 right-3 text-right">
                    <span className="block font-mono text-accent font-bold text-lg leading-none">
                        {item.quantity}
                    </span>
                    {item.units && (
                        <span className="block text-[9px] text-gray-500 uppercase font-mono tracking-wider">{item.units}</span>
                    )}
                </div>
            </div>

            <div className="space-y-1 mt-auto">
                <div className="flex flex-col gap-0.5 text-[10px] font-mono">
                    {item.unit_cost ? (
                        <>
                            <span className="text-white font-bold flex justify-between">
                                <span>TOTAL:</span>
                                <span>${(item.unit_cost * item.quantity).toFixed(2)}</span>
                            </span>
                            <span className="text-gray-500 flex justify-between">
                                <span>UNIT:</span>
                                <span>${Number(item.unit_cost).toFixed(2)} / {item.units || 'ea'}</span>
                            </span>
                        </>
                    ) : (
                        <span className="text-gray-700 italic">--</span>
                    )}
                </div>
            </div>

            <div className="absolute bottom-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity flex gap-1">
                {onPrint && (
                    <button
                        onClick={(e) => { e.stopPropagation(); onPrint(item); }}
                        className="p-1.5 text-gray-400 hover:text-white hover:bg-white/10 rounded"
                        title="Print Label"
                    >
                        <Printer size={12} />
                    </button>
                )}
                <Ruler size={12} className="text-gray-600 p-1.5" />
            </div>
        </UniversalCard>
    );
}
