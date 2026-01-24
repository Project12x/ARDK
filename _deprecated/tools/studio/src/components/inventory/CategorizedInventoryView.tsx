
import { db, type InventoryItem } from '../../lib/db';
import { InventoryTable } from './InventoryTable';
import { FilamentDistributionChart } from './FilamentDistributionChart';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, BarChart, Bar, XAxis } from 'recharts';
import { Package, Wrench, Layers, Box } from 'lucide-react';

interface CategorizedInventoryViewProps {
    inventory: InventoryItem[];
}

export function CategorizedInventoryView({ inventory }: CategorizedInventoryViewProps) {
    // 1. Split Data
    const parts = inventory.filter(i => i.type === 'part' || (!i.type && !i.category?.includes('Filament')));
    const tools = inventory.filter(i => i.type === 'tool' || i.type === 'equipment');
    const consumables = inventory.filter(i => i.type === 'consumable' && i.category !== 'Filament');
    const filament = inventory.filter(i => i.category === 'Filament' || (i.type === 'consumable' && i.category === 'Filament'));

    // 2. Metrics Helper
    const getMetrics = (items: InventoryItem[]) => {
        const totalValue = items.reduce((acc, i) => acc + ((i.unit_cost || 0) * (i.quantity || 0)), 0);
        const totalCount = items.length;
        const lowStock = items.filter(i => (i.quantity || 0) < (i.min_stock || 1)).length;
        return { totalValue, totalCount, lowStock };
    };

    const partMetrics = getMetrics(parts);
    const toolMetrics = getMetrics(tools);
    const consumableMetrics = getMetrics(consumables);

    return (
        <div className="space-y-12">

            {/* SECTION 1: PARTS */}
            <div className="space-y-4">
                <SectionHeader icon={<Package />} title="Components & Hardware" metrics={partMetrics} color="text-accent" />
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <div className="lg:col-span-1 h-64 bg-black/20 border border-white/5 rounded-xl p-4">
                        <h4 className="text-[10px] font-bold uppercase text-gray-500 mb-4">Value by Category</h4>
                        <SimplePieChart items={parts} />
                    </div>
                    <div className="lg:col-span-3">
                        <InventoryTable
                            data={parts}
                            variant="general"
                            onUpdate={(id, u) => db.inventory.update(id, u)}
                            onDelete={(id) => { if (confirm("Delete?")) db.inventory.delete(id); }}
                        />
                    </div>
                </div>
            </div>

            {/* SECTION 2: TOOLS */}
            <div className="space-y-4">
                <SectionHeader icon={<Wrench />} title="Tools & Equipment" metrics={toolMetrics} color="text-blue-400" />
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <div className="lg:col-span-1 h-64 bg-black/20 border border-white/5 rounded-xl p-4">
                        <h4 className="text-[10px] font-bold uppercase text-gray-500 mb-4">Tool Types</h4>
                        <SimplePieChart items={tools} colors={['#3b82f6', '#1d4ed8', '#60a5fa', '#93c5fd']} />
                    </div>
                    <div className="lg:col-span-3">
                        <InventoryTable
                            data={tools}
                            variant="general"
                            onUpdate={(id, u) => db.inventory.update(id, u)}
                            onDelete={(id) => { if (confirm("Delete?")) db.inventory.delete(id); }}
                        />
                    </div>
                </div>
            </div>

            {/* SECTION 3: CONSUMABLES (Non-Filament) */}
            <div className="space-y-4">
                <SectionHeader icon={<Layers />} title="Consumables & Materials" metrics={consumableMetrics} color="text-green-400" />
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <div className="lg:col-span-1 h-64 bg-black/20 border border-white/5 rounded-xl p-4">
                        <h4 className="text-[10px] font-bold uppercase text-gray-500 mb-4">Stock Levels</h4>
                        {/* Bar Chart for stock levels of top 5 items */}
                        <SimpleBarChart items={consumables} />
                    </div>
                    <div className="lg:col-span-3">
                        <InventoryTable
                            data={consumables}
                            variant="general"
                            onUpdate={(id, u) => db.inventory.update(id, u)}
                            onDelete={(id) => { if (confirm("Delete?")) db.inventory.delete(id); }}
                        />
                    </div>
                </div>
            </div>

            {/* SECTION 4: FILAMENT */}
            <div className="space-y-4">
                <SectionHeader icon={<Box />} title="Filament Bunker" metrics={getMetrics(filament)} color="text-industrial" />
                <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
                    <div className="lg:col-span-1 h-64 bg-black/20 border border-white/5 rounded-xl p-4 flex flex-col items-center justify-center">
                        <FilamentDistributionChart items={filament} />
                        <span className="text-xs font-mono text-gray-500 mt-2">Material Distribution</span>
                    </div>
                    <div className="lg:col-span-3">
                        <InventoryTable
                            data={filament}
                            variant="filament"
                            onUpdate={(id, u) => db.inventory.update(id, u)}
                            onDelete={(id) => { if (confirm("Delete?")) db.inventory.delete(id); }}
                        />
                    </div>
                </div>
            </div>

        </div>
    )
}

