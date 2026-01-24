import { useState, useRef } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { Link } from 'react-router-dom';
import { toast } from 'sonner';
import { db, type LLMInstruction } from '../lib/db';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import {
    Plus, Upload, FileText, GitBranch,
    Sparkles, Search, MoreVertical, Trash2, Copy
} from 'lucide-react';
import clsx from 'clsx';

// Categories for LLM Instructions
const INSTRUCTION_CATEGORIES = [
    'System',
    'Creative',
    'Technical',
    'Research',
    'Coding',
    'Analysis',
    'Roleplay',
    'Other'
];

export function InstructionsPage() {
    const instructions = useLiveQuery(() => db.llm_instructions.toArray());
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
    const [isImporting, setIsImporting] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Filter instructions
    const filteredInstructions = instructions?.filter(inst => {
        const matchesSearch = !searchQuery ||
            inst.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
            inst.description.toLowerCase().includes(searchQuery.toLowerCase()) ||
            inst.tags.some(t => t.toLowerCase().includes(searchQuery.toLowerCase()));
        const matchesCategory = !selectedCategory || inst.category === selectedCategory;
        return matchesSearch && matchesCategory;
    });

    // Handle batch file import
    const handleFileImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files || files.length === 0) return;

        setIsImporting(true);
        let imported = 0;

        try {
            for (const file of Array.from(files)) {
                if (!file.name.endsWith('.md') && !file.name.endsWith('.txt')) {
                    toast.warning(`Skipped ${file.name} - only .md and .txt supported`);
                    continue;
                }

                const content = await file.text();

                // Parse the file - extract metadata if present
                const parsed = parseInstructionFile(content, file.name);

                await db.llm_instructions.add({
                    name: parsed.name,
                    description: parsed.description,
                    category: parsed.category || 'Other',
                    tags: parsed.tags,
                    current_version: '1.0.0',
                    content: parsed.content,
                    versions: [{
                        version: '1.0.0',
                        content: parsed.content,
                        changelog: 'Initial import',
                        created_at: new Date()
                    }],
                    source_file: file.name,
                    token_estimate: estimateTokens(parsed.content),
                    is_active: false,
                    is_draft: true,
                    created_at: new Date(),
                    updated_at: new Date()
                });
                imported++;
            }

            toast.success(`Imported ${imported} instruction set${imported !== 1 ? 's' : ''}`);
        } catch (err) {
            console.error('Import error:', err);
            toast.error('Failed to import files');
        } finally {
            setIsImporting(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    // Create new blank instruction
    const handleCreateNew = async () => {
        await db.llm_instructions.add({
            name: 'New Instruction Set',
            description: '',
            category: 'Other',
            tags: [],
            current_version: '1.0.0',
            content: '',
            versions: [],
            is_active: false,
            is_draft: true,
            created_at: new Date(),
            updated_at: new Date()
        });
        toast.success('Created new instruction set');
        // Could navigate to detail page here
    };

    // Delete instruction
    const handleDelete = async (id: number) => {
        await db.llm_instructions.delete(id);
        toast.success('Deleted instruction set');
    };

    // Duplicate instruction
    const handleDuplicate = async (inst: LLMInstruction) => {
        const copy = { ...inst };
        delete copy.id;
        copy.name = `${inst.name} (Copy)`;
        copy.created_at = new Date();
        copy.updated_at = new Date();
        await db.llm_instructions.add(copy);
        toast.success('Duplicated instruction set');
    };

    return (
        <div className="min-h-screen bg-black p-6">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-black uppercase tracking-tight text-white flex items-center gap-3">
                        <Sparkles className="text-accent" size={28} />
                        LLM Instructions
                    </h1>
                    <p className="text-gray-500 text-sm mt-1">
                        Workshop and manage your custom AI instruction sets
                    </p>
                </div>
                <div className="flex gap-2">
                    <input
                        ref={fileInputRef}
                        type="file"
                        multiple
                        accept=".md,.txt"
                        onChange={handleFileImport}
                        className="hidden"
                    />
                    <Button
                        variant="ghost"
                        onClick={() => fileInputRef.current?.click()}
                        disabled={isImporting}
                    >
                        <Upload size={16} className="mr-2" />
                        {isImporting ? 'Importing...' : 'Import Files'}
                    </Button>
                    <Button onClick={handleCreateNew}>
                        <Plus size={16} className="mr-2" />
                        New
                    </Button>
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-6">
                <div className="flex-1 relative">
                    <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                    <Input
                        placeholder="Search instructions..."
                        value={searchQuery}
                        onChange={e => setSearchQuery(e.target.value)}
                        className="pl-10"
                    />
                </div>
                <div className="flex gap-1 bg-white/5 p-1 rounded border border-white/10">
                    <button
                        onClick={() => setSelectedCategory(null)}
                        className={clsx(
                            "px-3 py-1.5 text-xs font-bold uppercase rounded transition-colors",
                            !selectedCategory ? "bg-accent text-black" : "text-gray-400 hover:text-white"
                        )}
                    >
                        All
                    </button>
                    {INSTRUCTION_CATEGORIES.map(cat => (
                        <button
                            key={cat}
                            onClick={() => setSelectedCategory(selectedCategory === cat ? null : cat)}
                            className={clsx(
                                "px-3 py-1.5 text-xs font-bold uppercase rounded transition-colors",
                                selectedCategory === cat ? "bg-accent text-black" : "text-gray-400 hover:text-white"
                            )}
                        >
                            {cat}
                        </button>
                    ))}
                </div>
            </div>

            {/* Instructions Grid */}
            {!instructions || instructions.length === 0 ? (
                <div className="text-center py-20 border border-dashed border-gray-800 rounded-lg">
                    <Sparkles size={48} className="mx-auto text-gray-700 mb-4" />
                    <p className="text-gray-500 mb-4">No instruction sets yet</p>
                    <Button onClick={() => fileInputRef.current?.click()}>
                        <Upload size={16} className="mr-2" />
                        Import Your First Instructions
                    </Button>
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {filteredInstructions?.map(inst => (
                        <InstructionCard
                            key={inst.id}
                            instruction={inst}
                            onDelete={() => handleDelete(inst.id!)}
                            onDuplicate={() => handleDuplicate(inst)}
                        />
                    ))}
                </div>
            )}
        </div>
    );
}

// === Instruction Card Component ===
function InstructionCard({
    instruction,
    onDelete,
    onDuplicate
}: {
    instruction: LLMInstruction;
    onDelete: () => void;
    onDuplicate: () => void;
}) {
    const [showMenu, setShowMenu] = useState(false);

    return (
        <Card className="group hover:border-accent/50 transition-all relative">
            <Link to={`/instructions/${instruction.id}`} className="block p-4">
                {/* Header */}
                <div className="flex items-start justify-between mb-3">
                    <div className="flex-1">
                        <h3 className="font-bold text-white group-hover:text-accent transition-colors">
                            {instruction.name}
                        </h3>
                        <span className={clsx(
                            "inline-block text-[10px] font-bold uppercase px-2 py-0.5 rounded mt-1",
                            instruction.is_draft
                                ? "bg-yellow-500/20 text-yellow-400"
                                : instruction.is_active
                                    ? "bg-green-500/20 text-green-400"
                                    : "bg-gray-500/20 text-gray-400"
                        )}>
                            {instruction.is_draft ? 'Draft' : instruction.is_active ? 'Active' : 'Inactive'}
                        </span>
                    </div>
                    <span className="text-[10px] font-mono text-gray-500 bg-white/5 px-2 py-1 rounded">
                        v{instruction.current_version}
                    </span>
                </div>

                {/* Description */}
                <p className="text-sm text-gray-400 line-clamp-2 mb-3">
                    {instruction.description || 'No description'}
                </p>

                {/* Tags */}
                {instruction.tags.length > 0 && (
                    <div className="flex flex-wrap gap-1 mb-3">
                        {instruction.tags.slice(0, 4).map(tag => (
                            <span key={tag} className="text-[10px] bg-accent/10 text-accent px-2 py-0.5 rounded">
                                {tag}
                            </span>
                        ))}
                        {instruction.tags.length > 4 && (
                            <span className="text-[10px] text-gray-500">+{instruction.tags.length - 4}</span>
                        )}
                    </div>
                )}

                {/* Footer Meta */}
                <div className="flex items-center justify-between text-[10px] text-gray-500 pt-3 border-t border-white/5">
                    <div className="flex items-center gap-3">
                        <span className="flex items-center gap-1">
                            <FileText size={10} />
                            {instruction.category}
                        </span>
                        {instruction.token_estimate && (
                            <span className="flex items-center gap-1">
                                ~{Math.round(instruction.token_estimate / 100) / 10}k tokens
                            </span>
                        )}
                    </div>
                    {instruction.github_repo && (
                        <span className="flex items-center gap-1 text-blue-400">
                            <GitBranch size={10} />
                            Linked
                        </span>
                    )}
                </div>
            </Link>

            {/* Actions Menu */}
            <div className="absolute top-3 right-3">
                <button
                    onClick={(e) => { e.preventDefault(); setShowMenu(!showMenu); }}
                    className="p-1.5 rounded hover:bg-white/10 transition-colors"
                >
                    <MoreVertical size={14} className="text-gray-500" />
                </button>
                {showMenu && (
                    <div className="absolute right-0 mt-1 bg-neutral-900 border border-white/10 rounded shadow-xl z-10 min-w-[120px]">
                        <button
                            onClick={(e) => { e.preventDefault(); onDuplicate(); setShowMenu(false); }}
                            className="w-full px-3 py-2 text-left text-sm text-gray-300 hover:bg-white/5 flex items-center gap-2"
                        >
                            <Copy size={12} /> Duplicate
                        </button>
                        <button
                            onClick={(e) => { e.preventDefault(); onDelete(); setShowMenu(false); }}
                            className="w-full px-3 py-2 text-left text-sm text-red-400 hover:bg-red-500/10 flex items-center gap-2"
                        >
                            <Trash2 size={12} /> Delete
                        </button>
                    </div>
                )}
            </div>
        </Card>
    );
}

// === Utility Functions ===

// Parse instruction file - look for YAML frontmatter or comments
function parseInstructionFile(content: string, filename: string): {
    name: string;
    description: string;
    category?: string;
    tags: string[];
    content: string;
} {
    // Remove file extension for default name
    const name = filename.replace(/\.(md|txt)$/i, '').replace(/_/g, ' ');

    // Check for YAML frontmatter
    const frontmatterMatch = content.match(/^---\n([\s\S]*?)\n---/);
    if (frontmatterMatch) {
        const frontmatter = frontmatterMatch[1];
        const extractedContent = content.slice(frontmatterMatch[0].length).trim();

        // Parse simple YAML-like frontmatter
        const getName = frontmatter.match(/name:\s*(.+)/i)?.[1]?.trim();
        const getDesc = frontmatter.match(/description:\s*(.+)/i)?.[1]?.trim();
        const getCat = frontmatter.match(/category:\s*(.+)/i)?.[1]?.trim();
        const getTags = frontmatter.match(/tags:\s*\[(.+)\]/i)?.[1]?.split(',').map(t => t.trim()) || [];

        return {
            name: getName || name,
            description: getDesc || '',
            category: getCat,
            tags: getTags,
            content: extractedContent
        };
    }

    // Check for first-line title (# Title)
    const titleMatch = content.match(/^#\s+(.+)/m);
    const extractedName = titleMatch?.[1] || name;

    return {
        name: extractedName,
        description: '',
        tags: [],
        content: content
    };
}

// Rough token estimation (4 chars ≈ 1 token for English)
function estimateTokens(text: string): number {
    return Math.ceil(text.length / 4);
}

export default InstructionsPage;
