import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import {
    BarChart,
    Bar,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Cell,
    ReferenceLine
} from 'recharts';
import { clsx } from 'clsx';
import { DollarSign, Activity } from 'lucide-react';

export function DashboardCharts() {
    const projects = useLiveQuery(() => db.projects.toArray());

    if (!projects) return null;

    // 1. Velocity / Status Data
    const statusCounts = projects.reduce((acc, curr) => {
        const s = curr.status || 'unknown';
        acc[s] = (acc[s] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const velocityData = [
        { name: 'Active', count: statusCounts['active'] || 0, color: '#00ffd2' },
        { name: 'WIP', count: statusCounts['in-progress'] || 0, color: '#00ffd2' },
        { name: 'Hold', count: statusCounts['on-hold'] || 0, color: '#fbbf24' },
        { name: 'Done', count: statusCounts['completed'] || 0, color: '#10b981' },
    ].filter(d => d.count > 0);

    // 2. Financial Data (Top Spenders)
    const financialData = projects
        .filter(p => !p.deleted_at && p.status === 'active' && (p.financial_budget || p.financial_spend))
        .map(p => ({
            name: p.project_code || p.title.substring(0, 10),
            budget: p.financial_budget || 0,
            spend: p.financial_spend || 0,
            fullTitle: p.title
        }))
        .sort((a, b) => b.budget - a.budget)
        .slice(0, 5); // Top 5

    return (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Velocity Chart */}
            <div className="bg-neutral-900 border border-white/10 p-6 rounded-xl relative overflow-hidden">
                <div className="flex items-center gap-2 mb-6">
                    <Activity className="text-accent" size={20} />
                    <div>
                        <h3 className="text-lg font-black text-white uppercase tracking-tighter">Project Velocity</h3>
                        <p className="text-xs text-gray-500 font-mono">ACTIVE WORKLOAD DISTRIBUTION</p>
                    </div>
                </div>

                <div style={{ width: '100%', height: 250 }}>
                    <ResponsiveContainer width="99%" height="100%" debounce={200}>
                        <BarChart data={velocityData}>
                            <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                            <XAxis
                                dataKey="name"
                                stroke="#666"
                                fontSize={10}
                                tickLine={false}
                                axisLine={false}
                            />
                            <YAxis
                                stroke="#666"
                                fontSize={10}
                                tickLine={false}
                                axisLine={false}
                            />
                            <Tooltip
                                cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px' }}
                                itemStyle={{ color: '#fff' }}
                            />
                            <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                                {velocityData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Bar>
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </div>

            {/* Financial Burn-down (Snapshot) */}
            <div className="bg-neutral-900 border border-white/10 p-6 rounded-xl relative overflow-hidden">
                <div className="flex items-center gap-2 mb-6">
                    <DollarSign className="text-green-400" size={20} />
                    <div>
                        <h3 className="text-lg font-black text-white uppercase tracking-tighter">Financial Burn</h3>
                        <p className="text-xs text-gray-500 font-mono">BUDGET VS SPEND (TOP 5 ACTIVE)</p>
                    </div>
                </div>

                <div style={{ width: '100%', height: 250 }}>
                    {financialData.length > 0 ? (
                        <ResponsiveContainer width="99%" height="100%" debounce={200}>
                            <BarChart data={financialData} layout="vertical" margin={{ left: 0 }}>
                                <CartesianGrid strokeDasharray="3 3" stroke="#333" horizontal={false} />
                                <XAxis type="number" hide />
                                <YAxis
                                    dataKey="name"
                                    type="category"
                                    stroke="#888"
                                    fontSize={10}
                                    tickLine={false}
                                    axisLine={false}
                                    width={80}
                                />
                                <Tooltip
                                    cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                                    contentStyle={{ backgroundColor: '#000', border: '1px solid #333', borderRadius: '8px' }}
                                    itemStyle={{ color: '#fff' }}
                                    formatter={(value: number) => [`$${value}`, '']}
                                />
                                <Bar dataKey="budget" stackId="a" fill="#1f2937" radius={[0, 4, 4, 0]} name="Budget" />
                                <Bar dataKey="spend" stackId="b" fill="#10b981" radius={[0, 4, 4, 0]} name="Spend" barSize={8} />
                                <Bar dataKey="spend" stackId="a" fill="transparent" stroke="#ef4444" strokeWidth={1} name="Actual" />
                            </BarChart>
                        </ResponsiveContainer>
                    ) : (
                        <div className="h-full flex items-center justify-center border border-dashed border-white/5 rounded">
                            <p className="text-xs text-gray-600 uppercase font-mono">No financial data found</p>
                        </div>
                    )}
                </div>

                {financialData.length > 0 && (
                    <div className="absolute bottom-4 right-4 flex gap-4 text-[10px] font-mono uppercase text-gray-500">
                        <span className="flex items-center gap-1"><div className="w-2 h-2 bg-gray-800 rounded-full" /> Total Budget</span>
                        <span className="flex items-center gap-1"><div className="w-2 h-2 bg-green-500 rounded-full" /> Actual Spend</span>
                    </div>
                )}
            </div>
        </div>
    );
}
