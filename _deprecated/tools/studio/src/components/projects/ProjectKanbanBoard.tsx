import { useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Project } from '../../lib/db';
import { DndContext, DragOverlay, useDraggable, useDroppable, type DragStartEvent, type DragEndEvent } from '@dnd-kit/core';
import { ProjectCard } from './ProjectCard';
import clsx from 'clsx';
import { useState } from 'react';
import { createPortal } from 'react-dom';

// Constants can be reintroduced if needed for more complex status mapping
// Currently the columns are derived dynamically or hardcoded in useMemo for MVP

export function ProjectKanbanBoard() {
    const projects = useLiveQuery(() => db.projects.toArray());
    const [activeId, setActiveId] = useState<number | null>(null);

    const columns = useMemo(() => {
        if (!projects) return { idea: [], active: [], completed: [] };

        const cols = {
            idea: [] as Project[],
            active: [] as Project[],
            completed: [] as Project[]
        };

        projects.forEach(p => {
            if (p.deleted_at) return;

            // Simple Logic
            if (p.status === 'active') cols.active.push(p);
            else if (p.status === 'completed' || p.status === 'archived') cols.completed.push(p);
            else cols.idea.push(p); // everything else (on-hold, legacy, etc)
        });

        return cols;
    }, [projects]);

    const handleDragStart = (event: DragStartEvent) => {
        setActiveId(Number(event.active.id));
    };

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;
        setActiveId(null);

        if (!over) return;

        const projectId = Number(active.id);
        const newStatus = over.id as string; // 'idea', 'active', 'completed'

        // Map Column ID back to DB Status
        let dbStatus = 'on-hold';
        if (newStatus === 'active') dbStatus = 'active';
        if (newStatus === 'completed') dbStatus = 'completed';

        // Optimistic UI updates happen via LiveQuery automatically if we write fast enough
        await db.projects.update(projectId, { status: dbStatus as any });
    };

    const activeProject = useMemo(() =>
        projects?.find(p => p.id === activeId),
        [activeId, projects]);

    return (
        <DndContext onDragStart={handleDragStart} onDragEnd={handleDragEnd}>
            <div className="flex h-full gap-4 overflow-x-auto pb-4">
                <KanbanColumn id="idea" title="BACKLOG / IDEAS" projects={columns.idea} color="border-gray-500/30" />
                <KanbanColumn id="active" title="IN PROGRESS" projects={columns.active} color="border-accent/50" />
                <KanbanColumn id="completed" title="COMPLETED" projects={columns.completed} color="border-green-500/30" />
            </div>

            {createPortal(
                <DragOverlay>
                    {activeProject ? (
                        <div className="w-[300px] opacity-90 rotate-2 cursor-grabbing">
                            <ProjectCard
                                project={activeProject}
                                layoutMode="list"
                                isTrash={false}
                                collapsed={true}
                                onClick={() => { }}
                                onPurge={() => { }}
                                onRestoreTrash={() => { }}
                            />
                        </div>
                    ) : null}
                </DragOverlay>,
                document.body
            )}
        </DndContext>
    );
}

function KanbanColumn({ id, title, projects, color }: { id: string, title: string, projects: Project[], color: string }) {
    const { setNodeRef } = useDroppable({ id });

    return (
        <div ref={setNodeRef} className={clsx("flex-1 min-w-[320px] bg-white/5 rounded-xl border border-white/5 flex flex-col", color)}>
            <div className="p-4 border-b border-white/5 font-bold tracking-wider text-sm text-gray-400 flex justify-between">
                {title}
                <span className="bg-white/10 px-2 rounded text-xs py-0.5">{projects.length}</span>
            </div>
            <div className="flex-1 p-3 space-y-3 overflow-y-auto min-h-[200px]">
                {projects.map(p => (
                    <DraggableProjectCard key={p.id} project={p} />
                ))}
            </div>
        </div>
    );
}

function DraggableProjectCard({ project }: { project: Project }) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: project.id!,
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
    } : undefined;

    return (
        <div ref={setNodeRef} style={style} {...listeners} {...attributes} className={clsx("touch-none", isDragging && "opacity-0")}>
            <ProjectCard
                project={project}
                layoutMode="list"
                className="hover:border-accent/50 cursor-grab active:cursor-grabbing"
                isTrash={false}
                collapsed={true}
                onClick={() => { }}
                onPurge={() => { }}
                onRestoreTrash={() => { }}
            />
        </div>
    );
}
