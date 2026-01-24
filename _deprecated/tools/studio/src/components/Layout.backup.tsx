import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { useUIStore } from '../store/useStore';
import { db } from '../lib/db';
import { Settings, LayoutDashboard, Package, FolderOpen, Menu, ChevronLeft, Wifi, Workflow, Bot, Calendar, Power, RefreshCw, Database, Inbox, HelpCircle, Monitor, Sparkles, Target } from 'lucide-react';
import { BackupService } from '../lib/backup';
import clsx from 'clsx';
import { GlobalProgressBar } from './GlobalProgressBar';
import { GlobalChat } from './GlobalChat';
import { QuickCapture } from './QuickCapture';
import { CreateProjectModal } from './projects/CreateProjectModal';

import { useState, useEffect } from 'react';
import { MusicProvider } from '../lib/MusicContext';
import { CommandBar } from './ui/CommandBar';
import { Breadcrumbs } from './navigation/Breadcrumbs';
import { QuickActionHUD } from './navigation/QuickActionHUD';
import { GlobalSearchInput } from './navigation/GlobalSearchInput';
import { OracleGlobalOverlay } from './ui/OracleGlobalOverlay';
import { TaskSchedulingModal } from './ui/TaskSchedulingModal';
import { SidebarStash } from './ui/GlobalTransporter';
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors } from '@dnd-kit/core';
import type { DragEndEvent } from '@dnd-kit/core';
import { createPortal } from 'react-dom';
import { toast } from 'sonner';

