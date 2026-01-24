import { useState, useEffect } from 'react';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import { IngestModal } from '../components/dashboard/IngestModal';
import { DashboardGrid } from '../components/dashboard/DashboardGrid';
import { WidgetPicker, AVAILABLE_WIDGETS } from '../components/dashboard/WidgetPicker';
import { Lock, Unlock, RotateCcw, Trash2, LayoutGrid } from 'lucide-react';
import { toast } from 'sonner';
import clsx from 'clsx';

const LAYOUT_KEY = 'DASHBOARD_LAYOUT_V3';
const WIDGETS_KEY = 'DASHBOARD_WIDGETS_V1';

const DEFAULT_WIDGETS = ['focus1', 'focus2', 'focus3', 'weather', 'audio', 'notes', 'goals', 'stats', 'routines', 'activity', 'ingest', 'create', 'pomodoro', 'blockers', 'projectStats', 'github'];

export function Dashboard() {
    const [isCreating, setIsCreating] = useState(false);
    const [isIngestModalOpen, setIsIngestModalOpen] = useState(false);
    const [isLocked, setIsLocked] = useState(true);
    const [isWidgetPickerOpen, setIsWidgetPickerOpen] = useState(false);
    const [layoutVersion, setLayoutVersion] = useState(0);

    // Active widgets state
    const [activeWidgets, setActiveWidgets] = useState<string[]>(() => {
        const saved = localStorage.getItem(WIDGETS_KEY);
        return saved ? JSON.parse(saved) : DEFAULT_WIDGETS;
    });

    // Save widgets to localStorage when changed
    useEffect(() => {
        localStorage.setItem(WIDGETS_KEY, JSON.stringify(activeWidgets));
    }, [activeWidgets]);

    const resetLayout = () => {
        localStorage.removeItem(LAYOUT_KEY);
        setActiveWidgets(DEFAULT_WIDGETS);
        setLayoutVersion(v => v + 1);
        toast.info('Layout Reset to Default');
    };

    const handleAddWidget = (widgetId: string) => {
        if (!activeWidgets.includes(widgetId)) {
            setActiveWidgets([...activeWidgets, widgetId]);
            toast.success(`Added ${AVAILABLE_WIDGETS.find(w => w.id === widgetId)?.name || widgetId}`);
        }
    };

    const handleRemoveWidget = (widgetId: string) => {
        setActiveWidgets(activeWidgets.filter(id => id !== widgetId));
        toast.info(`Removed ${AVAILABLE_WIDGETS.find(w => w.id === widgetId)?.name || widgetId}`);
    };

    return (
        <div className="h-full flex flex-col overflow-y-auto overflow-x-hidden relative">
            {isCreating && <CreateProjectModal onClose={() => setIsCreating(false)} />}
            {isIngestModalOpen && <IngestModal isOpen={isIngestModalOpen} onClose={() => setIsIngestModalOpen(false)} />}

            {/* Widget Picker */}
            <WidgetPicker
                isOpen={isWidgetPickerOpen}
                onClose={() => setIsWidgetPickerOpen(false)}
                activeWidgets={activeWidgets}
                onAddWidget={handleAddWidget}
                onRemoveWidget={handleRemoveWidget}
            />

            {/* Floating Dashboard Controls */}
            <div className="absolute top-4 right-4 z-50 flex items-center gap-1 bg-black/60 backdrop-blur-md px-2 py-1.5 rounded-lg border border-white/10 shadow-2xl transition-all hover:bg-black/80">
                <button
                    onClick={() => setIsLocked(!isLocked)}
                    className={clsx(
                        "p-1.5 rounded-md transition-all",
                        isLocked ? "text-gray-500 hover:text-white" : "bg-accent text-black shadow-[0_0_10px_rgba(var(--accent-rgb),0.5)]"
                    )}
                    title={isLocked ? "Unlock Layout" : "Lock Layout"}
                >
                    {isLocked ? <Lock size={12} /> : <Unlock size={12} />}
                </button>

                <div className="w-px h-3 bg-white/10 mx-1" />

                {/* Widget Picker Button */}
                <button
                    onClick={() => setIsWidgetPickerOpen(true)}
                    title="Manage Widgets"
                    className="p-1.5 text-gray-500 hover:text-accent transition-colors rounded hover:bg-white/5"
                >
                    <LayoutGrid size={12} />
                </button>

                <button
                    onClick={resetLayout}
                    title="Reset Layout to Default"
                    className="p-1.5 text-gray-500 hover:text-red-400 transition-colors rounded hover:bg-white/5"
                >
                    <RotateCcw size={12} />
                </button>

                {!isLocked && (
                    <button
                        onClick={() => setActiveWidgets([])}
                        title="Clear Dashboard"
                        className="p-1.5 text-gray-500 hover:text-red-500 transition-colors rounded hover:bg-white/5"
                    >
                        <Trash2 size={12} />
                    </button>
                )}
            </div>

            {/* The Grid */}
            <DashboardGrid
                key={layoutVersion}
                onIngest={() => setIsIngestModalOpen(true)}
                onCreate={() => setIsCreating(true)}
                isLocked={isLocked}
                layoutKey={LAYOUT_KEY}
                activeWidgets={activeWidgets}
            />
        </div>
    );
}
