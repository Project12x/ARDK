import { useState, useMemo, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Project } from '../lib/db';
import { useProjectSearch } from '../lib/search';
import { Upload, Plus, LayoutGrid, Layers, Maximize2, Minimize2, Trash2, Database, Loader2, Folder, ChevronRight, ChevronDown, Archive, CheckSquare, Square, X, List, Clock, Rows, Grid3x3, Smartphone } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { safeTs } from '../lib/utils';
import { Button } from '../components/ui/Button';
import { ProjectCard, type ProjectCardDensity } from '../components/projects/ProjectCard';
import { CreateProjectModal } from '../components/projects/CreateProjectModal';
import { DataManagementModal } from '../components/projects/DataManagementModal';
import { IngestionService } from '../lib/ingest';
import { LinkTypeSelectorModal } from '../components/projects/LinkTypeSelectorModal';
import { ProjectKanbanBoard } from '../components/projects/ProjectKanbanBoard';
import { ProjectTimeline } from '../components/projects/ProjectTimeline';

export function ProjectListPage() {
    const navigate = useNavigate();
    const projects = useLiveQuery(() => db.projects.toArray());
    const { performSearch, searchResults } = useProjectSearch(projects);

    // Sort & Filter State
    const [sortBy, setSortBy] = useState<'lastActive' | 'newest' | 'priority' | 'alpha'>('lastActive');
    const [filterQuery, setFilterQuery] = useState('');
    const [showTrash, setShowTrash] = useState(false);
    const [showArchived, setShowArchived] = useState(false);
    const [showSomeday, setShowSomeday] = useState(false);
    const [isDataModalOpen, setIsDataModalOpen] = useState(false);

    // View State
    const [viewMode, setViewMode] = useState<'grid' | 'list' | 'tree' | 'board' | 'timeline'>('grid');
    const [cardDensity, setCardDensity] = useState<ProjectCardDensity>('moderate');
    const [allCollapsed, setAllCollapsed] = useState(false);

    // Ingestion & Creation State
    const [isIngesting, setIsIngesting] = useState(false);
    const [isCreating, setIsCreating] = useState(false);

    // Selection State
    const [selectedIds, setSelectedIds] = useState<Set<number>>(new Set());
    const [isSelectionMode, setIsSelectionMode] = useState(false);

    // Link Request State
    const [activeLinkRequest, setActiveLinkRequest] = useState<{ sourceId: number, targetId: number } | null>(null);

    // Trigger Search
    useEffect(() => {
        performSearch(filterQuery);
    }, [filterQuery, performSearch]);

    // Listener for Global Search
    useEffect(() => {
        const handleGlobalSearch = (e: CustomEvent<string>) => {
            setFilterQuery(e.detail);
        };
        window.addEventListener('global-search', handleGlobalSearch as EventListener);
        return () => window.removeEventListener('global-search', handleGlobalSearch as EventListener);
    }, []);

    // Filter Logic
    const filteredProjects = useMemo(() => {
        let source = projects;
        if (filterQuery) {
            source = searchResults || [];
        }

        if (!source) return [];

        const filtered = source.filter(p => {
            if (showTrash) return p.deleted_at;
            if (p.deleted_at) return false;
            if (showSomeday) return (p.status as string) === 'someday';
            if ((p.status as string) === 'someday') return false; // Hide someday from regular view
            if (p.status === 'archived' && !showArchived) return false;
            return true;
        });

        return filtered.sort((a, b) => {
            if (a.sort_order !== undefined && b.sort_order !== undefined) {
                return a.sort_order - b.sort_order;
            }
            switch (sortBy) {
                case 'newest': return safeTs(b.created_at) - safeTs(a.created_at);
                case 'priority': return (b.priority || 0) - (a.priority || 0);
                case 'alpha': return a.title.localeCompare(b.title);
                case 'lastActive': default: return safeTs(b.updated_at) - safeTs(a.updated_at);
            }
        });
    }, [projects, searchResults, filterQuery, sortBy, showTrash, showArchived, showSomeday]);

    // Grouping for Tree View
    const groupedProjects = useMemo(() => {
        const groups: Record<string, Project[]> = {};
        filteredProjects.forEach(p => {
            const cat = p.category || 'Uncategorized';
            if (!groups[cat]) groups[cat] = [];
            groups[cat].push(p);
        });
        return groups;
    }, [filteredProjects]);

    // Category Collapse State
    const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});
    const toggleCategory = (cat: string) => setCollapsedCategories(prev => ({ ...prev, [cat]: !prev[cat] }));

    useMemo(() => {
        if (viewMode === 'list' || viewMode === 'tree') {
            setAllCollapsed(true);
        } else {
            setAllCollapsed(false);
        }
    }, [viewMode]);

    // --- Actions ---

    const handlePurge = async (id: number) => {
        if (!confirm("PERMANENTLY DELETE project and ALL associated data? This cannot be undone.")) return;
        try {
            await db.transaction('rw', [db.projects, db.project_files, db.project_bom, db.logs, db.project_tasks, db.notebook], async () => {
                await db.project_files.where({ project_id: id }).delete();
                await db.project_bom.where({ project_id: id }).delete();
                await db.project_tasks.where({ project_id: id }).delete();
                await db.notebook.where({ project_id: id }).delete();
                await db.logs.where({ project_id: id }).delete();
                await db.projects.delete(id);
            });
        } catch (error) {
            console.error("Purge failed:", error);
            toast.error("Failed to purge project.");
        }
    }

    const handleRestoreTrash = async (id: number) => {
        await db.projects.update(id, { deleted_at: undefined });
    }

    const handleEmptyTrash = async () => {
        const count = projects?.filter(p => p.deleted_at).length || 0;
        if (!confirm(`Permanently delete ${count} items? This cannot be undone.`)) return;
        await db.transaction('rw', [db.projects, db.project_files, db.project_bom, db.project_tasks, db.notebook, db.logs], async () => {
            const trashedProjects = await db.projects.where('deleted_at').above(new Date(0)).toArray();
            const projectIds = trashedProjects.map(p => p.id!);
            await db.projects.bulkDelete(projectIds);
        });
        toast.success("Trash emptied.");
    };

    // --- Selection & Batch Logic ---

    const toggleSelection = (id: number) => {
        const newSet = new Set(selectedIds);
        if (newSet.has(id)) newSet.delete(id);
        else newSet.add(id);
        setSelectedIds(newSet);
    };

    const handleBatchArchive = async () => {
        if (!confirm(`Archive ${selectedIds.size} projects?`)) return;
        const ids = Array.from(selectedIds);
        await db.projects.bulkUpdate(ids.map(id => ({ key: id, changes: { status: 'archived', is_archived: true } })));
        setSelectedIds(new Set());
        setIsSelectionMode(false);
    };

    const handleBatchDelete = async () => {
        if (!confirm(`Move ${selectedIds.size} projects to Trash?`)) return;
        const ids = Array.from(selectedIds);
        await db.projects.bulkUpdate(ids.map(id => ({ key: id, changes: { deleted_at: new Date() } })));
        setSelectedIds(new Set());
        setIsSelectionMode(false);
    };

    // --- Drag & Drop Linking Logic ---

    const handleDropLink = async (sourceId: number, targetId: number) => {
        if (sourceId === targetId) return;
        setActiveLinkRequest({ sourceId, targetId });
    };

    // --- Category Drag & Drop ---
    const handleDragOverCategory = (e: React.DragEvent) => {
        e.preventDefault();
        e.dataTransfer.dropEffect = 'move';
        e.currentTarget.classList.add('bg-accent/10');
    };

    const handleDragLeaveCategory = (e: React.DragEvent) => {
        e.currentTarget.classList.remove('bg-accent/10');
    };

    const handleDropOnCategory = async (e: React.DragEvent, category: string) => {
        e.preventDefault();
        e.currentTarget.classList.remove('bg-accent/10');
        const projectIdResult = e.dataTransfer.getData('application/project-id');
        if (!projectIdResult) return;
        const id = Number(projectIdResult);
        await db.projects.update(id, { category });
    };

    const handleNewCategoryDrop = async (e: React.DragEvent) => {
        e.preventDefault();
        e.currentTarget.classList.remove('bg-accent/10');
        const projectIdResult = e.dataTransfer.getData('application/project-id');
        if (!projectIdResult) return;

        const name = prompt("Enter new Category Name:");
        if (name) {
            const id = Number(projectIdResult);
            await db.projects.update(id, { category: name });
        }
    };

    // --- Render ---

    const renderProjectList = (projs: Project[]) => (
        <motion.div
            className={clsx(
                "grid gap-4 pb-32",
                viewMode === 'grid' ? (
                    cardDensity === 'compact' ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5" :
                        cardDensity === 'dense' ? "grid-cols-1 md:grid-cols-2 lg:grid-cols-3" :
                            cardDensity === 'text' ? "grid-cols-1 lg:grid-cols-2" :
                                "grid-cols-1 xl:grid-cols-2"
                ) : "grid-cols-1"
            )}
        >
            <AnimatePresence mode='popLayout' initial={false}>
                {projs.map(project => (
                    <motion.div
                        layout="position"
                        key={project.id}
                        initial={{ opacity: 0, scale: 0.95 }}
                        animate={{ opacity: 1, scale: 1 }}
                        exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.1 } }}
                        transition={{ layout: { type: "spring", bounce: 0, duration: 0.3 } }}
                    >
                        <ProjectCard
                            project={project}
                            onClick={() => {
                                if (isSelectionMode) toggleSelection(project.id!);
                                else navigate(`/projects/${project.id}`);
                            }}
                            isTrash={!!project.deleted_at}
                            onPurge={() => handlePurge(project.id!)}
                            onRestoreTrash={() => handleRestoreTrash(project.id!)}
                            collapsed={allCollapsed}
                            density={cardDensity}
                            layoutMode={viewMode === 'grid' ? 'grid' : 'list'}
                            selectable={isSelectionMode}
                            selected={selectedIds.has(project.id!)}
                            onToggleSelect={() => toggleSelection(project.id!)}
                            onDropLink={handleDropLink}
                        />
                    </motion.div>
                ))}
            </AnimatePresence>
            {!showTrash && !allCollapsed && viewMode === 'grid' && (
                <motion.div layout initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
                    <Button
                        variant="outline"
                        className="h-[200px] w-full border-dashed border-2 border-white/10 hover:border-accent/50 hover:bg-accent/5 gap-4 flex flex-col items-center justify-center text-gray-500 hover:text-accent transition-all group"
                        onClick={() => setIsCreating(true)}
                    >
                        <Plus size={48} className="text-gray-700 group-hover:text-accent group-hover:scale-110 transition-transform" />
                        <span className="font-mono uppercase tracking-widest text-xs">Initialize New Node</span>
                    </Button>
                </motion.div>
            )}
        </motion.div>
    );

    return (
        <div className="flex flex-col h-full gap-6 relative overflow-hidden">
            {isCreating && <CreateProjectModal onClose={() => setIsCreating(false)} />}
            {activeLinkRequest && (
                <LinkTypeSelectorModal
                    sourceId={activeLinkRequest.sourceId}
                    targetId={activeLinkRequest.targetId}
                    onClose={() => setActiveLinkRequest(null)}
                    onComplete={() => setActiveLinkRequest(null)}
                />
            )}

            {/* Header Toolbar */}
            <div className="flex justify-between items-center z-10 relative border-b border-white/10 pb-6 flex-wrap gap-4">
                <h1 className="text-3xl font-black uppercase tracking-tighter flex items-center gap-3">
                    {showTrash ? <Trash2 className="text-red-500" /> : <LayoutGrid className="text-accent" />}
                    {showTrash ? 'Trash Bin' : 'Project Array'}
                    <span className="text-sm font-mono text-gray-500 ml-2 mt-2 opacity-50">{filteredProjects.length} NODES</span>
                </h1>

                <div className="flex gap-4 items-center flex-wrap">
                    <div className="flex gap-2">
                        <Button
                            variant="ghost"
                            size="sm"
                            title="Toggle Batch Selection"
                            onClick={() => {
                                setIsSelectionMode(!isSelectionMode);
                                setSelectedIds(new Set());
                            }}
                            className={clsx(isSelectionMode ? "bg-accent/20 text-accent border-accent" : "text-gray-500 hover:text-white")}
                        >
                            {isSelectionMode ? <CheckSquare size={16} /> : <Square size={16} />}
                        </Button>

                        <Button
                            variant="primary"
                            size="sm"
                            className="bg-accent text-black hover:bg-white border-none font-bold"
                            onClick={() => setIsCreating(true)}
                        >
                            <Plus size={16} className="mr-1" /> NEW
                        </Button>
                        <Button
                            variant="outline"
                            size="sm"
                            title="Ingest Document or Restore Backup"
                            disabled={isIngesting}
                            onClick={() => {
                                const input = document.createElement('input');
                                input.type = 'file';
                                input.accept = '.json,.pdf,.txt,.md,image/*';
                                input.onchange = async (e) => {
                                    const file = (e.target as HTMLInputElement).files?.[0];
                                    if (!file) return;

                                    try {
                                        setIsIngesting(true);
                                        const newId = await IngestionService.ingestFile(file);
                                        navigate(`/projects/${newId}`);
                                    } catch (err) {
                                        console.error(err);
                                        toast.error("Ingestion Failed: " + (err as Error).message);
                                    } finally {
                                        setIsIngesting(false);
                                    }
                                };
                                input.click();
                            }}
                        >
                            {isIngesting ? <Loader2 size={16} className="animate-spin mr-1" /> : <Upload size={16} className="mr-1" />}
                            {isIngesting ? 'ANALYZING...' : 'INGEST'}
                        </Button>
                    </div>

                    <div className="h-6 w-px bg-white/10 mx-2" />

                    {/* View Controls */}
                    <div className="flex bg-white/5 rounded border border-white/10 p-0.5">
                        <button onClick={() => setViewMode('grid')} className={clsx("p-1.5 rounded-sm transition-colors", viewMode === 'grid' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Grid View"><LayoutGrid size={16} /></button>
                        <button onClick={() => setViewMode('list')} className={clsx("p-1.5 rounded-sm transition-colors", viewMode === 'list' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="List View"><List size={16} /></button>
                        <button onClick={() => setViewMode('tree')} className={clsx("p-1.5 rounded-sm transition-colors", viewMode === 'tree' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Tree View"><Layers size={16} /></button>
                        <button onClick={() => setViewMode('board')} className={clsx("p-1.5 rounded-sm transition-colors", viewMode === 'board' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Kanban Board"><Square size={16} /></button>
                        <button onClick={() => setViewMode('timeline')} className={clsx("p-1.5 rounded-sm transition-colors", viewMode === 'timeline' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Timeline View"><Clock size={16} /></button>
                    </div>

                    <div className="h-6 w-px bg-white/10 mx-2" />

                    {/* Density Controls */}
                    <div className="flex bg-white/5 rounded border border-white/10 p-0.5">
                        <button onClick={() => setCardDensity('compact')} className={clsx("p-1.5 rounded-sm transition-colors", cardDensity === 'compact' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Compact (Mobile)"><Smartphone size={16} /></button>
                        <button onClick={() => setCardDensity('moderate')} className={clsx("p-1.5 rounded-sm transition-colors", cardDensity === 'moderate' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Moderate (Default)"><LayoutGrid size={16} /></button>
                        <button onClick={() => setCardDensity('text')} className={clsx("p-1.5 rounded-sm transition-colors", cardDensity === 'text' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Text (Solo Aero)"><Rows size={16} /></button>
                        <button onClick={() => setCardDensity('dense')} className={clsx("p-1.5 rounded-sm transition-colors", cardDensity === 'dense' ? "bg-white text-black" : "text-gray-500 hover:text-white")} title="Dense (Enterprise)"><Grid3x3 size={16} /></button>
                    </div>

                    <Button variant="ghost" size="sm" onClick={() => setAllCollapsed(!allCollapsed)} className="border border-white/10 text-gray-500 hover:text-white w-9 p-0" title={allCollapsed ? "Expand All" : "Collapse All"}>
                        {allCollapsed ? <Maximize2 size={16} /> : <Minimize2 size={16} />}
                    </Button>

                    <div className="h-6 w-px bg-white/10 mx-2" />

                    <div className="flex bg-white/5 rounded border border-white/10 p-0.5">
                        {[
                            { id: 'lastActive', label: 'ACTV' },
                            { id: 'newest', label: 'NEW' },
                            { id: 'priority', label: 'PRIO' },
                            { id: 'alpha', label: 'A-Z' },
                        ].map(s => (
                            <button
                                key={s.id}
                                onClick={() => setSortBy(s.id as 'lastActive' | 'newest' | 'priority' | 'alpha')}
                                className={clsx(
                                    "px-3 py-1 text-[10px] font-bold uppercase transition-all rounded-sm",
                                    sortBy === s.id ? "bg-white text-black" : "text-gray-500 hover:text-white"
                                )}
                            >
                                {s.label}
                            </button>
                        ))}
                    </div>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsDataModalOpen(true)}
                        className="border border-white/10 text-gray-500 hover:text-white"
                        title="Database Management"
                    >
                        <Database size={16} />
                    </Button>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowArchived(!showArchived)}
                        className={clsx("border border-dashed transition-colors", showArchived ? "border-yellow-500 text-yellow-500" : "border-white/10 hover:border-white/30 text-gray-500")}
                        title="Toggle Archived Projects"
                    >
                        {showArchived ? "ACTIVE" : <Archive size={16} />}
                    </Button>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => {
                            setShowSomeday(!showSomeday);
                            if (!showSomeday) {
                                setShowTrash(false);
                                setShowArchived(false);
                            }
                        }}
                        className={clsx("border border-dashed transition-colors", showSomeday ? "border-purple-500 text-purple-500" : "border-white/10 hover:border-white/30 text-gray-500")}
                        title="Show Someday/Maybe Projects"
                    >
                        {showSomeday ? "ACTIVE" : <Clock size={16} />}
                    </Button>

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setShowTrash(!showTrash)}
                        className={clsx("border border-dashed transition-colors", showTrash ? "border-red-500 text-red-500" : "border-white/10 hover:border-white/30 text-gray-500")}
                    >
                        {showTrash ? "ACTIVE" : <Trash2 size={16} />}
                    </Button>
                    {showTrash && (
                        <Button
                            variant="danger"
                            size="sm"
                            onClick={handleEmptyTrash}
                            className="bg-red-900/50 hover:bg-red-900 border border-red-500/50"
                        >
                            <Trash2 size={16} className="mr-2" /> EMPTY BIN
                        </Button>
                    )}
                </div>
            </div>

            {isDataModalOpen && <DataManagementModal onClose={() => setIsDataModalOpen(false)} />}

            <div className="flex-1 overflow-y-auto pr-2 flex flex-col gap-6 relative">
                {selectedIds.size > 0 && (
                    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 bg-neutral-900 border border-white/20 shadow-2xl rounded-full px-6 py-3 z-50 flex items-center gap-6 animate-in slide-in-from-bottom-10 fade-in data-[state=open]:animate-in">
                        <span className="font-mono font-bold text-accent">{selectedIds.size} SELECTED</span>
                        <div className="h-4 w-px bg-white/20" />
                        <button onClick={handleBatchArchive} className="flex items-center gap-2 hover:text-white text-gray-400 transition-colors uppercase text-xs font-bold"><Archive size={14} /> Archive</button>
                        <button onClick={() => toast.info("Tag editing coming soon!")} className="flex items-center gap-2 hover:text-white text-gray-400 transition-colors uppercase text-xs font-bold"><Database size={14} /> Tag</button>
                        <button onClick={handleBatchDelete} className="flex items-center gap-2 hover:text-red-400 text-gray-400 transition-colors uppercase text-xs font-bold"><Trash2 size={14} /> Delete</button>
                        <div className="h-4 w-px bg-white/20" />
                        <button onClick={() => setSelectedIds(new Set())} className="hover:text-white text-gray-500"><X size={16} /></button>
                    </div>
                )}

                {viewMode === 'board' ? (
                    <ProjectKanbanBoard />
                ) : viewMode === 'timeline' ? (
                    <ProjectTimeline />
                ) : viewMode === 'tree' ? (
                    <div className="space-y-8 pb-32">
                        {Object.entries(groupedProjects).map(([category, projs]) => (
                            <div key={category} className="space-y-4">
                                <h2
                                    onClick={() => toggleCategory(category)}
                                    // Make header droppable
                                    onDragOver={handleDragOverCategory}
                                    onDragLeave={handleDragLeaveCategory}
                                    onDrop={(e) => handleDropOnCategory(e, category)}
                                    className="flex items-center gap-2 text-accent font-mono text-sm uppercase tracking-widest border-b border-accent/20 pb-2 cursor-pointer hover:text-white transition-colors select-none w-full hover:bg-white/5 rounded p-2"
                                >
                                    {collapsedCategories[category] ? <ChevronRight size={14} /> : <ChevronDown size={14} />}
                                    <Folder size={14} /> {category} <span className="text-gray-600 text-[10px]">({projs.length})</span>
                                </h2>
                                {!collapsedCategories[category] && renderProjectList(projs)}
                            </div>
                        ))}

                        <div
                            onDragOver={handleDragOverCategory}
                            onDragLeave={handleDragLeaveCategory}
                            onDrop={handleNewCategoryDrop}
                            className="border-2 border-dashed border-white/10 rounded-xl p-8 flex flex-col items-center justify-center text-gray-500 hover:border-accent hover:text-accent transition-all cursor-copy"
                        >
                            <Folder size={32} className="mb-2" />
                            <span className="font-bold text-xs uppercase tracking-widest">Drag here to Create New Category</span>
                        </div>
                    </div>
                ) : (
                    renderProjectList(filteredProjects)
                )}
            </div>
        </div>
    );
}
