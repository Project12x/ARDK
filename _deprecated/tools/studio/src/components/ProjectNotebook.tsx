import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { db } from '../lib/db';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Save, Trash2, Calendar, Sparkles, Maximize2, Minimize2, Bot } from 'lucide-react';
import { TipTapEditor } from './ui/TipTapEditor';
import { useUIStore } from '../store/useStore';
import { createPortal } from 'react-dom';
import clsx from 'clsx';

interface ProjectNotebookProps {
    projectId: number;
}

export function ProjectNotebook({ projectId }: ProjectNotebookProps) {
    const { setOracleChatOpen, isOracleChatOpen } = useUIStore();
    const entries = useLiveQuery(() =>
        db.notebook.where('project_id').equals(projectId).reverse().sortBy('date')
    );
    const [isAdding, setIsAdding] = useState(false);
    const [newContent, setNewContent] = useState('');
    const [isZenMode, setIsZenMode] = useState(false);
    const [toolbarContainer, setToolbarContainer] = useState<HTMLDivElement | null>(null);

    const handleAdd = async () => {
        if (!newContent.trim()) return;
        await db.notebook.add({
            project_id: projectId,
            date: new Date(),
            content: newContent,
            tags: []
        });
        setNewContent('');
        setIsAdding(false);
    };

    const handleDelete = (id: number) => {
        if (confirm('Delete this entry?')) {
            db.notebook.delete(id);
        }
    };

    const content = (
        <div className={clsx(
            "space-y-6 animate-in fade-in duration-500 transition-all flex flex-col h-full",
            isZenMode ? "fixed inset-0 z-[99999] bg-black" : "relative"
        )}>
            {/* Quick Note Input Area (Now acting as main interface) */}
            <Card className={clsx(
                "transition-all flex flex-col p-0 overflow-hidden border-accent/20",
                isZenMode
                    ? "flex-1 rounded-none border-none"
                    : "border bg-accent/5"
            )}>
                {/* Unified Toolbar Header */}
                <div className="h-12 border-b border-white/10 flex items-center justify-between px-4 bg-white/5 shrink-0 gap-4">
                    <div className="flex items-center gap-3 shrink-0">
                        <h2 className="text-sm font-bold text-white uppercase tracking-tight">
                            {isZenMode ? "Note" : "Lab Notebook"}
                        </h2>
                    </div>

                    {/* PORTAL TARGET FOR TIPTAP TOOLBAR */}
                    <div ref={setToolbarContainer} className="flex-1 flex justify-center items-center overflow-x-auto no-scrollbar" />

                    <div className="flex items-center gap-2 shrink-0">
                        {/* Auto-Link */}
                        <Button
                            onClick={async () => {
                                const { NeurolinkService } = await import('../lib/neurolinks');
                                const linked = await NeurolinkService.linkify(newContent);
                                if (linked !== newContent) {
                                    setNewContent(linked);
                                    toast.success("✨ Entities Auto-Linked");
                                } else {
                                    toast.info("No known entities found.");
                                }
                            }}
                            variant="ghost"
                            size="sm"
                            disabled={!newContent.trim()}
                            className="text-purple-400 hover:text-purple-300 hover:bg-purple-900/20"
                            title="Auto-link known projects, inventory, and tasks"
                        >
                            <Sparkles size={14} />
                        </Button>

                        <div className="h-4 w-px bg-white/10 mx-1" />

                        {/* Oracle Trigger */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setOracleChatOpen(!isOracleChatOpen)}
                            className={clsx("hover:bg-white/10", isOracleChatOpen ? "text-accent" : "text-gray-400")}
                            title="Ask Oracle"
                        >
                            <Bot size={14} />
                        </Button>

                        {/* Zen Mode Toggle */}
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setIsZenMode(!isZenMode)}
                            className={clsx("hover:bg-white/10", isZenMode ? "text-accent" : "text-gray-400")}
                            title="Toggle Zen Mode"
                        >
                            {isZenMode ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                        </Button>

                        <div className="h-4 w-px bg-white/10 mx-1" />

                        {/* Save Button */}
                        <Button
                            onClick={handleAdd}
                            disabled={!newContent.trim() || newContent === '<p></p>'}
                            size="sm"
                            className="text-green-400 hover:text-green-300 hover:bg-green-900/20"
                        >
                            <Save size={14} className="mr-2" /> Save
                        </Button>
                    </div>
                </div>

                <div className={clsx("relative flex-1 flex flex-col", isZenMode && "flex-1")}>
                    <TipTapEditor
                        value={newContent}
                        onChange={setNewContent}
                        onSave={handleAdd}
                        placeholder="Quick Note: Write thoughts, use / commands, format with markdown..."
                        className={clsx(
                            "bg-black/50 !border-none !rounded-none focus-within:ring-0",
                            isZenMode ? "flex-1 h-full min-h-0 text-lg p-8 max-w-5xl mx-auto w-full" : "min-h-[150px]"
                        )}
                        toolbarContainer={toolbarContainer}
                    />
                    {/* Footer Info (Shortcuts) */}
                    <div className="absolute bottom-1 right-2 pointer-events-none opacity-50">
                        <span className="text-[10px] text-gray-500 font-mono">CTRL+ENTER to Save</span>
                    </div>
                </div>
            </Card>

            {!isZenMode && (
                <div className="space-y-4">
                    {entries?.map(entry => {
                        const isHtml = entry.content.trim().startsWith('<');
                        return (
                            <div key={entry.id} className="bg-white/5 border border-white/10 p-6 relative group hover:border-white/20 transition-all rounded-lg">
                                <div className="flex justify-between items-start mb-4 border-b border-white/5 pb-2">
                                    <div className="flex items-center gap-2 text-xs font-mono text-gray-500">
                                        <Calendar size={12} />
                                        <span>{(() => {
                                            const d = new Date(entry.date);
                                            return isNaN(d.getTime()) ? 'INVALID DATE' : d.toLocaleString();
                                        })()}</span>
                                    </div>
                                    <button
                                        onClick={() => entry.id && handleDelete(entry.id)}
                                        className="text-gray-600 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                                    >
                                        <Trash2 size={14} />
                                    </button>
                                </div>

                                {isHtml ? (
                                    <div
                                        className="prose prose-invert prose-sm max-w-none text-gray-300 font-mono [&_p]:mb-2 [&_h1]:text-white [&_h2]:text-white [&_strong]:text-white [&_code]:bg-white/10 [&_code]:px-1 [&_code]:rounded"
                                        dangerouslySetInnerHTML={{ __html: entry.content }}
                                    />
                                ) : (
                                    <div className="prose prose-invert prose-sm max-w-none text-gray-300 font-mono whitespace-pre-wrap">
                                        {entry.content}
                                    </div>
                                )}
                            </div>
                        );
                    })}

                    {entries?.length === 0 && !isAdding && (
                        <div className="text-center py-12 border border-dashed border-gray-800 rounded">
                            <p className="text-gray-600 font-mono italic">No notebook entries yet.</p>
                        </div>
                    )}
                </div>
            )}
        </div>
    );

    if (isZenMode) {
        return createPortal(content, document.body);
    }

    return content;
}
