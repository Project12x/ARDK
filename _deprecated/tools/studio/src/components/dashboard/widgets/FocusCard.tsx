import { useLiveQuery } from 'dexie-react-hooks';
import type { Project } from '../../../lib/db';
import { db } from '../../../lib/db';
import { ArrowRight, AlertTriangle, Milestone, Zap, Clock, Calendar, Github, LinkIcon, Target, Printer } from 'lucide-react';
import { formatVersion, safeDateStr } from '../../../lib/utils';
import { STATUS_COLORS } from '../../../lib/constants';
import { RatingBar } from '../../ui/RatingBar';
import clsx from 'clsx';

interface FocusCardProps {
    project?: Project;
    index: number;
    onNavigate: (id: number) => void;
    disabled?: boolean;
}

export function FocusCard({ project, index, onNavigate, disabled }: FocusCardProps) {
    // Fetch next pending task for this project
    const nextTask = useLiveQuery(
        () => project?.id
            ? db.project_tasks.where({ project_id: project.id }).filter(t => t.status === 'pending').first()
            : undefined,
        [project?.id]
    );

    if (!project) {
        return (
            <div className={`h-full bg-black/40 border border-white/10 rounded-xl flex items-center justify-center overflow-hidden ${disabled ? 'opacity-50' : ''}`}>
                <div className="text-center text-gray-600">
                    <div className="text-4xl mb-2 opacity-30">#{index + 1}</div>
                    <div className="text-xs">No Active Project</div>
                </div>
            </div>
        );
    }

    const statusColor = project.label_color || STATUS_COLORS[project.status] || STATUS_COLORS['active'];

    return (
        <div
            className={`h-full bg-black border border-white/10 rounded-xl overflow-hidden flex flex-col group transition-all relative ${disabled
                ? 'opacity-50 cursor-not-allowed'
                : 'hover:border-accent/50 cursor-pointer'
                }`}
            onClick={disabled ? undefined : () => project.id && onNavigate(project.id)}
        >
            {/* Background Image Overlay */}
            {project.image_url && (
                <>
                    <div
                        className="absolute inset-0 z-0 bg-cover bg-center opacity-20 mix-blend-overlay pointer-events-none"
                        style={{ backgroundImage: `url(${project.image_url})` }}
                    />
                    <div className="absolute inset-0 z-0 bg-gradient-to-r from-black via-black/90 to-transparent pointer-events-none" />
                </>
            )}

            {/* Status Indicator Stripe */}
            <div
                style={{ backgroundColor: statusColor }}
                className="absolute top-0 left-0 w-2 h-full z-10"
            />

            {/* Header */}
            <div className="p-4 pl-5 relative z-10 border-b border-white/10 bg-white/5">
                {/* Meta Badges */}
                <div className="flex flex-wrap items-center gap-1.5 mb-2">
                    {/* Rank Badge */}
                    <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded font-mono font-bold">
                        #{index + 1}
                    </span>

                    {/* Project Code */}
                    <span className="text-[10px] font-mono text-accent uppercase tracking-widest bg-black/50 border border-accent/20 px-1.5 py-0.5 rounded-sm">
                        {project.project_code || `P-${project.id}`}
                    </span>

                    {/* Version */}
                    <span className="text-[10px] font-mono uppercase bg-white/10 text-white px-1.5 py-0.5 rounded-sm font-bold">
                        {formatVersion(project.version)}
                    </span>

                    {/* Priority Badge */}
                    {project.priority && project.priority >= 4 && (
                        <span className="text-[9px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded font-bold uppercase">
                            Priority
                        </span>
                    )}

                    {/* Design Status */}
                    {project.design_status && (
                        <span className="text-[9px] font-mono uppercase text-blue-400 border border-blue-500/30 px-1 py-0.5 rounded-sm bg-blue-900/10">
                            {project.design_status}
                        </span>
                    )}

                    {/* Build Status */}
                    {project.build_status && (
                        <span className="text-[9px] font-mono uppercase text-amber-400 border border-amber-500/30 px-1 py-0.5 rounded-sm bg-amber-900/10">
                            {project.build_status}
                        </span>
                    )}

                    {/* GitHub */}
                    {project.github_repo && (
                        <a
                            href={`https://github.com/${project.github_repo}`}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-[9px] font-mono text-white border border-white/20 px-1 py-0.5 rounded-sm bg-white/10 flex items-center gap-1 hover:bg-white/20"
                            onClick={e => e.stopPropagation()}
                        >
                            <Github size={9} /> REPO
                        </a>
                    )}

                    {/* Goal Link */}
                    {project.goal_id && (
                        <span className="text-[9px] font-mono text-purple-400 border border-purple-500/30 px-1 py-0.5 rounded-sm bg-purple-900/10 flex items-center gap-1">
                            <Target size={9} /> GOAL
                        </span>
                    )}

                    {/* Dependencies */}
                    {(project.upstream_dependencies?.length || 0) > 0 && (
                        <span className="text-[9px] text-blue-400 bg-blue-900/20 px-1 py-0.5 rounded border border-blue-500/20 flex items-center gap-0.5">
                            <LinkIcon size={8} /> {project.upstream_dependencies!.length}
                        </span>
                    )}

                    {/* 3D Print */}
                    {(project.print_parts?.length || 0) > 0 && (
                        <span className="text-[9px] text-orange-400 border border-orange-500/30 px-1 py-0.5 rounded-sm bg-orange-900/10 flex items-center gap-1">
                            <Printer size={9} /> 3D
                        </span>
                    )}
                </div>

                {/* Title */}
                <h3 className="text-lg font-black uppercase text-white leading-tight group-hover:text-accent transition-colors truncate">
                    {project.title}
                </h3>
                {project.role && (
                    <p className="text-[10px] font-mono text-gray-400 mt-0.5 uppercase truncate">{project.role}</p>
                )}
            </div>

            {/* Body */}
            <div className="flex-1 p-4 pl-5 flex flex-col gap-3 overflow-y-auto no-scrollbar relative z-10">
                {/* Metrics Row */}
                <div className="grid grid-cols-2 gap-3">
                    <div>
                        <span className="text-[9px] text-gray-500 uppercase font-bold flex items-center gap-1 mb-1">
                            <Zap size={9} /> Priority
                        </span>
                        <RatingBar value={project.priority || 0} activeColor="bg-red-600" max={5} mini />
                    </div>
                    <div>
                        <span className="text-[9px] text-gray-500 uppercase font-bold flex items-center gap-1 mb-1">
                            <AlertTriangle size={9} /> Intrusive
                        </span>
                        <RatingBar value={project.intrusiveness || 0} activeColor="bg-blue-500" max={5} mini />
                    </div>
                </div>

                {/* Time Info */}
                {(project.target_completion_date || project.total_theorized_hours) && (
                    <div className="flex gap-3 text-[10px] text-gray-500">
                        {project.target_completion_date && (
                            <span className="flex items-center gap-1">
                                <Calendar size={10} /> {safeDateStr(project.target_completion_date)}
                            </span>
                        )}
                        {project.total_theorized_hours && (
                            <span className="flex items-center gap-1">
                                <Clock size={10} /> {project.total_theorized_hours}H
                            </span>
                        )}
                    </div>
                )}

                {/* Blockers or Next Step */}
                {project.blockers && project.blockers.length > 0 ? (
                    <div className="bg-red-900/10 border border-red-500/20 p-2 rounded flex items-start gap-2">
                        <AlertTriangle size={14} className="text-red-500 mt-0.5 shrink-0" />
                        <div>
                            <div className="text-[9px] text-red-400 uppercase font-bold mb-0.5">Blocker</div>
                            <p className="text-xs text-red-200 line-clamp-2">{project.blockers[0]}</p>
                        </div>
                    </div>
                ) : project.next_step ? (
                    <div className="bg-accent/5 border border-accent/20 p-2 rounded flex items-start gap-2">
                        <Milestone size={14} className="text-accent mt-0.5 shrink-0" />
                        <div>
                            <div className="text-[9px] text-accent uppercase font-bold mb-0.5">Next Step</div>
                            <p className="text-xs text-gray-300 line-clamp-2">{project.next_step}</p>
                        </div>
                    </div>
                ) : nextTask ? (
                    <div className="bg-white/5 border border-white/10 p-2 rounded flex items-start gap-2">
                        <Milestone size={14} className="text-gray-400 mt-0.5 shrink-0" />
                        <div>
                            <div className="text-[9px] text-gray-500 uppercase font-bold mb-0.5">Next Task</div>
                            <p className="text-xs text-gray-300 line-clamp-2">{nextTask.title}</p>
                        </div>
                    </div>
                ) : null}

                {/* Status Description */}
                {project.status_description && (
                    <p className="text-[10px] text-gray-500 leading-relaxed line-clamp-2">{project.status_description}</p>
                )}
            </div>

            {/* Footer */}
            <div className="p-2 pl-5 border-t border-white/10 flex justify-between items-center bg-white/5 relative z-10">
                <span className="text-[10px] text-gray-500 uppercase font-mono">Open Project</span>
                <ArrowRight size={14} className="text-gray-500 group-hover:text-accent transition-colors" />
            </div>
        </div>
    );
}
