import { useState, useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { db, type ProjectTask } from '../lib/db';
import { useUIStore } from '../store/useStore';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Card } from './ui/Card';
import { Plus, CheckCircle2, Circle, AlertCircle, Clock, Trash2, Square, Battery, BatteryCharging, BatteryWarning, ArrowRight, Target } from 'lucide-react';
import clsx from 'clsx';
import { TaskKanban } from './tasks/TaskKanban';
import { TaskFlowchart } from './projects/TaskFlowchart';
import { LayoutList, Workflow } from 'lucide-react';
import { parseRecurrence } from '../lib/recurrence';

export function ProjectTasks({ projectId }: { projectId: number }) {
    const tasks = useLiveQuery(() => db.project_tasks.where({ project_id: projectId }).toArray());
    const { addToStash } = useUIStore();
    const [viewMode, setViewMode] = useState<'list' | 'flow' | 'board' | 'recurring'>('list');
    const [isAdding, setIsAdding] = useState(false);
    const [taskListRef] = useAutoAnimate();

    // v37 Energy Based Planning
    const [lowCapacityMode, setLowCapacityMode] = useState(false);

    // New Task State
    const [newTaskTitle, setNewTaskTitle] = useState('');
    const [newTaskPhase, setNewTaskPhase] = useState('Planning');
    const [newTaskPriority, setNewTaskPriority] = useState<number>(3);
    const [newTaskEst, setNewTaskEst] = useState('');
    const [newTaskEnergy, setNewTaskEnergy] = useState<'low' | 'medium' | 'high'>('medium');
    const [newTaskRecurrence, setNewTaskRecurrence] = useState('');
    // Use useMemo for synchronous derivation to avoid effect loops
    const recurrencePreview = useMemo(() => {
        return newTaskRecurrence ? parseRecurrence(newTaskRecurrence) : null;
    }, [newTaskRecurrence]);

    // Filter Tasks
    const visibleTasks = tasks?.filter(t => {
        if (lowCapacityMode) {
            return t.energy_level === 'low' && t.status !== 'blocked';
        }
        return true;
    });

    // Group tasks by Phase
    const phases = ['Planning', 'Procurement', 'Fabrication', 'Assembly', 'Testing', 'Deployment'];
    const tasksByPhase = visibleTasks?.reduce((acc, task) => {
        const phase = task.phase || 'Uncategorized';
        if (!acc[phase]) acc[phase] = [];
        acc[phase].push(task);
        return acc;
    }, {} as Record<string, ProjectTask[]>) || {};

    const handleAddTask = async () => {
        if (!projectId || isNaN(projectId)) {
            console.error("Invalid Project ID");
            return;
        }
        if (!newTaskTitle) return;

        try {
            const recurrenceObj = recurrencePreview ? {
                pattern: newTaskRecurrence,
                nextDue: recurrencePreview,
                fromCompletion: true // Default to completion-based for now
            } : undefined;

            await db.project_tasks.add({
                project_id: projectId,
                title: newTaskTitle,
                status: 'pending',
                phase: newTaskPhase,
                priority: newTaskPriority as 1 | 2 | 3 | 4 | 5,
                estimated_time: newTaskEst,
                energy_level: newTaskEnergy,
                sensory_load: [],
                recurrence: recurrenceObj,
                scheduled_date: recurrenceObj?.nextDue // Set initial scheduled date if recurring
            });
            setNewTaskTitle('');
            setNewTaskRecurrence(''); // Reset
            setIsAdding(false);
        } catch (error) {
            console.error("Failed to add task:", error);
            toast.error("Failed to create task.");
        }
    };

    const toggleStatus = async (task: ProjectTask) => {
        const newStatus = task.status === 'completed' ? 'pending' : 'completed';
        await db.project_tasks.update(task.id!, { status: newStatus });

        // Handle Recurrence on Completion
        if (newStatus === 'completed' && task.recurrence) {
            const nextDate = parseRecurrence(task.recurrence.pattern); // Default to from now
            if (nextDate) {
                // Create next instance
                await db.project_tasks.add({
                    ...task,
                    id: undefined, // New ID
                    status: 'pending',
                    scheduled_date: nextDate,
                    recurrence: { ...task.recurrence, nextDue: nextDate },
                    // We should probably strip ID and ensure other fields are clean
                });
                toast.success(`Recurring task scheduled for ${nextDate.toLocaleDateString()}`);
            }
        }
    };

    const deleteTask = async (id: number) => {
        await db.project_tasks.delete(id);
    };

    const getEnergyIcon = (level?: string) => {
        switch (level) {
            case 'low': return <BatteryCharging size={12} className="text-green-400" />;
            case 'high': return <BatteryWarning size={12} className="text-red-400" />;
            default: return <Battery size={12} className="text-yellow-400" />;
        }
    };

    return (
        <div className={clsx("space-y-8 h-full flex flex-col transition-colors duration-500", lowCapacityMode ? "bg-black" : "")}>
            <div className="flex justify-between items-center bg-black border-b border-white/10 pb-4">
                <div className="flex items-center gap-4">
                    <h2 className="text-xl font-bold uppercase tracking-tight text-white flex items-center gap-2">
                        Operational Tasks
                        {lowCapacityMode && <span className="text-[10px] bg-green-900/50 text-green-400 px-2 py-0.5 rounded border border-green-500/30 animate-pulse">LOW CAP MODE</span>}
                    </h2>

                    <div className="flex bg-white/5 rounded p-0.5 border border-white/10">
                        <button onClick={() => setViewMode('list')} className={clsx("p-1.5 rounded transition-colors", viewMode === 'list' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="List View"><LayoutList size={16} /></button>
                        <button onClick={() => setViewMode('flow')} className={clsx("p-1.5 rounded transition-colors", viewMode === 'flow' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Flowchart View"><Workflow size={16} /></button>
                        <button onClick={() => setViewMode('board')} className={clsx("p-1.5 rounded transition-colors", viewMode === 'board' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Kanban Board"><Square size={16} /></button>
                        <button onClick={() => setViewMode('recurring')} className={clsx("p-1.5 rounded transition-colors", viewMode === 'recurring' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Recurring Tasks"><Clock size={16} /></button>
                    </div>

                    {/* Energy Toggle */}
                    <button
                        onClick={() => setLowCapacityMode(!lowCapacityMode)}
                        className={clsx(
                            "flex items-center gap-2 px-3 py-1.5 rounded border text-xs font-bold transition-all ml-4",
                            lowCapacityMode
                                ? "bg-green-500/20 border-green-500 text-green-400 shadow-[0_0_10px_rgba(74,222,128,0.2)]"
                                : "bg-white/5 border-white/10 text-gray-500 hover:text-white"
                        )}
                        title="Toggle Low Capacity Mode (Filters for low-energy tasks)"
                    >
                        {lowCapacityMode ? <BatteryCharging size={14} /> : <Battery size={14} />}
                        {lowCapacityMode ? "RECHARGING..." : "Mode"}
                    </button>
                </div>
                <Button onClick={() => setIsAdding(!isAdding)} size="sm">
                    <Plus size={16} className="mr-2" /> Add Task
                </Button>
            </div>

            {isAdding && (
                <Card className="mb-6 animate-in fade-in slide-in-from-top-2">
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4 items-end">
                        <div className="lg:col-span-2">
                            <Input label="Task Description" value={newTaskTitle} onChange={e => setNewTaskTitle(e.target.value)} autoFocus />
                        </div>
                        <div>
                            <label className="block text-xs font-mono text-gray-500 mb-1 uppercase">Phase</label>
                            <select
                                className="w-full bg-black border border-gray-700 text-white p-2 text-sm focus:border-accent outline-none font-mono uppercase"
                                value={newTaskPhase}
                                onChange={e => setNewTaskPhase(e.target.value)}
                            >
                                {phases.map(p => <option key={p} value={p}>{p}</option>)}
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-mono text-gray-500 mb-1 uppercase">Energy Req.</label>
                            <select
                                className="w-full bg-black border border-gray-700 text-white p-2 text-sm focus:border-accent outline-none font-mono uppercase"
                                value={newTaskEnergy}
                                onChange={e => setNewTaskEnergy(e.target.value as 'low' | 'medium' | 'high')}
                            >
                                <option value="low">Low (Chill)</option>
                                <option value="medium">Medium</option>
                                <option value="high">High (Focus)</option>
                            </select>
                        </div>
                        {/* New Recurrence Input */}
                        <div className="lg:col-span-1">
                            <label className="block text-xs font-mono text-gray-500 mb-1 uppercase">Recurrence</label>
                            <div className="relative">
                                <Input
                                    placeholder="e.g. 'every Monday'"
                                    value={newTaskRecurrence}
                                    onChange={e => setNewTaskRecurrence(e.target.value)}
                                    className="text-xs"
                                />
                                {recurrencePreview && (
                                    <div className="absolute right-2 top-1/2 -translate-y-1/2 text-[10px] text-green-500 bg-green-500/10 px-1 rounded pointer-events-none">
                                        Next: {recurrencePreview.toLocaleDateString()}
                                    </div>
                                )}
                            </div>
                        </div>
                        <div className="flex gap-2 lg:col-span-1">
                            <Button onClick={handleAddTask} disabled={!newTaskTitle} className="w-full">Save</Button>
                            <Button variant="ghost" onClick={() => setIsAdding(false)}>Cancel</Button>
                        </div>
                    </div>
                </Card>
            )}

            {
                viewMode === 'flow' ? (
                    <div className="h-[600px]">
                        <TaskFlowchart tasks={visibleTasks || []} />
                    </div>
                ) : viewMode === 'board' ? (
                    <div className="h-[600px] overflow-hidden">
                        <TaskKanban projectId={projectId} />
                    </div>
                ) : viewMode === 'recurring' ? (
                    <div className="space-y-4">
                        <h3 className="text-sm font-bold text-accent uppercase tracking-widest border-b border-accent/20 pb-1 mb-3">Recurring Patterns</h3>
                        {tasks?.filter(t => t.recurrence).length === 0 ? (
                            <div className="text-center py-12 text-gray-500">No recurring tasks found.</div>
                        ) : (
                            <div className="grid gap-4">
                                {tasks?.filter(t => t.recurrence).map(task => (
                                    <div key={task.id} className="p-4 bg-black border border-white/10 rounded flex items-center justify-between">
                                        <div>
                                            <div className="font-bold text-white">{task.title}</div>
                                            <div className="text-xs text-gray-500 font-mono mt-1 flex items-center gap-2">
                                                <span className="text-accent">{task.recurrence?.pattern}</span>
                                                <span>•</span>
                                                <span>Next Due: {task.recurrence?.nextDue?.toLocaleDateString()}</span>
                                            </div>
                                        </div>
                                        <div className="flex items-center gap-2">
                                            <span className={clsx("text-[10px] px-2 py-1 rounded uppercase", task.status === 'completed' ? "bg-green-900/20 text-green-500" : "bg-yellow-900/20 text-yellow-500")}>
                                                {task.status}
                                            </span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="space-y-6">
                        {Object.entries(tasksByPhase).map(([phase, phaseTasks]) => (
                            <div key={phase} className="space-y-3">
                                <h3 className="text-sm font-bold text-accent uppercase tracking-widest border-b border-accent/20 pb-1 mb-3">
                                    {phase} <span className="text-xs text-gray-600 ml-2">({phaseTasks.length})</span>
                                </h3>
                                <div ref={taskListRef} className="grid gap-3">
                                    {phaseTasks.map(task => (
                                        <div key={task.id} className={clsx(
                                            "group flex items-center gap-4 p-4 border transition-all",
                                            task.status === 'completed' ? "bg-white/5 border-transparent opacity-60" : "bg-black border-white/10 hover:border-white/30"
                                        )}
                                            draggable
                                            onDragStart={(e) => {
                                                e.dataTransfer.setData('application/task-id', String(task.id));
                                                e.dataTransfer.effectAllowed = 'copy';
                                            }}
                                        >
                                            <button onClick={() => toggleStatus(task)} className="text-gray-500 hover:text-accent transition-colors">
                                                {task.status === 'completed' ? <CheckCircle2 size={24} className="text-terminal" /> : <Circle size={24} />}
                                            </button>

                                            <div className="flex-1">
                                                <div className={clsx("font-mono text-sm mb-1 flex items-center gap-2", task.status === 'completed' && "line-through text-gray-500")}>
                                                    <span
                                                        className="[&_span[data-type=mention]]:align-baseline [&_span[data-type=mention]]:text-xs"
                                                        dangerouslySetInnerHTML={{ __html: task.title }}
                                                    />
                                                    {task.energy_level && (
                                                        <span className={clsx(
                                                            "text-[10px] px-1.5 py-0.5 rounded border flex items-center gap-1 uppercase tracking-wider",
                                                            task.energy_level === 'low' ? "border-green-500/30 bg-green-500/10 text-green-400" :
                                                                task.energy_level === 'high' ? "border-red-500/30 bg-red-500/10 text-red-400" :
                                                                    "border-yellow-500/30 bg-yellow-500/10 text-yellow-400"
                                                        )}>
                                                            {getEnergyIcon(task.energy_level)}
                                                            {task.energy_level} Energy
                                                        </span>
                                                    )}
                                                </div>
                                                <div className="flex gap-4 text-[10px] uppercase font-bold text-gray-500">
                                                    {task.estimated_time && (
                                                        <span className="flex items-center gap-1 text-gray-400">
                                                            <Clock size={10} /> {task.estimated_time}
                                                        </span>
                                                    )}
                                                    {task.priority >= 4 && (
                                                        <span className="flex items-center gap-1 text-orange-500">
                                                            <AlertCircle size={10} /> HIGH PRIORITY
                                                        </span>
                                                    )}
                                                    {task.recurrence && (
                                                        <span className="flex items-center gap-1 text-green-400 group-hover:bg-green-500/10 px-1 rounded transition-colors" title={`Recurrence: ${task.recurrence.pattern}`}>
                                                            <Clock size={10} /> {task.recurrence.pattern}
                                                        </span>
                                                    )}
                                                    {task.goal_id && (
                                                        <span className="flex items-center gap-1 text-purple-400 border border-purple-500/30 px-1 rounded bg-purple-900/10">
                                                            <Target size={10} /> LINKED
                                                        </span>
                                                    )}
                                                </div>
                                            </div>

                                            <div className="flex items-center gap-1">
                                                <button
                                                    onClick={() => {
                                                        addToStash({
                                                            id: crypto.randomUUID(),
                                                            originalId: task.id!,
                                                            type: 'task',
                                                            title: task.title,
                                                            subtitle: task.phase || `Project #${projectId}`,
                                                            data: task
                                                        });
                                                        toast.success("Task added to Transporter");
                                                    }}
                                                    className="opacity-0 group-hover:opacity-100 text-accent hover:bg-accent/10 p-2 rounded transition-all"
                                                    title="Add to Transporter"
                                                >
                                                    <ArrowRight size={16} />
                                                </button>
                                                <button onClick={() => deleteTask(task.id!)} className="opacity-0 group-hover:opacity-100 text-red-500 hover:bg-red-500/10 p-2 rounded transition-all">
                                                    <Trash2 size={16} />
                                                </button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}

                        {(!visibleTasks || visibleTasks.length === 0) && !isAdding && (
                            <div className="text-center py-12 border border-dashed border-gray-800 rounded bg-black/40">
                                <p className="text-gray-600 font-mono mb-2">
                                    {lowCapacityMode ? "No 'Low Energy' tasks found." : "No tasks initialized."}
                                </p>
                                {lowCapacityMode && <p className="text-xs text-gray-500">Great job resting 💤. Add some low-effort tasks to get started gently.</p>}
                            </div>
                        )}
                    </div>
                )
            }
        </div>
    );
}
