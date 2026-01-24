import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../../lib/db';
import { BarChart3, Folder, CheckCircle, Archive, Pause } from 'lucide-react';

export function ProjectStatsWidget() {
    // Fetch all projects for stats
    const stats = useLiveQuery(async () => {
        const allProjects = await db.projects
            .filter(p => !p.deleted_at)
            .toArray();

        const active = allProjects.filter(p => p.status === 'active' && !p.is_archived).length;
        const completed = allProjects.filter(p => p.status === 'completed').length;
        const onHold = allProjects.filter(p => p.status === 'on-hold').length;
        const archived = allProjects.filter(p => p.is_archived || p.status === 'archived').length;
        const total = allProjects.length;

        // Calculate completion rate (completed / total non-archived)
        const workableTotal = total - archived;
        const completionRate = workableTotal > 0 ? Math.round((completed / workableTotal) * 100) : 0;

        return { active, completed, onHold, archived, total, completionRate };
    });

    if (!stats) {
        return <div className="h-full flex items-center justify-center text-gray-500 text-xs">Loading...</div>;
    }

    const statItems = [
        { label: 'Active', value: stats.active, icon: Folder, color: 'text-accent', bg: 'bg-accent/10' },
        { label: 'Completed', value: stats.completed, icon: CheckCircle, color: 'text-green-400', bg: 'bg-green-500/10' },
        { label: 'On Hold', value: stats.onHold, icon: Pause, color: 'text-yellow-400', bg: 'bg-yellow-500/10' },
        { label: 'Archived', value: stats.archived, icon: Archive, color: 'text-gray-400', bg: 'bg-gray-500/10' },
    ];

    return (
        <div className="h-full flex flex-col p-4 bg-black/40">
            {/* Header */}
            <div className="flex items-center justify-between mb-3 shrink-0">
                <div className="flex items-center gap-2">
                    <BarChart3 size={14} className="text-accent" />
                    <span className="text-[10px] font-mono uppercase font-bold text-gray-400">Project Stats</span>
                </div>
                <span className="text-[10px] font-mono text-gray-600">
                    {stats.total} total
                </span>
            </div>

            {/* Stats Grid */}
            <div className="flex-1 grid grid-cols-2 gap-2">
                {statItems.map(item => (
                    <div
                        key={item.label}
                        className={`${item.bg} rounded-lg p-3 flex flex-col items-center justify-center`}
                    >
                        <item.icon size={16} className={item.color} />
                        <span className={`text-xl font-bold font-mono mt-1 ${item.color}`}>
                            {item.value}
                        </span>
                        <span className="text-[9px] text-gray-500 uppercase font-bold">
                            {item.label}
                        </span>
                    </div>
                ))}
            </div>

            {/* Completion Rate */}
            <div className="mt-3 pt-3 border-t border-white/5">
                <div className="flex items-center justify-between mb-1">
                    <span className="text-[9px] text-gray-500 uppercase font-bold">Completion Rate</span>
                    <span className="text-[10px] font-mono text-accent font-bold">{stats.completionRate}%</span>
                </div>
                <div className="h-2 bg-white/5 rounded-full overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-accent to-green-500 transition-all duration-500"
                        style={{ width: `${stats.completionRate}%` }}
                    />
                </div>
            </div>
        </div>
    );
}
