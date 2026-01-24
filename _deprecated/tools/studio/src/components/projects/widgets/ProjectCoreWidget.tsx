import { Project } from '../../../lib/db';
import { formatVersion } from '../../../lib/utils';
import { Badge } from '../../ui/Badge';

export function ProjectCoreWidget({ project }: { project: Project }) {
    return (
        <div className="h-full bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col gap-4 overflow-hidden relative group">
            {/* Background Glow */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-3xl group-hover:bg-accent/10 transition-colors pointer-events-none" />

            <div className="flex justify-between items-start">
                <h3 className="text-gray-500 font-mono text-xs uppercase tracking-widest">Core Directive</h3>
                <span className="text-accent font-mono text-xs font-bold">ID: {project.id}</span>
            </div>

            <div className="flex-1">
                <h2 className="text-xl font-black text-white uppercase tracking-tight line-clamp-2" title={project.title}>
                    {project.title}
                </h2>
                <div className="flex flex-wrap gap-2 mt-2">
                    <Badge variant="outline" className="font-mono">{formatVersion(project.version)}</Badge>
                    <Badge variant={project.status === 'active' ? 'default' : 'secondary'}>{project.status.toUpperCase()}</Badge>
                    <Badge variant="outline" className="border-blue-500/30 text-blue-400">{project.priority > 3 ? 'HIGH PRIORITY' : 'NORMAL'}</Badge>
                </div>
            </div>

            <div className="text-sm text-gray-400 line-clamp-3">
                {project.description || "No mission briefing available."}
            </div>
        </div>
    );
}