function SectionHeader({ icon, title, metrics, color }: { icon: React.ReactNode, title: string, metrics: { totalCount: number, totalValue: number, lowStock: number }, color: string }) {
    return (
        <div className={`flex items-center gap-4 border-b border-white/10 pb-2 ${color}`}>
            {icon}
            <h3 className="text-xl font-black uppercase tracking-tight text-white">{title}</h3>
            <div className="flex gap-4 ml-auto text-xs font-mono text-gray-500">
                <span>COUNT: <b className="text-white">{metrics.totalCount}</b></span>
                <span>VALUE: <b className="text-white">${metrics.totalValue.toFixed(2)}</b></span>
                {metrics.lowStock > 0 && <span className="text-red-500 font-bold">LOW STOCK: {metrics.lowStock}</span>}
            </div>
        </div>
    )
}

function SimplePieChart({ items, colors = ['#eab308', '#facc15', '#fde047', '#fef08a'] }: { items: InventoryItem[], colors?: string[] }) {
    // Group by category, sum value
    const grouped = items.reduce((acc, item) => {
        const cat = item.category || 'Misc';
        acc[cat] = (acc[cat] || 0) + (item.quantity || 1);
        return acc;
    }, {} as Record<string, number>);

    const data = Object.entries(grouped)
        .map(([name, value]) => ({ name, value }))
        .sort((a, b) => b.value - a.value)
        .slice(0, 5); // Top 5

    return (
        <ResponsiveContainer width="100%" height="100%">
            <PieChart>
                <Pie data={data} innerRadius={40} outerRadius={60} paddingAngle={2} dataKey="value">
                    {data.map((_, index) => (
                        <Cell key={`cell-${index}`} fill={colors[index % colors.length]} stroke="rgba(0,0,0,0.5)" />
                    ))}
                </Pie>
                <Tooltip
                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '4px' }}
                    itemStyle={{ color: '#fff', fontSize: '12px', fontFamily: 'monospace' }}
                />
            </PieChart>
        </ResponsiveContainer>
    )
}

function SimpleBarChart({ items }: { items: InventoryItem[] }) {
    const data = items.slice(0, 5).map(i => ({ name: i.name.substring(0, 10), qty: i.quantity || 0 }));
    return (
        <ResponsiveContainer width="100%" height="100%">
            <BarChart data={data}>
                <XAxis dataKey="name" fontSize={10} stroke="#666" tick={{ fill: 'gray' }} />
                <Tooltip cursor={{ fill: 'rgba(255,255,255,0.05)' }} contentStyle={{ backgroundColor: '#000', border: '1px solid #333' }} />
                <Bar dataKey="qty" fill="#4ade80" radius={[2, 2, 0, 0]} />
            </BarChart>
        </ResponsiveContainer>
    )
}
