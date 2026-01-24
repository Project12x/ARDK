import { useState, useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useNavigate } from 'react-router-dom';
import { db, type Goal, type GoalLevel, type GoalStatus } from '../lib/db';
import { useUIStore } from '../store/useStore';
import { toast } from 'sonner';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import {
    Target, Plus, ChevronRight, ChevronDown, Star, Calendar,
    CheckCircle2, PauseCircle, XCircle, Circle, ArrowRight,
    Sparkles, Flag, TrendingUp, MoreVertical, Edit2, Trash2
} from 'lucide-react';
import clsx from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { useDroppable, useDraggable } from '@dnd-kit/core';
import { UniversalCard } from '../components/ui/UniversalCard';
import { ResponsiveTabs } from '../components/ui/ResponsiveTabs';

const LEVEL_CONFIG: Record<GoalLevel, { label: string; color: string; indent: number }> = {
    vision: { label: 'Vision', color: 'text-purple-400 border-purple-500/30 bg-purple-500/10', indent: 0 },
    year: { label: 'Yearly Goal', color: 'text-blue-400 border-blue-500/30 bg-blue-500/10', indent: 1 },
    quarter: { label: 'Quarterly', color: 'text-green-400 border-green-500/30 bg-green-500/10', indent: 2 },
    objective: { label: 'Objective', color: 'text-amber-400 border-amber-500/30 bg-amber-500/10', indent: 3 }
};

const STATUS_ICONS: Record<GoalStatus, { icon: typeof Circle; color: string }> = {
    active: { icon: Circle, color: 'text-blue-400' },
    achieved: { icon: CheckCircle2, color: 'text-green-400' },
    paused: { icon: PauseCircle, color: 'text-yellow-400' },
    abandoned: { icon: XCircle, color: 'text-gray-500' }
};

interface GoalNode extends Goal {
    children: GoalNode[];
}

function buildTree(goals: Goal[]): GoalNode[] {
    const map = new Map<number, GoalNode>();
    const roots: GoalNode[] = [];

    // First pass: create nodes
    goals.forEach(g => {
        map.set(g.id!, { ...g, children: [] });
    });

    // Second pass: build hierarchy
    goals.forEach(g => {
        const node = map.get(g.id!)!;
        if (g.parent_id && map.has(g.parent_id)) {
            map.get(g.parent_id)!.children.push(node);
        } else {
            roots.push(node);
        }
    });

    // Sort by priority then title
    const sortNodes = (nodes: GoalNode[]) => {
        nodes.sort((a, b) => (b.priority || 0) - (a.priority || 0) || a.title.localeCompare(b.title));
        nodes.forEach(n => sortNodes(n.children));
    };
    sortNodes(roots);

    return roots;
}

