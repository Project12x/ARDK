import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type ProjectTemplate } from '../../lib/db';
import { BlueprintService } from '../../lib/blueprints';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Plus, Trash2, Edit, Sparkles, Wand2, Save, X, Ghost } from 'lucide-react';
import { toast } from 'sonner';
import { AIService } from '../../lib/AIService';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { OracleActionCard } from '../ui/OracleActionCard';
import { clsx } from 'clsx';

export function TemplateManager() {
    // Fetch ALL templates from DB.
    // If empty, we trigger BlueprintService.getAll() which handles seeding.
    const templates = useLiveQuery(() => db.project_templates.toArray());

    // Ensure seeding triggers if DB is empty on mount
    useEffect(() => {
        BlueprintService.getAll().catch(console.error);
    }, []);

    const [isEditing, setIsEditing] = useState(false);
    const [editingId, setEditingId] = useState<number | null>(null);

    // Editor State
    const [draft, setDraft] = useState<Partial<ProjectTemplate>>({
        name: '', category: 'General', description: '', tasks: [], tags: [], priority: 3, status: 'active', github_repo: ''
    });

    // Oracle State
    const [oraclePrompt, setOraclePrompt] = useState('');
    const [isGenerating, setIsGenerating] = useState(false);
    const [proposedDraft, setProposedDraft] = useState<Partial<ProjectTemplate> | null>(null);

    const [taskListParent] = useAutoAnimate();

    const handleEdit = (t: ProjectTemplate) => {
        setDraft(t);
        setEditingId(t.id!);
        setIsEditing(true);
        setProposedDraft(null); // Clear any pending proposal
    };

    const handleCreateNew = () => {
        setDraft({
            name: 'New Blueprint',
            category: 'General',
            description: '',
            tasks: [],
            tags: [],
            priority: 3,
            status: 'active',
            github_repo: ''
        });
        setEditingId(null);
        setIsEditing(true);
        setProposedDraft(null);
    };

    const handleSave = async () => {
        if (!draft.name) return toast.error("Name is required");

        try {
            const dataToSave: Omit<ProjectTemplate, 'id' | 'created_at'> & { created_at?: Date } = {
                name: draft.name,
                category: draft.category || 'General',
                description: draft.description || '',
                tasks: draft.tasks || [],
                tags: draft.tags || [],
                priority: draft.priority || 3,
                status: draft.status || 'active',
                github_repo: draft.github_repo || '',
                // Extended fields
                kingdom: draft.kingdom,
                phylum: draft.phylum,
                taxonomy_path: draft.taxonomy_path,
                domains: draft.domains,
                label_color: draft.label_color,
                time_estimate_active: draft.time_estimate_active,
                time_estimate_passive: draft.time_estimate_passive,
                financial_budget: draft.financial_budget,
                total_theorized_hours: draft.total_theorized_hours,
                design_status: draft.design_status,
                build_status: draft.build_status,
                risk_level: draft.risk_level,
                hazards: draft.hazards,
                external_links: draft.external_links,
                io_spec: draft.io_spec,
                design_philosophy: draft.design_philosophy,
                is_custom: true
            };

            if (editingId) {
                await db.project_templates.update(editingId, dataToSave);
                toast.success("Blueprint updated");
            } else {
                await db.project_templates.add({
                    ...dataToSave,
                    created_at: new Date()
                });
                toast.success("Blueprint created");
            }
            setIsEditing(false);
        } catch (e) {
            console.error(e);
            toast.error("Failed to save");
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm("Delete this blueprint?")) {
            await db.project_templates.delete(id);
            toast.success("Deleted");
        }
    };

    const handleOracleGenerate = async () => {
        if (!oraclePrompt.trim()) return;
        setIsGenerating(true);
        try {
            const prompt = `
            Create a comprehensive Project Blueprint/Template based on: "${oraclePrompt}".

            Return ONLY a JSON object:
            {
                "name": "Title",
                "category": "Category",
                "description": "Description",
                "tags": ["tag1", "tag2"],
                "priority": 3,
                "tasks": [
                    { "title": "Task Name", "phase": "Planning|Design|Fabrication|Testing|Release", "priority": 1-5, "estimated_time": "2h" }
                ]
            }
            `;

            // Use specialized chatWithGemini for now, OR AIService.chat if refactored.
            // Using direct AIService method since I added a wrapper for chatWithGemini or I can use .chat().
            // TemplateManager likely passes prompt and context.
            // Let's assume using chatWithGemini or chat.
            const response = await AIService.chatWithGemini(prompt, undefined, 'gemini-2.5-flash', undefined, true);

            try {
                let json = JSON.parse(response);
                if (json.message && !json.tasks) {
                    const innerMatch = json.message.match(/\{[\s\S]*\}/);
                    if (innerMatch) json = JSON.parse(innerMatch[0]);
                }

                if (json.tasks || json.name) {
                    // INSTEAD of applying directly, set Proposal
                    setProposedDraft({
                        name: json.name || draft.name,
                        category: json.category || draft.category,
                        description: json.description || draft.description,
                        tags: json.tags || [],
                        priority: json.priority || 3,
                        tasks: json.tasks || []
                    });
                    toast.info("Oracle proposal ready for review.");
                } else {
                    toast.error("Oracle response was not a valid blueprint.");
                }

            } catch (e) {
                console.warn("Parse error", response, e);
                toast.error("Failed to parse Oracle response.");
            }

        } catch (e) {
            console.error(e);
            toast.error("Oracle connection failed.");
        } finally {
            setIsGenerating(false);
        }
    };

    const applyProposal = () => {
        if (proposedDraft) {
            setDraft(prev => ({ ...prev, ...proposedDraft }));
            setProposedDraft(null);
            toast.success("Oracle changes applied! Review and Save to commit.");
        }
    };

    // Tab state for editor
    const [activeTab, setActiveTab] = useState<'meta' | 'classification' | 'safety' | 'tasks'>('meta');

    const tabs = [
        { id: 'meta' as const, label: 'Meta & Config' },
        { id: 'classification' as const, label: 'Classification' },
        { id: 'safety' as const, label: 'Safety & Specs' },
        { id: 'tasks' as const, label: 'Tasks' },
    ];

    if (isEditing) {
        return (
            <div className="space-y-6 animate-in slide-in-from-right duration-200 pb-20">
                <div className="flex items-center justify-between">
                    <h3 className="text-xl font-bold text-white flex items-center gap-2">
                        {editingId ? <Edit className="text-accent" /> : <Plus className="text-accent" />}
                        {editingId ? 'Edit Blueprint' : 'Create New Blueprint'}
                    </h3>
                    <Button variant="ghost" onClick={() => setIsEditing(false)}><X /></Button>
                </div>

                {/* Oracle Generator */}
                <div className="bg-black/40 border border-neon/30 p-4 rounded-xl relative overflow-hidden group">
                    <div className="absolute top-0 right-0 p-2 opacity-50"><Sparkles size={40} className="text-neon/20" /></div>
                    <label className="text-neon text-xs font-bold uppercase tracking-wider mb-2 flex items-center gap-2">
                        <Wand2 size={12} /> Workshop Oracle Architect
                    </label>
                    <div className="flex gap-2 relative z-10">
                        <input
                            className="flex-1 bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-neon outline-none"
                            placeholder="e.g. 'Build a custom mechanical keyboard from scratch'..."
                            value={oraclePrompt}
                            onChange={(e) => setOraclePrompt(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleOracleGenerate()}
                        />
                        <Button
                            onClick={handleOracleGenerate}
                            disabled={isGenerating}
                            className="bg-neon/10 text-neon hover:bg-neon hover:text-black border border-neon/50"
                        >
                            {isGenerating ? 'Weaving...' : 'Generate'}
                        </Button>
                    </div>
                </div>

                {/* PROPOSAL CARD */}
                {proposedDraft && (
                    <div className="my-4">
                        <OracleActionCard
                            title="Blueprint Proposal"
                            description="The Oracle has constructed a new protocol based on your request. Review the changes before applying."
                            proposedData={proposedDraft}
                            onConfirm={applyProposal}
                            onCancel={() => setProposedDraft(null)}
                        />
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="flex gap-1 border-b border-white/10 pb-1">
                    {tabs.map(tab => (
                        <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={clsx(
                                "px-4 py-2 text-xs font-bold uppercase tracking-wider transition-colors rounded-t",
                                activeTab === tab.id
                                    ? "bg-accent/20 text-accent border-b-2 border-accent"
                                    : "text-gray-500 hover:text-white hover:bg-white/5"
                            )}
                        >
                            {tab.label}
                        </button>
                    ))}
                </div>

                {/* Tab Content */}
                <div className="min-h-[300px]">
                    {/* META TAB */}
                    {activeTab === 'meta' && (
                        <div className="grid grid-cols-2 gap-4 animate-in fade-in duration-150">
                            <div className="col-span-1">
                                <label className="text-gray-500 text-xs uppercase font-bold">Template Name *</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none"
                                    value={draft.name} onChange={e => setDraft({ ...draft, name: e.target.value })}
                                />
                            </div>
                            <div className="col-span-1">
                                <label className="text-gray-500 text-xs uppercase font-bold">Category</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none"
                                    value={draft.category} onChange={e => setDraft({ ...draft, category: e.target.value })}
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">Description</label>
                                <textarea
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none h-20 resize-none"
                                    value={draft.description} onChange={e => setDraft({ ...draft, description: e.target.value })}
                                />
                            </div>
                            <div className="col-span-1">
                                <label className="text-gray-500 text-xs uppercase font-bold">Default Tags (comma sep)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none text-sm font-mono"
                                    value={draft.tags?.join(', ')}
                                    onChange={e => setDraft({ ...draft, tags: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                                    placeholder="e.g. mdbd, electronics, urgent"
                                />
                            </div>
                            <div className="col-span-1 flex gap-2">
                                <div className="flex-1">
                                    <label className="text-gray-500 text-xs uppercase font-bold">Priority</label>
                                    <select
                                        className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none"
                                        value={draft.priority} onChange={e => setDraft({ ...draft, priority: Number(e.target.value) })}
                                    >
                                        {[1, 2, 3, 4, 5].map(n => <option key={n} value={n}>{n}</option>)}
                                    </select>
                                </div>
                                <div className="flex-1">
                                    <label className="text-gray-500 text-xs uppercase font-bold">Status</label>
                                    <select
                                        className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none"
                                        value={draft.status} onChange={e => setDraft({ ...draft, status: e.target.value as ProjectTemplate['status'] })}
                                    >
                                        {['active', 'on-hold', 'rnd_long', 'someday'].map(s => <option key={s} value={s}>{s}</option>)}
                                    </select>
                                </div>
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">GitHub Repo (owner/repo)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none font-mono text-sm"
                                    value={draft.github_repo || ''}
                                    onChange={e => setDraft({ ...draft, github_repo: e.target.value })}
                                    placeholder="username/repository"
                                />
                            </div>
                        </div>
                    )}

                    {/* CLASSIFICATION TAB */}
                    {activeTab === 'classification' && (
                        <div className="grid grid-cols-2 gap-4 animate-in fade-in duration-150">
                            <div className="col-span-1">
                                <label className="text-gray-500 text-xs uppercase font-bold">Kingdom (Top Domain)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none"
                                    value={draft.kingdom || ''}
                                    onChange={e => setDraft({ ...draft, kingdom: e.target.value })}
                                    placeholder="e.g. Electronics, Woodworking, Software"
                                />
                            </div>
                            <div className="col-span-1">
                                <label className="text-gray-500 text-xs uppercase font-bold">Phylum (Sub-Domain)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none"
                                    value={draft.phylum || ''}
                                    onChange={e => setDraft({ ...draft, phylum: e.target.value })}
                                    placeholder="e.g. Synths, Furniture, Web Apps"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">Taxonomy Path (Full)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none font-mono text-sm"
                                    value={draft.taxonomy_path || ''}
                                    onChange={e => setDraft({ ...draft, taxonomy_path: e.target.value })}
                                    placeholder="e.g. Electronics>Music>Guitar>Pedal"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">Domains (comma sep)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none font-mono text-sm"
                                    value={draft.domains?.join(', ') || ''}
                                    onChange={e => setDraft({ ...draft, domains: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                                    placeholder="e.g. Electronics, Software (for hybrid projects)"
                                />
                            </div>
                            <div className="col-span-1">
                                <label className="text-gray-500 text-xs uppercase font-bold">Label Color (Hex)</label>
                                <div className="flex gap-2">
                                    <input
                                        type="color"
                                        className="w-12 h-10 bg-transparent border border-white/10 rounded cursor-pointer"
                                        value={draft.label_color || '#22c55e'}
                                        onChange={e => setDraft({ ...draft, label_color: e.target.value })}
                                    />
                                    <input
                                        className="flex-1 bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none font-mono text-sm"
                                        value={draft.label_color || ''}
                                        onChange={e => setDraft({ ...draft, label_color: e.target.value })}
                                        placeholder="#22c55e"
                                    />
                                </div>
                            </div>
                        </div>
                    )}



                    {/* SAFETY TAB */}
                    {activeTab === 'safety' && (
                        <div className="grid grid-cols-2 gap-4 animate-in fade-in duration-150">
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">Risk Level</label>
                                <div className="flex gap-2 mt-1">
                                    {(['low', 'medium', 'high'] as const).map(level => (
                                        <button
                                            key={level}
                                            type="button"
                                            onClick={() => setDraft({ ...draft, risk_level: level })}
                                            className={clsx(
                                                "flex-1 py-2 px-4 rounded border text-sm font-bold uppercase transition-colors",
                                                draft.risk_level === level
                                                    ? level === 'low' ? 'bg-green-500/20 border-green-500 text-green-400'
                                                        : level === 'medium' ? 'bg-yellow-500/20 border-yellow-500 text-yellow-400'
                                                            : 'bg-red-500/20 border-red-500 text-red-400'
                                                    : 'bg-white/5 border-white/10 text-gray-500 hover:border-white/30'
                                            )}
                                        >
                                            {level}
                                        </button>
                                    ))}
                                </div>
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">Hazards (comma sep)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none font-mono text-sm"
                                    value={draft.hazards?.join(', ') || ''}
                                    onChange={e => setDraft({ ...draft, hazards: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                                    placeholder="e.g. mains, high_current, chemicals, fumes, lead"
                                />
                                <p className="text-[10px] text-gray-600 mt-1">Keywords: mains, high_current, chemicals, blades, fumes, lead, esd</p>
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">I/O Spec (comma sep)</label>
                                <input
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none font-mono text-sm"
                                    value={draft.io_spec?.join(', ') || ''}
                                    onChange={e => setDraft({ ...draft, io_spec: e.target.value.split(',').map(t => t.trim()).filter(Boolean) })}
                                    placeholder="e.g. Audio In, CV Out, MIDI Thru"
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold">Design Philosophy</label>
                                <textarea
                                    className="w-full bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none h-24 resize-none"
                                    value={draft.design_philosophy || ''}
                                    onChange={e => setDraft({ ...draft, design_philosophy: e.target.value })}
                                    placeholder="Core ethos, design principles, constraints..."
                                />
                            </div>
                            <div className="col-span-2">
                                <label className="text-gray-500 text-xs uppercase font-bold mb-2 flex items-center justify-between">
                                    <span>External Links</span>
                                    <Button size="sm" variant="ghost" onClick={() => setDraft({
                                        ...draft,
                                        external_links: [...(draft.external_links || []), { label: '', url: '' }]
                                    })}>
                                        <Plus size={12} /> Add Link
                                    </Button>
                                </label>
                                <div className="space-y-2">
                                    {draft.external_links?.map((link, i) => (
                                        <div key={i} className="flex gap-2">
                                            <input
                                                className="w-1/3 bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none text-sm"
                                                placeholder="Label"
                                                value={link.label}
                                                onChange={e => {
                                                    const newLinks = [...draft.external_links!];
                                                    newLinks[i].label = e.target.value;
                                                    setDraft({ ...draft, external_links: newLinks });
                                                }}
                                            />
                                            <input
                                                className="flex-1 bg-white/5 border border-white/10 p-2 text-white rounded focus:border-accent outline-none text-sm font-mono"
                                                placeholder="URL"
                                                value={link.url}
                                                onChange={e => {
                                                    const newLinks = [...draft.external_links!];
                                                    newLinks[i].url = e.target.value;
                                                    setDraft({ ...draft, external_links: newLinks });
                                                }}
                                            />
                                            <Button size="sm" variant="ghost" className="text-red-400" onClick={() => {
                                                setDraft({ ...draft, external_links: draft.external_links?.filter((_, idx) => idx !== i) });
                                            }}>
                                                <X size={14} />
                                            </Button>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* TASKS TAB */}
                    {activeTab === 'tasks' && (
                        <div className="animate-in fade-in duration-150">
                            <div className="flex justify-between items-end mb-3">
                                <label className="text-gray-500 text-xs uppercase font-bold">Protocol Sequence (Tasks)</label>
                                <Button size="sm" variant="ghost" onClick={() => setDraft(prev => ({ ...prev, tasks: [...(prev.tasks || []), { title: 'New Task', phase: 'Planning', priority: 3 }] }))}>
                                    <Plus size={14} /> Add Step
                                </Button>
                            </div>
                            <div className="space-y-2" ref={taskListParent}>
                                {draft.tasks?.map((task, i) => (
                                    <div key={i} className="flex gap-2 items-center bg-white/5 p-2 rounded border border-white/5 group">
                                        <span className="text-gray-500 font-mono text-xs w-6 text-center">{i + 1}</span>
                                        <input
                                            className="flex-1 bg-transparent border-none text-sm text-white focus:outline-none"
                                            value={task.title}
                                            onChange={(e) => {
                                                const newTasks = [...draft.tasks!];
                                                newTasks[i].title = e.target.value;
                                                setDraft({ ...draft, tasks: newTasks });
                                            }}
                                        />
                                        <select
                                            className="bg-black/50 text-xs text-gray-400 border border-white/10 rounded px-1 py-1"
                                            value={task.phase}
                                            onChange={(e) => {
                                                const newTasks = [...draft.tasks!];
                                                newTasks[i].phase = e.target.value;
                                                setDraft({ ...draft, tasks: newTasks });
                                            }}
                                        >
                                            {['Planning', 'Design', 'Procurement', 'Fabrication', 'Testing', 'Release'].map(p => <option key={p} value={p}>{p}</option>)}
                                        </select>
                                        <select
                                            className="bg-black/50 text-xs text-gray-400 border border-white/10 rounded px-1 py-1 w-12"
                                            value={task.priority}
                                            onChange={(e) => {
                                                const newTasks = [...draft.tasks!];
                                                newTasks[i].priority = Number(e.target.value) as 1 | 2 | 3 | 4 | 5;
                                                setDraft({ ...draft, tasks: newTasks });
                                            }}
                                        >
                                            {[1, 2, 3, 4, 5].map(p => <option key={p} value={p}>P{p}</option>)}
                                        </select>
                                        <input
                                            className="w-16 bg-transparent text-xs text-gray-400 text-right border-b border-white/10 focus:border-accent outline-none"
                                            placeholder="Est."
                                            value={task.estimated_time || ''}
                                            onChange={(e) => {
                                                const newTasks = [...draft.tasks!];
                                                newTasks[i].estimated_time = e.target.value;
                                                setDraft({ ...draft, tasks: newTasks });
                                            }}
                                        />
                                        <Button size="sm" variant="ghost" className="opacity-0 group-hover:opacity-100 text-red-400" onClick={() => {
                                            const newTasks = draft.tasks!.filter((_, idx) => idx !== i);
                                            setDraft({ ...draft, tasks: newTasks });
                                        }}><X size={14} /></Button>
                                    </div>
                                ))}
                                {(!draft.tasks || draft.tasks.length === 0) && (
                                    <div className="text-center py-8 text-gray-600 italic border border-dashed border-white/10 rounded">
                                        No tasks defined. Ask the Oracle to generate some!
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                <div className="flex justify-end gap-2 border-t border-white/10 pt-4">
                    <Button variant="ghost" onClick={() => setIsEditing(false)}>Cancel</Button>
                    <Button variant="primary" onClick={handleSave}><Save size={16} className="mr-2" /> Save Blueprint</Button>
                </div>
            </div>
        );
    }

    // Helper to remove duplicate templates by name
    const handleRemoveDuplicates = async () => {
        const all = await db.project_templates.toArray();
        const seen = new Map<string, number>();
        const toDelete: number[] = [];

        for (const t of all) {
            if (seen.has(t.name)) {
                toDelete.push(t.id!);
            } else {
                seen.set(t.name, t.id!);
            }
        }

        if (toDelete.length === 0) {
            toast.info("No duplicates found.");
            return;
        }

        if (confirm(`Found ${toDelete.length} duplicate templates. Delete them?`)) {
            await db.project_templates.bulkDelete(toDelete);
            toast.success(`Removed ${toDelete.length} duplicates`);
        }
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-300">
            <div className="flex justify-between items-center">
                <div>
                    <h3 className="text-xl font-bold text-white">Blueprint Center</h3>
                    <p className="text-gray-500 text-xs">Manage project templates and automation protocols.</p>
                </div>
                <div className="flex gap-2">
                    <Button
                        onClick={handleRemoveDuplicates}
                        variant="ghost"
                        className="text-gray-500 hover:text-yellow-400"
                        title="Remove duplicate templates"
                    >
                        <Trash2 size={14} className="mr-1" /> Dedupe
                    </Button>
                    <Button onClick={handleCreateNew} className="bg-neon text-black font-bold hover:bg-white"><Plus size={16} className="mr-2" /> CREATE NEW</Button>
                </div>
            </div>

            {/* Template Grid - Combined */}
            <div>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {templates?.map(t => (
                        <Card key={t.id} className="hover:border-accent transition-colors group relative">
                            <div className="flex justify-between items-start mb-2">
                                <h5 className="font-bold text-lg text-white">{t.name}</h5>
                                <div className="flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                                    <Button size="sm" variant="ghost" onClick={() => handleEdit(t)}><Edit size={14} /></Button>
                                    <Button size="sm" variant="ghost" onClick={() => handleDelete(t.id!)} className="text-red-400 hover:text-red-300"><Trash2 size={14} /></Button>
                                </div>
                            </div>
                            <p className="text-xs text-gray-500 mb-3 line-clamp-2">{t.description}</p>
                            <div className="flex flex-wrap gap-1 mb-2">
                                <span className={clsx("text-[10px] px-2 py-0.5 rounded border uppercase font-bold", t.is_custom ? "bg-accent/10 text-accent border-accent/20" : "bg-white/5 text-gray-400 border-white/5")}>
                                    {t.category}
                                </span>
                                <span className="bg-white/5 text-gray-400 text-[10px] px-2 py-0.5 rounded border border-white/5">{t.tasks.length} Steps</span>
                                {t.priority && t.priority !== 3 && (
                                    <span className="bg-yellow-500/10 text-yellow-400 text-[10px] px-2 py-0.5 rounded border border-yellow-500/20">P{t.priority}</span>
                                )}
                                {t.risk_level && (
                                    <span className={clsx(
                                        "text-[10px] px-2 py-0.5 rounded border",
                                        t.risk_level === 'low' && "bg-green-500/10 text-green-400 border-green-500/20",
                                        t.risk_level === 'medium' && "bg-yellow-500/10 text-yellow-400 border-yellow-500/20",
                                        t.risk_level === 'high' && "bg-red-500/10 text-red-400 border-red-500/20"
                                    )}>
                                        {t.risk_level} risk
                                    </span>
                                )}
                            </div>
                            {t.tags && t.tags.length > 0 && (
                                <div className="flex flex-wrap gap-1">
                                    {t.tags.slice(0, 4).map(tag => (
                                        <span key={tag} className="text-[9px] bg-white/5 text-gray-500 px-1.5 py-0.5 rounded">{tag}</span>
                                    ))}
                                    {t.tags.length > 4 && <span className="text-[9px] text-gray-600">+{t.tags.length - 4}</span>}
                                </div>
                            )}
                        </Card>
                    ))}
                    {(!templates || templates.length === 0) && (
                        <div className="col-span-3 text-center py-10 border border-dashed border-gray-800 rounded bg-white/5">
                            <Ghost className="mx-auto text-gray-600 mb-2" />
                            <p className="text-gray-500 text-sm">No blueprints found. Check DB initialization.</p>
                            <Button
                                variant="ghost"
                                size="sm"
                                className="mt-2 text-xs text-accent"
                                onClick={() => BlueprintService.getAll().then(() => window.location.reload())}
                            >
                                Force Re-seed
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
