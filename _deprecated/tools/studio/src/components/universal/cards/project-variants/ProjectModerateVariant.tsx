import React from 'react';
import { clsx } from 'clsx';
import { db, type Project } from '../../../../lib/db';
import { GradientLEDBar } from '../../../ui/GradientLEDBar';
import { formatDistanceToNow } from 'date-fns';
import { Folder, Github, Sparkles, Target, Plus, Clock, Zap, Calendar, Square, CheckSquare, Settings, RotateCcw, Archive, Trash2, Layers, Check, Hammer } from 'lucide-react';
import { toast } from 'sonner';
import { TagsRow } from '../../../ui/TagsRow';
import { useUIStore } from '../../../../store/useStore';

interface ProjectModerateVariantProps {
    project: Project;
    nextTask?: any; // Ideally typed from DB
    isCollapsed: boolean;
    onToggleCollapse?: () => void;
    onEdit: () => void;
    handleNavigate: () => void;
    handleDelete: () => void;
}

export function ProjectModerateVariant({
    project,
    nextTask,
    isCollapsed,
    onToggleCollapse,
    onEdit,
    handleNavigate,
    handleDelete
}: ProjectModerateVariantProps) {

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

    const statusColor = project.label_color || (project.status === 'active' ? '#10b981' : '#374151');

    return (
        /**
         * ARCHITECTURE NOTE:
         * This component owns the PADDING (p-4) and BACKGROUND (absolute inset-0).
         * The parent UniversalCard provides the FRAME (border, rounded corners, overflow-hidden).
         * We use remove existing padding from the parent (via cardVariants 'moderate') to allow this full-bleed background.
         */
        <div className="flex flex-col gap-3 relative group/card p-4">
            {/* Background hoisted to UniversalProjectCard */}

            <LegacyActions />
            {/* Header with Layout Parity */}
            <div className="flex gap-3 relative z-10">
                {/* Thumbnail */}
                <div className="w-14 h-14 rounded-lg bg-gradient-to-br from-white/[0.06] to-transparent border border-white/[0.06] flex items-center justify-center flex-shrink-0 overflow-hidden">
                    {project.image_url ? (
                        <img src={project.image_url} alt={project.title} className="w-full h-full object-cover" />
                    ) : (
                        <Folder size={22} className="text-gray-600" />
                    )}
                </div>

                {/* Title & Meta */}
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-1.5 mb-1.5">
                        <span className="text-[10px] font-mono font-semibold text-accent/90 bg-accent/[0.08] px-1.5 py-0.5 rounded">
                            {project.project_code || `P-${project.id}`}
                        </span>
                        {project.status && (
                            <span className="inline-flex items-center gap-1 text-[9px] font-medium capitalize px-1.5 py-0.5 rounded bg-white/[0.04] text-gray-500">
                                <div className="w-1 h-1 rounded-full bg-emerald-500" />
                                {project.status.replace('_', ' ')}
                            </span>
                        )}
                        {/* Feature Badges */}
                        <div className="flex items-center gap-1.5 ml-auto">
                            {project.github_repo && <div className="w-6 h-6 rounded-md bg-white/[0.06] flex items-center justify-center"><Github size={13} className="text-gray-400" /></div>}
                            {project.has_ai_content && <div className="w-6 h-6 rounded-md bg-purple-500/15 flex items-center justify-center"><Sparkles size={13} className="text-purple-400" /></div>}
                        </div>
                    </div>
                    <h3 className="text-base font-bold text-white leading-tight cursor-pointer hover:text-accent transition-colors line-clamp-2 uppercase tracking-wide"
                        onClick={(e) => { e.stopPropagation(); handleNavigate(); }}>
                        {project.title}
                    </h3>
                </div>
            </div>

            {/* Next Action - Premium Style */}
            <div className="rounded-lg bg-white/[0.08] border border-white/10 relative z-10">
                <div className="p-3 flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent/25 via-accent/10 to-transparent flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(var(--accent-rgb),0.15)]">
                        <Target size={16} className="text-accent" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <span className="text-[9px] text-gray-400 font-semibold uppercase tracking-wide">Next Action</span>
                        {nextTask ? (
                            <div className="text-[14px] text-white font-medium leading-snug line-clamp-2 mt-0.5">{nextTask.title}</div>
                        ) : (
                            <div className="flex items-center gap-1.5 mt-0.5 text-gray-500"><Plus size={12} /><span className="text-[13px]">Add first task</span></div>
                        )}
                    </div>
                </div>
            </div>

            {/* Metrics Row - Clean 3-Column Grid */}
            <div className="grid grid-cols-3 gap-3 relative z-10">
                {/* Column 1: Stacked Progress Bars */}
                {/* Column 1: Stacked Progress Bars */}
                <div className="space-y-2">
                    <GradientLEDBar value={project.priority || 0} max={5} gradient="priority" size="sm" label="Priority" showValue onChange={(val) => db.projects.update(project.id!, { priority: val })} />
                    <GradientLEDBar value={project.intrusiveness || 0} max={5} gradient="impact" size="sm" label="Impact" showValue onChange={(val) => db.projects.update(project.id!, { intrusiveness: val })} />
                </div>
                {/* Column 2: Time Tracking */}
                <div className="flex flex-col justify-center gap-1.5 border-l border-white/10 pl-3">
                    <div className="flex items-center gap-2 text-[11px] text-gray-400 font-medium">
                        <Clock size={12} className="text-gray-500" />
                        <span>Est: <span className="text-gray-200 font-mono">{project.total_theorized_hours || 0}h</span></span>
                    </div>
                    <div className={clsx("flex items-center gap-2 text-[11px] font-medium", (project.time_estimate_active || 0) > (project.total_theorized_hours || 0) ? "text-red-400" : "text-gray-300")}>
                        <Zap size={12} className={(project.time_estimate_active || 0) > (project.total_theorized_hours || 0) ? "text-red-400" : "text-amber-500"} />
                        <span>Active: <span className="font-mono text-gray-200">{project.time_estimate_active || 0}h</span></span>
                    </div>
                </div>
                {/* Column 3: Schedule */}
                <div className="flex flex-col justify-center gap-1.5 border-l border-white/10 pl-3">
                    <div className="flex items-center gap-2 text-[11px] text-gray-400 font-medium">
                        <Calendar size={12} className="text-gray-500" />
                        <span className={project.target_completion_date ? "text-gray-200" : "text-gray-600"}>{project.target_completion_date ? new Date(project.target_completion_date).toLocaleDateString() : 'No deadline'}</span>
                    </div>
                    {project.category && <div className="flex items-center gap-1.5 text-[10px] text-accent font-medium"><Folder size={11} /><span>{project.category}</span></div>}
                </div>
            </div>

            {/* Bottom Status Section - Premium Three Column */}
            <div className="pt-2 border-t border-white/[0.06] relative z-10 w-full">
                <div className="grid grid-cols-3 gap-2">
                    {/* Design Phase */}
                    <div className="flex items-center gap-3">
                        <div className="relative w-10 h-10">
                            <svg className="w-10 h-10 -rotate-90" viewBox="0 0 36 36">
                                <circle cx="18" cy="18" r="15" fill="none" stroke="currentColor" strokeWidth="3" className="text-white/10" />
                                <circle
                                    cx="18" cy="18" r="15" fill="none" stroke="currentColor" strokeWidth="3"
                                    strokeDasharray={`${(['idea', 'draft', 'full', 'frozen'].indexOf(project.design_status || 'idea') + 1) * 25}, 100`}
                                    className="text-accent"
                                    strokeLinecap="round"
                                />
                            </svg>
                            <Layers size={14} className="absolute inset-0 m-auto text-gray-400" />
                        </div>
                        <div>
                            <div className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider">Design Phase</div>
                            <div className="text-sm text-white font-medium capitalize">{project.design_status || 'Idea'}</div>
                        </div>
                    </div>

                    {/* Build Status */}
                    <div className="flex items-center gap-3 border-l border-white/10 pl-3">
                        <div className="w-10 h-10 rounded-full bg-white/[0.04] border border-white/10 flex items-center justify-center">
                            {project.build_status === 'finished' ? (
                                <Check size={16} className="text-green-500" />
                            ) : (
                                <Hammer size={14} className="text-gray-400" />
                            )}
                        </div>
                        <div>
                            <div className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider">Build Status</div>
                            <div className="text-sm text-white font-medium capitalize flex items-center gap-1.5">
                                {project.build_status === 'wip' && <div className="w-1.5 h-1.5 rounded-full bg-yellow-500 animate-pulse" />}
                                {project.build_status || 'Unbuilt'}
                            </div>
                        </div>
                    </div>

                    {/* Last Updated */}
                    <div className="flex items-center gap-3 border-l border-white/10 pl-3">
                        <div className="w-10 h-10 rounded-full bg-white/[0.04] border border-white/10 flex items-center justify-center">
                            <Clock size={14} className="text-gray-400" />
                        </div>
                        <div>
                            <div className="text-[10px] text-gray-500 font-semibold uppercase tracking-wider">Last Updated</div>
                            <div className="text-sm text-white font-medium">
                                {project.updated_at ? formatDistanceToNow(new Date(project.updated_at), { addSuffix: false }) : 'Never'}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Tags Row */}
                <div className="mt-2 pt-2 border-t border-white/[0.04] flex items-center justify-between">
                    <TagsRow
                        tags={[
                            ...(project.category ? [{ label: project.category, color: 'accent' as const }] : []),
                            ...(project.project_type ? [{ label: project.project_type, color: 'default' as const }] : []),
                            ...(project.tags || []).slice(0, 3).map(tag => ({ label: tag, color: 'default' as const })),
                        ]}
                        size="md"
                        variant="monochrome"
                        onTagClick={(tag) => {
                            useUIStore.getState().openGlobalSearchWithQuery(tag.label);
                        }}
                    />
                    {/* GitHub link if present */}
                    {project.github_repo && (
                        <div className="ml-auto text-[11px] text-gray-400 flex items-center gap-1">
                            <Github size={12} /> {project.github_repo.split('/').pop()}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
