import { useState } from 'react';
import { useParams, useNavigate, useSearchParams } from 'react-router-dom';
import { toast } from 'sonner';
import { useFormPersistence } from '../hooks/useFormPersistence';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { useUIStore } from '../store/useStore';
import { AIService } from '../lib/AIService';
import { PortfolioService } from '../lib/portfolio';
import { VaultService } from '../services/VaultService';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Input } from '../components/ui/Input';

import clsx from 'clsx';
import { ProjectTasks } from '../components/ProjectTasks';
import { ProjectBOM } from '../components/ProjectBOM';
import { ProjectChangelog } from '../components/ProjectChangelog';
import { ProjectNotebook } from '../components/ProjectNotebook';
import { ProjectManuscript } from '../components/ProjectManuscript';
import { ProjectProduction } from '../components/ProjectProduction';

import { ProjectSpecs } from '../components/projects/ProjectSpecs';
import { VoiceMemoManager } from '../components/projects/VoiceMemoManager';
import { ProjectBlueprint } from '../components/ProjectBlueprint';
import { ProjectScripts } from '../components/ProjectScripts';
import { ProjectTools } from '../components/projects/ProjectTools';
import { ProjectAssets } from '../components/projects/ProjectAssets';
import { ProjectSafetyQA } from '../components/projects/ProjectSafetyQA';
import { HAZARD_DEFS } from '../lib/safety';
import { type HazardClass } from '../lib/db';
import { UploadConfirmationModal } from '../components/UploadConfirmationModal';
import { RatingBar } from '../components/ui/RatingBar';
import { safeDateStr, safeDateDisplay, safeArr, safeStr } from '../lib/utils';
import { FileText, ChevronLeft, Pencil, ListTodo, Cpu, Book, Settings, Zap, History as HistoryIcon, Clock, DollarSign, Upload, LayoutGrid, X, AlertTriangle, Save, Loader2, Sliders, Layers, Link as LinkIcon, Box, Code, Target, Printer, Shield, Wrench, FileType, Clapperboard, Eye, EyeOff } from 'lucide-react';
import { motion } from 'framer-motion';
import { ThreeViewer } from '../components/ui/ThreeViewer';
import { ReferencesPanel } from '../components/ui/ReferencesPanel';

import { AssetCard } from '../components/assets/AssetCard';
import { useDroppable } from '@dnd-kit/core';
import { PrintPartsManager } from '../components/projects/PrintPartsManager';

type Tab = 'overview' | 'tasks' | 'tools' | 'bom' | 'manuscript' | 'production' | 'notebook' | 'changelog' | 'specs' | 'blueprint' | 'code' | 'assets' | 'printing' | 'safety_qa';

const isImage = (file: { name: string, type: string }) => {
    return file.type.startsWith('image/') || /\.(jpg|jpeg|png|gif|webp)$/i.test(file.name);
};

// ... imports

