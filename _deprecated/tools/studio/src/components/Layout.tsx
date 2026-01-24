import { NavLink, Outlet, useLocation } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { useUIStore } from '../store/useStore';
import { db } from '../lib/db';
import { Settings, LayoutDashboard, Package, FolderOpen, Menu, ChevronLeft, ChevronRight, ChevronDown, Wifi, Workflow, Bot, Calendar, Power, RefreshCw, Database, Inbox, HelpCircle, Monitor, Sparkles, Target, Repeat, Network, Music, BarChart3, Book, Box, BrainCircuit, GitFork, LayoutTemplate } from 'lucide-react';
import { LinkService } from '../services/LinkService';
import type { EntityType, LinkType } from '../lib/universal';
import clsx from 'clsx';
import { GlobalProgressBar } from './GlobalProgressBar';
import { GlobalChat } from './GlobalChat';
import { QuickCapture } from './QuickCapture';
import { CreateProjectModal } from './projects/CreateProjectModal';
import { DOMAIN_CONFIG } from '../lib/domain-config';

import { useState, useEffect } from 'react';
import { MusicProvider } from '../lib/MusicContext';
import { CommandBar } from './ui/CommandBar';
import { Breadcrumbs } from './navigation/Breadcrumbs';
import { QuickActionHUD } from './navigation/QuickActionHUD';
import { GlobalSearchInput } from './navigation/GlobalSearchInput';
import { OracleGlobalOverlay } from './ui/OracleGlobalOverlay';
import { HeaderMiniPlayer } from './music/HeaderMiniPlayer';
import { TaskSchedulingModal } from './ui/TaskSchedulingModal';
import { SidebarStash, FloatingTransporter } from './ui/GlobalTransporter';
import { MiniPomodoro } from './ui/MiniPomodoro';
import { GlobalNotebookPanel } from './ui/GlobalNotebookPanel';
import { DndContext, DragOverlay, PointerSensor, useSensor, useSensors, useDroppable, pointerWithin } from '@dnd-kit/core';
import { snapCenterToCursor } from '@dnd-kit/modifiers';
import type { DragEndEvent } from '@dnd-kit/core';
import { createPortal } from 'react-dom';
import { toast } from 'sonner';
import { WorkshopMusicPlayer } from './music/WorkshopMusicPlayer';
import { UniversalModalManager } from './universal/modals/UniversalModalManager';

