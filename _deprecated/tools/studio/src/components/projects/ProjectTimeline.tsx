import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { ResponsiveContainer, BarChart, Bar, XAxis, YAxis, Tooltip, Cell, CartesianGrid } from 'recharts';

export function ProjectTimeline() {
    const projects = useLiveQuery(() =>
        db.projects
            .where('status')
            .notEqual('archived')
            .filter(p => !p.deleted_at && !!p.target_completion_date)
            .toArray()
    );

    if (!projects || projects.length === 0) {
        return (
            <div className="h-full flex items-center justify-center border border-dashed border-white/5 rounded-xl bg-white/5">
                <p className="text-gray-500 font-mono text-sm">NO ACTIVE PROJECTS WITH TARGET DATES</p>
            </div>
        );
    }

    // Transform Data for Recharts Range Bar
    // We need [start, end] for X-Axis. 
    // Since we only have target_completion_date, we'll estimate start date 
    // or use created_at if available, or just a fixed duration back from target.

    const data = projects.map(p => {
        const start = new Date(p.created_at).getTime();
        const end = new Date(p.target_completion_date!).getTime();

        // Sanity check: if end < start, swap or fix
        const safeStart = start < end ? start : end - (86400000 * 7); // Default 1 week if bad data

        return {
            name: p.project_code || p.title.substring(0, 15) + (p.title.length > 15 ? '...' : ''),
            fullTitle: p.title,
            // Recharts Range Bar expects [min, max]
            dateRange: [safeStart, end],
            duration: (end - safeStart) / (1000 * 60 * 60 * 24), // Days
            status: p.status,
            color: p.label_color || '#3b82f6', // Default blue if no color
            progress: p.status === 'completed' ? 100 : (p.status === 'active' ? 50 : 0)
        };
    }).sort((a, b) => a.dateRange[0] - b.dateRange[0]);

    return (
        <div className="h-full bg-black/20 rounded-xl border border-white/5 p-4 flex flex-col">
            <h3 className="text-sm font-bold text-gray-400 mb-4 flex items-center gap-2 uppercase tracking-wider">
                Project Timeline <span className="text-xs bg-white/10 px-2 rounded text-white">{data.length}</span>
            </h3>

            <div className="flex-1 w-full min-h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                    <BarChart
                        data={data}
                        layout="vertical"
                        barSize={20}
                        margin={{ left: 20, right: 30 }}
                    >
                        <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#333" />
                        <XAxis
                            type="number"
                            domain={['dataMin', 'dataMax']}
                            tickFormatter={(unixTime) => new Date(unixTime).toLocaleDateString(undefined, { month: 'short', day: 'numeric' })}
                            stroke="#666"
                            fontSize={10}
                        />
                        <YAxis
                            type="category"
                            dataKey="name"
                            stroke="#888"
                            fontSize={10}
                            width={100}
                        />
                        <Tooltip
                            cursor={{ fill: 'rgba(255,255,255,0.05)' }}
                            content={({ active, payload }) => {
                                if (active && payload && payload.length) {
                                    const d = payload[0].payload;
                                    return (
                                        <div className="bg-black border border-white/20 p-2 rounded shadow-xl">
                                            <p className="font-bold text-white text-xs mb-1">{d.fullTitle}</p>
                                            <p className="text-[10px] text-gray-400 font-mono">
                                                {new Date(d.dateRange[0]).toLocaleDateString()} - {new Date(d.dateRange[1]).toLocaleDateString()}
                                            </p>
                                            <p className="text-[10px] uppercase font-bold mt-1" style={{ color: d.color }}>
                                                {d.status} ({Math.round(d.duration)} days)
                                            </p>
                                        </div>
                                    );
                                }
                                return null;
                            }}
                        />
                        <Bar dataKey="dateRange" radius={[4, 4, 4, 4]}>
                            {data.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={entry.color} />
                            ))}
                        </Bar>
                    </BarChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
}
