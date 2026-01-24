import React, { useState, useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { formatDistanceToNow } from 'date-fns';
import {
    Github, ExternalLink, Save, X, Trash2,
    RotateCcw, Calendar, TrendingUp, AlertTriangle, Zap, Clock, Circle, List,
    Folder, Sparkles, Box, Cpu, Settings, Archive, Target, Plus, Layers, Check, Hammer,
    Square, CheckSquare, Activity, AlertCircle, GitBranch
} from 'lucide-react';
import clsx from 'clsx';
import { useNavigate } from 'react-router-dom';
import { GradientLEDBar } from '../../ui/GradientLEDBar';
import { LEDBar } from '../../ui/LEDBar';
import { TagsRow } from '../../ui/TagsRow';
import { RadialGauge } from '../../ui/RadialGauge';
import { HeatmapGrid } from '../../ui/HeatmapGrid';
import { MiniLinkMap } from '../../ui/MiniLinkMap';
import { MiniLineChart } from '../../ui/MiniLineChart';
import { CountdownTimer } from '../../ui/CountdownTimer';

import { db, type Project } from '../../../lib/db';
import { UniversalCard } from '../UniversalCard';
import { toUniversalProject } from '../../../lib/universal/adapters/projectAdapter';
import { AsyncBadge } from '../AsyncBadge';
import { Button } from '../../ui/Button';
import { Input } from '../../ui/Input';
import { ProjectSchema, type ProjectFormData } from '../../../lib/schemas';
import { useUIStore } from '../../../store/useStore';

// Imported Variant Components
import { ProjectDenseVariant } from './project-variants/ProjectDenseVariant';
import { ProjectCompactVariant } from './project-variants/ProjectCompactVariant';
import { ProjectTextVariant } from './project-variants/ProjectTextVariant';
import { ProjectModerateVariant } from './project-variants/ProjectModerateVariant';

// ============================================================================
// PROJECT FORM (Edit Slot)

// ============================================================================

interface ProjectFormProps {
    project: Project;
    onClose: () => void;
    onDelete: () => void;
}

function ProjectForm({ project, onClose, onDelete }: ProjectFormProps) {
    const navigate = useNavigate();
    const { register, handleSubmit, watch, formState: { errors } } = useForm<ProjectFormData>({
        resolver: zodResolver(ProjectSchema),
        defaultValues: {
            title: project.title,
            status: project.status,
            priority: project.priority,
            intrusiveness: project.intrusiveness,
            project_code: project.project_code || '',
            target_completion_date: project.target_completion_date ? new Date(project.target_completion_date) : undefined,
            total_theorized_hours: project.total_theorized_hours,
            time_estimate_active: project.time_estimate_active,
        }
    });

    const onSubmit = async (data: ProjectFormData) => {
        try {
            await db.projects.update(project.id!, {
                title: data.title,
                status: data.status,
                priority: data.priority,
                intrusiveness: data.intrusiveness,
                project_code: data.project_code,
                target_completion_date: data.target_completion_date,
                total_theorized_hours: data.total_theorized_hours,
                time_estimate_active: data.time_estimate_active,
                updated_at: new Date()
            });
            toast.success('Project updated');
            onClose();
        } catch (e) {
            console.error(e);
            toast.error('Failed to update project');
        }
    };

    return (
        <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-3 h-full">
            {/* Header */}
            <div className="flex justify-between items-center border-b border-white/10 pb-2">
                <div className="flex items-center gap-2">
                    <input
                        {...register('project_code')}
                        className="bg-white/5 border border-white/10 rounded px-1.5 py-0.5 text-[10px] font-mono w-20 text-accent uppercase focus:border-accent outline-none"
                        placeholder="CODE"
                    />
                </div>

            </div>

            {/* Main Fields */}
            <div className="space-y-4 flex-1 overflow-y-auto custom-scrollbar pr-1">
                <div>
                    <label className="text-[10px] uppercase text-gray-500 font-bold">Title</label>
                    <input
                        {...register('title')}
                        className="w-full bg-transparent border-b border-white/10 text-lg font-bold text-white focus:border-accent outline-none py-1"
                        autoFocus
                    />
                    {errors.title && <span className="text-red-500 text-[10px]">{errors.title.message}</span>}
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Status</label>
                        <select {...register('status')} className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs text-white uppercase [&>option]:bg-black">
                            <option value="active">Active</option>
                            <option value="on-hold">On Hold</option>
                            <option value="completed">Completed</option>
                            <option value="rnd_long">R&D Long</option>
                            <option value="legacy">Legacy</option>
                            <option value="archived">Archived</option>
                        </select>
                    </div>
                    <div>
                        <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Complete By</label>
                        <input
                            type="date"
                            {...register('target_completion_date')}
                            className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs text-white min-h-[28px]"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4 pt-2">
                    <div>
                        <label className="text-[9px] uppercase text-gray-500 font-bold flex justify-between">Priority <span className="text-white">{watch('priority')}</span></label>
                        <input
                            type="range" min="1" max="5" step="1"
                            {...register('priority')}
                            className="w-full accent-red-500 h-1 bg-white/10 rounded appearance-none cursor-pointer mt-1"
                        />
                    </div>
                    <div>
                        <label className="text-[9px] uppercase text-gray-500 font-bold flex justify-between">Intrusive <span className="text-white">{watch('intrusiveness')}</span></label>
                        <input
                            type="range" min="1" max="5" step="1"
                            {...register('intrusiveness')}
                            className="w-full accent-blue-500 h-1 bg-white/10 rounded appearance-none cursor-pointer mt-1"
                        />
                    </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Total Est (H)</label>
                        <input
                            type="number"
                            {...register('total_theorized_hours')}
                            className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs text-white"
                        />
                    </div>
                    <div>
                        <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Active (H)</label>
                        <input
                            type="number"
                            {...register('time_estimate_active')}
                            className="w-full bg-white/5 border border-white/10 rounded px-2 py-1.5 text-xs text-white"
                        />
                    </div>
                </div>
            </div>

            <div className="flex justify-between items-center pt-2 border-t border-white/10">
                <div className="flex gap-2">
                    <Button type="button" variant="ghost" className="text-gray-500 hover:text-white" onClick={() => navigate(`/projects/${project.id}`)}>
                        <ExternalLink size={14} className="mr-1" /> Details
                    </Button>
                    <Button type="button" variant="ghost" className="text-red-500 hover:bg-red-500/10" onClick={onDelete}>
                        <Trash2 size={14} />
                    </Button>
                </div>
                <Button type="submit" className="bg-accent text-black hover:bg-white border-0">
                    <Save size={14} className="mr-1" /> Save
                </Button>
            </div>
        </form>
    );
}

// ============================================================================
// UNIVERSAL PROJECT CARD (V2)
// ============================================================================

interface UniversalProjectCardProps {
    project: Project;
    onClick?: () => void;
    layoutMode?: 'grid' | 'list';
    variant?: 'default' | 'dense' | 'compact' | 'moderate' | 'expanded'; // Added variants

    // Lifecycle Props
    isTrash?: boolean;
    isArchived?: boolean;
    onRestoreTrash?: () => void;
    onPurge?: () => void;

    // Selection Props
    selectable?: boolean;
    selected?: boolean;
    onSelectChange?: (selected: boolean) => void;

    // Display Props
    className?: string;
    onToggleCollapse?: () => void;
    isCollapsed?: boolean;
}

export function UniversalProjectCard({
    project,
    onClick,
    layoutMode = 'grid',
    variant = 'default', // Default to 'default'
    isTrash,
    isArchived,
    onRestoreTrash,
    onPurge,
    selectable,
    selected,
    onSelectChange,
    className,
    onToggleCollapse,
    isCollapsed,
}: UniversalProjectCardProps) {
    const navigate = useNavigate();
    const handleNavigate = () => navigate(`/projects/${project.id}`);

    // 9. Handle Delete/Archive Actions (Hoisted)
    const handleDelete = async () => {
        if (confirm('Move to trash?')) {
            await db.projects.update(project.id!, { deleted_at: new Date() });
            toast.success('Moved to trash');
        }
    };


    const [isEditing, setIsEditing] = useState(false);

    // Parity: "Collapse" means switching to 'compact' variant logic
    const effectiveVariant = isCollapsed ? 'compact' : (variant || 'default');

    const actions = useMemo(() => [
        {
            id: 'toggle-collapse',
            label: isCollapsed ? 'Expand' : 'Collapse',
            icon: isCollapsed ? CheckSquare : Square,
            action: () => onToggleCollapse?.(),
            hidden: !onToggleCollapse
        },
        {
            id: 'archive',
            label: isArchived ? 'Restore' : 'Archive',
            icon: isArchived ? RotateCcw : Archive,
            action: async () => {
                if (isArchived) {
                    await db.projects.update(project.id!, { status: 'active' });
                    toast.success('Project Restored');
                } else {
                    await db.projects.update(project.id!, { status: 'archived' });
                    toast.success('Project Archived');
                }
            }
        },
        {
            id: 'delete',
            label: 'Delete',
            icon: Trash2,
            variant: 'danger' as const,
            action: async () => {
                if (confirm('Are you sure you want to delete this project?')) {
                    await db.projects.delete(project.id!);
                    toast.success('Project Deleted');
                }
            }
        }
    ], [project.status, project.id, isCollapsed, isArchived, onToggleCollapse]);

    // 1. Fetch Related Data (Next Pending Task)
    const nextTask = useLiveQuery(
        () => db.project_tasks.where({ project_id: project.id! }).filter(t => t.status === 'pending').first(),
        [project.id]
    );

    // 2. Convert to Universal Entity
    const entity = useMemo(() => toUniversalProject(project), [project]);

    // 3. Construct Dynamic Badges
    const badges = useMemo(() => {
        const b = [];

        // GitHub Async Badge
        const githubLink = project.external_links?.find(l => l.url.includes('github.com'));
        if (githubLink) {
            const repoPath = githubLink.url.split('github.com/')[1];
            if (repoPath) {
                b.push(
                    <AsyncBadge
                        key="github"
                        url={githubLink.url}
                        icon={Github}
                        fetcher={async () => {
                            const res = await fetch(`https://api.github.com/repos/${repoPath}`);
                            if (!res.ok) throw new Error('Failed to fetch');
                            const json = await res.json();
                            const pushed = new Date(json.pushed_at);
                            const daysAgo = Math.floor((Date.now() - pushed.getTime()) / (1000 * 60 * 60 * 24));
                            const isActive = daysAgo < 7;
                            return {
                                label: isActive ? 'DEV' : 'REPO',
                                status: isActive ? 'active' : 'default',
                                tooltip: `Stars: ${json.stargazers_count} | Updated: ${daysAgo}d ago`
                            };
                        }}
                    />
                );
            }
        }

        // Version Badge
        if (project.version) {
            b.push({ label: `v${project.version}`, color: '#64748b' });
        }

        return b;
    }, [project]);

    // 4. Construct Ratings (Standard Mode)
    const ratings = useMemo(() => [
        {
            label: 'Priority',
            value: project.priority,
            max: 5,
            color: '#ef4444',
            onChange: (val: number) => db.projects.update(project.id!, { priority: val })
        },
        {
            label: 'Intrusive',
            value: project.intrusiveness,
            max: 5,
            color: '#3b82f6',
            onChange: (val: number) => db.projects.update(project.id!, { intrusiveness: val })
        }
    ], [project.priority, project.intrusiveness, project.id]);

    // 5. Construct Next Action
    const nextAction = useMemo(() => {
        if (!nextTask) return undefined;
        return {
            label: nextTask.title,
            subtitle: nextTask.due_date ? `Due ${formatDistanceToNow(new Date(nextTask.due_date))} ago` : 'Next Step',
            icon: <Calendar size={14} />,
            onClick: () => navigate(`/projects/${project.id}?task=${nextTask.id}`)
        };
    }, [nextTask, project.id, navigate]);

    // 6. Metrics Dashboard (Standard Mode)
    const metrics = useMemo(() => (
        <div className="flex flex-col items-end text-[10px] gap-0.5 font-mono text-gray-400">
            {(project.total_theorized_hours || 0) > 0 && (
                <div className="flex items-center gap-1.5" title="Theorized Hours">
                    <Zap size={10} className="text-yellow-500" />
                    <span>{project.total_theorized_hours}h</span>
                </div>
            )}
            {(project.time_estimate_active || 0) > 0 && (
                <div className="flex items-center gap-1.5" title="Active Hours">
                    <Clock size={10} className="text-blue-500" />
                    <span>{project.time_estimate_active}h</span>
                </div>
            )}
        </div>
    ), [project.total_theorized_hours, project.time_estimate_active]);

    // 7. Meta Grid (Standard Mode)
    const metaGrid = useMemo(() => {
        const m = [
            { label: 'CODE', value: project.project_code || '---' },
            { label: 'UPDATED', value: `${formatDistanceToNow(new Date(project.updated_at))} ago` },
        ];
        if (project.target_completion_date) {
            m.push({
                label: 'TARGET',
                value: new Date(project.target_completion_date).toLocaleDateString(),
                color: '#ef4444'
            });
        }
        return m;
    }, [project.project_code, project.updated_at, project.target_completion_date]);

    // 8. Custom Body Content (Dispatcher)
    const customBody = useMemo(() => {
        const standardProps = {
            project,
            isCollapsed,
            onToggleCollapse,
            onEdit: () => setIsEditing(true),
            handleNavigate,
            handleDelete
        };

        switch (effectiveVariant) {
            case 'dense':
                return <ProjectDenseVariant {...standardProps} />;
            case 'compact':
                return <ProjectCompactVariant {...standardProps} />;
            case 'text':
                return <ProjectTextVariant project={project} handleNavigate={handleNavigate} />;
            case 'moderate':
                return <ProjectModerateVariant {...standardProps} nextTask={nextTask} />;
            default:
                return null;
        }
    }, [effectiveVariant, project, isCollapsed, onToggleCollapse, handleNavigate, handleDelete, nextTask]);




    return (
        <UniversalCard
            entity={entity}
            layoutMode={layoutMode}
            variant={effectiveVariant as any}
            statusGlow={project.status === 'active'}
            statusStripeColor={project.label_color || (project.status === 'active' ? '#10b981' : '#374151')}
            backgroundImage={project.image_url}
            className={className}

            // Interaction
            onClick={onClick}
            dragOnType="card"
            isDraggable={!isTrash}
            selectable={selectable}
            selected={selected}
            onSelectChange={onSelectChange}

            // Lifecycle
            isTrash={isTrash}
            isArchived={isArchived}
            onRestoreTrash={onRestoreTrash}
            onPurge={onPurge}
            onDelete={handleDelete}
            onArchive={() => db.projects.update(project.id!, { status: 'archived' })}

            // Collapsing
            collapsible={true}
            isCollapsed={isCollapsed}
            onToggleCollapse={onToggleCollapse}

            // Content Flow - Switch based on variant
            badges={badges}
            // If custom variant, we hijack the body slots to prevent default rendering
            header={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant) ? undefined : undefined}
            noDefaultStyles={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant)}
            ratings={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant) ? undefined : ratings}
            metrics={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant) ? undefined : metrics}
            metaGrid={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant) ? undefined : metaGrid}

            nextAction={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant) ? undefined : nextAction}
            children={['moderate', 'dense', 'text', 'compact'].includes(effectiveVariant) ? customBody : undefined}

            // Edit Mode
            isEditing={isEditing}
            onEditChange={setIsEditing}
            editSlot={
                <ProjectForm
                    project={project}
                    onClose={() => { }}
                    onDelete={handleDelete}
                />
            }
        />
    );
}
