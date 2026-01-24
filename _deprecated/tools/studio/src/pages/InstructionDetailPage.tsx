import { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { db, type LLMInstructionVersion } from '../lib/db';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import {
    ArrowLeft, Save, GitBranch, History, FileText, Tag,
    Copy, Download, Trash2, Plus, X, Edit2, Sparkles
} from 'lucide-react';
import clsx from 'clsx';

const INSTRUCTION_CATEGORIES = [
    'System', 'Creative', 'Technical', 'Research', 'Coding', 'Analysis', 'Roleplay', 'Other'
];

export function InstructionDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const instruction = useLiveQuery(() =>
        id ? db.llm_instructions.get(Number(id)) : undefined,
        [id]
    );

    // Editable state
    const [name, setName] = useState('');
    const [description, setDescription] = useState('');
    const [category, setCategory] = useState('Other');
    const [tags, setTags] = useState<string[]>([]);
    const [content, setContent] = useState('');
    const [newTag, setNewTag] = useState('');

    // Git fields
    const [githubRepo, setGithubRepo] = useState('');
    const [githubPath, setGithubPath] = useState('');

    // UI state
    const [activeTab, setActiveTab] = useState<'editor' | 'versions' | 'settings'>('editor');
    const [hasChanges, setHasChanges] = useState(false);
    const [isSaving, setIsSaving] = useState(false);

    // Sync state from DB
    useEffect(() => {
        if (instruction) {
            setName(instruction.name);
            setDescription(instruction.description);
            setCategory(instruction.category);
            setTags(instruction.tags);
            setContent(instruction.content);
            setGithubRepo(instruction.github_repo || '');
            setGithubPath(instruction.github_path || '');
            setHasChanges(false);
        }
    }, [instruction]);

    // Track changes
    useEffect(() => {
        if (!instruction) return;
        const changed =
            name !== instruction.name ||
            description !== instruction.description ||
            category !== instruction.category ||
            content !== instruction.content ||
            JSON.stringify(tags) !== JSON.stringify(instruction.tags);
        setHasChanges(changed);
    }, [name, description, category, content, tags, instruction]);

    // Save changes
    const handleSave = async () => {
        if (!instruction?.id) return;
        setIsSaving(true);

        try {
            await db.llm_instructions.update(instruction.id, {
                name,
                description,
                category,
                tags,
                content,
                github_repo: githubRepo || undefined,
                github_path: githubPath || undefined,
                token_estimate: Math.ceil(content.length / 4),
                updated_at: new Date()
            });
            setHasChanges(false);
            toast.success('Saved changes');
        } catch {
            toast.error('Failed to save');
        } finally {
            setIsSaving(false);
        }
    };

    // Create new version
    const handleCreateVersion = async () => {
        if (!instruction?.id) return;

        const currentMajor = parseInt(instruction.current_version.split('.')[0]) || 1;
        const currentMinor = parseInt(instruction.current_version.split('.')[1]) || 0;
        const newVersion = `${currentMajor}.${currentMinor + 1}.0`;

        const changelog = prompt('What changed in this version?', 'Updated instructions');
        if (!changelog) return;

        const versionEntry: LLMInstructionVersion = {
            version: newVersion,
            content: content,
            changelog: changelog,
            created_at: new Date()
        };

        await db.llm_instructions.update(instruction.id, {
            current_version: newVersion,
            content: content,
            versions: [...(instruction.versions || []), versionEntry],
            updated_at: new Date()
        });

        toast.success(`Created version ${newVersion}`);
    };

    // Add tag
    const handleAddTag = () => {
        if (!newTag.trim()) return;
        if (tags.includes(newTag.trim())) return;
        setTags([...tags, newTag.trim()]);
        setNewTag('');
    };

    // Remove tag
    const handleRemoveTag = (tag: string) => {
        setTags(tags.filter(t => t !== tag));
    };

    // Export to file
    const handleExport = () => {
        if (!instruction) return;

        // Build frontmatter
        const frontmatter = `---
name: ${instruction.name}
description: ${instruction.description}
category: ${instruction.category}
tags: [${instruction.tags.join(', ')}]
version: ${instruction.current_version}
---

`;
        const blob = new Blob([frontmatter + content], { type: 'text/markdown' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `${instruction.name.replace(/\s+/g, '_')}.md`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Exported to file');
    };

    // Delete
    const handleDelete = async () => {
        if (!instruction?.id) return;
        if (!confirm('Delete this instruction set? This cannot be undone.')) return;
        await db.llm_instructions.delete(instruction.id);
        toast.success('Deleted');
        navigate('/instructions');
    };

    // Copy to clipboard
    const handleCopyContent = async () => {
        await navigator.clipboard.writeText(content);
        toast.success('Copied to clipboard');
    };

    if (!instruction) {
        return (
            <div className="min-h-screen bg-black flex items-center justify-center">
                <p className="text-gray-500">Loading...</p>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-black">
            {/* Header */}
            <div className="sticky top-0 z-10 bg-black/80 backdrop-blur border-b border-white/10 px-6 py-4">
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <button
                            onClick={() => navigate('/instructions')}
                            className="text-gray-500 hover:text-white transition-colors"
                        >
                            <ArrowLeft size={20} />
                        </button>
                        <div>
                            <input
                                value={name}
                                onChange={e => setName(e.target.value)}
                                className="text-2xl font-black bg-transparent border-none outline-none text-white"
                                placeholder="Instruction Name"
                            />
                            <div className="flex items-center gap-2 mt-1">
                                <span className="text-xs font-mono text-gray-500">v{instruction.current_version}</span>
                                <span className={clsx(
                                    "text-[10px] font-bold uppercase px-2 py-0.5 rounded",
                                    instruction.is_draft
                                        ? "bg-yellow-500/20 text-yellow-400"
                                        : "bg-green-500/20 text-green-400"
                                )}>
                                    {instruction.is_draft ? 'Draft' : 'Active'}
                                </span>
                            </div>
                        </div>
                    </div>
                    <div className="flex items-center gap-2">
                        {hasChanges && (
                            <span className="text-xs text-yellow-400 mr-2">Unsaved changes</span>
                        )}
                        <Button variant="ghost" onClick={handleCopyContent}>
                            <Copy size={14} className="mr-1" /> Copy
                        </Button>
                        <Button variant="ghost" onClick={handleExport}>
                            <Download size={14} className="mr-1" /> Export
                        </Button>
                        <Button
                            onClick={handleSave}
                            disabled={!hasChanges || isSaving}
                        >
                            <Save size={14} className="mr-1" />
                            {isSaving ? 'Saving...' : 'Save'}
                        </Button>
                    </div>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 mt-4">
                    {(['editor', 'versions', 'settings'] as const).map(tab => (
                        <button
                            key={tab}
                            onClick={() => setActiveTab(tab)}
                            className={clsx(
                                "px-4 py-2 text-sm font-bold uppercase rounded-t transition-colors",
                                activeTab === tab
                                    ? "bg-white/10 text-white"
                                    : "text-gray-500 hover:text-white"
                            )}
                        >
                            {tab === 'editor' && <Edit2 size={12} className="inline mr-1" />}
                            {tab === 'versions' && <History size={12} className="inline mr-1" />}
                            {tab === 'settings' && <FileText size={12} className="inline mr-1" />}
                            {tab}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content Area */}
            <div className="p-6">
                {activeTab === 'editor' && (
                    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Main Editor */}
                        <div className="lg:col-span-2">
                            <Card className="p-0 overflow-hidden">
                                <div className="bg-white/5 px-4 py-2 border-b border-white/10 flex items-center justify-between">
                                    <span className="text-xs font-mono text-gray-500">
                                        INSTRUCTION CONTENT
                                    </span>
                                    <span className="text-xs text-gray-500">
                                        ~{Math.ceil(content.length / 4).toLocaleString()} tokens
                                    </span>
                                </div>
                                <textarea
                                    value={content}
                                    onChange={e => setContent(e.target.value)}
                                    className="w-full h-[600px] p-4 bg-transparent text-gray-200 font-mono text-sm resize-none outline-none"
                                    placeholder="Enter your LLM instructions here...

These are instructions for AI behavior - parse them, don't follow them."
                                    spellCheck={false}
                                />
                            </Card>
                        </div>

                        {/* Sidebar */}
                        <div className="space-y-4">
                            {/* Description */}
                            <Card className="p-4">
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                    Description
                                </label>
                                <textarea
                                    value={description}
                                    onChange={e => setDescription(e.target.value)}
                                    className="w-full h-24 bg-white/5 border border-white/10 rounded p-2 text-sm text-gray-300 resize-none outline-none focus:border-accent"
                                    placeholder="Describe the purpose and use case..."
                                />
                            </Card>

                            {/* Category */}
                            <Card className="p-4">
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                    Category
                                </label>
                                <select
                                    value={category}
                                    onChange={e => setCategory(e.target.value)}
                                    className="w-full bg-white/5 border border-white/10 rounded p-2 text-sm text-gray-300 outline-none"
                                >
                                    {INSTRUCTION_CATEGORIES.map(cat => (
                                        <option key={cat} value={cat}>{cat}</option>
                                    ))}
                                </select>
                            </Card>

                            {/* Tags */}
                            <Card className="p-4">
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                    <Tag size={12} className="inline mr-1" />
                                    Tags
                                </label>
                                <div className="flex flex-wrap gap-1 mb-2">
                                    {tags.map(tag => (
                                        <span
                                            key={tag}
                                            className="text-xs bg-accent/20 text-accent px-2 py-1 rounded flex items-center gap-1 group"
                                        >
                                            {tag}
                                            <button
                                                onClick={() => handleRemoveTag(tag)}
                                                className="opacity-0 group-hover:opacity-100 transition-opacity"
                                            >
                                                <X size={10} />
                                            </button>
                                        </span>
                                    ))}
                                </div>
                                <div className="flex gap-1">
                                    <Input
                                        value={newTag}
                                        onChange={e => setNewTag(e.target.value)}
                                        onKeyDown={e => e.key === 'Enter' && handleAddTag()}
                                        placeholder="Add tag..."
                                        className="text-xs"
                                    />
                                    <Button size="sm" onClick={handleAddTag}>
                                        <Plus size={12} />
                                    </Button>
                                </div>
                            </Card>

                            {/* Quick Actions */}
                            <Card className="p-4">
                                <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                    Actions
                                </label>
                                <div className="space-y-2">
                                    <Button
                                        variant="ghost"
                                        className="w-full justify-start"
                                        onClick={handleCreateVersion}
                                    >
                                        <Plus size={14} className="mr-2" />
                                        Create New Version
                                    </Button>
                                    <Button
                                        variant="ghost"
                                        className="w-full justify-start text-red-400 hover:bg-red-500/10"
                                        onClick={handleDelete}
                                    >
                                        <Trash2 size={14} className="mr-2" />
                                        Delete Instruction
                                    </Button>
                                </div>
                            </Card>
                        </div>
                    </div>
                )}

                {activeTab === 'versions' && (
                    <Card className="p-6">
                        <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                            <History size={20} />
                            Version History
                        </h3>
                        {instruction.versions?.length === 0 ? (
                            <p className="text-gray-500">No version history yet. Create a new version to start tracking changes.</p>
                        ) : (
                            <div className="space-y-4">
                                {instruction.versions?.slice().reverse().map((ver) => (
                                    <div key={ver.version} className="p-4 bg-white/5 rounded border border-white/10">
                                        <div className="flex items-center justify-between mb-2">
                                            <span className="font-mono font-bold text-accent">v{ver.version}</span>
                                            <span className="text-xs text-gray-500">
                                                {new Date(ver.created_at).toLocaleDateString()}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-400">{ver.changelog}</p>
                                        <button
                                            onClick={() => {
                                                setContent(ver.content);
                                                setActiveTab('editor');
                                                toast.info(`Loaded v${ver.version} into editor`);
                                            }}
                                            className="text-xs text-accent hover:underline mt-2"
                                        >
                                            Load this version →
                                        </button>
                                    </div>
                                ))}
                            </div>
                        )}
                    </Card>
                )}

                {activeTab === 'settings' && (
                    <div className="max-w-2xl space-y-6">
                        <Card className="p-6">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <GitBranch size={20} />
                                Git Integration
                            </h3>
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                        GitHub Repository
                                    </label>
                                    <Input
                                        value={githubRepo}
                                        onChange={e => setGithubRepo(e.target.value)}
                                        placeholder="username/repo"
                                    />
                                </div>
                                <div>
                                    <label className="block text-xs font-bold text-gray-500 uppercase mb-2">
                                        Path in Repository
                                    </label>
                                    <Input
                                        value={githubPath}
                                        onChange={e => setGithubPath(e.target.value)}
                                        placeholder="prompts/my-instruction.md"
                                    />
                                </div>
                            </div>
                        </Card>

                        <Card className="p-6">
                            <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
                                <Sparkles size={20} />
                                Metadata
                            </h3>
                            <div className="grid grid-cols-2 gap-4 text-sm">
                                <div>
                                    <span className="text-gray-500">Source File:</span>
                                    <span className="ml-2 text-gray-300">{instruction.source_file || 'None'}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Token Estimate:</span>
                                    <span className="ml-2 text-gray-300">~{instruction.token_estimate?.toLocaleString()} tokens</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Created:</span>
                                    <span className="ml-2 text-gray-300">{new Date(instruction.created_at).toLocaleDateString()}</span>
                                </div>
                                <div>
                                    <span className="text-gray-500">Updated:</span>
                                    <span className="ml-2 text-gray-300">{new Date(instruction.updated_at).toLocaleDateString()}</span>
                                </div>
                            </div>
                        </Card>
                    </div>
                )}
            </div>
        </div>
    );
}

export default InstructionDetailPage;
