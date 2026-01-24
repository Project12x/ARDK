import React from 'react';
import { db, type Project } from '../../../../lib/db';
import { Square, CheckSquare, RotateCcw, Archive, Trash2, Settings } from 'lucide-react';
import { toast } from 'sonner';

interface ProjectCompactVariantProps {
    project: Project;
    isCollapsed: boolean;
    onToggleCollapse?: () => void;
    onEdit: () => void;
    handleNavigate: () => void;
    handleDelete: () => void;
}

export function ProjectCompactVariant({
    project,
    isCollapsed,
    onToggleCollapse,
    onEdit,
    handleNavigate,
    handleDelete
}: ProjectCompactVariantProps) {

    const LegacyActions = () => (
        <div className="absolute top-2 right-2 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity z-50 bg-black/50 backdrop-blur rounded-lg p-0.5 border border-white/10">
            <button
                onClick={(e) => { e.stopPropagation(); onToggleCollapse?.(); }}
                className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/10"
                title={isCollapsed ? "Expand" : "Collapse"}
            >
                {isCollapsed ? <CheckSquare size={12} /> : <Square size={12} />}
            </button>
            <button
                onClick={(e) => { e.stopPropagation(); onEdit(); }}
                className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/10"
                title="Edit"
            >
                <Settings size={12} />
            </button>
            <button
                onClick={(e) => {
                    e.stopPropagation();
                    void (project.status === 'archived'
                        ? db.projects.update(project.id!, { status: 'active' })
                        : db.projects.update(project.id!, { status: 'archived' }));
                }}
                className="p-1 rounded text-gray-400 hover:text-white hover:bg-white/10"
                title={project.status === 'archived' ? "Restore" : "Archive"}
            >
                {project.status === 'archived' ? <RotateCcw size={12} /> : <Archive size={12} />}
            </button>
            <button
                onClick={(e) => { e.stopPropagation(); handleDelete(); }}
                className="p-1 rounded text-red-500/80 hover:text-red-400 hover:bg-red-500/10"
                title="Delete"
            >
                <Trash2 size={12} />
            </button>
        </div>
    );

    return (
        <div className="flex flex-col h-full relative z-10 group p-3">
            <LegacyActions />
            <div className="flex flex-col gap-1 z-10 mb-auto">
                <div className="flex justify-between items-start mb-1">
                    <span className="text-[10px] font-mono text-gray-500 bg-black/20 px-1.5 rounded">{project.project_code || `P-${project.id}`}</span>
                </div>
                <h3 className="font-bold text-base text-white leading-tight line-clamp-2 cursor-pointer hover:text-accent transition-colors" onClick={(e) => { e.stopPropagation(); handleNavigate(); }}>
                    {project.title}
                </h3>
            </div>

            <div className="mt-4 space-y-3 z-10">
                {/* Priority Bar */}
                <div className="space-y-1">
                    <div className="flex justify-between text-[10px] text-gray-400 uppercase font-bold">
                        <span>Prio {project.priority}</span>
                        <span>{project.progress || 0}%</span>
                    </div>
                    <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                        <div className="h-full bg-accent" style={{ width: `${project.progress || 0}%` }} />
                    </div>
                </div>

                {/* Meta Grid */}
                <div className="grid grid-cols-2 gap-2 pt-2 border-t border-white/5">
                    <div>
                        <span className="block text-[9px] text-gray-600 uppercase">Version</span>
                        <span className="block text-xs font-mono text-gray-300">v{project.version || '0.1'}</span>
                    </div>
                    <div className="text-right">
                        <span className="block text-[9px] text-gray-600 uppercase">Est.</span>
                        <span className="block text-xs font-mono text-gray-300">{project.time_estimate_active || 0}h</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
