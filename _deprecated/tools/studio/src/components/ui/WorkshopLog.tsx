import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { formatDistanceToNow } from 'date-fns';
import { Activity, GitCommit, CalendarClock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function WorkshopLog() {
    const navigate = useNavigate();

    // Fetch last 15 logs joined with project titles
    const logs = useLiveQuery(async () => {
        const latestLogs = await db.logs
            .orderBy('date')
            .reverse()
            .limit(15)
            .toArray();

        if (!latestLogs || latestLogs.length === 0) return [];

        // Fetch project titles for these logs
        const projectIds = [...new Set(latestLogs.map(l => l.project_id))];
        const projects = await db.projects.where('id').anyOf(projectIds).toArray();
        const projectMap = new Map(projects.map(p => [p.id!, p.title]));

        return latestLogs.map(log => ({
            ...log,
            projectTitle: projectMap.get(log.project_id) || 'Unknown Project'
        }));
    });

    if (!logs) return <div className="animate-pulse h-full bg-white/5 rounded-xl" />;

    return (
        <div className="bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col h-full overflow-hidden relative">
            {/* Header */}
            <div className="flex items-center gap-2 mb-4 text-accent shrink-0">
                <Activity size={18} />
                <h3 className="font-mono text-sm font-bold uppercase tracking-wider">Activity Stream</h3>
            </div>

            {/* Scrollable List */}
            <div className="flex-1 overflow-y-auto pr-2 space-y-4 custom-scrollbar">
                {logs.length === 0 && (
                    <div className="text-gray-500 text-xs text-center py-10">
                        No recent neural activity recorded.
                    </div>
                )}

                {logs.map((log) => (
                    <div
                        key={log.id}
                        onClick={() => navigate(`/projects/${log.project_id}`)}
                        className="group cursor-pointer relative"
                    >
                        {/* Timeline Line */}
                        <div className="absolute left-[5px] top-6 bottom-[-16px] w-px bg-white/5 group-hover:bg-accent/20 transition-colors last:hidden" />

                        <div className="flex justify-between items-baseline mb-1 pl-4 relative">
                            {/* Dot */}
                            <div className="absolute left-[3px] top-1.5 w-1.5 h-1.5 rounded-full bg-gray-600 group-hover:bg-accent transition-colors shadow-[0_0_8px_rgba(0,0,0,0.5)]" />

                            <span className="text-xs font-bold text-gray-300 group-hover:text-accent transition-colors truncate pr-2">
                                {log.projectTitle}
                            </span>
                            <span className="text-[10px] text-gray-600 font-mono shrink-0">
                                {formatDistanceToNow(log.date, { addSuffix: true })}
                            </span>
                        </div>

                        <div className="ml-4 pl-3 border-l border-white/5 group-hover:border-accent/10 transition-colors pb-2">
                            <div className="flex items-center gap-2 text-[10px] text-gray-500 mb-1 font-mono">
                                <GitCommit size={10} />
                                <span className={log.type === 'auto' ? 'text-purple-400' : 'text-green-400'}>
                                    {log.version}
                                </span>
                            </div>
                            <p className="text-xs text-gray-400 leading-relaxed line-clamp-2 group-hover:text-gray-200 transition-colors">
                                {log.summary}
                            </p>
                        </div>
                    </div>
                ))}
            </div>

            {/* Fade overlay at bottom */}
            <div className="absolute bottom-0 left-0 right-0 h-8 bg-gradient-to-t from-black to-transparent pointer-events-none" />
        </div>
    );
}
