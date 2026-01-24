import { useState, useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Routine } from '../lib/db';
import { RoutineService } from '../services/RoutineService';
import { LinkService } from '../services/LinkService';
import { Card } from '../components/ui/Card';
import { Repeat, Calendar, CheckCircle2, Circle, Clock, AlertCircle, Plus, Trash2, Edit2, Play, Pause, RotateCcw } from 'lucide-react';
import clsx from 'clsx';
import { format, isPast, isToday } from 'date-fns';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { useDroppable, useDraggable } from '@dnd-kit/core';

export function RoutinesPage() {
    const routines = useLiveQuery(() => db.routines.orderBy('next_due').toArray());
    const [showAddModal, setShowAddModal] = useState(false);
    const [listRef] = useAutoAnimate();

    // Grouping Logic
    const dueNow = routines?.filter(r => isPast(r.next_due) || isToday(r.next_due)) || [];
    const upcoming = routines?.filter(r => !isPast(r.next_due) && !isToday(r.next_due)) || [];

    const handleComplete = async (routine: Routine) => {
        if (!routine.id) return;
        const nextDate = RoutineService.calculateNextDue(routine.frequency, new Date());

        await db.routines.update(routine.id, {
            last_completed: new Date(),
            next_due: nextDate
        });
    };

    const handleDelete = async (id: number) => {
        if (confirm('Delete this routine?')) {
            await db.routines.delete(id);
        }
    };

    return (
        <div className="p-8 max-w-6xl mx-auto space-y-8 pb-32">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-accent/10 rounded-xl">
                        <Clock size={28} className="text-accent" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-white uppercase tracking-tight">Routines</h1>
                        <p className="text-gray-400 text-sm font-mono">
                            Recurring tasks, maintenance, and seasonal rituals
                        </p>
                    </div>
                </div>
                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent/90 text-white font-bold rounded-lg transition-colors"
                >
                    <Plus size={18} />
                    <span>New Routine</span>
                </button>
            </div>

            {/* Quick Filters (Optional, keeping simple for now) */}

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Main Content */}
                <div className="lg:col-span-2 space-y-8" ref={listRef}>

                    {/* DUE NOW */}
                    {dueNow.length > 0 && (
                        <div className="space-y-4">
                            <h2 className="text-sm font-bold text-red-400 flex items-center gap-2 uppercase tracking-wider">
                                <Clock size={16} /> Due Now
                            </h2>
                            <div className="space-y-3">
                                {dueNow.map(routine => (
                                    <RoutineCard
                                        key={routine.id}
                                        routine={routine}
                                        onComplete={() => handleComplete(routine)}
                                        onDelete={() => handleDelete(routine.id!)}
                                    />
                                ))}
                            </div>
                        </div>
                    )}

                    {/* UPCOMING */}
                    <div className="space-y-4">
                        <h2 className="text-sm font-bold text-gray-500 flex items-center gap-2 uppercase tracking-wider">
                            <Calendar size={16} /> Upcoming
                        </h2>
                        {upcoming.length === 0 && dueNow.length === 0 && (
                            <div className="text-center py-20 bg-white/5 rounded-xl border border-dashed border-white/10">
                                <p className="text-gray-500">No routines found. Create one to get started.</p>
                            </div>
                        )}
                        <div className="space-y-3">
                            {upcoming.map(routine => (
                                <RoutineCard
                                    key={routine.id}
                                    routine={routine}
                                    onComplete={() => handleComplete(routine)}
                                    onDelete={() => handleDelete(routine.id!)}
                                />
                            ))}
                        </div>
                    </div>
                </div>

                {/* Sidebar / Stats */}
                <div className="space-y-6">
                    <Card className="p-6 sticky top-8">
                        <h3 className="font-bold text-white mb-4">Stats</h3>
                        <div className="grid grid-cols-2 gap-4">
                            <div className="bg-black/30 p-3 rounded border border-white/5">
                                <div className="text-2xl font-bold text-white">{routines?.length || 0}</div>
                                <div className="text-xs text-gray-500 uppercase">Total</div>
                            </div>
                            <div className="bg-black/30 p-3 rounded border border-white/5">
                                <div className="text-2xl font-bold text-accent">{dueNow.length}</div>
                                <div className="text-xs text-gray-500 uppercase">Due</div>
                            </div>
                        </div>
                    </Card>
                </div>
            </div>

            {/* Add Modal */}
            {showAddModal && (
                <AddRoutineModal onClose={() => setShowAddModal(false)} />
            )}
        </div>
    );
}