export function Layout() {
    const { sidebarOpen, toggleSidebar, isOracleChatOpen, setOracleChatOpen, isCreateProjectOpen, setCreateProjectOpen, removeFromStash, addToStash, setTaskScheduleModal } = useUIStore();
    const [isShutdown, setIsShutdown] = useState(false);
    const location = useLocation();

    // Inbox count for badge
    const inboxCount = useLiveQuery(() =>
        db.inbox_items.filter(item => !item.triaged_at).count()
    ) || 0;

    // Calendar overlay state
    const [isCalendarOpen, setIsCalendarOpen] = useState(false);

    // Today's scheduled tasks
    const todaysTasks = useLiveQuery(async () => {
        const today = new Date();
        today.setHours(0, 0, 0, 0);
        const tomorrow = new Date(today);
        tomorrow.setDate(tomorrow.getDate() + 1);

        // Get tasks scheduled for today
        const tasks = await db.project_tasks
            .filter(t => {
                if (!t.scheduled_date) return false;
                const taskDate = new Date(t.scheduled_date);
                taskDate.setHours(0, 0, 0, 0);
                return taskDate.getTime() === today.getTime() &&
                    (t.status === 'pending' || t.status === 'in-progress');
            })
            .toArray();

        return tasks;
    }) || [];

    // Quick Capture state
    const [isQuickCaptureOpen, setIsQuickCaptureOpen] = useState(false);

    // Global Ctrl+Shift+Space hotkey for Quick Capture
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (e.ctrlKey && e.shiftKey && e.code === 'Space') {
                e.preventDefault();
                setIsQuickCaptureOpen(true);
            }
        };
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, []);

    // DnD Sensors for Transporter
    const sensors = useSensors(
        useSensor(PointerSensor, {
            activationConstraint: {
                distance: 8,
            },
        })
    );

    // Handle drops from Transporter
    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;
        if (!over) return;

        // Handle Drop ONTO the Sidebar Stash
        if (over.id === 'sidebar-stash-drop-zone') {
            const itemData = active.data.current;

            if (itemData?.type === 'inventory-item') {
                // Dragging from Inventory table row to Stash
                const item = itemData.item;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: item.id,
                    type: 'inventory',
                    title: item.name,
                    subtitle: `${item.quantity} ${item.units || 'units'}`,
                    data: item
                });
                toast.success("Added to Transporter");
                return;
            }
        }

        // Handle Drop ONTO Project BOM
        if (over.id.toString().startsWith('bom-drop-zone-')) {
            const projectId = over.data.current?.projectId;
            const itemData = active.data.current;

            if (itemData?.type === 'stash-item' && itemData.payload?.type === 'inventory') {
                const originalId = itemData.payload.originalId;
                const fullInvItem = await db.inventory.get(originalId);

                if (fullInvItem && projectId) {
                    await db.project_bom.add({
                        project_id: projectId,
                        part_name: fullInvItem.name,
                        quantity_required: 1,
                        status: 'missing',
                        inventory_item_id: fullInvItem.id,
                        est_unit_cost: 0
                    });
                    removeFromStash(itemData.payload.id);
                    toast.success("Item moved from Transporter to BOM");
                }
            }
        }

        // Handle Drop ONTO Calendar Cell
        if (over.id.toString().startsWith('calendar-cell-')) {
            const dateStr = over.id.toString().replace('calendar-cell-', '');
            // Create date in local timezone to avoid off-by-one errors due to UTC conversion
            const dateParts = dateStr.split('-');
            const targetDate = new Date(Number(dateParts[0]), Number(dateParts[1]) - 1, Number(dateParts[2]));

            const itemData = active.data.current;

            if (itemData?.type === 'stash-item' && itemData.payload?.type === 'task') {
                const taskId = itemData.payload.originalId;
                const taskTitle = itemData.payload.title;

                // Open Modal
                setTaskScheduleModal({
                    isOpen: true,
                    taskId: taskId,
                    taskTitle: taskTitle,
                    targetDate: targetDate,
                    stashId: itemData.payload.id
                });
                return;
            }
        }


        // Handle Drop ONTO Goal
        if (over.id.toString().startsWith('goal-drop-zone-')) {
            const goalId = Number(over.id.toString().replace('goal-drop-zone-', ''));
            const itemData = active.data.current;

            if (itemData?.type === 'stash-item') {
                const payload = itemData.payload;

                // Link Project
                if (payload.type === 'project') {
                    await db.projects.update(Number(payload.originalId), { goal_id: goalId, updated_at: new Date() });
                    toast.success("Project linked to Goal");
                }

                // Link Task
                if (payload.type === 'task') {
                    await db.project_tasks.update(Number(payload.originalId), { goal_id: goalId });
                    toast.success("Task linked to Goal");
                }
            }
        }
    };

    if (isShutdown) {
        return (
            <div className="h-screen w-screen bg-black flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                    style={{ backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', backgroundSize: '40px 40px' }}
                />
                <div className="space-y-4 text-center z-10">
                    <div className="text-red-900 font-mono tracking-widest text-4xl animate-pulse">SYSTEM HALTED</div>
                    <button
                        onClick={() => window.location.reload()}
                        className="text-red-500/50 hover:text-red-500 font-mono text-sm border border-red-900/30 px-4 py-2 rounded hover:bg-red-900/10 transition-all"
                    >
                        MANUAL REBOOT
                    </button>
                </div>
            </div>
        )
    }

    return (
        <MusicProvider>

            <div className="flex h-screen w-full bg-black text-white overflow-hidden relative selection:bg-accent selection:text-black">
                {/* Background Mesh (Fixed) */}
                <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-navy/40 via-background to-background" />

                {/* Sidebar */}
                <aside
                    className={clsx(
                        "bg-black/90 backdrop-blur-md border-r border-white/5 flex flex-col transition-all duration-300 relative z-20 shadow-2xl shrink-0",
                        sidebarOpen ? "w-64" : "w-16"
                    )}
                >
                    <div className="h-16 flex items-center justify-between px-4 border-b border-white/10">
                        {sidebarOpen && (
                            <div className="flex items-center gap-2">
                                <div className="w-1.5 h-6 bg-industrial relative overflow-hidden group">
                                    <div className="absolute top-0 left-0 w-full h-full bg-accent/50 animate-pulse" />
                                </div>
                                <span className="font-mono font-black text-lg tracking-tighter text-white">
                                    WORKSHOP<span className="text-industrial">.OS</span>
                                </span>
                            </div>
                        )}
                        <button onClick={toggleSidebar} className="text-gray-500 hover:text-white transition-colors">
                            {sidebarOpen ? <ChevronLeft size={20} /> : <Menu size={20} />}
                        </button>
                    </div>

                    <nav className="flex-1 py-4 flex flex-col gap-2 px-2">
                        <NavLink to="/" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <LayoutDashboard size={18} />
                            {sidebarOpen && <span>FOCUS</span>}
                        </NavLink>
                        <NavLink to="/projects" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <FolderOpen size={18} />
                            {sidebarOpen && <span>PROJECTS</span>}
                        </NavLink>
                        <NavLink to="/flow" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <Workflow size={18} />
                            {sidebarOpen && <span>FLOW</span>}
                        </NavLink>
                        <NavLink to="/inventory" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive && !location.search.includes('tab=filament') ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <Package size={18} />
                            {sidebarOpen && <span>INVENTORY</span>}
                        </NavLink>

                        <NavLink to="/portfolio" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <FolderOpen size={18} />
                            {sidebarOpen && <span>PORTFOLIO</span>}
                        </NavLink>
                        <NavLink to="/assets" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <Monitor size={18} />
                            {sidebarOpen && <span>ASSETS</span>}
                        </NavLink>
                        <NavLink to="/instructions" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <Sparkles size={18} />
                            {sidebarOpen && <span>INSTRUCTIONS</span>}
                        </NavLink>
                        <NavLink to="/goals" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-purple-400 border-purple-400 bg-purple-500/10 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <Target size={18} />
                            {sidebarOpen && <span>GOALS</span>}
                        </NavLink>
                        <NavLink to="/blueprints" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <div className="relative">
                                <Workflow size={18} />
                                {/* Detail: Tiny accent dot for 'Dev Phase' */}
                                <div className="absolute -top-1 -right-1 w-1.5 h-1.5 bg-accent rounded-full animate-pulse" />
                            </div>
                            {sidebarOpen && <span>BLUEPRINTS</span>}
                        </NavLink>
                        <NavLink to="/settings" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <Settings size={18} />
                            {sidebarOpen && <span>SETTINGS</span>}
                        </NavLink>
                        <NavLink to="/help" className={({ isActive }) => clsx(
                            "flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border-l-2",
                            isActive ? "text-accent border-accent bg-accent/5 font-bold" : "text-gray-500 border-transparent hover:text-white hover:bg-white/5",
                            !sidebarOpen && "justify-center"
                        )}>
                            <HelpCircle size={18} />
                            {sidebarOpen && <span>HELP</span>}
                        </NavLink>

                    </nav>

                    {/* Transporter / Stash Drop Zone */}
                    <SidebarStash isCollapsed={!sidebarOpen} />

                    <div className="px-2 pb-4 space-y-2">
                        <button
                            onClick={() => setOracleChatOpen(!isOracleChatOpen)}
                            className={clsx(
                                "w-full flex items-center gap-3 px-4 py-3 text-sm font-mono tracking-wider transition-all border border-accent/20 rounded-lg text-accent hover:bg-accent/10 hover:shadow-[0_0_15px_rgba(59,130,246,0.2)]",
                                !sidebarOpen && "justify-center"
                            )}
                            title="Oracle"
                        >
                            <Bot size={20} />
                            {sidebarOpen && <span>ORACLE</span>}
                        </button>

                    </div>

                    <div className="p-4 border-t border-border">

                        {sidebarOpen && (
                            <div className="flex items-center gap-3">
                                <button
                                    onClick={() => {
                                        if (window.confirm("Confirm System Restart? Unsaved data may be lost.")) {
                                            window.location.reload();
                                        }
                                    }}
                                    className="text-yellow-600 hover:text-yellow-400 transition-colors"
                                    title="System Restart"
                                >
                                    <RefreshCw size={14} />
                                </button>
                                <button
                                    onClick={() => {
                                        if (window.confirm("Confirm System Shutdown?")) {
                                            setIsShutdown(true);
                                        }
                                    }}
                                    className="text-red-700 hover:text-red-500 transition-colors"
                                    title="System Shutdown"
                                >
                                    <Power size={14} />
                                </button>
                            </div>
                        )}
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 flex flex-col h-full relative overflow-hidden">
                    {/* Header */}
                    <header className="h-16 border-b border-border bg-background/50 backdrop-blur-sm flex items-center justify-between px-6 shrink-0 relative z-10">
                        <div className="flex-1 flex justify-between items-center relative z-20">
                            {/* Breadcrumbs (Left) */}
                            <Breadcrumbs />

                            {/* Center Search - Now Visible */}
                            <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 pointer-events-auto flex items-center gap-4">
                                <GlobalSearchInput />
                            </div>

                            {/* Right Actions */}
                            <div className="flex items-center gap-4">
                                <QuickActionHUD />

                                <button
                                    onClick={() => BackupService.exportToZip()}
                                    className="p-2 text-gray-500 hover:text-accent transition-colors hover:bg-white/5 rounded-full"
                                    title="Quick Backup Database"
                                >
                                    <Database size={18} />
                                </button>

                                <NavLink to="/inbox" className={({ isActive }) => clsx(
                                    "p-2 rounded-full transition-colors relative",
                                    isActive ? "text-accent bg-white/5" : "text-gray-500 hover:text-white hover:bg-white/5"
                                )}>
                                    <Inbox size={18} />
                                    {inboxCount > 0 && (
                                        <span className="absolute -top-1 -right-1 bg-accent text-black text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                                            {inboxCount > 9 ? '9+' : inboxCount}
                                        </span>
                                    )}
                                </NavLink>

                                {/* Calendar Button with Badge */}
                                <div
                                    className="relative"
                                    data-calendar-dropdown
                                    onMouseEnter={() => setIsCalendarOpen(true)}
                                    onMouseLeave={() => setIsCalendarOpen(false)}
                                >
                                    <NavLink
                                        to="/schedule"
                                        className={({ isActive }) => clsx(
                                            "p-2 rounded-full transition-colors relative block",
                                            isActive ? "text-accent bg-white/5" : "text-gray-500 hover:text-white hover:bg-white/5"
                                        )}
                                        title="Schedule & Calendar"
                                    >
                                        <Calendar size={18} />
                                        {todaysTasks.length > 0 && (
                                            <span className="absolute -top-1 -right-1 bg-blue-500 text-white text-[9px] font-bold rounded-full w-4 h-4 flex items-center justify-center">
                                                {todaysTasks.length > 9 ? '9+' : todaysTasks.length}
                                            </span>
                                        )}
                                    </NavLink>

                                    {/* Calendar Overlay (on hover) */}
                                    {isCalendarOpen && (
                                        <div
                                            className="absolute right-0 top-full mt-2 w-80 rounded-lg shadow-2xl animate-in slide-in-from-top-2 fade-in duration-200"
                                            style={{ zIndex: 99999, backgroundColor: '#090909', border: '1px solid rgba(255,255,255,0.15)', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
                                        >
                                            <div className="p-4" style={{ borderBottom: '1px solid rgba(255,255,255,0.1)' }}>
                                                <div className="flex items-center justify-between">
                                                    <div>
                                                        <div className="text-xs text-gray-500 uppercase font-mono">Today</div>
                                                        <div className="text-xl font-bold text-white">
                                                            {new Date().toLocaleDateString('en-US', { weekday: 'long', month: 'short', day: 'numeric' })}
                                                        </div>
                                                    </div>
                                                    <span className="text-xs text-accent">
                                                        Click to open →
                                                    </span>
                                                </div>
                                            </div>
                                            <div className="p-4 max-h-64 overflow-y-auto" style={{ backgroundColor: '#090909' }}>
                                                {todaysTasks.length === 0 ? (
                                                    <div className="text-center py-4 text-gray-600">
                                                        <Calendar size={24} className="mx-auto mb-2 opacity-30" />
                                                        <p className="text-xs">No tasks scheduled for today</p>
                                                        <p className="text-[10px] text-gray-700 mt-1">Drag tasks to calendar to schedule</p>
                                                    </div>
                                                ) : (
                                                    <div className="space-y-2">
                                                        <div className="text-[10px] uppercase text-gray-500 font-bold mb-2">
                                                            Pending Tasks ({todaysTasks.length})
                                                        </div>
                                                        {todaysTasks.slice(0, 5).map(task => (
                                                            <div
                                                                key={task.id}
                                                                className="p-2 bg-white/5 rounded border border-white/10 hover:border-accent/30 transition-colors"
                                                            >
                                                                <div className="text-sm text-white truncate">{task.title}</div>
                                                                <div className="flex items-center gap-2 mt-1">
                                                                    <span className={clsx(
                                                                        "text-[9px] px-1.5 py-0.5 rounded uppercase font-bold",
                                                                        task.status === 'in-progress' ? "bg-blue-500/20 text-blue-400" : "bg-white/10 text-gray-400"
                                                                    )}>
                                                                        {task.status}
                                                                    </span>
                                                                    {task.phase && (
                                                                        <span className="text-[9px] text-gray-600">{task.phase}</span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                        ))}
                                                        {todaysTasks.length > 5 && (
                                                            <div className="text-center text-xs text-gray-500 pt-2">
                                                                +{todaysTasks.length - 5} more tasks
                                                            </div>
                                                        )}
                                                    </div>
                                                )}
                                            </div>
                                        </div>
                                    )}
                                </div>

                                <div className="h-6 w-px bg-white/10" />

                                <div className="flex items-center gap-4 text-xs font-mono text-gray-500 relative group cursor-help">
                                    <div className="flex items-center gap-2 border border-border px-3 py-1 rounded-sm bg-black/50 group-hover:border-green-500/50 transition-colors">
                                        <div className="relative">
                                            <Wifi size={14} className="text-green-500" />
                                            <div className="absolute inset-0 bg-green-500 blur-[2px] opacity-40 animate-pulse" />
                                        </div>
                                        <span className="text-gray-300">ONLINE</span>
                                    </div>

                                    {/* Robust Status Overlay */}
                                    <div
                                        className="absolute right-0 top-full mt-2 w-64 rounded-lg shadow-2xl p-4 hidden group-hover:block animate-in fade-in slide-in-from-top-1"
                                        style={{ zIndex: 99999, backgroundColor: '#090909', border: '1px solid rgba(255,255,255,0.15)', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
                                    >
                                        <div className="space-y-3">
                                            <div>
                                                <div className="text-[10px] uppercase text-gray-500 font-bold mb-1">System Status</div>
                                                <div className="flex items-center gap-2 text-green-400">
                                                    <div className="w-1.5 h-1.5 rounded-full bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.5)]" />
                                                    Operational
                                                </div>
                                            </div>

                                            <div className="h-px bg-white/10" />

                                            <div>
                                                <div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Active Connections</div>
                                                <div className="space-y-1">
                                                    <div className="flex items-center justify-between text-gray-300">
                                                        <span>Gemini 1.5 Pro</span>
                                                        <div className="w-1.5 h-1.5 rounded-full bg-green-500/50" />
                                                    </div>
                                                    <div className="flex items-center justify-between text-gray-300">
                                                        <span>Vector DB (Hybrid)</span>
                                                        <div className="w-1.5 h-1.5 rounded-full bg-green-500/50" />
                                                    </div>
                                                </div>
                                            </div>

                                            <div className="h-px bg-white/10" />

                                            <div>
                                                <div className="text-[10px] uppercase text-gray-500 font-bold mb-1">Local Network</div>
                                                <div className="font-mono text-xs text-gray-400">
                                                    {window.location.host}
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </header>

                    {/* Content Area */}
                    <div className="flex-1 overflow-auto p-6 relative">
                        {/* Grid Pattern Background */}
                        <div className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                            style={{ backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', backgroundSize: '40px 40px' }}
                        />
                        <div className="relative z-10 h-[calc(100%-2px)]">
                            <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
                                <Outlet />

                                {/* Draggable Overlay if needed */}
                                {createPortal(
                                    <DragOverlay>
                                        {/* We can render a generic drag preview here if we track active item */}
                                    </DragOverlay>,
                                    document.body
                                )}
                            </DndContext>
                        </div>
                    </div>

                    <GlobalProgressBar />
                    <GlobalChat isOpen={isOracleChatOpen} onClose={() => setOracleChatOpen(false)} />
                    <CommandBar />
                    <QuickCapture isOpen={isQuickCaptureOpen} onClose={() => setIsQuickCaptureOpen(false)} />
                    <OracleGlobalOverlay />
                    <TaskSchedulingModal />
                    {isCreateProjectOpen && <CreateProjectModal onClose={() => setCreateProjectOpen(false)} />}
                </main>
            </div >
        </MusicProvider >
    );
}
