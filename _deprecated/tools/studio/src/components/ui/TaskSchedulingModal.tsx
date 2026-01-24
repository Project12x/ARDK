
import { useState, useEffect } from 'react';
import { useUIStore } from '../../store/useStore';
import { db } from '../../lib/db';
import { Button } from './Button';
import { toast } from 'sonner';
import { Calendar, Clock, AlertCircle } from 'lucide-react';
import { format as formatDateStr } from 'date-fns';
import { AnimatePresence, motion } from 'framer-motion';

export function TaskSchedulingModal() {
    const { taskScheduleModal, closeTaskScheduleModal, removeFromStash } = useUIStore();
    const { isOpen, taskId, taskTitle, targetDate, stashId } = taskScheduleModal;
    const [time, setTime] = useState('');

    useEffect(() => {
        if (isOpen) {
            setTime(''); // Reset time on open
        }
    }, [isOpen]);

    const handleSchedule = async () => {
        if (!targetDate) return;

        // Construct final date object
        // Keep the date part from targetDate, explicitly set time
        const scheduleParams: Partial<import('../../lib/db').ProjectTask> = {
            scheduled_date: targetDate,
            scheduled_time: time || undefined
        };

        try {
            await db.project_tasks.update(taskId, scheduleParams);

            // Remove from stash if it came from there
            if (stashId) {
                removeFromStash(stashId);
            }

            toast.success("Task scheduled successfully");
            closeTaskScheduleModal();
        } catch (error) {
            console.error("Failed to schedule task:", error);
            toast.error("Failed to schedule task");
        }
    };

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/50 backdrop-blur-sm">
                <motion.div
                    initial={{ opacity: 0, scale: 0.95 }}
                    animate={{ opacity: 1, scale: 1 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    className="bg-zinc-900 border border-white/10 rounded-lg shadow-xl w-full max-w-md p-6 relative overflow-hidden"
                >
                    {/* Background decoration */}
                    <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />

                    <h2 className="text-lg font-bold text-white mb-2 flex items-center gap-2">
                        <Calendar className="text-accent" size={20} />
                        Schedule Task
                    </h2>

                    <div className="space-y-4 mt-4">
                        <div className="p-3 bg-white/5 rounded border border-white/10">
                            <label className="text-xs uppercase text-gray-500 font-bold block mb-1">Task</label>
                            <div className="text-white font-mono text-sm">{taskTitle}</div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <div className="p-3 bg-white/5 rounded border border-white/10">
                                <label className="text-xs uppercase text-gray-500 font-bold block mb-1">Target Date</label>
                                <div className="text-white font-mono text-lg truncate">
                                    {targetDate ? formatDateStr(targetDate, 'EEE, MMM d') : '-'}
                                </div>
                            </div>

                            <div className="p-3 bg-white/5 rounded border border-white/10">
                                <label className="text-xs uppercase text-gray-500 font-bold mb-1 flex items-center gap-1">
                                    <Clock size={10} /> Time (Optional)
                                </label>
                                <input
                                    type="time"
                                    value={time}
                                    onChange={(e) => setTime(e.target.value)}
                                    className="bg-transparent border-none text-white font-mono w-full focus:ring-0 p-0 text-lg"
                                />
                            </div>
                        </div>

                        <div className="flex items-start gap-2 text-xs text-gray-500 bg-blue-500/10 p-2 rounded border border-blue-500/20">
                            <AlertCircle size={14} className="text-blue-400 mt-0.5 shrink-0" />
                            <p>Scheduling this task will set its target date. It will remain in the operational task list but also appear on your calendar.</p>
                        </div>

                        <div className="flex gap-2 mt-6 justify-end">
                            <Button variant="ghost" onClick={closeTaskScheduleModal}>Cancel</Button>
                            <Button onClick={handleSchedule}>Confirm Schedule</Button>
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
