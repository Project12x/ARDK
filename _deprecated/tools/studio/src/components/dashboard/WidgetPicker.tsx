import { useState } from 'react';
import { X, Plus, Grip, Cloud, Music, FileText, Target, Clock, Activity, LayoutGrid, Inbox, PlusCircle, Timer, AlertTriangle, BarChart3, Github } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

// All available widgets
export const AVAILABLE_WIDGETS = [
    { id: 'focus1', name: 'Focus Card 1', icon: LayoutGrid, category: 'Projects', defaultSize: { w: 4, h: 5 } },
    { id: 'focus2', name: 'Focus Card 2', icon: LayoutGrid, category: 'Projects', defaultSize: { w: 4, h: 5 } },
    { id: 'focus3', name: 'Focus Card 3', icon: LayoutGrid, category: 'Projects', defaultSize: { w: 4, h: 5 } },
    { id: 'weather', name: 'Weather', icon: Cloud, category: 'Status', defaultSize: { w: 2, h: 3 } },
    { id: 'audio', name: 'Audio Deck', icon: Music, category: 'Media', defaultSize: { w: 6, h: 3 } },
    { id: 'notes', name: 'Notes', icon: FileText, category: 'Tools', defaultSize: { w: 3, h: 5 } },
    { id: 'goals', name: 'Goals', icon: Target, category: 'Planning', defaultSize: { w: 3, h: 5 } },
    { id: 'stats', name: 'Reminders', icon: Clock, category: 'Planning', defaultSize: { w: 3, h: 5 } },
    { id: 'routines', name: 'Routines', icon: Clock, category: 'Planning', defaultSize: { w: 3, h: 2 } },
    { id: 'activity', name: 'Activity Stream', icon: Activity, category: 'Logs', defaultSize: { w: 3, h: 3 } },
    { id: 'ingest', name: 'Ingest Button', icon: Inbox, category: 'Actions', defaultSize: { w: 2, h: 2 } },
    { id: 'create', name: 'Create Button', icon: PlusCircle, category: 'Actions', defaultSize: { w: 2, h: 2 } },
    // New widgets
    { id: 'pomodoro', name: 'Pomodoro Timer', icon: Timer, category: 'Productivity', defaultSize: { w: 3, h: 4 } },
    { id: 'blockers', name: 'Blockers Board', icon: AlertTriangle, category: 'Projects', defaultSize: { w: 3, h: 4 } },
    { id: 'projectStats', name: 'Project Stats', icon: BarChart3, category: 'Status', defaultSize: { w: 3, h: 4 } },
    { id: 'github', name: 'GitHub Activity', icon: Github, category: 'Dev', defaultSize: { w: 3, h: 4 } },
];

interface WidgetPickerProps {
    isOpen: boolean;
    onClose: () => void;
    activeWidgets: string[];
    onAddWidget: (widgetId: string) => void;
    onRemoveWidget: (widgetId: string) => void;
}

export function WidgetPicker({ isOpen, onClose, activeWidgets, onAddWidget, onRemoveWidget }: WidgetPickerProps) {
    const [filter, setFilter] = useState<string>('all');

    const categories = ['all', ...new Set(AVAILABLE_WIDGETS.map(w => w.category))];
    const filteredWidgets = filter === 'all'
        ? AVAILABLE_WIDGETS
        : AVAILABLE_WIDGETS.filter(w => w.category === filter);

    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        onClick={onClose}
                    />

                    {/* Panel */}
                    <motion.div
                        initial={{ opacity: 0, x: 300 }}
                        animate={{ opacity: 1, x: 0 }}
                        exit={{ opacity: 0, x: 300 }}
                        className="fixed right-0 top-0 bottom-0 w-80 bg-black border-l border-white/10 z-50 flex flex-col shadow-2xl"
                    >
                        {/* Header */}
                        <div className="p-4 border-b border-white/10 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <Grip size={16} className="text-accent" />
                                <h2 className="font-mono font-bold text-white uppercase text-sm">Widget Manager</h2>
                            </div>
                            <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                                <X size={18} />
                            </button>
                        </div>

                        {/* Category Filter */}
                        <div className="p-3 border-b border-white/10 flex gap-2 flex-wrap">
                            {categories.map(cat => (
                                <button
                                    key={cat}
                                    onClick={() => setFilter(cat)}
                                    className={`px-2 py-1 text-[10px] font-mono uppercase rounded transition-colors ${filter === cat
                                        ? 'bg-accent text-black font-bold'
                                        : 'bg-white/5 text-gray-400 hover:bg-white/10'
                                        }`}
                                >
                                    {cat}
                                </button>
                            ))}
                        </div>

                        {/* Widget List */}
                        <div className="flex-1 overflow-y-auto p-3 space-y-2 custom-scrollbar">
                            {filteredWidgets.map(widget => {
                                const isActive = activeWidgets.includes(widget.id);
                                const Icon = widget.icon;

                                return (
                                    <div
                                        key={widget.id}
                                        className={`p-3 rounded-lg border transition-all flex items-center justify-between ${isActive
                                            ? 'bg-accent/10 border-accent/30'
                                            : 'bg-white/5 border-white/10 hover:border-white/20'
                                            }`}
                                    >
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded ${isActive ? 'bg-accent/20 text-accent' : 'bg-white/10 text-gray-400'}`}>
                                                <Icon size={16} />
                                            </div>
                                            <div>
                                                <div className="text-sm font-bold text-white">{widget.name}</div>
                                                <div className="text-[10px] text-gray-500 font-mono uppercase">{widget.category}</div>
                                            </div>
                                        </div>

                                        <button
                                            onClick={() => isActive ? onRemoveWidget(widget.id) : onAddWidget(widget.id)}
                                            className={`p-1.5 rounded transition-colors ${isActive
                                                ? 'text-red-400 hover:bg-red-500/20 hover:text-red-300'
                                                : 'text-accent hover:bg-accent/20'
                                                }`}
                                            title={isActive ? 'Remove from Dashboard' : 'Add to Dashboard'}
                                        >
                                            {isActive ? <X size={16} /> : <Plus size={16} />}
                                        </button>
                                    </div>
                                );
                            })}
                        </div>

                        {/* Footer Info */}
                        <div className="p-3 border-t border-white/10 text-[10px] text-gray-500 font-mono">
                            {activeWidgets.length} / {AVAILABLE_WIDGETS.length} widgets active
                        </div>
                    </motion.div>
                </>
            )}
        </AnimatePresence>
    );
}