export function Layout() {
    const {
        sidebarOpen, toggleSidebar,
        isOracleChatOpen, setOracleChatOpen,
        isCreateProjectOpen, setCreateProjectOpen,
        removeFromStash, addToStash,
        setTaskScheduleModal,

        pomodoro, tickPomodoro,
        mainTheme, musicTheme
    } = useUIStore();
    const [isShutdown, setIsShutdown] = useState(false);
    const location = useLocation();

    // Pomodoro Tick logic
    useEffect(() => {
        let interval: NodeJS.Timeout | null = null;
        if (pomodoro.isRunning) {
            interval = setInterval(() => {
                tickPomodoro();
            }, 1000);
        }
        return () => {
            if (interval) clearInterval(interval);
        };
    }, [pomodoro.isRunning, tickPomodoro]);

    // TEST: Simple drop zone component to verify DnD works
    const TestDropZone = () => {
        const { setNodeRef, isOver } = useDroppable({
            id: 'test-drop-zone',
            data: { type: 'test' }
        });

        return (
            <div
                ref={setNodeRef}
                className={clsx(
                    "fixed bottom-20 left-1/2 -translate-x-1/2 z-[9999] p-4 rounded-lg border-2 border-dashed",
                    isOver ? "bg-green-500/30 border-green-500 text-green-400" : "bg-red-500/30 border-red-500 text-red-400"
                )}
            >
                {isOver ? "✓ DROP HERE WORKS!" : "TEST DROP ZONE - Drag items here"}
            </div>
        );
    };

    // Auto-Theme Logic (Music Context)
    // Theme Logic
    const isMusicContext = location.pathname.startsWith('/songs') || location.pathname.startsWith('/albums');
    const effectiveTheme = isMusicContext ? musicTheme : mainTheme;

    // Inbox count for badge
    const inboxCount = useLiveQuery(() =>
        db.inbox_items.filter(item => !item.triaged_at).count()
    ) || 0;

    // Calendar overlay state
    const [isCalendarOpen, setIsCalendarOpen] = useState(false);

    // Visualization Group State (Unified)
    const [visualizationOpen, setVisualizationOpen] = useState(false);
    const visualizationActive = location.pathname.startsWith('/flow') || location.pathname.startsWith('/galaxy');

    // Debug Group State
    const [debugOpen, setDebugOpen] = useState(true);
    const debugActive = location.pathname.startsWith('/sandbox');

    // Auto-expand groups if active
    useEffect(() => {
        if (visualizationActive) {
            setVisualizationOpen(true);
        }
        if (debugActive) {
            setDebugOpen(true);
        }
    }, [visualizationActive, debugActive]);


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
                distance: 4, // Reduced from 8 for snappier start
            },
        })
    );

    const [activeDragItem, setActiveDragItem] = useState<any>(null);

    const handleDragStart = (event: any) => {
        setActiveDragItem(event.active);
    };

    // Handle drops from Transporter
    const handleDragEnd = async (event: DragEndEvent) => {
        setActiveDragItem(null); // Clear drag preview
        const { active, over } = event;

        console.log('[DnD] DragEnd:', {
            activeId: active?.id,
            overId: over?.id,
            activeType: active?.data?.current?.type,
            overType: over?.data?.current?.type
        });

        if (!over) return;

        // Handle Drop ONTO the Sidebar Stash (or Floating Transporter)
        if (over.id === 'transporter-sidebar' || over.id === 'transporter-floating' || over.id === 'sidebar-stash-drop-zone') {
            const itemData = active.data.current;

            // UNIVERSAL CARD HANDLER (new standard)
            if (itemData?.type === 'universal-card' || itemData?.type === 'inventory-item') {
                // Support both flattened format and entity-nested format
                const entityData = itemData.entity;
                const isLegacyInventory = itemData.type === 'inventory-item';
                const actualType = isLegacyInventory
                    ? 'inventory-item'
                    : (itemData.entityType || entityData?.type || 'unknown');

                // Extract subtitle and additional data
                let subtitle = '';
                let data = itemData;
                const title = itemData.title || entityData?.title || itemData.item?.name;

                if (actualType === 'inventory-item' || actualType === 'inventory') {
                    const invItem = isLegacyInventory ? itemData.item : (itemData.metadata || entityData?.metadata);
                    if (invItem) {
                        subtitle = `${invItem.quantity} ${invItem.units || 'units'}`;
                        data = invItem;
                    }
                } else if (itemData.metadata || entityData?.metadata) {
                    const meta = itemData.metadata || entityData?.metadata || { status: entityData?.status };
                    subtitle = meta.status || meta.category || meta.type || actualType;
                    data = meta;
                }

                addToStash({
                    id: crypto.randomUUID(),
                    originalId: itemData.id ?? entityData?.id ?? itemData.item?.id,
                    type: actualType === 'inventory-item' ? 'inventory' : (actualType === 'project-item' ? 'project' : actualType),
                    title: title,
                    subtitle: subtitle,
                    data: data
                });
                toast.success("Added to Transporter");
                return;
            }

            if (itemData?.type === 'project-item') {
                // Dragging Project to Stash
                const project = itemData.project;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: project.id,
                    type: 'project',
                    title: project.title,
                    subtitle: project.project_code || `P-${project.id}`,
                    data: project
                });
                toast.success("Project added to Transporter");
                return;
            }

            if (itemData?.type === 'goal-item') {
                // Dragging Goal to Stash
                const goal = itemData.goal || itemData.item;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: goal.id,
                    type: 'goal',
                    title: goal.title,
                    subtitle: goal.level,
                    data: goal
                });
                toast.success("Goal added to Transporter");
                return;
            }

            if (itemData?.type === 'task-item') {
                const item = itemData.item;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: item.id,
                    type: 'task',
                    title: item.title,
                    subtitle: item.status,
                    data: item
                });
                toast.success("Task added to Transporter");
                return;
            }

            if (itemData?.type === 'asset-item') {
                const item = itemData.item;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: item.id,
                    type: 'asset',
                    title: item.name,
                    subtitle: item.category,
                    data: item
                });
                toast.success("Asset added to Transporter");
                return;
            }

            if (itemData?.type === 'routine-item') {
                const item = itemData.item;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: item.id!,
                    type: 'routine',
                    title: item.title,
                    subtitle: item.frequency,
                    data: item
                });
                toast.success("Routine added to Transporter");
                return;
            }

            if (itemData?.type === 'library-item') {
                const item = itemData.item;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: item.id!,
                    type: 'library',
                    title: item.title,
                    subtitle: item.category,
                    data: item
                });
                toast.success("Library Item added to Transporter");
                return;
            }

            // UNIVERSAL CARD HANDLER (new standard)
            if (itemData?.type === 'universal-card') {
                // Support both flattened format and entity-nested format
                const entityData = itemData.entity;
                const entityType = itemData.entityType || entityData?.type || 'unknown';
                const id = itemData.id ?? entityData?.id;
                const title = itemData.title || entityData?.title || 'Untitled';
                const meta = itemData.metadata || entityData?.metadata || { status: entityData?.status };
                const subtitle = meta.status || meta.category || meta.type || entityType;

                addToStash({
                    id: crypto.randomUUID(),
                    originalId: id,
                    type: entityType,
                    title: title,
                    subtitle: subtitle,
                    data: meta
                });
                toast.success(`${entityType} added to Transporter`);
                return;
            }

            // Legacy: Song/Album (Music)
            if (itemData?.type === 'song') {
                const song = itemData.song;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: song.id,
                    type: 'song',
                    title: song.title,
                    subtitle: song.status,
                    data: song
                });
                toast.success("Song added to Transporter");
                return;
            }

            if (itemData?.type === 'album') {
                const album = itemData.album;
                addToStash({
                    id: crypto.randomUUID(),
                    originalId: album.id,
                    type: 'album',
                    title: album.title,
                    subtitle: `${album.songs?.length || 0} tracks`,
                    data: album
                });
                toast.success("Album added to Transporter");
                return;
            }
        }
        // Handle Drops ONTO Calendar Cells (Scheduling)
        if (over.id.toString().startsWith('calendar-cell-')) {
            const dateStr = over.id.toString().replace('calendar-cell-', '');

            // Extract item data
            const type = active.data.current?.type;
            const item = active.data.current?.item || active.data.current?.data || active.data.current?.payload;

            if (!item) return;

            console.log('Dropping on calendar:', dateStr, type, item);

            // Handle Stash Items being dropped on Calendar
            if (active.data.current?.type === 'stash-item') {
                const stashItem = active.data.current.payload;

                if (stashItem.type === 'project') {
                    await db.projects.update(stashItem.originalId, {
                        target_completion_date: new Date(dateStr)
                    });
                    toast.success(`Project rescheduled to ${dateStr}`);
                } else if (stashItem.type === 'task') { // Tasks via stash
                    await db.project_tasks.update(stashItem.originalId, {
                        scheduled_date: new Date(dateStr)
                    });
                    toast.success(`Task rescheduled to ${dateStr}`);
                } else if (stashItem.type === 'routine') { // Routines via stash
                    // For routines, maybe set next_due?
                    await db.routines.update(stashItem.originalId, {
                        next_due: new Date(dateStr)
                    });
                    toast.success(`Routine due date updated to ${dateStr}`);
                }

                // Optionally remove from stash after successful drop?
                // removeFromStash(stashItem.id); 
                return;
            }

            // Handle Direct Drags (Sidebar/Lists -> Calendar)
            if (type === 'project-item') {
                await db.projects.update(item.id, {
                    target_completion_date: new Date(dateStr)
                });
                toast.success(`Project scheduled for ${dateStr}`);
            } else if (type === 'task-item') {
                await db.project_tasks.update(item.id, {
                    scheduled_date: new Date(dateStr)
                });
                toast.success(`Task scheduled for ${dateStr}`);
            } else if (type === 'routine-item') {
                await db.routines.update(item.id, {
                    next_due: new Date(dateStr)
                });
                toast.success(`Routine scheduled for ${dateStr}`);
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


        // Handle Drop ONTO Project Assets
        if (over.id.toString().startsWith('project-assets-dropzone-')) {
            const projectId = over.data.current?.projectId;
            if (projectId && active.data.current?.type === 'asset-item') {
                const asset = active.data.current.item;
                await db.assets.where('id').equals(asset.id).modify((a: any) => {
                    if (!a.related_project_ids) a.related_project_ids = [];
                    if (!a.related_project_ids.includes(projectId)) {
                        a.related_project_ids.push(projectId);
                    }
                });
                toast.success(`Linked ${asset.name} to project`);
                return;
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

                // Universal Linking
                if (payload.type === 'project' || payload.type === 'routine' || payload.type === 'goal') {
                    // Determine relationship
                    let rel: LinkType = 'supports'; // Default: Linked item supports the Goal
                    if (payload.type === 'goal') rel = 'relates_to';

                    await LinkService.link(payload.type as EntityType, Number(payload.originalId), 'goal', goalId, rel);
                    toast.success(`Linked ${payload.type} to Goal`);
                }
            }
        }

        // Handle Drop ONTO Project
        if (over.id.toString().startsWith('project-drop-zone-')) {
            const projectId = Number(over.id.toString().replace('project-drop-zone-', ''));
            const itemData = active.data.current;

            if (itemData?.type === 'stash-item') {
                const payload = itemData.payload;

                if (payload.type === 'project') {
                    // Linking Project to Project
                    await LinkService.link('project', Number(payload.originalId), 'project', projectId, 'blocks'); // Default to blocks? Or relates? Let's say relates for generic drag
                    // Actually user might want to set dependency. Let's default to 'related' for now to be safe.
                    await LinkService.link('project', Number(payload.originalId), 'project', projectId, 'relates_to');
                    toast.success("Projects linked");
                } else if (payload.type === 'goal') {
                    // Goal -> Project (Goal supports Project)
                    await LinkService.link('goal', Number(payload.originalId), 'project', projectId, 'supports');
                    toast.success("Goal linked to Project");
                } else if (payload.type === 'routine') {
                    // Routine -> Project
                    await LinkService.link('routine', Number(payload.originalId), 'project', projectId, 'maintains');
                    toast.success("Routine linked to Project");
                }
            }
        }

        // Handle Drop ONTO Routine
        if (over.id.toString().startsWith('routine-drop-zone-')) {
            const routineId = Number(over.id.toString().replace('routine-drop-zone-', ''));
            const itemData = active.data.current;

            if (itemData?.type === 'stash-item') {
                const payload = itemData.payload;

                if (payload.type === 'project') {
                    // Linking Project to Routine
                    await LinkService.link('project', Number(payload.originalId), 'routine', routineId, 'relates_to');
                    toast.success("Project linked to Routine");
                } else if (payload.type === 'goal') {
                    // Goal -> Routine
                    await LinkService.link('goal', Number(payload.originalId), 'routine', routineId, 'supports');
                    toast.success("Goal linked to Routine");
                } else if (payload.type === 'routine') {
                    // Routine -> Routine
                    await LinkService.link('routine', Number(payload.originalId), 'routine', routineId, 'relates_to');
                    toast.success("Routines linked");
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

    // ... rest of the Layout component

    return (
        <MusicProvider>
            <div data-theme={effectiveTheme} className="flex h-screen w-full bg-background text-white overflow-hidden relative selection:bg-accent selection:text-black transition-colors duration-500">
                {/* Background Mesh (Fixed) */}
                <div className="fixed inset-0 z-0 pointer-events-none bg-[radial-gradient(circle_at_top_right,_var(--tw-gradient-stops))] from-navy/40 via-background to-background" />

                <WorkshopMusicPlayer />
                <UniversalModalManager />

                <GlobalNotebookPanel />
                <GlobalChat isOpen={isOracleChatOpen} onClose={() => setOracleChatOpen(false)} />
                <OracleGlobalOverlay />

                <DndContext
                    sensors={sensors}
                    collisionDetection={pointerWithin}
                    onDragStart={handleDragStart}
                    onDragEnd={handleDragEnd}
                >    {/* Sidebar */}
                    <aside
                        className={clsx(
                            "sidebar-industrial bg-background border-r border-white/5 flex flex-col transition-all duration-300 relative z-20 shadow-2xl shrink-0",
                            sidebarOpen ? "w-44" : "w-12"
                        )}
                    >
                        <div className={clsx("h-12 flex items-center border-b border-white/10 shrink-0", sidebarOpen ? "justify-between px-3" : "justify-center")}>
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

                        <nav className="flex-1 py-2 flex flex-col gap-1 px-2 overflow-y-auto scrollbar-none [&::-webkit-scrollbar]:hidden">
                            {/* --- CORE --- */}
                            <NavLink to="/" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <LayoutDashboard size={18} className="shrink-0" />
                                {sidebarOpen && <span>DASHBOARD</span>}
                            </NavLink>
                            <NavLink to="/projects" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <FolderOpen size={18} className="shrink-0" />
                                {sidebarOpen && <span>PROJECTS</span>}
                            </NavLink>
                            <NavLink to="/goals" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-purple-400 bg-purple-500/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Target size={18} className="shrink-0" />
                                {sidebarOpen && <span>GOALS</span>}
                            </NavLink>

                            <div className="h-px bg-white/5 my-1 mx-2" />

                            {/* --- RESOURCES --- */}
                            <NavLink to="/inventory" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Package size={18} className="shrink-0" />
                                {sidebarOpen && <span>INVENTORY</span>}
                            </NavLink>
                            <NavLink to="/assets" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Monitor size={18} className="shrink-0" />
                                {sidebarOpen && <span>ASSETS</span>}
                            </NavLink>
                            <NavLink to="/portfolio" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <FolderOpen size={18} className="shrink-0" />
                                {sidebarOpen && <span>PORTFOLIO</span>}
                            </NavLink>

                            <div className="h-px bg-white/5 my-1 mx-2" />

                            {/* --- KNOWLEDGE --- */}
                            <NavLink to="/library" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Book size={18} className="shrink-0" />
                                {sidebarOpen && <span>LIBRARY</span>}
                            </NavLink>
                            <NavLink to="/blueprints" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Workflow size={18} className="shrink-0" />
                                {sidebarOpen && <span>BLUEPRINTS</span>}
                            </NavLink>
                            <NavLink to="/instructions" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Repeat size={20} className="rotate-90 shrink-0" />
                                {sidebarOpen && <span>INSTRUCTIONS</span>}
                            </NavLink>

                            <div className="h-px bg-white/5 my-1 mx-2" />

                            {/* --- TOOLS --- */}
                            <NavLink to="/routines" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Repeat size={18} className="shrink-0" />
                                {sidebarOpen && <span>ROUTINES</span>}
                            </NavLink>

                            {/* DYNAMIC COLLECTIONS (From Domain Config) */}
                            {DOMAIN_CONFIG.collections.map(col => (
                                <NavLink key={col.tableName} to={`/collection/${col.tableName}`} className={({ isActive }) => clsx(
                                    "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                    isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                    !sidebarOpen && "justify-center px-0"
                                )}>
                                    {/* Default Icon for Dynamic Collections: Database or configured */}
                                    <Database size={18} className="shrink-0" />
                                    {sidebarOpen && <span>{col.label.toUpperCase()}</span>}
                                </NavLink>
                            ))}

                            {/* --- VISUALIZATION GROUP --- */}
                            <div className="mt-2 w-full flex flex-col">
                                <button
                                    onClick={() => setVisualizationOpen(!visualizationOpen)}
                                    className={clsx(
                                        "w-full flex items-center py-2 text-sm font-mono tracking-wider text-gray-400 hover:text-white transition-all rounded-lg hover:bg-white/5 text-left",
                                        sidebarOpen ? "justify-start gap-3 px-3" : "justify-center px-0"
                                    )}
                                >
                                    {sidebarOpen ? (
                                        <>
                                            <BrainCircuit size={18} className="shrink-0" />
                                            <span>VISUAL AIDS</span>
                                            <ChevronDown size={14} className={clsx("ml-auto transition-transform opacity-50", visualizationOpen ? "rotate-180" : "")} />
                                        </>
                                    ) : (
                                        <BrainCircuit size={18} className="shrink-0" />
                                    )}
                                </button>

                                {/* Sub-items */}
                                {visualizationOpen && (
                                    <div className={clsx("mt-1 flex flex-col gap-1", sidebarOpen ? "ml-2 pl-2 border-l border-white/10" : "")}>
                                        <NavLink to="/flow" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <GitFork size={18} className="shrink-0" />
                                            {sidebarOpen && <span>FLOW</span>}
                                        </NavLink>
                                        <NavLink to="/galaxy" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <Network size={18} className="shrink-0" />
                                            {sidebarOpen && <span>GALAXY</span>}
                                        </NavLink>
                                    </div>
                                )}
                            </div>

                            <div className="h-px bg-white/5 my-1 mx-2" />

                            <NavLink to="/songs" className={({ isActive }) => clsx(
                                "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                !sidebarOpen && "justify-center px-0"
                            )}>
                                <Music size={18} className="shrink-0" />
                                {sidebarOpen && <span>SONGS</span>}
                            </NavLink>


                            <div className="h-px bg-white/5 my-1 mx-2" />

                            {/* --- DEBUG / SANDBOX --- */}
                            <div className="mt-2 w-full flex flex-col">
                                <button
                                    onClick={() => setDebugOpen(!debugOpen)}
                                    className={clsx(
                                        "w-full flex items-center py-2 text-sm font-mono tracking-wider text-gray-400 hover:text-white transition-all rounded-lg hover:bg-white/5 text-left",
                                        sidebarOpen ? "justify-start gap-3 px-3" : "justify-center px-0"
                                    )}
                                >
                                    {sidebarOpen ? (
                                        <>
                                            <Sparkles size={18} className="shrink-0 text-amber-500" />
                                            <span>DEBUG</span>
                                            <ChevronDown size={14} className={clsx("ml-auto transition-transform opacity-50", debugOpen ? "rotate-180" : "")} />
                                        </>
                                    ) : (
                                        <Sparkles size={18} className="shrink-0 text-amber-500" />
                                    )}
                                </button>

                                {/* Sub-items */}
                                {debugOpen && (
                                    <div className={clsx("mt-1 flex flex-col gap-1", sidebarOpen ? "ml-2 pl-2 border-l border-white/10" : "")}>
                                        <NavLink to="/sandbox/components" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <Box size={16} className="shrink-0" />
                                            {sidebarOpen && <span>COMPONENTS</span>}
                                        </NavLink>
                                        <NavLink to="/sandbox/layout" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <LayoutDashboard size={16} className="shrink-0" />
                                            {sidebarOpen && <span>LAYOUT V2</span>}
                                        </NavLink>
                                        <NavLink to="/sandbox/registry" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-accent bg-accent/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <Database size={16} className="shrink-0" />
                                            {sidebarOpen && <span>REGISTRY</span>}
                                        </NavLink>
                                        <NavLink to="/sandbox/universal-page" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-amber-400 bg-amber-500/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <LayoutTemplate size={16} className="shrink-0" />
                                            {sidebarOpen && <span>UNIVERSAL PAGES</span>}
                                        </NavLink>
                                        <NavLink to="/sandbox/universal-detail" className={({ isActive }) => clsx(
                                            "flex items-center gap-3 px-3 py-2 text-sm font-mono tracking-wider transition-all rounded-lg",
                                            isActive ? "text-purple-400 bg-purple-500/10 font-bold shadow-[inset_0_1px_0_0_rgba(255,255,255,0.05)]" : "text-gray-400 hover:text-white hover:bg-white/5",
                                            !sidebarOpen && "justify-center px-0"
                                        )}>
                                            <LayoutTemplate size={16} className="shrink-0" />
                                            {sidebarOpen && <span>DETAIL SANDBOX</span>}
                                        </NavLink>
                                    </div>
                                )}
                            </div>

                        </nav>

                        {/* Transporter / Stash Drop Zone */}
                        <SidebarStash isCollapsed={!sidebarOpen} isDraggingGlobal={!!activeDragItem} />

                        <div className={clsx("pb-3 space-y-1", sidebarOpen ? "px-3" : "px-1")}>
                            <div className="relative group/oracle">
                                {/* Speech bubble tail */}
                                {sidebarOpen && <div className="absolute bottom-[3px] left-8 -translate-x-1/2 translate-y-full border-8 border-transparent border-t-accent z-0 transition-all duration-300 group-hover/oracle:border-t-white"></div>}

                                <button
                                    onClick={() => setOracleChatOpen(!isOracleChatOpen)}
                                    className={clsx(
                                        "w-full flex items-center gap-3 py-2 text-sm font-mono tracking-wider transition-all rounded-xl relative z-10",
                                        sidebarOpen
                                            ? "px-3 bg-accent text-black font-black shadow-[0_4px_15px_rgba(var(--accent-rgb),0.4)] hover:shadow-[0_6px_20px_rgba(var(--accent-rgb),0.6)] hover:bg-white hover:-translate-y-1 active:translate-y-0"
                                            : "px-0 justify-center rounded-lg bg-transparent text-accent border border-accent hover:bg-accent hover:text-black shadow-none"
                                    )}
                                    title="Oracle"
                                >
                                    <Bot size={20} className={clsx(!sidebarOpen && "mx-auto", "shrink-0")} />
                                    {sidebarOpen && <span>ASK ORACLE</span>}
                                </button>
                            </div>

                        </div>

                        <div className={clsx("border-t border-border", !sidebarOpen ? "p-1" : "px-2 py-1.5")}>
                            <div className={clsx(
                                "transition-all",
                                sidebarOpen ? "flex items-center justify-between" : "grid grid-cols-2 gap-1"
                            )}>
                                {/* Left: Settings & Help */}
                                <div className={clsx("flex items-center gap-1", !sidebarOpen && "contents")}>
                                    <NavLink
                                        to="/settings"
                                        className={({ isActive }) => clsx(
                                            "text-gray-500 hover:text-white transition-colors rounded-md hover:bg-white/5",
                                            isActive && "text-accent bg-white/5",
                                            sidebarOpen ? "p-1.5" : "w-full aspect-square flex items-center justify-center p-0.5"
                                        )}
                                        title="Settings"
                                    >
                                        <Settings size={18} className="shrink-0" />
                                    </NavLink>
                                    <NavLink
                                        to="/help"
                                        className={({ isActive }) => clsx(
                                            "text-gray-500 hover:text-white transition-colors rounded-md hover:bg-white/5",
                                            isActive && "text-accent bg-white/5",
                                            sidebarOpen ? "p-1.5" : "w-full aspect-square flex items-center justify-center p-0.5"
                                        )}
                                        title="Help"
                                    >
                                        <HelpCircle size={18} className="shrink-0" />
                                    </NavLink>
                                </div>

                                {/* Status Indicator - Center (Hide on collapse) */}
                                {sidebarOpen && (
                                    <div className="relative group/status flex justify-center">
                                        <div className="flex items-center gap-1.5 px-1.5 py-0.5 rounded-sm bg-black/30 border border-white/5 group-hover/status:border-green-500/30 transition-colors cursor-help">
                                            <div className="relative">
                                                <Wifi size={10} className="text-green-500" />
                                                <div className="absolute inset-0 bg-green-500 blur-[2px] opacity-40 animate-pulse" />
                                            </div>
                                            <span className="text-[9px] text-gray-400 font-mono">OK</span>
                                        </div>
                                    </div>
                                )}

                                {/* Right: System Controls */}
                                <div className={clsx("flex items-center gap-1", !sidebarOpen && "contents")}>
                                    <button
                                        onClick={() => {
                                            if (window.confirm("Confirm System Restart? Unsaved data may be lost.")) {
                                                window.location.reload();
                                            }
                                        }}
                                        className={clsx(
                                            "text-gray-600 hover:text-yellow-400 transition-colors rounded-md hover:bg-white/5",
                                            sidebarOpen ? "p-1.5" : "w-full aspect-square flex items-center justify-center p-0.5"
                                        )}
                                        title="System Restart"
                                    >
                                        <RefreshCw size={16} className="shrink-0" />
                                    </button>
                                    <button
                                        onClick={() => {
                                            if (window.confirm("Confirm System Shutdown?")) {
                                                setIsShutdown(true);
                                            }
                                        }}
                                        className={clsx(
                                            "text-gray-600 hover:text-red-500 transition-colors rounded-md hover:bg-white/5",
                                            sidebarOpen ? "p-1.5" : "w-full aspect-square flex items-center justify-center p-0.5"
                                        )}
                                        title="System Shutdown"
                                    >
                                        <Power size={16} className="shrink-0" />
                                    </button>
                                </div>
                            </div>
                        </div>
                    </aside>

                    {/* Main Content */}
                    <div className="flex-1 flex flex-col min-w-0 bg-background relative transition-colors duration-500">
                        {/* Visual Flair */}
                        <div className="absolute inset-0 bg-noise opacity-[0.02] pointer-events-none" />

                        {/* Header */}
                        <header className="h-12 flex items-center justify-between px-3 shrink-0 relative z-30 border-b border-white/10 bg-background/95 backdrop-blur-md transition-colors duration-500">
                            <div className="flex items-center gap-4 flex-1 min-w-0">
                                {/* Breadcrumbs */}
                                <div className="hidden md:block overflow-hidden shrink-0">
                                    <Breadcrumbs />
                                </div>

                                {/* Global Search Input */}
                                <GlobalSearchInput />
                            </div>

                            <div className="flex items-center gap-2 shrink-0 ml-4">
                                <CommandBar />
                                <QuickActionHUD />
                                <div className="w-px h-6 bg-white/10" />

                                <div className="flex items-center gap-1">
                                    <NavLink
                                        to="/inbox"
                                        className={({ isActive }) => clsx(
                                            "relative p-2 rounded-full transition-colors",
                                            isActive ? "text-accent bg-white/5" : "text-gray-500 hover:text-white hover:bg-white/5"
                                        )}
                                        title="Inbox"
                                    >
                                        <Inbox size={18} />
                                        {inboxCount > 0 && (
                                            <span className="absolute top-0 right-0 w-2.5 h-2.5 bg-red-500 rounded-full border-2 border-black flex items-center justify-center text-[8px] font-bold text-white">
                                                {/* Dot only for cleaner look, or just badge */}
                                            </span>
                                        )}
                                    </NavLink>

                                    {/* Calendar Button with Badge */}
                                    <div
                                        className="relative group/calendar"
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

                                        {/* Calendar Overlay - Fixed positioning with group-hover */}
                                        <div
                                            className="fixed top-14 right-4 w-80 rounded-lg shadow-2xl opacity-0 invisible group-hover/calendar:opacity-100 group-hover/calendar:visible transition-all duration-200 pointer-events-none group-hover/calendar:pointer-events-auto animate-in slide-in-from-top-2 fade-in"
                                            style={{ zIndex: 999999, backgroundColor: '#090909', border: '1px solid rgba(255,255,255,0.15)', boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5)' }}
                                        >
                                            <div className="px-4 py-3 border-b border-white/5 bg-black">
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
                                    </div>

                                </div>

                            </div>

                        </header>        {/* Audio Player Bar */}
                        <HeaderMiniPlayer />

                        {/* Content Area */}
                        <div className="flex-1 overflow-auto p-3 relative">
                            {/* Grid Pattern Background */}
                            <div className="absolute inset-0 z-0 opacity-10 pointer-events-none"
                                style={{ backgroundImage: 'linear-gradient(#333 1px, transparent 1px), linear-gradient(90deg, #333 1px, transparent 1px)', backgroundSize: '40px 40px' }}
                            />
                            <div className="relative z-10 h-[calc(100%-2px)]">
                                <Outlet />
                            </div>
                        </div>

                        <GlobalProgressBar />
                        <GlobalChat isOpen={isOracleChatOpen} onClose={() => setOracleChatOpen(false)} />
                        <CommandBar />
                        <QuickCapture isOpen={isQuickCaptureOpen} onClose={() => setIsQuickCaptureOpen(false)} />
                        <OracleGlobalOverlay />
                        <TaskSchedulingModal />
                        <FloatingTransporter />
                        {isCreateProjectOpen && <CreateProjectModal onClose={() => setCreateProjectOpen(false)} />}
                    </div>





                    {/* DragOverlay for cross-container dragging */}
                    {createPortal(
                        // pointer-events-none is CRITICAL here so the overlay doesn't block drop targets underneath it
                        <DragOverlay
                            dropAnimation={null}
                            zIndex={9999}
                            className="pointer-events-none"
                            modifiers={[snapCenterToCursor]}
                        >
                            {activeDragItem ? (
                                <DragPreview item={activeDragItem} />
                            ) : null}
                        </DragOverlay>,
                        document.body
                    )}
                </DndContext>
            </div >
        </MusicProvider >
    );
}

function DragPreview({ item }: { item: any }) {
    const data = item.data?.current;
    if (!data) return null;

    if (data.type === 'library-item') {
        return (
            <div className="bg-neutral-800 border border-indigo-500/50 rounded-lg p-3 shadow-2xl w-48 flex items-center gap-3">
                <div className="p-2 bg-neutral-900 rounded">
                    <Book size={20} className="text-indigo-400" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="font-bold text-xs text-white truncate">{data.item.title}</div>
                    <div className="text-[10px] text-gray-400 uppercase">{data.item.category}</div>
                </div>
            </div>
        );
    }

    if (data.type === 'stash-item') {
        return (
            <div className="bg-neutral-800 border border-neon/50 rounded p-2 shadow-2xl w-48 flex items-center gap-2 opacity-90 cursor-grabbing">
                <Box size={16} className="text-neon" />
                <div className="font-bold text-xs text-white truncate">{data.payload.title}</div>
            </div>
        );
    }

    // Song Preview
    if (data.type === 'song') {
        return (
            <div className="bg-neutral-800 border border-pink-500/50 rounded-lg p-3 shadow-2xl w-48 flex items-center gap-3">
                <div className="p-2 bg-neutral-900 rounded">
                    <Music size={20} className="text-pink-400" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="font-bold text-xs text-white truncate">{data.song.title}</div>
                    <div className="text-[10px] text-gray-400 uppercase">{data.song.status}</div>
                </div>
            </div>
        );
    }

    // Album Preview
    if (data.type === 'album') {
        return (
            <div className="bg-neutral-800 border border-purple-500/50 rounded-lg p-3 shadow-2xl w-48 flex items-center gap-3">
                <div className="p-2 bg-neutral-900 rounded">
                    <Music size={20} className="text-purple-400" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="font-bold text-xs text-white truncate">{data.album.title}</div>
                    <div className="text-[10px] text-gray-400 uppercase">Album</div>
                </div>
            </div>
        );
    }

    // Universal Card Preview (NEW STANDARD)
    if (data.type === 'universal-card') {
        const meta = data.metadata || {};
        const subtitle = meta.status || meta.category || meta.type || data.entityType;

        return (
            <div className="bg-neutral-800 border border-accent/50 rounded-lg p-3 shadow-2xl w-48 flex items-center gap-3">
                <div className="p-2 bg-neutral-900 rounded">
                    <Box size={20} className="text-accent" />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="font-bold text-xs text-white truncate">{data.title}</div>
                    <div className="text-[10px] text-gray-400 uppercase">{subtitle}</div>
                </div>
            </div>
        );
    }

    // Fallback
    return (
        <div className="bg-neutral-800 border border-white/20 rounded p-2 shadow-xl opacity-80">
            Scanning...
        </div>
    )
}