function GoalCard({ goal, depth = 0, onSelect }: { goal: GoalNode; depth?: number; onSelect: (g: Goal) => void }) {
    const [isExpanded, setIsExpanded] = useState(true);
    const { addToStash } = useUIStore();
    const config = LEVEL_CONFIG[goal.level];
    const StatusIcon = STATUS_ICONS[goal.status].icon;

    // Get linked projects count
    const linkedProjects = useLiveQuery(() =>
        db.projects.where('goal_id').equals(goal.id!).count()
        , [goal.id]);

    // Get linked tasks count
    const linkedTasks = useLiveQuery(() =>
        db.project_tasks.where('goal_id').equals(goal.id!).count()
        , [goal.id]);

    const progress = goal.progress || 0;

    const [isNativeOver, setIsNativeOver] = useState(false);

    const handleNativeDragOver = (e: React.DragEvent) => {
        if (e.dataTransfer.types.includes('application/project-id')) {
            e.preventDefault();
            e.stopPropagation();
            if (!isNativeOver) setIsNativeOver(true);
        }
    };

    const handleNativeDragLeave = (e: React.DragEvent) => {
        e.preventDefault();
        setIsNativeOver(false);
    };

    const handleNativeDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        setIsNativeOver(false);
        const pid = e.dataTransfer.getData('application/project-id');
        if (pid) {
            e.stopPropagation();
            await db.projects.update(Number(pid), { goal_id: goal.id, updated_at: new Date() });
            toast.success(`Project linked to ${goal.title}`);
        }
    };

    return (
        <motion.div
            initial={{ opacity: 0, x: -10 }}
            animate={{ opacity: 1, x: 0 }}
            className="group"
            style={{ marginLeft: depth * 24 }}
            onDragOver={handleNativeDragOver}
            onDragLeave={handleNativeDragLeave}
            onDrop={handleNativeDrop}
        >
            <UniversalCard
                entityType="goal-item"
                entityId={goal.id!}
                title={goal.title}
                metadata={{
                    goal: goal,
                    level: goal.level,
                    status: goal.status
                }}
                dropZoneId={`goal-drop-zone-${goal.id}`}
                isDroppable={true}
                onClick={() => onSelect(goal)}
                className={clsx(
                    "flex items-center gap-3 p-3 rounded-lg border transition-all cursor-grab active:cursor-grabbing hover:bg-white/5",
                    (isNativeOver) ? "bg-accent/20 border-accent scale-[1.02] shadow-[0_0_15px_rgba(59,130,246,0.5)] z-10" : config.color
                )}
            >
                <div className="flex-1 flex items-center gap-3">
                    <button
                        onClick={(e) => { e.stopPropagation(); setIsExpanded(!isExpanded); }}
                        className={clsx("p-0.5 rounded hover:bg-white/10 transition-colors", goal.children.length === 0 && "invisible")}
                    >
                        {isExpanded ? <ChevronDown size={14} className="text-gray-500" /> : <ChevronRight size={14} className="text-gray-500" />}
                    </button>

                    <div className="relative">
                        <StatusIcon size={18} className={STATUS_ICONS[goal.status].color} />
                        {goal.priority === 5 && (
                            <div className="absolute -top-1 -right-1">
                                <Star size={8} className="text-amber-400 fill-amber-400 animate-pulse" />
                            </div>
                        )}
                    </div>

                    <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-0.5">
                            <div className="flex items-center gap-2">
                                <span className="text-[10px] font-mono uppercase opacity-50 px-1 border border-current rounded">
                                    {config.label}
                                </span>
                                {(linkedProjects || 0) > 0 && (
                                    <span className="text-[10px] font-mono text-blue-400 flex items-center gap-0.5" title="Linked Projects">
                                        <Target size={10} /> {linkedProjects}
                                    </span>
                                )}
                                {(linkedTasks || 0) > 0 && (
                                    <span className="text-[10px] font-mono text-green-400 flex items-center gap-0.5" title="Linked Tasks">
                                        <CheckCircle2 size={10} /> {linkedTasks}
                                    </span>
                                )}
                            </div>
                        </div>
                        <h3 className="font-bold text-sm text-gray-200 truncate">{goal.title}</h3>
                    </div>
                </div>

                {/* Progress Bar (Mini) */}
                <div className="w-16 h-1 bg-black/50 rounded-full overflow-hidden">
                    <div className="h-full bg-current opacity-50" style={{ width: `${progress}%` }} />
                </div>

                <div className="opacity-0 group-hover:opacity-100 flex items-center gap-1 transition-opacity">
                    <button
                        onClick={(e) => {
                            e.stopPropagation();
                            addToStash({
                                id: crypto.randomUUID(),
                                originalId: goal.id!,
                                type: 'goal',
                                title: goal.title,
                                subtitle: config.label,
                                data: goal
                            });
                            toast.success("Goal added to Transporter");
                        }}
                        className="p-1.5 hover:bg-white/10 rounded text-gray-400 hover:text-white"
                        title="Add to Transporter"
                    >
                        <ArrowRight size={14} />
                    </button>
                    <button className="p-1.5 hover:bg-white/10 rounded text-gray-400 hover:text-white">
                        <MoreVertical size={14} />
                    </button>
                </div>
            </UniversalCard>

            {/* Children Tree */}
            <AnimatePresence>
                {isExpanded && goal.children.length > 0 && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden"
                    >
                        <div className="mt-1 space-y-1 ml-2 pl-2">
                            {/* Recursive render, depth is handled by padding/margin in this new structure or manually */}
                            {goal.children.map(child => (
                                <GoalCard key={child.id} goal={child} depth={0} onSelect={onSelect} />
                            ))}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </motion.div>
    );
}

