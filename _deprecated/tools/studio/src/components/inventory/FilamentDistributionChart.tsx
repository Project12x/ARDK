import { useMemo } from 'react';
import type { InventoryItem } from '../../lib/db';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import clsx from 'clsx';

interface FilamentDistributionChartProps {
    items: InventoryItem[];
}

const COLORS = {
    PLA: '#00ffd2',   // Cyan (Industrial)
    PETG: '#ff4d00',  // Orange (Accent)
    ABS: '#ff4499',   // Pink (Neon)
    TPU: '#004687',   // Marine
    ASA: '#ffffff',
    Resin: '#333333'
};

export function FilamentDistributionChart({ items }: FilamentDistributionChartProps) {
    const data = useMemo(() => {
        const distribution: Record<string, number> = {};

        items.forEach(item => {
            const material = item.properties?.material || 'Unknown';
            // Sum by weight (grams)
            distribution[material] = (distribution[material] || 0) + item.quantity;
        });

        return Object.entries(distribution)
            .map(([name, value]) => ({ name, value }))
            .sort((a, b) => b.value - a.value); // Sort descending
    }, [items]);

    if (items.length === 0) return null;

    return (
        <div className="h-64 bg-black/40 border border-white/5 rounded-xl p-4 flex flex-col relative overflow-hidden backdrop-blur-sm">
            <div className="absolute top-0 left-0 w-1 h-full bg-gradient-to-b from-industrial via-accent to-neon opacity-50" />
            <h3 className="text-xs font-bold uppercase tracking-widest text-gray-400 mb-2 flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-industrial" /> Material Distribution (By Weight)
            </h3>

            <div className="flex-1 w-full min-h-0">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={60}
                            outerRadius={80}
                            paddingAngle={5}
                            dataKey="value"
                            stroke="none"
                        >
                            {data.map((entry, index) => (
                                <Cell
                                    key={`cell-${index}`}
                                    fill={(COLORS as any)[entry.name] || '#8884d8'}
                                    className="outline-none"
                                />
                            ))}
                        </Pie>
                        <Tooltip
                            contentStyle={{
                                backgroundColor: '#000000',
                                border: '1px solid #333',
                                borderRadius: '8px',
                                textTransform: 'uppercase',
                                fontSize: '12px',
                                fontWeight: 'bold'
                            }}
                            itemStyle={{ color: '#fff' }}
                            formatter={(value: number) => [`${(value / 1000).toFixed(1)}kg`, 'Mass']}
                        />
                        <Legend
                            layout="vertical"
                            verticalAlign="middle"
                            align="right"
                            wrapperStyle={{ fontSize: '10px', textTransform: 'uppercase', fontFamily: '"JetBrains Mono", monospace' }}
                        />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Total Weight Stat */}
            <div className="absolute bottom-4 left-6">
                <div className="text-2xl font-black text-white tabular-nums tracking-tighter">
                    {(data.reduce((acc, curr) => acc + curr.value, 0) / 1000).toFixed(1)}
                    <span className="text-sm text-gray-500 font-normal ml-1">kg</span>
                </div>
                <div className="text-[10px] text-gray-500 font-mono uppercase">Total Reserves</div>
            </div>
        </div>
    );
}
