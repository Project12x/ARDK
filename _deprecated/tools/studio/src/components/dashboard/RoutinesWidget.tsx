
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Routine } from '../../lib/db';
import { RoutineService } from '../../services/RoutineService';
import { CheckCircle2 } from 'lucide-react';
import { format, isPast, isToday } from 'date-fns';
import clsx from 'clsx';
import { Link } from 'react-router-dom';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';

export function RoutinesWidget() {
    const routines = useLiveQuery(() => db.routines.orderBy('next_due').toArray());

    // Filter for Due/Overdue or very soon (e.g. tomorrow)
    const dueItems = routines?.filter(r => isPast(r.next_due) || isToday(r.next_due)).slice(0, 5) || [];

    // If nothing due, maybe show next 3 upcoming?
    const upcomingItems = routines?.filter(r => !isPast(r.next_due) && !isToday(r.next_due)).slice(0, 3) || [];

    const displayItems = dueItems.length > 0 ? dueItems : upcomingItems;
    const isOverdueState = dueItems.length > 0;

    const handleComplete = async (routine: Routine) => {
        if (!routine.id) return;

        const nextDate = RoutineService.calculateNextDue(routine.frequency, new Date());
        await db.routines.update(routine.id, {
            last_completed: new Date(),
            next_due: nextDate
        });
    };

    return (
        <div className="bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col h-full min-h-[140px] hover:border-accent/50 transition-colors relative overflow-hidden">
            {/* Background Gradient */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-purple-500/50 to-transparent opacity-20" />

            <div className="flex items-center justify-between mb-4">
                <Link to="/routines" className="flex items-center gap-2 hover:text-white transition-colors">
                    <h2 className="text-xs font-mono font-bold uppercase tracking-widest text-gray-400 hover:text-white transition-colors">Routines</h2>
                </Link>
                <div className="flex items-center gap-2">
                    {isOverdueState && (
                        <span className="text-[10px] bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded font-mono animate-pulse">
                            {dueItems.length} DUE
                        </span>
                    )}
                </div>
            </div>

            <div className="space-y-2 flex-1 overflow-y-auto custom-scrollbar">
                {displayItems.map(routine => (
                    <DraggableRoutineItem
                        key={routine.id}
                        routine={routine}
                        isOverdueState={isOverdueState}
                        onComplete={() => handleComplete(routine)}
                    />
                ))}

                {displayItems.length === 0 && (
                    <div className="text-center py-4 text-gray-600 text-xs italic">
                        All caught up.
                    </div>
                )}
            </div>
        </div>
    );
}

function DraggableRoutineItem({ routine, isOverdueState, onComplete }: { routine: Routine, isOverdueState: boolean, onComplete: () => void }) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `routine-widget-${routine.id}`,
        data: {
            type: 'routine-item',
            item: routine
        }
    });

    const style = transform ? {
        transform: CSS.Translate.toString(transform),
        zIndex: 9999, // Ensure it pops out
    } : undefined;

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={clsx(
                "group flex items-center gap-3 p-2 rounded hover:bg-white/5 transition-colors cursor-grab active:cursor-grabbing",
                isDragging && "opacity-50"
            )}
        >
            <button
                onClick={(e) => {
                    e.stopPropagation(); // prevent drag start if clicking button? 
                    // preventing default on button click usually handles it.
                    // But listeners are on parent div.
                    onComplete();
                }}
                onPointerDown={(e) => e.stopPropagation()} // Vital for dnd-kit draggable parent
                className={clsx(
                    "w-4 h-4 rounded-full border flex items-center justify-center transition-all",
                    isOverdueState ? "border-red-400/50 text-red-400 hover:bg-red-400/20 hover:border-red-400" : "border-gray-600 hover:border-accent hover:text-accent"
                )}
                title="Mark Complete"
            >
                <CheckCircle2 size={10} className="opacity-0 group-hover:opacity-100 transition-opacity" />
            </button>

            <div className="flex-1 min-w-0">
                <div className="flex items-center justify-between">
                    <span className={clsx("text-sm truncate", isOverdueState ? "text-white" : "text-gray-300")}>
                        {routine.title}
                    </span>
                    <span className={clsx("text-[10px] font-mono", isOverdueState ? "text-red-400" : "text-gray-600")}>
                        {format(routine.next_due, 'MMM d')}
                    </span>
                </div>
            </div>
        </div>
    );
}