export function ProjectDetail() {
    const { id } = useParams();
    const navigate = useNavigate();
    const projectId = Number(id);

    const project = useLiveQuery(() => db.projects.get(projectId), [projectId]);
    const activeGoals = useLiveQuery(() => db.goals.where('status').equals('active').toArray());

    const files = useLiveQuery(() => db.project_files.where({ project_id: projectId }).toArray());

    // Fetch Linked Projects
    const linkedProjects = useLiveQuery(async () => {
        if (!project) return { upstream: [], downstream: [], related: [] };

        // Upstream: Projects that BLOCK this one (in upstream_dependencies)
        const upstreamIds = project.upstream_dependencies || [];
        const upstream = await db.projects.where('id').anyOf(upstreamIds).toArray();

        // Downstream: Projects BLOCKED BY this one (where upstream_dependencies contains projectId)
        // Dexie doesn't have a simple array 'contains' query index without custom index, but we can filter or use basic where clause if indexed 'upstream_dependencies' is MultiEntry
        const downstream = await db.projects.where('upstream_dependencies').equals(projectId).toArray();

        // Related: Mutual links (related_projects contains projectId OR id is in project.related_projects)
        const relatedIds = project.related_projects || [];
        const relatedDirect = await db.projects.where('id').anyOf(relatedIds).toArray();
        const relatedReverse = await db.projects.where('related_projects').equals(projectId).toArray();

        // Merge related (and dedup if necessary, though logic should prevent dupes)
        const relatedMap = new Map();
        relatedDirect.forEach(p => relatedMap.set(p.id, p));
        relatedReverse.forEach(p => relatedMap.set(p.id, p));

        return {
            upstream,
            downstream,
            related: Array.from(relatedMap.values())
        };
    }, [project]) || { upstream: [], downstream: [], related: [] };

    const [searchParams, setSearchParams] = useSearchParams();
    const activeTab = (searchParams.get('tab') as Tab) || 'overview';
    const setActiveTab = (tab: Tab) => setSearchParams({ tab }, { replace: true });

    const { isIngesting } = useUIStore();

    const [pendingUpload, setPendingUpload] = useState<{ file: File, extraction: Record<string, any> } | null>(null);
    const [uploadFile, setUploadFile] = useState<File | null>(null); // Moved to top level


    // --- Edit Mode State ---
    const [isEditing, setIsEditing] = useState(false);
    const [editForm, setEditForm, clearDraft] = useFormPersistence<Record<string, any>>(`project_draft_${projectId}`, {});
    const [editSpecs, setEditSpecs] = useState('');
    const [editTags, setEditTags] = useState('');
    const [editLinks, setEditLinks] = useState<Array<{ label: string; url: string }>>([]);
    const [editHiddenTabs, setEditHiddenTabs] = useState<string[]>([]); // New state for hidden tabs
    const [hoveredImage, setHoveredImage] = useState<{ url: string, x: number, y: number } | null>(null);



    // --- Tab Navigation Component ---
    // ... (inside ProjectDetail)

    // --- TAB CONFIGURATION ---
    // Logical Order: Overview -> Planning (Tasks, Specs, Blueprint, BOM) -> Prep (Tools, Safety) -> Execution (Printing, Code) -> Data (Assets, Notebook) -> History
    const TABS = [
        { id: 'overview' as const, label: 'Overview', icon: LayoutGrid },
        { id: 'manuscript' as const, label: 'Manuscript', icon: FileType },
        { id: 'production' as const, label: 'Production', icon: Clapperboard },
        { id: 'tasks' as const, label: 'Tasks', icon: ListTodo },
        { id: 'specs' as const, label: 'Specs', icon: Sliders },
        { id: 'blueprint' as const, label: 'Blueprint', icon: Layers },
        { id: 'bom' as const, label: 'Procurement', icon: DollarSign },
        { id: 'tools' as const, label: 'Tools', icon: Wrench },
        { id: 'safety_qa' as const, label: 'Safety & QA', icon: Shield },
        { id: 'printing' as const, label: 'Fabrication', icon: Printer },
        { id: 'code' as const, label: 'Code', icon: Code },
        { id: 'assets' as const, label: 'Assets', icon: Box },
        { id: 'notebook' as const, label: 'Notebook', icon: Book },
        { id: 'changelog' as const, label: 'Changelog', icon: HistoryIcon },
    ];

    // --- Tab Navigation Component ---
    const TabNav = () => {
        const visibleTabs = TABS.filter(t => !project?.settings?.hidden_tabs?.includes(t.id));
        return (
            <div className="grid grid-cols-3 md:grid-cols-4 lg:grid-cols-6 gap-2 mb-6">
                {visibleTabs.map(tab => (
                    <button
                        key={tab.id}
                        onClick={() => setActiveTab(tab.id as Tab)}
                        className={clsx(
                            "flex items-center justify-center gap-2 px-3 py-3 text-[10px] sm:text-xs font-bold uppercase tracking-wider transition-all rounded border border-transparent",
                            activeTab === tab.id
                                ? "bg-accent text-black border-accent shadow-lg shadow-accent/20"
                                : "bg-white/5 text-gray-500 border-white/5 hover:bg-white/10 hover:text-white hover:border-white/10"
                        )}
                    >
                        <tab.icon size={14} strokeWidth={activeTab === tab.id ? 2.5 : 2} />
                        <span className="truncate">{tab.label}</span>
                    </button>
                ))}
            </div>
        );
    };

    if (!project) return (
        <div className="flex items-center justify-center h-full bg-black text-white font-mono uppercase tracking-widest animate-pulse">
            Establishing Secure Link...
        </div>
    );

    const startEditing = () => {
        // Check for existing draft
        if (editForm && editForm.title) {
            const useDraft = confirm("Unsaved draft found. Resume editing?");
            if (useDraft) {
                // Draft already loaded by hook
                setEditSpecs(safeArr(project.io_spec).join(', '));
                setEditTags(safeArr(project.tags).join(', '));
                setEditLinks(project.external_links || []);
                setIsEditing(true);
                return;
            }
        }

        // Seed from DB
        setEditForm({
            title: project.title,
            status: project.status,
            version: project.version,
            priority: project.priority || 3,
            description: project.status_description || '',
            role: project.role || '',
            category: project.category || '',
            intrusiveness: project.intrusiveness || 1,
            estHours: project.total_theorized_hours || 0,
            targetDate: safeDateStr(project.target_completion_date),
            goldenVoltages: project.golden_voltages || '',
            // v16
            projectCode: project.project_code || '',
            designStatus: project.design_status || 'idea',
            buildStatus: project.build_status || 'unbuilt',
            expCvUsage: project.exp_cv_usage || '',
            // v17
            timeActive: project.time_estimate_active || 0,
            timePassive: project.time_estimate_passive || 0,
            budget: project.financial_budget || 0,
            spend: project.financial_spend || 0,
            rationale: project.rationale || '',
            riskLevel: project.risk_level || 'low',
            // v38 Safety
            hazards: project.safety_data?.hazards || [],
            controls: project.safety_data?.controls || [],
            // v42 Goal
            goalId: project.goal_id
        });
        setEditSpecs(safeArr(project.io_spec).join(', '));
        setEditTags(safeArr(project.tags).join(', '));
        setEditLinks(project.external_links || []);
        setEditHiddenTabs(project.settings?.hidden_tabs || []);
        setIsEditing(true);
    };

    const handleSave = async () => {
        if (!editForm) return;
        try {
            await db.projects.update(projectId, {
                title: editForm.title,
                status: editForm.status,
                version: editForm.version,
                priority: Number(editForm.priority),
                status_description: editForm.description,
                role: editForm.role,
                category: editForm.category,
                intrusiveness: Number(editForm.intrusiveness),
                total_theorized_hours: Number(editForm.estHours),
                target_completion_date: editForm.targetDate ? new Date(editForm.targetDate) : undefined,
                golden_voltages: editForm.goldenVoltages,
                goal_id: editForm.goalId,
                // v16
                project_code: editForm.projectCode,
                design_status: editForm.designStatus,
                build_status: editForm.buildStatus,
                exp_cv_usage: editForm.expCvUsage,
                // v17
                time_estimate_active: Number(editForm.timeActive),
                time_estimate_passive: Number(editForm.timePassive),
                financial_budget: Number(editForm.budget),
                financial_spend: Number(editForm.spend),
                rationale: editForm.rationale,
                risk_level: editForm.riskLevel,
                external_links: editLinks.filter(l => l.label && l.url),
                io_spec: editSpecs.split(',').map(s => s.trim()).filter(Boolean),
                tags: editTags.split(',').map(t => t.trim()).filter(Boolean),
                updated_at: new Date(),
                safety_data: {
                    hazards: editForm.hazards,
                    controls: editForm.controls,
                    is_ready: (editForm.hazards || []).length === 0 ? true : (editForm.controls || []).every((c: any) => c.is_checked)
                },
                settings: {
                    hidden_tabs: editHiddenTabs
                }
            });
            await VaultService.syncProject(projectId); // Sync to Vault
            clearDraft(); // Clear persistence
            setIsEditing(false);
        } catch (e) {
            console.error(e);
            toast.error("Save failed.");
        }
    };

    const updateForm = (field: string, value: any) => {
        setEditForm((prev: Record<string, any>) => ({ ...prev, [field]: value }));
    };

    const quickUpdate = async (field: string, value: any) => {
        try {
            await db.projects.update(projectId, { [field]: value });
        } catch (e) { console.error(e); }
    };

    const toggleEditHazard = (hazard: HazardClass) => {
        setEditForm(prev => {
            const currentHazards = prev.hazards || [];
            const currentControls = prev.controls || [];
            const newHazards = currentHazards.includes(hazard)
                ? currentHazards.filter((h: string) => h !== hazard)
                : [...currentHazards, hazard];

            let newControls = [...currentControls];

            if (newHazards.includes(hazard)) {
                // Add missing controls
                const defs = HAZARD_DEFS[hazard].controls;
                defs.forEach((desc: string) => {
                    if (!newControls.find((c: any) => c.hazard === hazard && c.description === desc)) {
                        newControls.push({
                            id: crypto.randomUUID(),
                            hazard,
                            description: desc,
                            is_checked: false
                        });
                    }
                });
            } else {
                // Remove controls
                newControls = newControls.filter((c: any) => newHazards.includes(c.hazard));
            }

            return { ...prev, hazards: newHazards, controls: newControls };
        });
    };

    // --- File Upload Logic ---


    const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) setUploadFile(file);
    };

    const runAnalysis = async () => {
        if (!uploadFile) return;
        setUploadFile(null); // Close pre-modal
        const { setIngesting } = useUIStore.getState();
        setIngesting(true, `Analyzing ${uploadFile.name}...`);

        try {
            let extraction: Record<string, any> = {};
            if (localStorage.getItem('GEMINI_API_KEY')) {
                extraction = await AIService.analyzeFile(uploadFile);
            }
            setPendingUpload({ file: uploadFile, extraction }); // Triggers the review modal
        } catch (err) {
            console.error(err);
            toast.error('AI Analysis Failed.');
            setIngesting(false);
        }
    };

    const runDirectUpload = async () => {
        if (!uploadFile) return;
        try {
            await db.project_files.add({
                project_id: projectId,
                name: uploadFile.name,
                type: uploadFile.type,
                content: uploadFile,
                created_at: new Date(),
                extracted_metadata: {}
            });
            toast.success("Asset uploaded!");
        } catch (e) {
            console.error(e);
            toast.error("Upload failed.");
        } finally {
            setUploadFile(null);
        }
    };

    const confirmUpload = async (isNewest: boolean) => {
        if (!pendingUpload) return;
        const { file, extraction } = pendingUpload;
        try {
            await db.transaction('rw', [db.projects, db.project_files, db.project_bom, db.logs, db.project_tasks, db.notebook], async () => {
                await db.project_files.add({
                    project_id: projectId,
                    name: file.name,
                    type: file.type,
                    content: file,
                    created_at: new Date(),
                    extracted_metadata: extraction
                });

                if (isNewest) {
                    const existing = await db.projects.get(projectId);
                    if (existing) {
                        const updates = PortfolioService.mergeProject(existing, extraction);

                        // Force manual description update if requested
                        if (extraction.description) updates.status_description = extraction.description;
                        if (extraction.version) updates.version = extraction.version;

                        // v20 MDBD
                        if (extraction.universal_map) updates.universal_data = extraction.universal_map;

                        await db.projects.update(projectId, updates);

                        // --- TASKS INGESTION ---
                        if (extraction.tasks && Array.isArray(extraction.tasks)) {
                            // We choose to APPEND new tasks. 
                            // Future improvement: Detect specific duplicates or replace "Auto-generated" ones.
                            const newTasks = extraction.tasks.map((t: any) => ({
                                project_id: projectId,
                                title: typeof t === 'string' ? t : t.title || 'Untitled Task',
                                status: 'pending',
                                priority: typeof t === 'object' ? (t.priority || 3) : 3,
                                created_at: new Date()
                            }));
                            if (newTasks.length > 0) await db.project_tasks.bulkAdd(newTasks as any);
                        }

                        // --- BOM INGESTION ---
                        if (extraction.bom && Array.isArray(extraction.bom)) {
                            const newBom = extraction.bom.map((b: any) => ({
                                project_id: projectId,
                                part_name: typeof b === 'string' ? b : b.name || 'Unknown Part',
                                status: 'missing',
                                quantity_required: typeof b === 'object' ? (b.quantity || 1) : 1,
                                est_unit_cost: typeof b === 'object' ? b.est_unit_cost : undefined
                            }));
                            if (newBom.length > 0) await db.project_bom.bulkAdd(newBom as any);
                        }
                    }
                }

                // Ingest Changelog History
                if (extraction.changelog_history && Array.isArray(extraction.changelog_history)) {
                    await db.logs.bulkAdd(extraction.changelog_history.map((c: any) => {
                        let parsedDate = new Date();
                        if (c.date) {
                            const d = new Date(c.date);
                            if (!isNaN(d.getTime())) parsedDate = d;
                        }
                        return {
                            project_id: projectId,
                            version: c.version || 'v1.0',
                            date: parsedDate,
                            summary: c.summary || 'Imported from document',
                            type: 'auto'
                        };
                    }));
                }
            });
        } catch (err) {
            console.error(err);
            toast.error("Sync Failed.");
        } finally {
            setPendingUpload(null);
            useUIStore.getState().setIngesting(false);
        }
    };

    const openFile = (file: Blob) => {
        const url = URL.createObjectURL(file);
        window.open(url, '_blank');
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: "easeOut" }}
            className="space-y-4 flex flex-col h-full relative overflow-auto"
        >
            {/* Header */}
            <div className="flex flex-col gap-2 border-b border-white/10 pb-3">
                <div className="flex justify-between items-center">
                    <Button variant="ghost" size="sm" className="w-fit -ml-2 text-gray-400 hover:text-white" onClick={() => navigate('/projects')}>
                        <ChevronLeft size={16} className="mr-1" /> BACK TO LIBRARY
                    </Button>
                    <div className="flex gap-2">
                        <Button variant="outline" size="sm" onClick={startEditing} className="border-accent text-accent hover:bg-accent hover:text-black">
                            <Pencil size={14} className="mr-2" /> EDIT PROJECT
                        </Button>
                    </div>
                </div>

                <div className="flex justify-between items-start flex-wrap gap-4">
                    <div className="flex-1">
                        <div className="flex items-center gap-2 mb-0.5">
                            <span className={clsx("text-xs font-mono border px-1",
                                (project.status || 'active') === 'active' ? 'text-accent border-accent' : 'text-gray-500 border-gray-500'
                            )}>{safeStr(project.status).toUpperCase()}</span>
                            <span className="text-xs font-mono text-accent font-bold">{project.project_code || `P - ${project.id} `}</span>
                            <span className="text-xs font-mono text-gray-400 opacity-50">v{safeStr(project.version)}</span>
                        </div>
                        <h1 className="text-3xl font-black uppercase tracking-tighter text-white mb-1">{safeStr(project.title)}</h1>
                        {project.role && <p className="text-accent font-mono text-sm underline decoration-dotted mb-1">{safeStr(project.role)}</p>}

                        {/* Hazards Display (v19) - Filtered */}
                        {project.hazards && project.hazards.length > 0 && (
                            <div className="flex flex-wrap gap-2 mt-2">
                                {project.hazards
                                    .filter((h: string) => {
                                        const lower = h.toLowerCase();
                                        // Filter out 'minor' hazards that don't need flashing warnings
                                        const ignored = [
                                            'low voltage', 'small parts', 'sharp edges', 'dust', 'fumes',
                                            'soldering', 'pinchers', 'splinters', 'noise', 'handling'
                                        ];
                                        return !ignored.some(i => lower.includes(i));
                                    })
                                    .map((h: string, i: number) => (
                                        <span key={i} className="flex items-center gap-1.5 px-2 py-1 bg-red-900/50 border border-red-500 text-red-100 text-[10px] font-bold uppercase rounded animate-pulse">
                                            <AlertTriangle size={12} className="text-red-500" />
                                            {h}
                                        </span>
                                    ))
                                }
                            </div>
                        )}
                    </div>

                    <div className="w-full mt-4">
                        <TabNav />
                    </div>
                </div>
            </div>

            {/* Content Area */}
            <div className="flex-1">
                {isEditing ? (
                    <Card className="max-w-4xl mx-auto p-6 space-y-6 border-accent/20 bg-white/5 animate-in fade-in slide-in-from-bottom-4 duration-300">
                        <div className="flex justify-between items-center border-b border-white/10 pb-4">
                            <h2 className="text-xl font-bold font-mono text-accent flex items-center gap-2">
                                <Settings size={20} /> EDIT CONFIGURATION
                            </h2>
                            <Button variant="ghost" onClick={() => setIsEditing(false)}><X size={20} /></Button>
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <div className="col-span-2 grid grid-cols-4 gap-4">
                                <div className="space-y-1 col-span-1">
                                    <label className="text-xs text-gray-500 font-bold uppercase">Project Code</label>
                                    <Input value={editForm.projectCode} onChange={e => updateForm('projectCode', e.target.value)} className="font-mono text-accent border-accent/30" placeholder={`P - ${project.id} `} />
                                </div>
                                <div className="space-y-1 col-span-3">
                                    <label className="text-xs text-gray-500 font-bold uppercase">Project Title</label>
                                    <Input value={editForm.title} onChange={e => updateForm('title', e.target.value)} className="font-bold text-lg" />
                                </div>
                                <div className="space-y-1 col-span-4">
                                    <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2">
                                        <Target size={12} /> Life Goal Alignment
                                    </label>
                                    <select
                                        className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white focus:border-accent outline-none"
                                        value={editForm.goalId || ''}
                                        onChange={e => updateForm('goalId', e.target.value ? Number(e.target.value) : undefined)}
                                    >
                                        <option value="">-- No Specific Goal --</option>
                                        {activeGoals?.map(g => (
                                            <option key={g.id} value={g.id}>{g.title}</option>
                                        ))}
                                    </select>
                                </div>
                            </div>

                            {/* NEW: Planning Inputs */}
                            <div className="col-span-2 grid grid-cols-2 gap-6 bg-white/5 p-4 rounded border border-white/10">
                                <div className="col-span-2">
                                    <label className="text-xs text-gray-500 font-bold uppercase">Rationale / Motivation</label>
                                    <textarea
                                        className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white focus:border-accent outline-none min-h-[60px]"
                                        value={editForm.rationale}
                                        onChange={e => updateForm('rationale', e.target.value)}
                                        placeholder="Why are we building this? (e.g. Relationship stress, safety)"
                                    />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2"><Clock size={12} /> Est. Active Hours</label>
                                    <Input type="number" value={editForm.timeActive} onChange={e => updateForm('timeActive', e.target.value)} />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2"><Clock size={12} /> Est. Passive Hours</label>
                                    <Input type="number" value={editForm.timePassive} onChange={e => updateForm('timePassive', e.target.value)} />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2"><DollarSign size={12} /> Budget ($)</label>
                                    <Input type="number" value={editForm.budget} onChange={e => updateForm('budget', e.target.value)} />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2"><DollarSign size={12} /> Actual Spend ($)</label>
                                    <Input type="number" value={editForm.spend} onChange={e => updateForm('spend', e.target.value)} />
                                </div>
                                <div className="space-y-1">
                                    <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2"><AlertTriangle size={12} /> Risk Level</label>
                                    <select
                                        className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white focus:border-accent outline-none"
                                        value={editForm.riskLevel}
                                        onChange={e => updateForm('riskLevel', e.target.value)}
                                    >
                                        <option value="low">Low</option>
                                        <option value="medium">Medium</option>
                                        <option value="high">High</option>
                                    </select>
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Version</label>
                                <Input value={editForm.version} onChange={e => updateForm('version', e.target.value)} />
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Status (Lifecycle)</label>
                                <select
                                    className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white focus:border-accent outline-none"
                                    value={editForm.status}
                                    onChange={e => updateForm('status', e.target.value)}
                                >
                                    <option value="active">Active</option>
                                    <option value="on-hold">On Hold</option>
                                    <option value="completed">Completed</option>
                                    <option value="archived">Archived</option>
                                </select>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Design Status</label>
                                <select
                                    className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white focus:border-accent outline-none"
                                    value={editForm.designStatus}
                                    onChange={e => updateForm('designStatus', e.target.value)}
                                >
                                    <option value="idea">Idea</option>
                                    <option value="draft">Draft (MDBD)</option>
                                    <option value="full">Full (MDBD)</option>
                                    <option value="frozen">Frozen</option>
                                </select>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Build Status</label>
                                <select
                                    className="w-full bg-black border border-white/20 rounded p-2 text-sm text-white focus:border-accent outline-none"
                                    value={editForm.buildStatus}
                                    onChange={e => updateForm('buildStatus', e.target.value)}
                                >
                                    <option value="unbuilt">Unbuilt</option>
                                    <option value="wip">WIP</option>
                                    <option value="boxed">Boxed</option>
                                    <option value="finished">Finished</option>
                                </select>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2">
                                    <Zap size={12} /> Priority (Click to Set)
                                </label>
                                <RatingBar
                                    value={editForm.priority}
                                    onChange={(v) => updateForm('priority', v)}
                                    activeColor="bg-red-600"
                                />
                                <div className="flex justify-between text-[9px] text-gray-600 font-mono uppercase">
                                    <span>Low</span>
                                    <span>Critical</span>
                                </div>
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase flex items-center gap-2">
                                    <AlertTriangle size={12} /> Intrusiveness (Click to Set)
                                </label>
                                <RatingBar
                                    value={editForm.intrusiveness}
                                    onChange={(v) => updateForm('intrusiveness', v)}
                                    activeColor="bg-accent"
                                />
                                <div className="flex justify-between text-[9px] text-gray-600 font-mono uppercase">
                                    <span>Minimal</span>
                                    <span>Disruptive</span>
                                </div>
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Context / Role</label>
                                <Input value={editForm.role} onChange={e => updateForm('role', e.target.value)} placeholder="e.g. Living room table repair" />
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Category / Domain</label>
                                <Input value={editForm.category} onChange={e => updateForm('category', e.target.value)} placeholder="e.g. Home Improvement, Electronics, Art" />
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Mission Brief (Description)</label>
                                <textarea
                                    className="w-full bg-black border border-white/20 rounded p-3 text-sm text-white focus:border-accent outline-none font-mono min-h-[100px]"
                                    value={editForm.description}
                                    onChange={e => updateForm('description', e.target.value)}
                                    placeholder="Describe the project goals, rationale, and scope..."
                                />
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Est. Active Hours</label>
                                <Input type="number" value={editForm.estHours} onChange={e => updateForm('estHours', e.target.value)} />
                            </div>

                            <div className="space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Target Date</label>
                                <Input type="date" value={editForm.targetDate} onChange={e => updateForm('targetDate', e.target.value)} />
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Key Specifications (Comma Separated)</label>
                                <Input value={editSpecs} onChange={e => setEditSpecs(e.target.value)} placeholder="e.g. 12V DC, Walnut Stain, 500GB, Drought Resistant" />
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Reference Notes / Key Data</label>
                                <textarea
                                    className="w-full bg-black border border-green-900/50 rounded p-3 text-sm text-green-500 focus:border-green-500 outline-none font-mono min-h-[80px]"
                                    value={editForm.goldenVoltages}
                                    onChange={e => updateForm('goldenVoltages', e.target.value)}
                                    placeholder="Critical reference values, dimensions, dry times, or notes..."
                                />
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Interaction / Operational Notes</label>
                                <textarea
                                    className="w-full bg-black border border-blue-900/50 rounded p-3 text-sm text-blue-200 focus:border-blue-500 outline-none font-mono min-h-[80px]"
                                    value={editForm.expCvUsage}
                                    onChange={e => updateForm('expCvUsage', e.target.value)}
                                    placeholder="Usage instructions, control details, or operational constraints..."
                                />
                            </div>

                            <div className="col-span-2 space-y-1">
                                <label className="text-xs text-gray-500 font-bold uppercase">Tags (Comma Separated)</label>
                                <Input value={editTags} onChange={e => setEditTags(e.target.value)} placeholder="e.g. urgent, v1, gift" />
                            </div>
                        </div>

                        {/* Safety Hazards Section */}
                        <div className="border-t border-white/10 pt-4 mt-6">
                            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-wider flex items-center gap-2">
                                <AlertTriangle size={14} className="text-accent" />
                                Safety Hazards & Protocols
                            </h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                                {(Object.entries(HAZARD_DEFS) as [HazardClass, any][]).map(([key, def]) => (
                                    <button
                                        key={key}
                                        onClick={() => toggleEditHazard(key)}
                                        className={clsx(
                                            "flex items-center gap-2 p-3 rounded border text-left transition-all",
                                            (editForm.hazards || []).includes(key)
                                                ? "bg-red-500/10 border-red-500 text-white"
                                                : "bg-white/5 border-white/10 text-gray-500 hover:bg-white/10"
                                        )}
                                    >
                                        <def.icon size={16} className={(editForm.hazards || []).includes(key) ? def.color : "text-gray-600"} />
                                        <span className="text-xs font-bold">{def.label}</span>
                                    </button>
                                ))}
                            </div>
                        </div>

                        {/* Tab Visibility Config */}
                        <div className="border-t border-white/10 pt-4 mt-6">
                            <h3 className="text-xs font-bold text-gray-500 mb-4 uppercase tracking-wider flex items-center gap-2">
                                <Eye size={14} className="text-accent" />
                                Interface Customization (Visible Tabs)
                            </h3>
                            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 gap-3">
                                {TABS.filter(t => t.id !== 'overview').map(tab => {
                                    const isHidden = editHiddenTabs.includes(tab.id);
                                    return (
                                        <button
                                            key={tab.id}
                                            onClick={() => setEditHiddenTabs(prev =>
                                                isHidden ? prev.filter(id => id !== tab.id) : [...prev, tab.id]
                                            )}
                                            className={clsx(
                                                "flex items-center gap-2 p-3 rounded border text-left transition-all",
                                                !isHidden
                                                    ? "bg-accent/10 border-accent text-accent"
                                                    : "bg-white/5 border-white/10 text-gray-600 hover:bg-white/10"
                                            )}
                                        >
                                            {isHidden ? <EyeOff size={16} /> : <Eye size={16} />}
                                            <span className="text-xs font-bold">{tab.label}</span>
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        <div className="flex justify-end pt-4 border-t border-white/10">
                            <Button variant="primary" onClick={handleSave} className="px-8"><Save size={16} className="mr-2" /> SAVE CHANGES</Button>
                        </div>
                    </Card>
                ) : (
                    <div className="h-full">
                        {(() => {
                            switch (activeTab) {
                                case 'overview':
                                    return (
                                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                                            <div className="lg:col-span-2 space-y-6">

                                                {/* Stats Grid */}
                                                <Card className="col-span-1 lg:col-span-2 bg-black border-white/5 shadow-2xl overflow-hidden relative p-8">
                                                    {/* Mission Brief Section */}
                                                    <div className="space-y-6 relative z-10">
                                                        <div className="flex justify-between items-start">
                                                            <div>
                                                                <h1 className="text-4xl font-black uppercase tracking-tighter text-white mb-2">
                                                                    {safeStr(project.title)}
                                                                </h1>
                                                                <div className="flex items-center gap-2 flex-wrap">
                                                                    <span className="text-[10px] font-mono text-gray-500 uppercase tracking-widest bg-white/5 px-2 py-0.5 border border-white/10">
                                                                        ID: {project.project_code || `P - ${project.id} `}
                                                                    </span>
                                                                    {project.version && (
                                                                        <span className="text-[10px] font-mono text-accent uppercase tracking-widest bg-accent/5 px-2 py-0.5 border border-accent/20">
                                                                            VERSION: {project.version}
                                                                        </span>
                                                                    )}
                                                                    {project.category && (
                                                                        <span className="text-[10px] font-mono uppercase tracking-widest px-2 py-0.5 border border-white/10 text-gray-400">
                                                                            {project.category}
                                                                        </span>
                                                                    )}
                                                                </div>
                                                            </div>
                                                            <div className="flex gap-2">
                                                                {project.design_status && (
                                                                    <span className="text-[10px] font-bold px-2 py-1 border uppercase tracking-widest text-gray-400 border-gray-600/30">
                                                                        DES: {project.design_status}
                                                                    </span>
                                                                )}
                                                                {project.build_status && (
                                                                    <span className="text-[10px] font-bold px-2 py-1 border uppercase tracking-widest text-gray-400 border-gray-600/30">
                                                                        BLD: {project.build_status}
                                                                    </span>
                                                                )}
                                                                <span className={clsx(
                                                                    "text-[10px] font-bold px-2 py-1 border uppercase tracking-widest",
                                                                    project.status === 'active' ? 'text-accent border-accent/20 bg-accent/5' : 'text-gray-500 border-gray-100/10'
                                                                )}>
                                                                    {project.status || 'ACTIVE'}
                                                                </span>
                                                            </div>
                                                        </div>

                                                        {project.role && (
                                                            <div className="border-l-2 border-accent/30 pl-4 py-1">
                                                                <p className="text-sm font-medium text-gray-400 italic font-mono uppercase tracking-tight">
                                                                    ROLE: {safeStr(project.role)}
                                                                </p>
                                                            </div>
                                                        )}

                                                        <div className="space-y-3">
                                                            <h2 className="text-[10px] font-black text-gray-500 uppercase tracking-[0.2em] border-b border-white/5 pb-2">
                                                                Mission Brief
                                                            </h2>
                                                            <p className="text-lg text-gray-200 leading-relaxed font-sans max-w-4xl">
                                                                {project.status_description || "No tactical description available for this project node."}
                                                            </p>
                                                        </div>

                                                        {/* Overview Stats */}
                                                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-6 border-t border-white/5 mt-6">
                                                            <div>
                                                                <span className="block text-[10px] text-gray-500 uppercase font-mono mb-1">Priority</span>
                                                                <RatingBar
                                                                    value={project.priority || 0}
                                                                    onChange={(v) => quickUpdate('priority', v)}
                                                                    activeColor="bg-red-600"
                                                                />
                                                            </div>
                                                            <div>
                                                                <span className="block text-[10px] text-gray-500 uppercase font-mono mb-1">Intrusiveness</span>
                                                                <RatingBar
                                                                    value={project.intrusiveness || 0}
                                                                    onChange={(v) => quickUpdate('intrusiveness', v)}
                                                                    activeColor="bg-accent"
                                                                />
                                                            </div>
                                                            <div>
                                                                <span className="block text-[10px] text-gray-500 uppercase font-mono mb-1">Theorized Hrs</span>
                                                                <span className="text-sm font-mono text-accent">{project.total_theorized_hours || 0}H</span>
                                                            </div>
                                                            <div>
                                                                <span className="block text-[10px] text-gray-500 uppercase font-mono mb-1">Target Date</span>
                                                                <span className="text-sm font-mono text-gray-400">{safeDateDisplay(project.target_completion_date)}</span>
                                                            </div>
                                                        </div>
                                                    </div>
                                                </Card>

                                                {/* Linked Projects / Network (Added for Flowchart Sync) */}
                                                {(linkedProjects.upstream.length > 0 || linkedProjects.downstream.length > 0 || linkedProjects.related.length > 0) && (
                                                    <Card title="Network & Dependencies">
                                                        <div className="space-y-4">
                                                            {/* Upstream (Blockers) */}
                                                            {linkedProjects.upstream.length > 0 && (
                                                                <div>
                                                                    <h4 className="text-[10px] uppercase text-red-500 font-bold mb-2 flex items-center gap-2">
                                                                        <AlertTriangle size={12} /> Blocked By (Upstream)
                                                                    </h4>
                                                                    <div className="space-y-2">
                                                                        {linkedProjects.upstream.map(p => (
                                                                            <div
                                                                                key={p.id}
                                                                                onClick={() => navigate(`/projects/${p.id}`)}
                                                                                className="flex items-center justify-between p-2 bg-red-900/10 border border-red-900/30 rounded cursor-pointer hover:bg-red-900/20 transition-colors"
                                                                            >
                                                                                <div className="flex items-center gap-2">
                                                                                    <span className="font-mono text-[10px] text-red-400">{p.project_code || `P-${p.id}`}</span>
                                                                                    <span className="text-xs font-bold text-gray-300">{p.title}</span>
                                                                                </div>
                                                                                <span className="text-[10px] text-gray-500 uppercase">{p.status}</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {/* Downstream (Blocking) */}
                                                            {linkedProjects.downstream.length > 0 && (
                                                                <div>
                                                                    <h4 className="text-[10px] uppercase text-blue-400 font-bold mb-2 flex items-center gap-2">
                                                                        <LinkIcon size={12} /> Blocking (Downstream)
                                                                    </h4>
                                                                    <div className="space-y-2">
                                                                        {linkedProjects.downstream.map(p => (
                                                                            <div
                                                                                key={p.id}
                                                                                onClick={() => navigate(`/projects/${p.id}`)}
                                                                                className="flex items-center justify-between p-2 bg-blue-900/10 border border-blue-900/30 rounded cursor-pointer hover:bg-blue-900/20 transition-colors"
                                                                            >
                                                                                <div className="flex items-center gap-2">
                                                                                    <span className="font-mono text-[10px] text-blue-400">{p.project_code || `P-${p.id}`}</span>
                                                                                    <span className="text-xs font-bold text-gray-300">{p.title}</span>
                                                                                </div>
                                                                                <span className="text-[10px] text-gray-500 uppercase">{p.status}</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}

                                                            {/* Related */}
                                                            {linkedProjects.related.length > 0 && (
                                                                <div>
                                                                    <h4 className="text-[10px] uppercase text-purple-400 font-bold mb-2 flex items-center gap-2">
                                                                        <LinkIcon size={12} /> Related Projects
                                                                    </h4>
                                                                    <div className="space-y-2">
                                                                        {linkedProjects.related.map(p => (
                                                                            <div
                                                                                key={p.id}
                                                                                onClick={() => navigate(`/projects/${p.id}`)}
                                                                                className="flex items-center justify-between p-2 bg-purple-900/10 border border-purple-900/30 rounded cursor-pointer hover:bg-purple-900/20 transition-colors"
                                                                            >
                                                                                <div className="flex items-center gap-2">
                                                                                    <span className="font-mono text-[10px] text-purple-400">{p.project_code || `P-${p.id}`}</span>
                                                                                    <span className="text-xs font-bold text-gray-300">{p.title}</span>
                                                                                </div>
                                                                                <span className="text-[10px] text-gray-500 uppercase">{p.status}</span>
                                                                            </div>
                                                                        ))}
                                                                    </div>
                                                                </div>
                                                            )}
                                                        </div>
                                                    </Card>
                                                )}

                                                {/* References / Backlinks Panel */}
                                                <ReferencesPanel entityType="project" entityId={projectId} />

                                                <Card title="Project Documents">
                                                    <div className="flex justify-between items-center mb-2 px-1">
                                                        <div className="text-gray-500 uppercase font-mono text-[10px] font-bold">Files</div>
                                                        <label className={clsx("cursor-pointer bg-white/5 hover:bg-white/10 text-[10px] px-2 py-1 rounded border border-white/10 flex items-center gap-1 text-accent transition-colors", isIngesting && "opacity-50 pointer-events-none")}>
                                                            {isIngesting ? <Loader2 size={10} className="animate-spin" /> : <Upload size={10} />}
                                                            {isIngesting ? "PROCESSING..." : "UPLOAD"}
                                                            <input type="file" className="hidden" onChange={(e) => { handleFileUpload(e); e.target.value = ''; }} disabled={isIngesting} />
                                                        </label>
                                                    </div>
                                                    <div className="space-y-2">
                                                        {(files || []).map(f => {
                                                            const is3D = f.name.toLowerCase().endsWith('.stl') || f.name.toLowerCase().endsWith('.obj');

                                                            if (is3D) {
                                                                const url = URL.createObjectURL(f.content as Blob);
                                                                // Note: Blobs from createObjectURL should ideally be revoked. 
                                                                // In a list like this, we'd need a useEffect to revoke on unmount, or just rely on page refresh for MVP cleanliness.
                                                                // For stability in this "Workshop OS", we'll generate it inline.

                                                                return (
                                                                    <div key={f.id} className="space-y-2 mb-4">
                                                                        <div className="flex justify-between items-center bg-white/5 p-2 px-3 border border-white/5">
                                                                            <div className="flex items-center gap-2">
                                                                                <Box size={14} className="text-blue-400" />
                                                                                <span className="text-xs font-bold text-gray-300">{f.name}</span>
                                                                            </div>
                                                                            <Button variant="ghost" size="sm" onClick={() => openFile(f.content)}><Upload size={12} /></Button>
                                                                        </div>
                                                                        <ThreeViewer url={url} fileName={f.name} className="h-48 w-full" />
                                                                    </div>
                                                                )
                                                            }

                                                            return (
                                                                <div
                                                                    key={f.id}
                                                                    className="bg-white/5 p-3 flex justify-between items-center hover:bg-white/10 transition-colors cursor-pointer border border-white/5 relative group"
                                                                    onClick={() => openFile(f.content)}
                                                                    onMouseEnter={(e) => {
                                                                        if (f.type.startsWith('image/')) {
                                                                            const url = URL.createObjectURL(f.content as Blob);
                                                                            setHoveredImage({ url, x: e.clientX, y: e.clientY });
                                                                        }
                                                                    }}
                                                                    onMouseLeave={() => {
                                                                        if (hoveredImage) {
                                                                            URL.revokeObjectURL(hoveredImage.url);
                                                                            setHoveredImage(null);
                                                                        }
                                                                    }}
                                                                    onMouseMove={(e) => {
                                                                        if (hoveredImage) {
                                                                            setHoveredImage(prev => prev ? { ...prev, x: e.clientX, y: e.clientY } : null);
                                                                        }
                                                                    }}
                                                                >
                                                                    <div className="flex items-center gap-3">
                                                                        <FileText size={16} className={clsx("text-accent", f.type.startsWith('image/') && "text-purple-400")} />
                                                                        <span className="font-bold text-sm text-gray-300">{safeStr(f.name)}</span>
                                                                    </div>
                                                                    <span className="text-xs font-mono text-gray-600">{safeDateDisplay(f.created_at)}</span>
                                                                </div>
                                                            );
                                                        })}
                                                        {(!files || files.length === 0) && <p className="text-gray-600 italic text-sm">No files uploaded.</p>}
                                                    </div>
                                                </Card>

                                                {/* Image Preview Portal */}
                                                {hoveredImage && (
                                                    <div
                                                        className="fixed z-[9999] pointer-events-none p-1 bg-black border border-white/20 shadow-2xl rounded-lg animate-in fade-in zoom-in-95 duration-150"
                                                        style={{
                                                            top: hoveredImage.y + 10,
                                                            left: hoveredImage.x + 10,
                                                            maxWidth: '300px'
                                                        }}
                                                    >
                                                        <img src={hoveredImage.url} alt="Preview" className="rounded max-w-full h-auto object-cover" />
                                                    </div>
                                                )}
                                            </div>

                                            <div className="space-y-6">
                                                <Card title="System Metadata">
                                                    <div className="space-y-3 font-mono text-xs">
                                                        <div className="flex justify-between border-b border-white/5 pb-1">
                                                            <span className="text-gray-500 uppercase">IDENTIFIER</span>
                                                            <span className="text-accent font-bold">{project.project_code || project.id}</span>
                                                        </div>
                                                        <div className="flex justify-between border-b border-white/5 pb-1">
                                                            <span className="text-gray-500 uppercase">INITIALIZED</span>
                                                            <span>{safeDateDisplay(project.created_at)}</span>
                                                        </div>
                                                        <div className="flex justify-between border-b border-white/5 pb-1">
                                                            <span className="text-gray-500 uppercase">UPDATED</span>
                                                            <span>{safeDateDisplay(project.updated_at)}</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-500 uppercase">INTRUSIVENESS</span>
                                                            <span className="text-accent">{project.intrusiveness || 0}/5</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-500 uppercase">PRIORITY</span>
                                                            <span className="text-red-500">{project.priority || 0}/5</span>
                                                        </div>
                                                        <div className="flex justify-between">
                                                            <span className="text-gray-500 uppercase">CATEGORY</span>
                                                            <span className="text-white">{project.category || 'N/A'}</span>
                                                        </div>
                                                        {project.tags && project.tags.length > 0 && (
                                                            <div className="pt-2">
                                                                <span className="block text-gray-500 uppercase mb-1">TAGS</span>
                                                                <div className="flex flex-wrap gap-1">
                                                                    {project.tags.map(t => <span key={t} className="px-1 bg-white/10 text-gray-400">{t}</span>)}
                                                                </div>
                                                            </div>
                                                        )}
                                                    </div>
                                                </Card>

                                                <Card title="Planning & Logistics">
                                                    <div className="space-y-4">
                                                        {/* Rationale */}
                                                        {project.rationale && (
                                                            <div className="bg-white/5 p-3 border-l-2 border-accent">
                                                                <span className="block text-[10px] text-gray-500 uppercase font-mono mb-1">RATIONALE / MOTIVATION</span>
                                                                <p className="text-sm italic text-gray-300">"{project.rationale}"</p>
                                                            </div>
                                                        )}

                                                        <div className="grid grid-cols-2 gap-4">
                                                            {/* Time */}
                                                            <div className="bg-black/40 p-2 rounded border border-white/5">
                                                                <div className="flex items-center gap-2 mb-2 border-b border-white/5 pb-1">
                                                                    <div className="p-1 bg-blue-500/20 rounded text-blue-400"><Clock size={12} /></div>
                                                                    <span className="text-[10px] font-bold text-gray-400 uppercase">Time ESTIMATE</span>
                                                                </div>
                                                                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                                                                    <div>
                                                                        <span className="block text-gray-600">ACTIVE</span>
                                                                        <span className="text-blue-300">{project.time_estimate_active || 0}h</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="block text-gray-600">PASSIVE</span>
                                                                        <span className="text-gray-400">{project.time_estimate_passive || 0}h</span>
                                                                    </div>
                                                                </div>
                                                            </div>

                                                            {/* Money */}
                                                            <div className="bg-black/40 p-2 rounded border border-white/5">
                                                                <div className="flex items-center gap-2 mb-2 border-b border-white/5 pb-1">
                                                                    <div className="p-1 bg-green-500/20 rounded text-green-400"><DollarSign size={12} /></div>
                                                                    <span className="text-[10px] font-bold text-gray-400 uppercase">Financials</span>
                                                                </div>
                                                                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                                                                    <div>
                                                                        <span className="block text-gray-600">BUDGET</span>
                                                                        <span className="text-green-300">${project.financial_budget || 0}</span>
                                                                    </div>
                                                                    <div>
                                                                        <span className="block text-gray-600">SPEND</span>
                                                                        <span className={clsx((project.financial_spend || 0) > (project.financial_budget || 0) ? "text-red-500" : "text-gray-400")}>
                                                                            ${project.financial_spend || 0}
                                                                        </span>
                                                                    </div>
                                                                </div>
                                                            </div>
                                                        </div>

                                                        {/* Edit Mode Inputs for Planning (Only visible when editing) */}
                                                    </div>
                                                </Card>

                                                <Card title="Specifications & Key Data">
                                                    <div className="flex flex-wrap gap-2 mb-4">
                                                        {safeArr(project.io_spec).length > 0 ? safeArr(project.io_spec).map((spec: string, i: number) => (
                                                            <span key={i} className="text-[10px] font-mono bg-accent/10 text-accent px-1 border border-accent/20">{safeStr(spec)}</span>
                                                        )) : <span className="text-[10px] text-gray-600 italic">No key specs defined.</span>}
                                                    </div>
                                                    {project.golden_voltages && (
                                                        <div className="bg-black p-2 border border-green-900/50 text-[10px] font-mono text-green-500">
                                                            <strong className="block text-green-700 mb-1 border-b border-green-900/30">REFERENCE / KEY DATA:</strong>
                                                            {safeStr(project.golden_voltages)}
                                                        </div>
                                                    )}
                                                    {project.exp_cv_usage && (
                                                        <div className="bg-black p-2 border border-blue-900/50 text-[10px] font-mono text-blue-200 mt-2">
                                                            <strong className="block text-blue-400 mb-1 border-b border-blue-900/30">INTERACTION / NOTES:</strong>
                                                            {safeStr(project.exp_cv_usage)}
                                                        </div>
                                                    )}
                                                </Card>

                                                <VoiceMemoManager projectId={projectId} />
                                            </div>

                                        </div>
                                    );

                                case 'manuscript':
                                    return <ProjectManuscript projectId={projectId} />;

                                case 'production':
                                    return <ProjectProduction projectId={projectId} activeTab={activeTab} />;

                                case 'tasks':
                                    return <ProjectTasks projectId={projectId} />;

                                case 'specs':
                                    return (
                                        <div className="max-w-6xl mx-auto">
                                            <ProjectSpecs
                                                project={project}
                                                projectId={projectId}
                                                onUpdate={(updates) => db.projects.update(projectId, updates)}
                                            />
                                        </div>
                                    );

                                case 'blueprint':
                                    return <ProjectBlueprint data={project.universal_data || {}} />;

                                case 'bom':
                                    return <ProjectBOM projectId={projectId} />;

                                case 'tools':
                                    return <ProjectTools projectId={projectId} />;

                                case 'safety_qa':
                                    return <ProjectSafetyQA project={project} projectId={projectId} />;

                                case 'printing':
                                    return (
                                        <div className="max-w-4xl mx-auto">
                                            <PrintPartsManager
                                                parts={safeArr(project.print_parts)}
                                                onChange={(updated) => db.projects.update(projectId, { print_parts: updated })}
                                            />
                                        </div>
                                    );

                                case 'code':
                                    return <div className="h-full"><ProjectScripts projectId={projectId} /></div>;

                                case 'assets':
                                    return <ProjectAssets projectId={projectId} />;

                                case 'notebook':
                                    return <ProjectNotebook projectId={projectId} />;

                                case 'changelog':
                                    return <ProjectChangelog projectId={projectId} />;

                                default:
                                    return (
                                        <div className="flex flex-col items-center justify-center py-20 opacity-50">
                                            <AlertTriangle size={48} className="mb-4" />
                                            <h3 className="text-xl font-bold">Unknown Tab: {activeTab}</h3>
                                        </div>
                                    );
                            }
                        })()}
                    </div>
                )
                }


            </div >

            <UploadConfirmationModal
                isOpen={!!pendingUpload}
                onClose={() => { setPendingUpload(null); useUIStore.getState().setIngesting(false); }}
                onConfirm={confirmUpload}
                fileName={pendingUpload?.file.name || ''}
                detectedVersion={pendingUpload?.extraction?.version}
            />

            {/* PRE-UPLOAD CHECK MODAL */}
            {
                uploadFile && (
                    <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                        <div className="bg-neutral-900 border border-white/10 p-6 rounded-xl shadow-2xl max-w-md w-full animate-in fade-in zoom-in-95">
                            <h3 className="text-xl font-bold text-white mb-4">File Handling</h3>
                            <p className="text-gray-400 text-sm mb-6">
                                How should <span className="text-accent font-mono">{uploadFile.name}</span> be processed?
                            </p>
                            <div className="space-y-3">
                                <button
                                    onClick={runAnalysis}
                                    className="w-full p-4 bg-accent/10 border border-accent/20 rounded-lg hover:bg-accent/20 hover:border-accent text-left transition-all group"
                                >
                                    <div className="font-bold text-accent mb-1 flex items-center gap-2">
                                        <Zap size={16} /> Analyze & Update Project
                                    </div>
                                    <div className="text-xs text-gray-500 group-hover:text-gray-300">
                                        Use AI to parse specs, tasks, BOM, and update this project's data (MDBD).
                                    </div>
                                </button>

                                <button
                                    onClick={runDirectUpload}
                                    className="w-full p-4 bg-white/5 border border-white/10 rounded-lg hover:bg-white/10 hover:border-white/20 text-left transition-all group"
                                >
                                    <div className="font-bold text-white mb-1 flex items-center gap-2">
                                        <Upload size={16} /> Just Upload Asset
                                    </div>
                                    <div className="text-xs text-gray-500 group-hover:text-gray-300">
                                        Store as a file attachment only. Do not change project data.
                                    </div>
                                </button>
                            </div>
                            <div className="mt-6 flex justify-center">
                                <button onClick={() => setUploadFile(null)} className="text-xs text-gray-500 hover:text-white">Cancel</button>
                            </div>
                        </div>
                    </div>
                )
            }
        </motion.div >
    );
}
