import React from 'react';
import { clsx } from 'clsx';
import { db, type Project } from '../../../../lib/db';
import { RadialGauge } from '../../../ui/RadialGauge';
import { MiniLinkMap } from '../../../ui/MiniLinkMap';
import { MiniLineChart } from '../../../ui/MiniLineChart';
import { GradientLEDBar } from '../../../ui/GradientLEDBar';
import { TagsRow } from '../../../ui/TagsRow';
import { HeatmapGrid } from '../../../ui/HeatmapGrid';
import { CountdownTimer } from '../../../ui/CountdownTimer';
import { useUIStore } from '../../../../store/useStore';
import { Square, CheckSquare, RotateCcw, Archive, Trash2, Settings, GitBranch } from 'lucide-react';
import { toast } from 'sonner';

interface ProjectDenseVariantProps {
    project: Project;
    isCollapsed: boolean;
    onToggleCollapse?: () => void;
    onEdit: () => void;
    handleNavigate: () => void;
    handleDelete: () => void;
}

export function ProjectDenseVariant({
    project,
    isCollapsed,
    onToggleCollapse,
    onEdit,
    handleNavigate,
    handleDelete
}: ProjectDenseVariantProps) {

    // Mock linked projects for demo (would come from actual data)
    const linkedProjects = [
        { id: 1, label: 'PROJ-A', type: 'blocker' as const },
        { id: 2, label: 'PROJ-B', type: 'related' as const },
        { id: 3, label: 'PROJ-C', type: 'related' as const },
    ];

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
        <div
            className="flex flex-col h-full bg-[#0a0a0a] select-none transition-colors relative group"
            onClick={(e) => { e.stopPropagation(); handleNavigate(); }}
        >
            <LegacyActions />
            {/* Header */}
            <div className="flex items-center justify-between px-4 py-2 border-b border-accent/20 bg-accent/5">
                <div className="flex items-center gap-2 min-w-0">
                    <span className={clsx(
                        "shrink-0 px-1.5 py-0.5 rounded text-[8px] font-bold uppercase",
                        project.status === 'active' ? "bg-emerald-500 text-black" : "bg-gray-700 text-gray-300"
                    )}>
                        {project.status === 'active' ? 'LIVE' : project.status?.slice(0, 4)}
                    </span>
                    <h3 className="text-sm font-bold text-white uppercase tracking-wide truncate">
                        {project.project_code || 'PROJECT'}: {project.title}
                    </h3>
                </div>
                <span className="text-[10px] font-mono text-accent shrink-0">
                    {project.progress || 0}%
                </span>
            </div>

            {/* Main Content Grid */}
            <div className="flex-1 grid grid-cols-4 gap-px bg-accent/10 min-h-0 overflow-hidden">

                {/* Column 1: Gauges (2 cols wide) */}
                <div className="col-span-2 bg-[#0a0a0a] p-2 flex items-center justify-around">
                    <RadialGauge value={project.progress || 0} max={100} size="sm" color="amber" label="Prog" />
                    <RadialGauge value={Math.min((project.financial_spend || 0) / Math.max(project.financial_budget || 1, 1) * 100, 100)} max={100} size="sm" color="green" label="Budg" />
                    <RadialGauge value={project.priority ? project.priority * 20 : 20} max={100} size="sm" color={project.priority && project.priority > 3 ? "red" : "blue"} label="Prio" />
                </div>

                {/* Column 2: Quick Stats */}
                <div className="bg-[#0a0a0a] p-2 flex flex-col justify-center gap-1 border-l border-accent/10">
                    <div className="flex justify-between text-[8px]">
                        <span className="text-gray-500">HOURS</span>
                        <span className="text-white font-mono">{project.time_estimate_active || 0}/{project.total_theorized_hours || 0}</span>
                    </div>
                    <div className="flex justify-between text-[8px]">
                        <span className="text-gray-500">RISK</span>
                        <span className={clsx("font-bold", project.risk_level === 'high' ? "text-red-400" : "text-emerald-400")}>{project.risk_level?.toUpperCase() || 'LOW'}</span>
                    </div>
                    <div className="flex justify-between text-[8px]">
                        <span className="text-gray-500">DESIGN</span>
                        <span className="text-blue-300 font-mono">{project.design_status?.slice(0, 6).toUpperCase() || 'N/A'}</span>
                    </div>
                    <div className="flex justify-between text-[8px]">
                        <span className="text-gray-500">BUILD</span>
                        <span className="text-amber-300 font-mono">{project.build_status?.slice(0, 6).toUpperCase() || 'N/A'}</span>
                    </div>
                </div>

                {/* Column 3: Link Map */}
                <div className="bg-[#0a0a0a] p-2 flex flex-col border-l border-accent/10">
                    <div className="text-[8px] text-gray-500 uppercase mb-1">Links</div>
                    <MiniLinkMap links={linkedProjects} maxVisible={3} />
                </div>
            </div>

            {/* Charts Row */}
            <div className="grid grid-cols-2 gap-px bg-accent/10 border-t border-accent/10">
                {/* Velocity Chart */}
                <div className="bg-[#0a0a0a] p-2">
                    <MiniLineChart label="Velocity" color="blue" height={32} />
                </div>
                {/* Issues Chart */}
                <div className="bg-[#0a0a0a] p-2">
                    <MiniLineChart label="Issues" color="red" height={32} />
                </div>
            </div>

            {/* LED Bars Row */}
            <div className="grid grid-cols-2 gap-4 px-3 py-1.5 border-t border-accent/10 bg-[#0a0a0a]">
                <GradientLEDBar
                    value={project.priority || 0}
                    max={5}
                    gradient="priority"
                    size="sm"
                    label="Priority"
                    showValue
                    onChange={(val) => db.projects.update(project.id!, { priority: val, updated_at: new Date() })}
                />
                <GradientLEDBar
                    value={project.intrusiveness || 1}
                    max={5}
                    gradient="impact"
                    size="sm"
                    label="Impact"
                    showValue
                    onChange={(val) => db.projects.update(project.id!, { intrusiveness: val, updated_at: new Date() })}
                />
            </div>

            {/* Tags Row */}
            <div className="px-3 py-1.5 border-t border-accent/10 bg-[#0a0a0a]">
                <TagsRow
                    tags={[
                        { label: project.project_type || 'PROJECT', color: 'accent' },
                        { label: project.design_status?.slice(0, 6) || 'N/A', color: project.design_status === 'complete' ? 'green' : 'blue' },
                        { label: project.build_status?.slice(0, 6) || 'N/A', color: project.build_status === 'complete' ? 'green' : 'amber' },
                    ].filter(t => t.label !== 'N/A')}
                    size="sm"
                    variant="colorful"
                    onTagClick={(tag) => {
                        useUIStore.getState().openGlobalSearchWithQuery(tag.label);
                    }}
                />
            </div>

            {/* Activity Heatmap */}
            <div className="px-3 py-1.5 border-t border-accent/10 bg-[#0a0a0a]">
                <div className="text-[7px] uppercase text-gray-500 mb-0.5">Activity</div>
                <HeatmapGrid rows={2} cols={12} color="accent" />
            </div>

            {/* Footer */}
            <div className="bg-accent/5 px-3 py-1 flex justify-between items-center text-[8px] text-gray-500 border-t border-accent/20">
                <div className="flex items-center gap-2">
                    <span className="font-mono">v{project.version || '0.1.0'}</span>
                    <span>|</span>
                    <span className="flex items-center gap-1"><GitBranch size={9} /> {project.github_repo?.split('/')[1] || 'local'}</span>
                </div>
                <CountdownTimer targetDate={project.target_completion_date} size="sm" showLabel={false} />
            </div>
        </div>
    );
}