function RoutineCard({ routine, onComplete, onDelete }: { routine: Routine, onComplete: () => void, onDelete: () => void }) {
    const isDue = isPast(routine.next_due) || isToday(routine.next_due);

    // dnd-kit drop zone for receiving items from transporter
    const { setNodeRef, isOver } = useDroppable({
        id: `routine - drop - zone - ${routine.id} `,
        data: { type: 'routine', routineId: routine.id }
    });

    // dnd-kit draggable for transporter
    const { attributes, listeners, setNodeRef: setDraggableRef, transform, isDragging } = useDraggable({
        id: `routine - drag - ${routine.id} `,
        data: {
            type: 'routine-item',
            item: routine
        }
    });

    const dragStyle = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 9999,
    } : undefined;

    return (
        <div
            ref={(node) => {
                setNodeRef(node); // for receiving drops (droppable)
                setDraggableRef(node); // for being dragged (draggable)
            }}
            style={dragStyle}
            {...listeners}
            {...attributes}
            className={clsx(
                "group relative flex items-center justify-between p-4 rounded-xl border transition-all cursor-grab active:cursor-grabbing",
                isDue
                    ? "bg-red-500/5 border-red-500/30 hover:border-red-500/50"
                    : "bg-white/5 border-white/5 hover:border-white/10",
                isOver && "border-neon bg-neon/10 shadow-[0_0_30px_rgba(34,197,94,0.3)]",
                isDragging && "opacity-50"
            )}
        >
            <div className="flex items-center gap-4">
                <button
                    onClick={onComplete}
                    className={clsx(
                        "w-6 h-6 rounded-full border-2 flex items-center justify-center transition-all",
                        isDue ? "border-red-400 text-red-400 hover:bg-red-400/20" : "border-gray-500 text-gray-500 hover:border-accent hover:text-accent"
                    )}
                >
                    <CheckCircle2 size={14} className="opacity-0 group-hover:opacity-100 transition-opacity" />
                </button>

                <div>
                    <h3 className={clsx("font-bold", isDue ? "text-white" : "text-gray-300")}>{routine.title}</h3>
                    <div className="flex items-center gap-3 text-xs text-gray-500 mt-1">
                        <span className="flex items-center gap-1">
                            <RotateCcw size={10} />
                            <span className="capitalize">{routine.frequency}</span>
                        </span>
                        <span>•</span>
                        <span className={clsx(isDue && "text-red-400 font-bold")}>
                            {isDue ? "Due " : "Due "}{format(routine.next_due, 'MMM d')}
                        </span>
                        {routine.last_completed && (
                            <>
                                <span>•</span>
                                <span>Last: {format(routine.last_completed, 'MMM d')}</span>
                            </>
                        )}
                    </div>
                </div>
            </div>

            <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                {/* Edit button placeholder - for now just delete */}
                <button onClick={onDelete} className="p-2 text-gray-500 hover:text-red-400 transition-colors">
                    <Trash2 size={16} />
                </button>
            </div>
        </div>
    );
}