export function GoalsPage() {
    const navigate = useNavigate();
    const goals = useLiveQuery(() => db.goals.toArray());
    const [isCreating, setIsCreating] = useState(false);
    const [filter, setFilter] = useState<GoalStatus | 'all'>('all');

    // Create Form State
    const [newTitle, setNewTitle] = useState('');
    const [newLevel, setNewLevel] = useState<GoalLevel>('objective');
    const [newParentId, setNewParentId] = useState<number | undefined>();

    const filteredGoals = useMemo(() => {
        if (!goals) return [];
        if (filter === 'all') return goals;
        return goals.filter(g => g.status === filter);
    }, [goals, filter]);

    const tree = useMemo(() => buildTree(filteredGoals), [filteredGoals]);

    // Stats
    const stats = useMemo(() => {
        if (!goals) return { total: 0, active: 0, achieved: 0, avgProgress: 0 };
        const active = goals.filter(g => g.status === 'active').length;
        const achieved = goals.filter(g => g.status === 'achieved').length;
        const avgProgress = goals.length > 0
            ? Math.round(goals.reduce((sum, g) => sum + (g.progress || 0), 0) / goals.length)
            : 0;
        return { total: goals.length, active, achieved, avgProgress };
    }, [goals]);

    const handleCreate = async () => {
        if (!newTitle.trim()) return;
        try {
            await db.goals.add({
                title: newTitle.trim(),
                level: newLevel,
                parent_id: newParentId,
                status: 'active',
                progress: 0,
                priority: 3,
                created_at: new Date(),
                updated_at: new Date()
            });
            setNewTitle('');
            setIsCreating(false);
            toast.success('Goal created!');
        } catch (e) {
            console.error(e);
            toast.error('Failed to create goal');
        }
    };





    return (
        <div className="h-full flex flex-col bg-black text-white overflow-hidden">
            {/* Header */}
            <div className="p-6 border-b border-white/10">
                <div className="flex justify-between items-start mb-4">
                    <div>
                        <h1 className="text-3xl font-black uppercase tracking-tight flex items-center gap-3">
                            <Target className="text-accent" size={28} />
                            Life Goals
                        </h1>
                        <p className="text-gray-500 text-sm mt-1">Vision → Years → Quarters → Objectives</p>
                    </div>
                    <Button onClick={() => setIsCreating(true)}>
                        <Plus size={16} className="mr-2" /> New Goal
                    </Button>
                </div>

                {/* Stats Bar */}
                <div className="grid grid-cols-4 gap-4">
                    <div className="bg-white/5 rounded p-3 border border-white/10">
                        <div className="text-2xl font-black text-white">{stats.total}</div>
                        <div className="text-[10px] text-gray-500 uppercase">Total Goals</div>
                    </div>
                    <div className="bg-blue-500/10 rounded p-3 border border-blue-500/20">
                        <div className="text-2xl font-black text-blue-400">{stats.active}</div>
                        <div className="text-[10px] text-gray-500 uppercase">Active</div>
                    </div>
                    <div className="bg-green-500/10 rounded p-3 border border-green-500/20">
                        <div className="text-2xl font-black text-green-400">{stats.achieved}</div>
                        <div className="text-[10px] text-gray-500 uppercase">Achieved</div>
                    </div>
                    <div className="bg-accent/10 rounded p-3 border border-accent/20">
                        <div className="text-2xl font-black text-accent">{stats.avgProgress}%</div>
                        <div className="text-[10px] text-gray-500 uppercase">Avg Progress</div>
                    </div>
                </div>

                {/* Filter Tabs */}
                <ResponsiveTabs
                    activeId={filter}
                    onChange={(id) => setFilter(id as any)}
                    items={[
                        { id: 'all', label: 'All Goals' },
                        { id: 'active', label: 'Active', icon: Circle },
                        { id: 'paused', label: 'Paused', icon: PauseCircle },
                        { id: 'achieved', label: 'Achieved', icon: CheckCircle2 },
                        { id: 'abandoned', label: 'Abandoned', icon: XCircle },
                    ]}
                    className="mt-4"
                />
            </div>

            {/* Main Content */}
            <div className="flex-1 flex overflow-hidden">
                {/* Tree View */}
                <div className="flex-1 p-6 overflow-auto">
                    {tree.length === 0 ? (
                        <div className="text-center py-20">
                            <Sparkles size={48} className="text-gray-700 mx-auto mb-4" />
                            <p className="text-gray-500">No goals yet. Start by creating your life vision!</p>
                            <Button className="mt-4" onClick={() => setIsCreating(true)}>
                                <Plus size={16} className="mr-2" /> Create First Goal
                            </Button>
                        </div>
                    ) : (
                        <div className="space-y-2">
                            {tree.map(goal => (
                                <GoalCard key={goal.id} goal={goal} onSelect={(g) => navigate(`/goals/${g.id}`)} />
                            ))}
                        </div>
                    )}
                </div>

                {/* Detail Panel Removed - navigating to GoalDetailPage instead */}
            </div>

            {/* Create Modal */}
            <AnimatePresence>
                {isCreating && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/80 flex items-center justify-center z-50"
                        onClick={() => setIsCreating(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.9, opacity: 0 }}
                            className="bg-gray-900 border border-white/10 rounded-lg p-6 w-full max-w-md"
                            onClick={e => e.stopPropagation()}
                        >
                            <h2 className="text-xl font-bold mb-4 flex items-center gap-2">
                                <Target className="text-accent" size={20} />
                                Create New Goal
                            </h2>

                            <div className="space-y-4">
                                <Input
                                    label="Goal Title"
                                    value={newTitle}
                                    onChange={e => setNewTitle(e.target.value)}
                                    placeholder="e.g. Master Electronics Design"
                                    autoFocus
                                />

                                <div>
                                    <label className="text-xs text-gray-500 uppercase mb-2 block">Level</label>
                                    <div className="grid grid-cols-2 gap-2">
                                        {(['vision', 'year', 'quarter', 'objective'] as GoalLevel[]).map(level => (
                                            <button
                                                key={level}
                                                onClick={() => setNewLevel(level)}
                                                className={clsx(
                                                    "py-2 rounded text-xs font-bold uppercase transition-all border",
                                                    newLevel === level
                                                        ? LEVEL_CONFIG[level].color
                                                        : "bg-white/5 text-gray-500 border-transparent hover:bg-white/10"
                                                )}
                                            >
                                                {LEVEL_CONFIG[level].label}
                                            </button>
                                        ))}
                                    </div>
                                </div>

                                <div>
                                    <label className="text-xs text-gray-500 uppercase mb-2 block">Parent Goal (Optional)</label>
                                    <select
                                        className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white"
                                        value={newParentId || ''}
                                        onChange={e => setNewParentId(e.target.value ? parseInt(e.target.value) : undefined)}
                                    >
                                        <option value="">None (Top Level)</option>
                                        {goals?.filter(g => g.level !== 'objective').map(g => (
                                            <option key={g.id} value={g.id}>
                                                {LEVEL_CONFIG[g.level].label}: {g.title}
                                            </option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            <div className="flex gap-2 mt-6">
                                <Button variant="ghost" onClick={() => setIsCreating(false)} className="flex-1">
                                    Cancel
                                </Button>
                                <Button onClick={handleCreate} disabled={!newTitle.trim()} className="flex-1">
                                    Create Goal
                                </Button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
