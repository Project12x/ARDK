import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../../lib/db';
import { AlertTriangle, ExternalLink } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export function BlockersWidget() {
    const navigate = useNavigate();

    // Fetch all projects with blockers
    const projectsWithBlockers = useLiveQuery(async () => {
        const projects = await db.projects
            .filter(p => !p.is_archived && !p.deleted_at && Array.isArray(p.blockers) && p.blockers.length > 0)
            .toArray();
        return projects;
    });

    if (!projectsWithBlockers) {
        return <div className="h-full flex items-center justify-center text-gray-500 text-xs">Loading...</div>;
    }

    const totalBlockers = projectsWithBlockers.reduce((sum, p) => sum + (p.blockers?.length || 0), 0);

    return (
        <div className="h-full flex flex-col p-4 bg-black/40">
            {/* Header */}
            <div className="flex items-center justify-between mb-3 shrink-0">
                <div className="flex items-center gap-2">
                    <AlertTriangle size={14} className="text-red-500" />
                    <span className="text-[10px] font-mono uppercase font-bold text-gray-400">Blockers</span>
                </div>
                <span className={`text-[10px] font-mono px-1.5 py-0.5 rounded ${totalBlockers > 0 ? 'bg-red-500/20 text-red-400' : 'bg-green-500/20 text-green-400'
                    }`}>
                    {totalBlockers}
                </span>
            </div>

            {/* Blockers List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2">
                {projectsWithBlockers.length === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 text-center">
                        <AlertTriangle size={24} className="mb-2 opacity-30" />
                        <span className="text-xs">No blockers!</span>
                        <span className="text-[10px] opacity-50">All clear 🎉</span>
                    </div>
                ) : (
                    projectsWithBlockers.map(project => (
                        <div key={project.id} className="space-y-1">
                            {/* Project Header */}
                            <div
                                className="flex items-center justify-between cursor-pointer group"
                                onClick={() => navigate(`/projects/${project.id}`)}
                            >
                                <span className="text-[10px] font-bold text-white group-hover:text-accent transition-colors truncate">
                                    {project.title}
                                </span>
                                <ExternalLink size={10} className="text-gray-600 group-hover:text-accent shrink-0" />
                            </div>

                            {/* Blockers */}
                            {project.blockers?.map((blocker, i) => (
                                <div
                                    key={i}
                                    className="bg-red-900/10 border border-red-500/20 p-2 rounded text-xs text-red-200 leading-relaxed"
                                >
                                    {blocker}
                                </div>
                            ))}
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