function AddRoutineModal({ onClose }: { onClose: () => void }) {
    const [title, setTitle] = useState('');
    const [frequency, setFrequency] = useState<Routine['frequency']>('weekly');
    const [date, setDate] = useState(format(new Date(), 'yyyy-MM-dd'));
    const [selectedProjects, setSelectedProjects] = useState<number[]>([]);
    const [selectedGoals, setSelectedGoals] = useState<number[]>([]);

    const projects = useLiveQuery(() => db.projects.where('deleted_at').equals(0).toArray()) || [];
    const goals = useLiveQuery(() => db.goals.toArray()) || [];

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim()) return;

        // 1. Create Routine
        const routineId = await db.routines.add({
            title: title.trim(),
            frequency,
            next_due: new Date(date),
            created_at: new Date()
        }) as number;

        // 2. Create Universal Links
        const promises = [];

        // Projects (Routine MAINTAINS Project)
        for (const projectId of selectedProjects) {
            promises.push(LinkService.link('routine', routineId, 'project', projectId, 'maintains'));
        }

        // Goals (Routine SUPPORTS Goal)
        for (const goalId of selectedGoals) {
            promises.push(LinkService.link('routine', routineId, 'goal', goalId, 'supports'));
        }

        await Promise.all(promises);

        onClose();
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
            <Card className="w-full max-w-md p-6 animate-in fade-in zoom-in-95 duration-200">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold text-white">New Routine</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-white">✕</button>
                </div>

                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-xs font-mono text-gray-500 uppercase mb-1">Title</label>
                        <input
                            autoFocus
                            type="text"
                            value={title}
                            onChange={e => setTitle(e.target.value)}
                            placeholder="e.g. Change Filter"
                            className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:border-accent focus:outline-none"
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-xs font-mono text-gray-500 uppercase mb-1">Frequency</label>
                            <select
                                value={frequency}
                                onChange={e => setFrequency(e.target.value as any)}
                                className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:border-accent focus:outline-none"
                            >
                                <option value="daily">Daily</option>
                                <option value="weekly">Weekly</option>
                                <option value="monthly">Monthly</option>
                                <option value="quarterly">Quarterly</option>
                                <option value="yearly">Yearly</option>
                                <option value="seasonal">Seasonal</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-xs font-mono text-gray-500 uppercase mb-1">First Due Date</label>
                            <input
                                type="date"
                                value={date}
                                onChange={e => setDate(e.target.value)}
                                className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:border-accent focus:outline-none"
                            />
                        </div>
                    </div>

                    {/* Linkages */}
                    <div className="space-y-3 pt-2 border-t border-white/10">
                        <label className="block text-xs font-mono text-gray-500 uppercase">Link Context</label>

                        {/* Projects */}
                        {projects.length > 0 && (
                            <div>
                                <label className="text-[10px] text-accent mb-1 block">Projects</label>
                                <div className="max-h-24 overflow-y-auto space-y-1 bg-black/30 p-2 rounded border border-white/5">
                                    {projects.map(p => (
                                        <label key={p.id} className="flex items-center gap-2 text-xs text-gray-400 hover:text-white cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={selectedProjects.includes(p.id!)}
                                                onChange={e => {
                                                    if (e.target.checked) setSelectedProjects([...selectedProjects, p.id!]);
                                                    else setSelectedProjects(selectedProjects.filter(id => id !== p.id));
                                                }}
                                                className="accent-accent"
                                            />
                                            <span className="truncate">{p.title}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        )}

                        {/* Goals */}
                        {goals.length > 0 && (
                            <div>
                                <label className="text-[10px] text-purple-400 mb-1 block">Goals</label>
                                <div className="max-h-24 overflow-y-auto space-y-1 bg-black/30 p-2 rounded border border-white/5">
                                    {goals.map(g => (
                                        <label key={g.id} className="flex items-center gap-2 text-xs text-gray-400 hover:text-white cursor-pointer">
                                            <input
                                                type="checkbox"
                                                checked={selectedGoals.includes(g.id!)}
                                                onChange={e => {
                                                    if (e.target.checked) setSelectedGoals([...selectedGoals, g.id!]);
                                                    else setSelectedGoals(selectedGoals.filter(id => id !== g.id));
                                                }}
                                                className="accent-purple-500"
                                            />
                                            <span className="truncate">{g.title}</span>
                                        </label>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="pt-4 flex justify-end gap-3">
                        <button type="button" onClick={onClose} className="text-gray-400 hover:text-white px-4 py-2 text-sm">Cancel</button>
                        <button type="submit" className="bg-accent hover:bg-accent/90 text-white font-bold px-4 py-2 rounded text-sm">
                            Create Routine
                        </button>
                    </div>
                </form>
            </Card>
        </div>
    );
}
