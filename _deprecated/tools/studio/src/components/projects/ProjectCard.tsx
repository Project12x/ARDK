import React, { useState } from 'react';
import { formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '../../store/useStore';
import { ProjectEditForm } from './ProjectEditForm';
import { useDroppable, useDraggable } from '@dnd-kit/core';
import { UniversalCard } from '../ui/UniversalCard';
import { useLiveQuery } from 'dexie-react-hooks';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { db } from '../../lib/db';
import type { Project } from '../../lib/db';
import { STATUS_COLORS } from '../../lib/constants';
import { Button } from '../ui/Button';
import { Settings, Zap, AlertTriangle, Clock, Calendar, Trash2, RotateCcw, X, Save, Archive, CheckSquare, Square, Link as LinkIcon, Sparkles, Upload, Github, Printer, Target, ExternalLink, Folder, Layers, Hammer, Plus, Tag, Check, Cpu, Activity, Box, List, GitBranch } from 'lucide-react';
import { RatingBar } from '../ui/RatingBar';
import { ProgressBar } from '../ui/ProgressBar';
import { safeDateStr, formatVersion } from '../../lib/utils';
import { ProjectSchema, type ProjectFormData } from '../../lib/schemas';
import clsx from 'clsx';
import { motion } from 'framer-motion';
import { LEDBar } from '../ui/LEDBar';
import { RadialGauge } from '../ui/RadialGauge';
import { HeatmapGrid } from '../ui/HeatmapGrid';
import { MiniLineChart } from '../ui/MiniLineChart';
import { MiniLinkMap } from '../ui/MiniLinkMap';
import { GradientLEDBar } from '../ui/GradientLEDBar';
import { TagsRow } from '../ui/TagsRow';
import { CountdownTimer } from '../ui/CountdownTimer';







export function GitHubLink({ repo }: { repo: string }) {
    const [data, setData] = useState<{ pushed_at: string, stars: number } | null>(null);
    const [loading, setLoading] = useState(false);

    const handleEnter = async () => {
        if (data || loading) return;
        setLoading(true);
        try {
            const res = await fetch(`https://api.github.com/repos/${repo}`);
            if (res.ok) {
                const json = await res.json();
                setData({ pushed_at: json.pushed_at, stars: json.stargazers_count });
            }
        } catch (e) { console.error(e); }
        setLoading(false);
    };

    const timeAgo = data ? Math.floor((new Date().getTime() - new Date(data.pushed_at).getTime()) / (1000 * 60 * 60 * 24)) : 0;
    const isActive = data && timeAgo < 7; // Active if < 7 days

    return (
        <a
            href={`https://github.com/${repo}`}
            target="_blank"
            rel="noopener noreferrer"
            className={clsx(
                "px-1.5 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border flex items-center gap-1 transition-colors relative group",
                isActive ? "border-green-500/50 text-green-400 bg-green-900/20" : "border-white/20 text-white bg-white/10 hover:bg-white/20"
            )}
            onClick={e => e.stopPropagation()}
            onMouseEnter={handleEnter}
            title={data ? `Last Push: ${new Date(data.pushed_at).toLocaleDateString()} (${timeAgo} days ago) | ${data.stars} Stars` : "Hover to check status"}
        >
            <Github size={10} className={clsx(loading && "animate-spin")} />
            {loading ? '...' : (data ? (isActive ? 'DEV' : 'REPO') : 'REPO')}

            {/* Tooltip visible on hover if data loaded */}
            {data && (
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-black border border-white/20 shadow-xl rounded whitespace-nowrap hidden group-hover:block z-50">
                    ⭐ {data.stars} | 🕒 {timeAgo}d
                </div>
            )}
        </a>
    );
}


export type ProjectCardDensity = 'compact' | 'moderate' | 'text' | 'dense';

function CardVariantText({ project, nextTask }: { project: Project, nextTask?: any }) {
    // Solo Aero Design - High Density Refactor
    const navigate = useNavigate();

    // Mock Data for Density Visualization
    const specs = [
        { k: 'MCU', v: 'ESP32-S3' },
        { k: 'PCB', v: 'Rev 1.2' },
        { k: 'Power', v: 'LiPo 2S' },
        { k: 'Sensor', v: 'IMU-X9' },
        { k: 'Disp', v: 'OLED 0.96"' }
    ];

    const tasks = [
        { t: 'Finalize enclosure CAD', s: 'active', p: 'high' },
        { t: 'Order PCB prototype', s: 'pending', p: 'med' },
        { t: 'Write sensor driver', s: 'pending', p: 'med' },
        { t: 'Battery life test', s: 'blocked', p: 'low' },
        { t: 'Doc update', s: 'pending', p: 'low' }
    ];

    return (
        <div className="flex flex-col h-full gap-3 font-mono">
            {/* Header: Compact & Info Dense */}
            <div className="flex items-center justify-between border-b border-white/10 pb-2">
                <div className="flex items-center gap-3 overflow-hidden">
                    <span className="text-[10px] text-accent/80 border border-accent/20 px-1.5 py-0.5 rounded bg-accent/5 shrink-0">
                        {project.project_code || `P-${project.id}`}
                    </span>
                    <h3
                        className="text-sm font-bold text-white hover:text-accent cursor-pointer truncate"
                        onClick={(e) => { e.stopPropagation(); navigate(`/project/${project.id}`); }}
                    >
                        {project.title}
                    </h3>
                    <div className="flex items-center gap-2 text-[10px] text-gray-500 shrink-0">
                        {project.github_repo && <span className="flex items-center gap-1 text-blue-400"><Github size={10} /> {project.github_repo.split('/')[1] || 'repo'}</span>}
                        <span>v{project.version || '0.1.0'}</span>
                    </div>
                </div>

                {/* Status Pill */}
                <div className={clsx(
                    "flex items-center gap-1.5 px-2 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider shrink-0",
                    project.status === 'active' ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20" :
                        "bg-gray-800 text-gray-400 border border-gray-700"
                )}>
                    <div className={clsx("w-1.5 h-1.5 rounded-full shadow-[0_0_5px_currentColor]",
                        project.status === 'active' ? "bg-emerald-400 animate-pulse" : "bg-gray-500")}
                    />
                    {project.status?.replace('_', ' ')}
                </div>
            </div>

            {/* Main Content Grid */}
            <div className="grid grid-cols-5 gap-3 flex-1 min-h-0">
                {/* Left Column: Task List (3/5 width) */}
                <div className="col-span-3 flex flex-col gap-2">
                    <div className="flex items-center justify-between text-[10px] text-gray-400 uppercase tracking-wider font-semibold">
                        <span className="flex items-center gap-1"><List size={10} /> Active Tasks</span>
                        <span className="text-accent">{tasks.length} Pending</span>
                    </div>
                    <div className="flex-1 overflow-y-auto custom-scrollbar pr-1 border border-white/5 rounded bg-white/[0.02]">
                        <table className="w-full text-left text-[10px] border-collapse">
                            <tbody>
                                {nextTask && (
                                    <tr className="border-b border-white/5 bg-accent/5">
                                        <td className="p-1.5 pl-2 text-white font-medium">{nextTask.title}</td>
                                        <td className="p-1.5 text-right"><span className="text-red-400 font-bold">NEXT</span></td>
                                    </tr>
                                )}
                                {tasks.map((t, i) => (
                                    <tr key={i} className="border-b border-white/5 last:border-0 hover:bg-white/5 transition-colors">
                                        <td className="p-1.5 pl-2 text-gray-300 truncate max-w-[120px]">{t.t}</td>
                                        <td className="p-1.5 text-right">
                                            <span className={clsx("px-1 rounded", t.p === 'high' ? "text-red-400" : "text-gray-600")}>{t.p === 'high' ? 'HI' : ''}</span>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>

                {/* Right Column: Key/Value Specs & BOM (2/5 width) */}
                <div className="col-span-2 flex flex-col gap-2">
                    {/* Specs Table */}
                    <div className="flex-1 border border-white/5 rounded bg-white/[0.02] p-1.5 flex flex-col gap-1">
                        <div className="text-[9px] text-gray-500 uppercase font-bold mb-0.5 flex items-center gap-1"><Cpu size={9} /> Specs</div>
                        {specs.map((s, i) => (
                            <div key={i} className="flex justify-between items-center text-[10px] border-b border-white/5 last:border-0 pb-0.5">
                                <span className="text-gray-500">{s.k}</span>
                                <span className="text-accent/90 font-mono">{s.v}</span>
                            </div>
                        ))}
                    </div>

                    {/* BOM & Progress */}
                    <div className="border border-white/5 rounded bg-white/[0.02] p-2 space-y-2">
                        <div className="space-y-1">
                            <div className="flex justify-between text-[9px] uppercase font-bold text-gray-500">
                                <span>BOM Status</span>
                                <span className="text-green-400">85%</span>
                            </div>
                            <LEDBar value={8} max={10} segments={10} color="green" size="sm" />
                        </div>
                        <div className="space-y-1">
                            <div className="flex justify-between text-[9px] uppercase font-bold text-gray-500">
                                <span>Budget</span>
                                <span className="text-amber-400">$450/$750</span>
                            </div>
                            <LEDBar value={6} max={10} segments={10} color="amber" size="sm" />
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

function CardVariantCompact({ project }: { project: Project }) {
    // Bento Tile - Clean, readable, focused
    const navigate = useNavigate();
    return (
        <div
            className="flex flex-col h-full bg-white/5 hover:bg-white/10 border border-white/10 hover:border-accent/50 transition-all rounded-lg p-4 cursor-pointer relative overflow-hidden group"
            onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}
        >
            {/* Status Background Glow */}
            <div className="absolute top-0 right-0 w-24 h-24 bg-accent/5 blur-3xl -translate-y-1/2 translate-x-1/2 rounded-full pointer-events-none group-hover:bg-accent/10 transition-colors" />

            <div className="flex flex-col gap-1 z-10">
                <div className="flex justify-between items-start">
                    <span className="text-[10px] font-mono text-gray-500 bg-black/20 px-1.5 rounded">{project.project_code || `P-${project.id}`}</span>
                    <div className={clsx("w-2 h-2 rounded-full", project.status === 'active' ? "bg-accent shadow-[0_0_5px_currentColor]" : "bg-gray-600")} />
                </div>
                <h3 className="font-bold text-base text-white leading-tight line-clamp-2 mt-1">{project.title}</h3>
            </div>

            <div className="mt-auto space-y-3 z-10">
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

function CardVariantCompact_HyperReal({ project }: { project: Project }) {
    // Hyper-Real Data Tile
    const navigate = useNavigate();
    return (
        <div
            className="flex flex-col h-full justify-between bg-black border border-white/10 hover:border-accent group transition-all p-3 relative overflow-hidden cursor-pointer"
            onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}
        >
            {/* Background Tech Line */}
            <div className="absolute top-0 right-0 w-16 h-[1px] bg-gradient-to-l from-accent to-transparent opacity-20" />

            <div className="flex justify-between items-start gap-2">
                <div className="min-w-0 flex-1">
                    <span className="text-[9px] font-mono text-accent block mb-0.5 tracking-tight">{project.project_code || `P-${project.id}`}</span>
                    <h3 className="font-bold text-xs text-white leading-tight truncate">{project.title}</h3>
                </div>
                <div className={clsx("w-1.5 h-1.5 rounded-sm mt-1 shrink-0", project.status === 'active' ? "bg-emerald-500 shadow-[0_0_4px_rgba(16,185,129,0.8)] animate-pulse" : "bg-gray-600")} />
            </div>

            <div className="mt-auto pt-2 grid grid-cols-2 gap-4 border-t border-white/5">
                {/* Priority Widget */}
                <div>
                    <span className="text-[8px] text-gray-500 uppercase font-bold block mb-0.5">Priority</span>
                    <div className="flex gap-0.5 h-1.5">
                        {[1, 2, 3, 4, 5].map(i => (
                            <div key={i} className={clsx("w-1.5 h-full rounded-[1px]", (project.priority || 0) >= i ? "bg-red-500" : "bg-white/10")} />
                        ))}
                    </div>
                </div>
                {/* Status/Progress Widget */}
                <div className="text-right">
                    <span className="text-[8px] text-gray-500 uppercase font-bold block mb-0.5">Status</span>
                    <span className="text-[9px] font-mono text-white inline-block px-1 py-0.5 bg-white/5 rounded border border-white/5 uppercase">
                        {project.status === 'active' ? 'ACTV' : project.status?.substring(0, 4).toUpperCase()}
                    </span>
                </div>
            </div>
        </div>
    );
}

function CardVariantCompact_Old({ project }: { project: Project }) {
    // Mobile / Tile Design - Data Rich
    const navigate = useNavigate();
    return (
        <div className="flex flex-col h-full justify-between p-3 gap-2" onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}>
            <div className="flex items-start justify-between gap-2">
                <div className="min-w-0">
                    <span className="text-[9px] font-mono text-accent opacity-70 block mb-0.5">{project.project_code || `P-${project.id}`}</span>
                    <h3 className="font-bold text-sm text-white leading-tight truncate">{project.title}</h3>
                </div>
                <div className={clsx("w-2 h-2 rounded-full shrink-0 mt-1", project.status === 'active' ? "bg-accent animate-pulse" : "bg-gray-600")} />
            </div>

            <div className="flex items-end justify-between gap-2 mt-auto">
                <div className="flex flex-col">
                    <span className="text-[9px] text-gray-500 uppercase font-bold">Priority</span>
                    <RatingBar value={project.priority} max={5} size="sm" activeColor="bg-red-500" passiveColor="bg-red-900/30" readonly />
                </div>
                <div className="flex flex-col items-end">
                    <span className="text-[9px] text-gray-500 uppercase font-bold">Progress</span>
                    <span className="text-xs font-mono font-bold text-white">{(project.progress || 0)}%</span>
                </div>
            </div>
        </div>
    );
}

function CardVariantDense({ project }: { project: Project }) {
    // Enterprise Dashboard Style - Full-Featured Dense Card
    const navigate = useNavigate();

    // Mock linked projects for demo (would come from actual data)
    const linkedProjects = React.useMemo(() => {
        // This would be populated from actual project links
        return [
            { id: 1, label: 'PROJ-A', type: 'blocker' as const },
            { id: 2, label: 'PROJ-B', type: 'related' as const },
            { id: 3, label: 'PROJ-C', type: 'related' as const },
        ].slice(0, Math.floor(Math.random() * 4)); // Randomize for demo
    }, [project.id]);

    return (
        <div
            className="flex flex-col h-full bg-[#0a0a0a] border border-accent/30 rounded-lg overflow-hidden hover:border-accent transition-all cursor-pointer select-none"
            onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}
        >
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

function CardVariantDense_HyperReal({ project }: { project: Project }) {
    // Hyper-Real Bloomberg Style
    const navigate = useNavigate();

    // Helper for Leaders
    const Row = ({ label, value, color = "text-white" }: { label: string, value: any, color?: string }) => (
        <div className="flex items-baseline justify-between text-[9px] min-w-0">
            <span className="text-gray-500 font-bold shrink-0">{label}</span>
            <span className="border-b border-dotted border-gray-800 flex-1 mx-1 mb-1 opacity-50" />
            <span className={clsx("font-mono truncate max-w-[50%]", color)}>{value}</span>
        </div>
    );

    return (
        <div
            className="flex flex-col h-full bg-black border border-white/20 select-none cursor-pointer group hover:border-accent transition-colors font-mono tracking-tight"
            onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}
        >
            {/* Inverted Header */}
            <div className="bg-white/10 text-white px-2 py-0.5 flex justify-between items-center text-[9px] font-bold border-b border-white/20">
                <span className="text-accent">{project.project_code || `P-${project.id}`}</span>
                <span className={clsx("uppercase", project.status === 'active' ? "text-emerald-400 blink-subtle" : "text-gray-500")}>
                    [{project.status === 'active' ? 'LIVE' : 'IDLE'}]
                </span>
            </div>

            <div className="grid grid-cols-2 divide-x divide-white/20 flex-1 min-h-0">
                {/* Col 1: Core Data */}
                <div className="flex flex-col">
                    <div className="p-2 border-b border-white/20">
                        <h3 className="text-white font-bold text-[10px] leading-tight line-clamp-2 uppercase group-hover:text-accent transition-colors">
                            {project.title}
                        </h3>
                    </div>
                    <div className="p-2 space-y-0.5 flex-1 min-h-0 overflow-hidden bg-[url('/noise.png')] bg-blend-overlay">
                        <Row label="PRIO" value={project.priority || 0} color={project.priority && project.priority > 3 ? "text-red-500" : "text-white"} />
                        <Row label="RISK" value={(project.risk_level || 'low').toUpperCase()} color={project.risk_level === 'high' ? "text-red-500" : "text-emerald-500"} />
                        <Row label="DSGN" value={(project.design_status || '-').toUpperCase().substring(0, 8)} />
                        <Row label="BLD" value={(project.build_status || '-').toUpperCase().substring(0, 8)} />
                        <div className="mt-2 flex gap-2">
                            <span className="text-[8px] text-gray-600 flex items-center gap-1">
                                <span className="text-green-500">{project.status === 'active' ? '[x]' : '[ ]'}</span> ACTV
                            </span>
                            <span className="text-[8px] text-gray-600 flex items-center gap-1">
                                <span className={project.financial_budget ? "text-green-500" : "text-gray-700"}>{project.financial_budget ? '[x]' : '[ ]'}</span> FUND
                            </span>
                        </div>
                    </div>
                </div>

                {/* Col 2: Metrics & Visualization */}
                <div className="flex flex-col bg-white/[0.02]">
                    <div className="flex-1 p-2 space-y-1">
                        <div className="flex justify-between items-end border-b border-white/10 pb-1">
                            <span className="text-[8px] text-gray-500 font-bold">HOURS</span>
                            <span className="text-xs font-bold text-amber-500">{project.time_estimate_active || 0}</span>
                        </div>
                        <div className="flex justify-between items-end border-b border-white/10 pb-1">
                            <span className="text-[8px] text-gray-500 font-bold">BUDGET</span>
                            <span className="text-xs font-bold text-emerald-500">${project.financial_spend || 0}</span>
                        </div>

                        {/* CSS Sparkline */}
                        <div className="mt-2 h-full min-h-[20px] flex items-end gap-[1px] opacity-70">
                            {[0.4, 0.7, 0.3, 0.9, 0.5, 0.2, 0.8, 0.6, 0.4].map((h, i) => (
                                <div key={i} className="flex-1 bg-accent" style={{ height: `${h * 100}%` }} />
                            ))}
                        </div>
                        <div className="text-[7px] text-gray-600 text-center font-mono">ACTIVITY VOL</div>
                    </div>
                    <div className="px-2 py-1 bg-white/5 border-t border-white/10 text-right">
                        <span className="text-[8px] text-gray-500 font-mono">{safeDateStr(project.updated_at)}</span>
                    </div>
                </div>
            </div>
        </div>
    );
}

function CardVariantDense_Old({ project }: { project: Project }) {
    // Bloomberg / Terminal Style (Theme Aware)
    // Concept: Monospace, High Contrast, Grid Lines, No Gradients
    const navigate = useNavigate();

    return (
        <div
            className="flex flex-col h-full font-mono text-[10px] bg-black border border-accent/20 select-none cursor-pointer group hover:border-accent transition-colors"
            onClick={(e) => { e.stopPropagation(); navigate(`/projects/${project.id}`); }}
        >
            {/* Terminal Header */}
            <div className="flex justify-between items-center bg-accent/10 px-2 py-1 border-b border-accent/20">
                <span className="font-bold text-accent uppercase tracking-wider">{project.project_code || `P-${project.id}`}</span>
                <span className={clsx("uppercase font-bold", project.status === 'active' ? "text-green-500 blink-subtle" : "text-gray-500")}>
                    {project.status === 'active' ? '● LIVE' : '○ IDLE'}
                </span>
            </div>

            {/* Data Grid */}
            <div className="grid grid-cols-2 h-full divide-x divide-accent/20">
                {/* Left Col: Main Info */}
                <div className="flex flex-col justify-between p-2">
                    <h3 className="text-white font-bold text-xs uppercase leading-tight line-clamp-2 mb-2 group-hover:text-accent group-hover:underline decoration-dashed transition-all">
                        {project.title}
                    </h3>
                    <div className="space-y-1">
                        <div className="flex justify-between">
                            <span className="text-gray-500">PRIO</span>
                            <span className="text-red-500 font-bold">{'!'.repeat(project.priority || 0)}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-gray-500">RISK</span>
                            <span className={clsx("font-bold uppercase", (project.risk_level === 'high') ? "text-red-500" : "text-green-500")}>
                                {project.risk_level?.substring(0, 3) || 'LOW'}
                            </span>
                        </div>
                    </div>
                </div>

                {/* Right Col: Metrics */}
                <div className="flex flex-col">
                    <div className="p-2 border-b border-accent/20 flex justify-between items-baseline">
                        <span className="text-gray-500">HRS</span>
                        <span className="text-amber-500 font-bold text-xs">{project.time_estimate_active || 0}</span>
                    </div>
                    <div className="p-2 border-b border-accent/20 flex justify-between items-baseline">
                        <span className="text-gray-500">BDGT</span>
                        <span className="text-green-500 font-bold text-xs">${project.financial_spend || 0}</span>
                    </div>

                    {/* Simulated Ticker/Sparkline */}
                    <div className="flex-1 p-1 flex items-end justify-end gap-0.5 bg-accent/5 overflow-hidden relative">
                        <div className="absolute top-0.5 left-1 text-[8px] text-accent/50">ACTV</div>
                        {[40, 20, 60, 30, 80, 50, 90, 20].map((h, i) => (
                            <div key={i} className="w-1.5 bg-accent/40" style={{ height: `${h}%` }} />
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
}

function CardVariantModerate({
    project,
    nextTask,
    onEdit,
    onArchive,
    onDelete,
    hideActions
}: {
    project: Project,
    nextTask: any,
    onEdit: () => void,
    onArchive: () => void,
    onDelete: () => void,
    hideActions?: boolean
}) {
    const navigate = useNavigate();

    return (
        <>
            {/* Header with Thumbnail & Badges */}
            <div className="flex gap-3 mb-3">
                {/* Thumbnail */}
                <div
                    className="w-14 h-14 rounded-lg bg-gradient-to-br from-white/[0.06] to-transparent border border-white/[0.06] flex items-center justify-center flex-shrink-0 overflow-hidden"
                >
                    {project.image_url ? (
                        <img
                            src={project.image_url}
                            alt={project.title}
                            className="w-full h-full object-cover"
                        />
                    ) : (
                        <Folder size={22} className="text-gray-600" />
                    )}
                </div>

                {/* Title & Meta */}
                <div className="flex-1 min-w-0">
                    {/* Top Badge Row */}
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

                        {/* Feature Badges - Larger */}
                        <div className="flex items-center gap-1.5 ml-auto">
                            {project.github_repo && (
                                <div className="w-6 h-6 rounded-md bg-white/[0.06] flex items-center justify-center" title="Git Connected">
                                    <Github size={13} className="text-gray-400" />
                                </div>
                            )}
                            {project.has_ai_content && (
                                <div className="w-6 h-6 rounded-md bg-purple-500/15 flex items-center justify-center" title="AI Enhanced">
                                    <Sparkles size={13} className="text-purple-400" />
                                </div>
                            )}
                            {project.has_3d_models && (
                                <div className="w-6 h-6 rounded-md bg-cyan-500/15 flex items-center justify-center" title="3D Models">
                                    <Box size={13} className="text-cyan-400" />
                                </div>
                            )}
                            {project.has_pcb && (
                                <div className="w-6 h-6 rounded-md bg-green-500/15 flex items-center justify-center" title="PCB/Electronics">
                                    <Cpu size={13} className="text-green-400" />
                                </div>
                            )}
                        </div>

                        {/* Actions - Edit, Archive, Trash */}
                        {!hideActions && (
                            <div className="flex gap-0.5 opacity-0 group-hover:opacity-100 transition-opacity ml-1">
                                <button
                                    className="p-1.5 rounded-md text-gray-600 hover:text-white hover:bg-white/[0.08] transition-all"
                                    onClick={(e) => { e.stopPropagation(); onEdit(); }}
                                    title="Edit"
                                >
                                    <Settings size={13} />
                                </button>
                                <button
                                    className="p-1.5 rounded-md text-gray-600 hover:text-amber-400 hover:bg-amber-500/10 transition-all"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onArchive();
                                    }}
                                    title="Archive"
                                >
                                    <Archive size={13} />
                                </button>
                                <button
                                    className="p-1.5 rounded-md text-gray-600 hover:text-red-400 hover:bg-red-500/10 transition-all"
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        onDelete();
                                    }}
                                    title="Trash"
                                >
                                    <Trash2 size={13} />
                                </button>
                            </div>
                        )}
                    </div>

                    {/* Title */}
                    <h3
                        className="text-base font-bold text-white leading-tight cursor-pointer hover:text-accent transition-colors line-clamp-2 uppercase tracking-wide"
                        onClick={(e) => { e.stopPropagation(); navigate(`/project/${project.id}`); }}
                    >
                        {project.title}
                    </h3>
                    {project.role && (
                        <p className="text-[12px] text-gray-600 mt-0.5">{project.role}</p>
                    )}
                </div>
            </div>

            {/* Next Action - Premium Style with Glow */}
            <div className="mb-4 rounded-lg bg-white/[0.08] border border-white/10">
                <div className="p-3 flex items-start gap-3">
                    <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-accent/25 via-accent/10 to-transparent flex items-center justify-center flex-shrink-0 shadow-[0_0_20px_rgba(var(--accent-rgb),0.15)]">
                        <Target size={16} className="text-accent" />
                    </div>
                    <div className="flex-1 min-w-0">
                        <span className="text-[9px] text-gray-400 font-semibold uppercase tracking-wide">Next Action</span>
                        {nextTask ? (
                            <div className="text-[14px] text-white font-medium leading-snug line-clamp-2 mt-0.5">
                                {nextTask.title}
                            </div>
                        ) : (
                            <div className="flex items-center gap-1.5 mt-0.5 text-gray-500">
                                <Plus size={12} />
                                <span className="text-[13px]">Add first task</span>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Metrics Row - Clean 3-Column Grid */}
            <div className="grid grid-cols-3 gap-3 mb-3">
                {/* Column 1: Stacked Progress Bars */}
                <div className="space-y-4 pt-1">
                    <GradientLEDBar
                        value={project.priority || 0}
                        max={5}
                        gradient="priority"
                        size="md"
                        label="Priority"
                        showValue
                        onChange={(val) => db.projects.update(project.id!, { priority: val, updated_at: new Date() })}
                    />
                    <GradientLEDBar
                        value={project.intrusiveness || 0}
                        max={5}
                        gradient="impact"
                        size="md"
                        label="Impact"
                        showValue
                        onChange={(val) => db.projects.update(project.id!, { intrusiveness: val, updated_at: new Date() })}
                    />
                </div>

                {/* Column 2: Time Tracking */}
                <div className="flex flex-col justify-center gap-1.5 border-l border-white/10 pl-3">
                    <div className="flex items-center gap-2 text-[11px] text-gray-400 font-medium">
                        <Clock size={12} className="text-gray-500" />
                        <span>Est: <span className="text-gray-200 font-mono">{project.total_theorized_hours || 0}h</span></span>
                    </div>
                    <div className={clsx(
                        "flex items-center gap-2 text-[11px] font-medium",
                        (project.time_estimate_active || 0) > (project.total_theorized_hours || 0) ? "text-red-400" : "text-gray-300"
                    )}>
                        <Zap size={12} className={(project.time_estimate_active || 0) > (project.total_theorized_hours || 0) ? "text-red-400" : "text-amber-500"} />
                        <span>Active: <span className="font-mono text-gray-200">{project.time_estimate_active || 0}h</span></span>
                    </div>
                </div>

                {/* Column 3: Schedule */}
                <div className="flex flex-col justify-center gap-1.5 border-l border-white/10 pl-3">
                    <div className="flex items-center gap-2 text-[11px] text-gray-400 font-medium">
                        <Calendar size={12} className="text-gray-500" />
                        <span className={project.target_completion_date ? "text-gray-200" : "text-gray-600"}>
                            {safeDateStr(project.target_completion_date) || 'No deadline'}
                        </span>
                    </div>
                    {project.github_repo ? (
                        <div className="flex items-center gap-2 text-[11px] text-gray-400">
                            <Github size={12} className="text-gray-500" />
                            <GitHubLink repo={project.github_repo} />
                        </div>
                    ) : project.category && (
                        <div className="flex items-center gap-1.5 text-[10px] text-accent font-medium">
                            <Folder size={11} />
                            <span>{project.category}</span>
                        </div>
                    )}
                </div>
            </div>

            {/* Bottom Status Section - Premium Three Column */}
            <div className="mt-auto pt-4 border-t border-white/[0.06]">
                <div className="grid grid-cols-3 gap-4">
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
                    <div className="flex items-center gap-3">
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
                    <div className="flex items-center gap-3">
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
                <div className="mt-4 pt-4 border-t border-white/[0.04] flex items-center justify-between">
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
                        <div className="ml-auto">
                            <GitHubLink repo={project.github_repo} />
                        </div>
                    )}
                </div>
            </div>
        </>
    );

}

export function ProjectCard({
    project,
    onClick,
    isTrash,
    onPurge,
    onRestoreTrash,
    collapsed,
    density = 'moderate', // Default density
    layoutMode = 'grid', // Legacy prop, kept for compatibility
    // v21 Batch & Drag Props
    selectable,
    selected,
    onToggleSelect,
    onDropLink,
    className,
    hideActions
}: {
    project: Project,
    onClick: () => void,
    isTrash: boolean,
    onPurge: () => void,
    onRestoreTrash: () => void,
    collapsed: boolean,
    density?: ProjectCardDensity,
    layoutMode?: 'grid' | 'list',
    selectable?: boolean,
    selected?: boolean,
    onToggleSelect?: () => void,
    onDropLink?: (sourceId: number, targetId: number) => void,
    className?: string,
    hideActions?: boolean
}) {
    // Effective density logic: Collapsed prop overrides density
    // If collapsed is true, we force 'compact' behavior (collapsed view)
    // If not collapsed, we use the density setting
    const effectiveDensity = collapsed ? 'compact' : density;

    const navigate = useNavigate();
    const { addToStash } = useUIStore();

    // Sync local state when global prop changes
    const [isCollapsed, setIsCollapsed] = useState(collapsed);
    if (collapsed !== isCollapsed) setIsCollapsed(collapsed);

    const handleToggleCollapse = (e: React.MouseEvent) => {
        e.stopPropagation();
        setIsCollapsed(!isCollapsed);
    };

    const nextTask = useLiveQuery(() =>
        db.project_tasks.where({ project_id: project.id! }).filter(t => t.status === 'pending').first()
    );

    const [isEditMode, setIsEditMode] = useState(false);


    // --- Render States ---

    // 1. Trash State
    if (isTrash) {
        return (
            <motion.div layout initial={{ opacity: 0 }} animate={{ opacity: 1 }} className={clsx("border border-red-900/30 bg-red-950/10 p-4 flex justify-between items-center bg-[url('/noise.png')]", className)}>
                <div className="opacity-50 flex items-center gap-4">
                    <Trash2 className="text-red-700" size={20} />
                    <div>
                        <h3 className="text-lg font-black text-red-700 line-through">{project.title}</h3>
                        <p className="text-xs font-mono text-red-900">DELETED: {safeDateStr(project.deleted_at)}</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); onRestoreTrash(); }}><RotateCcw size={14} className="mr-1" /> RESTORE</Button>
                    <Button size="sm" className="bg-red-900 hover:bg-red-800 text-white border-none" onClick={(e) => { e.stopPropagation(); onPurge(); }}><Trash2 size={14} /> PURGE</Button>
                </div>
            </motion.div>
        )
    }

    // 2. Edit Mode
    // For brevity in this refactor, delegating edit mode back to original or separate component would be ideal, 
    // but here we keep it or better yet, we might simplify.
    // However, since UniversalCard wraps the content, we can render the Edit Mode as an overlay OR 
    // if Edit Mode is active, we just return the Edit Form (not Draggable).
    // 2. Edit Mode
    if (isEditMode) {
        return <ProjectEditForm project={project} onClose={() => setIsEditMode(false)} className={cardVariants({ density: 'compact', variant: 'default' })} />;
    }

    // 3. Main Universal Card (Handles Draggable & Droppable internally)
    return (
        <UniversalCard
            entityType="project-item"
            entityId={project.id!}
            title={project.title}
            metadata={{
                priority: project.priority,
                status: project.status,
                code: project.project_code || `P-${project.id}`,
                project: project
            }}
            isDroppable={true}
            dropZoneId={`project-drop-zone-${project.id}`}
            onClick={onClick}
            noDefaultStyles={true} // Full Control Over Styling
            className={clsx(
                "group relative flex flex-col gap-0 rounded-2xl overflow-hidden transition-all duration-300",
                "bg-gradient-to-b from-[rgba(26,26,26,0.95)] to-[rgba(13,13,13,0.95)] backdrop-blur-xl",
                "border border-white/[0.08] shadow-2xl shadow-black/50",
                "hover:border-white/[0.15] hover:shadow-[0_8px_40px_rgba(0,0,0,0.4)] hover:-translate-y-0.5",
                selected && "ring-2 ring-accent shadow-[0_0_30px_rgba(var(--accent-rgb),0.2)]",
                collapsed ? "h-14 min-h-0" :
                    density === 'compact' ? "h-52 min-h-0" :
                        density === 'text' ? "h-auto min-h-[14rem]" :
                            density === 'dense' ? "h-[30rem] min-h-0" :
                                "min-h-[18rem]", // Default/Moderate - tighter
                className
            )}
        >
            {/* 1. Background Image & Gradient Overlay */}
            {
                !collapsed && (
                    <div className="absolute inset-0 z-0 pointer-events-none">
                        {project.image_url ? (
                            <div className="absolute inset-0 bg-cover bg-center opacity-40 mix-blend-overlay transition-transform duration-700 group-hover:scale-105" style={{ backgroundImage: `url(${project.image_url})` }} />
                        ) : (
                            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-50" />
                        )}
                        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/90 to-black/40" />
                        {/* Status Color Glow */}
                        <div
                            className="absolute top-0 right-0 w-64 h-64 bg-current opacity-10 blur-[80px] -translate-y-1/2 translate-x-1/2 rounded-full mix-blend-screen pointer-events-none"
                            style={{ color: project.label_color || STATUS_COLORS[project.status] || STATUS_COLORS['active'] }}
                        />
                    </div>
                )
            }

            {/* 2. Selection & Actions Checkbox */}
            {
                selectable && (
                    <div
                        className={clsx("absolute z-50 cursor-pointer transition-transform duration-200", collapsed ? "left-2 top-1/2 -translate-y-1/2" : "top-4 right-4 group-hover:scale-110")}
                        onClick={(e) => { e.stopPropagation(); onToggleSelect?.(); }}
                    >
                        {selected ? <CheckSquare size={18} className="text-accent drop-shadow-[0_0_5px_rgba(0,0,0,1)]" /> : <Square size={18} className="text-gray-500 hover:text-white drop-shadow-[0_0_5px_rgba(0,0,0,1)]" />}
                    </div>
                )
            }

            {/* 3. Status Stripe/Indicator */}
            <div
                onClick={handleToggleCollapse}
                title={isCollapsed ? "Expand" : "Collapse"}
                style={{ backgroundColor: project.label_color || STATUS_COLORS[project.status] || STATUS_COLORS['active'] }}
                className={clsx(
                    "absolute left-0 top-0 bottom-0 z-20 cursor-row-resize transition-all shadow-[0_0_10px_currentColor]",
                    collapsed ? "w-1" : "w-1 group-hover:w-1.5"
                )}
            />

            {/* 4. Content Container - Balanced padding */}
            <div className={clsx("relative z-10 flex-1 flex flex-col", collapsed ? "p-2 pl-4 flex-row items-center" : "p-4")}>

                {/* Collapsed Header View */}
                {collapsed ? (
                    <div className="flex items-center justify-between w-full gap-4">
                        {/* Left: Code + Title */}
                        <div className="flex items-center gap-3 min-w-0 flex-1">
                            <span className="text-[10px] font-mono text-accent bg-accent/10 px-2 py-0.5 rounded shrink-0">
                                {project.project_code || `P-${project.id}`}
                            </span>
                            <h3 className="text-sm font-semibold text-white truncate">
                                {project.title}
                            </h3>
                        </div>

                        {/* Center: Status + Progress */}
                        <div className="flex items-center gap-4 shrink-0">
                            <span className={clsx(
                                "text-[9px] font-bold uppercase px-2 py-0.5 rounded-full",
                                project.status === 'active' ? "bg-emerald-500/20 text-emerald-400" : "bg-gray-700 text-gray-400"
                            )}>
                                {project.status?.replace('_', ' ')}
                            </span>
                            <div className="flex items-center gap-1.5 text-[10px] text-gray-400">
                                <span className="font-mono text-white">{project.progress || 0}%</span>
                                <div className="w-16 h-1.5 bg-gray-800 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-accent rounded-full transition-all"
                                        style={{ width: `${project.progress || 0}%` }}
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Right: Priority Indicator */}
                        <div className="flex items-center gap-1 shrink-0">
                            {[1, 2, 3, 4, 5].map(i => (
                                <div
                                    key={i}
                                    className={clsx(
                                        "w-1.5 h-3 rounded-sm transition-all",
                                        i <= (project.priority || 0) ? "bg-gradient-to-t from-red-500 to-amber-400" : "bg-gray-800"
                                    )}
                                />
                            ))}
                        </div>
                    </div>
                ) : effectiveDensity === 'compact' ? (
                    // --- COMPACT / TILE VIEW ---
                    <CardVariantCompact project={project} />
                ) : effectiveDensity === 'text' ? (
                    // --- TEXT / SOLO AERO VIEW ---
                    <CardVariantText project={project} nextTask={nextTask} />
                ) : effectiveDensity === 'dense' ? (
                    // --- DENSE / ENTERPRISE VIEW ---
                    <CardVariantDense project={project} />
                ) : (
                    // --- MODERATE / BALANCED VIEW (Default) ---
                    <CardVariantModerate
                        project={project}
                        nextTask={nextTask}
                        hideActions={hideActions}
                        onEdit={() => setIsEditMode(true)}
                        onArchive={() => {
                            db.projects.update(project.id!, { is_archived: true, updated_at: new Date() });
                            toast.success('Archived');
                        }}
                        onDelete={() => {
                            if (confirm('Move to trash?')) {
                                db.projects.update(project.id!, { deleted_at: new Date(), updated_at: new Date() });
                                toast.success('Moved to trash');
                            }
                        }}
                    />
                )}
            </div>
        </UniversalCard >
    );
}
