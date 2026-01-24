import { useMemo, useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type ProjectTask } from '../../lib/db';
import { DragOverlay, useDroppable, type DragStartEvent, type DragEndEvent, useDndMonitor } from '@dnd-kit/core';
import { UniversalCard } from '../ui/UniversalCard';
import clsx from 'clsx';
import { createPortal } from 'react-dom';
import { Clock, AlertCircle, Box, Target } from 'lucide-react';

interface TaskKanbanProps {
    projectId?: number; // Optional: if present, filter by project
}

export function TaskKanban({ projectId }: TaskKanbanProps) {
    const tasks = useLiveQuery(() => {
        if (projectId) {
            return db.project_tasks.where({ project_id: projectId }).toArray();
        } else {
            // Global view: fetch active tasks (exclude completed maybe? or show all)
            // Ideally we filter out tasks from archived projects, but for now just all tasks
            return db.project_tasks.toArray();
        }
    }, [projectId]);

    const [activeId, setActiveId] = useState<number | null>(null);

    const columns = useMemo(() => {
        if (!tasks) return { pending: [], in_progress: [], blocked: [], completed: [] };

        const cols: Record<string, ProjectTask[]> = {
            pending: [],
            in_progress: [],
            blocked: [],
            completed: []
        };

        tasks.forEach(t => {
            const status = t.status || 'pending';
            // Map 'active' or others to our columns if needed. 
            // Assuming DB status matches or we map it. 
            // Current DB statuses might be 'pending', 'completed'. 
            // Let's assume we might want to extend statuses later. 
            // For now, map 'pending' -> pending. 'completed' -> completed.
            // But we want 'in_progress', 'blocked'. 
            // We'll treat status field as the source of truth.

            if (cols[status]) {
                cols[status].push(t);
            } else {
                // Fallback for unknown statuses
                cols.pending.push(t);
            }
        });

        return cols;
    }, [tasks]);

    useDndMonitor({
        onDragStart(event) {
            if (event.active.data.current?.type === 'universal-card' && event.active.data.current?.entityType === 'project-task') {
                setActiveId(event.active.data.current.id);
            }
        },
        onDragEnd(event) {
            const { active, over } = event;
            setActiveId(null);
            if (!over) return;

            // Validate it's a task
            if (active.data.current?.type !== 'universal-card' || active.data.current?.entityType !== 'project-task') return;

            // Handle Column Drop
            const validColumns = ['pending', 'in_progress', 'blocked', 'completed'];
            if (validColumns.includes(over.id as string)) {
                const taskId = active.data.current.id;
                const newStatus = over.id as 'pending' | 'in-progress' | 'completed' | 'blocked';
                db.project_tasks.update(taskId, { status: newStatus });
            }
        }
    });

    const activeTask = useMemo(() => tasks?.find(t => t.id === activeId), [tasks, activeId]);

    return (

        <>
            <div className="flex h-full gap-4 overflow-x-auto pb-4 items-start">
                <KanbanColumn id="pending" title="PENDING" tasks={columns.pending} color="border-white/10" />
                <KanbanColumn id="in_progress" title="IN PROGRESS" tasks={columns.in_progress} color="border-blue-500/30" />
                <KanbanColumn id="blocked" title="BLOCKED" tasks={columns.blocked} color="border-red-500/30" />
                <KanbanColumn id="completed" title="DONE" tasks={columns.completed} color="border-green-500/30" />
            </div>

            {createPortal(
                <DragOverlay>
                    {activeTask ? (
                        <div className="w-[280px] opacity-90 rotate-2 cursor-grabbing">
                            {/* Optimized overlay rendering */}
                            <div className={clsx(
                                "bg-neutral-900 border border-white/10 p-3 rounded shadow-xl flex flex-col gap-2",
                                activeTask.priority >= 4 && "border-l-2 border-l-orange-500"
                            )}>
                                <div className="text-sm font-mono text-white leading-tight">{activeTask.title}</div>
                            </div>
                        </div>
                    ) : null}
                </DragOverlay>,
                document.body
            )}
        </>
    );
}

function KanbanColumn({ id, title, tasks, color }: { id: string, title: string, tasks: ProjectTask[], color: string }) {
    const { setNodeRef } = useDroppable({ id });

    return (
        <div ref={setNodeRef} className={clsx("flex-1 min-w-[280px] bg-black/40 rounded-xl border flex flex-col max-h-full", color)}>
            <div className="p-3 border-b border-white/5 font-bold tracking-wider text-xs text-gray-400 flex justify-between uppercase">
                {title}
                <span className="bg-white/10 px-2 rounded text-[10px] py-0.5 text-white">{tasks.length}</span>
            </div>
            <div className="flex-1 p-2 space-y-2 overflow-y-auto min-h-[150px]">
                {tasks.map(t => (
                    <TaskCard key={t.id} task={t} />
                ))}
            </div>
        </div>
    );
}

function TaskCard({ task, className }: { task: ProjectTask, className?: string }) {
    return (
        <UniversalCard
            entityType="project-task"
            entityId={task.id!}
            title={task.title}
            metadata={task}
            className={clsx("mb-2", className)} // mb-2 for spacing in stack
        >
            <div className={clsx(
                "bg-neutral-900/50 border border-white/5 p-3 rounded shadow-sm flex flex-col gap-2 transition-colors hover:bg-neutral-800",
                task.priority >= 4 && "border-l-2 border-l-orange-500"
            )}>
                <div className="text-sm font-mono text-white leading-tight">
                    {task.title}
                </div>

                <div className="flex justify-between items-center text-[10px] text-gray-500 font-bold uppercase">
                    <div className="flex gap-2">
                        {task.estimated_time && <span className="flex items-center gap-1"><Clock size={10} /> {task.estimated_time}</span>}
                        {task.materials_needed && task.materials_needed.length > 0 && <span className="flex items-center gap-1 text-blue-400"><Box size={10} /> MAT</span>}
                        {task.goal_id && <span className="flex items-center gap-1 text-purple-400" title="Linked to Goal"><Target size={10} /></span>}
                    </div>
                    {task.priority >= 4 && <AlertCircle size={10} className="text-orange-500" />}
                </div>

                {task.phase && (
                    <div className="self-start text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400 uppercase tracking-wider">
                        {task.phase}
                    </div>
                )}
            </div>
        </UniversalCard>
    );
}
