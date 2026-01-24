import Editor, { type OnMount } from '@monaco-editor/react';
import { useState, useEffect, useRef } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { db } from '../lib/db';
import { Plus, Save, Trash2, Code, FileCode, Maximize2, Minimize2, Braces, MessageSquare, Bot, Book } from 'lucide-react';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { createPortal } from 'react-dom';
import clsx from 'clsx';
import { useUIStore } from '../store/useStore';

interface ProjectScriptsProps {
    projectId: number;
}

export function ProjectScripts({ projectId }: ProjectScriptsProps) {
    const { setOracleChatOpen, isOracleChatOpen, setNotebookPanelOpen, isNotebookPanelOpen } = useUIStore();
    const scripts = useLiveQuery(() => db.project_scripts.where({ project_id: projectId }).toArray());
    const [activeScriptId, setActiveScriptId] = useState<number | null>(null);
    const [code, setCode] = useState('');
    const [isCreating, setIsCreating] = useState(false);
    const [newScriptName, setNewScriptName] = useState('');
    const [newScriptLang, setNewScriptLang] = useState('javascript');

    // Zen Mode State
    const [isZenMode, setIsZenMode] = useState(false);

    // Editor Ref for Actions
    const editorRef = useRef<any>(null);

    const activeScript = scripts?.find(s => s.id === activeScriptId);

    useEffect(() => {
        if (activeScript) {
            setCode(activeScript.content);
        } else {
            setCode('');
        }
    }, [activeScript]);

    const handleCreate = async () => {
        if (!newScriptName) return;
        try {
            const id = await db.project_scripts.add({
                project_id: projectId,
                name: newScriptName,
                language: newScriptLang,
                content: '// Start coding...',
                created_at: new Date(),
                updated_at: new Date()
            });
            setActiveScriptId(id as number);
            setIsCreating(false);
            setNewScriptName('');
        } catch (error) {
            console.error("Failed to create script:", error);
            toast.error(`Failed to create script: ${error}`);
        }
    };

    const handleSave = async () => {
        if (!activeScriptId) return;
        try {
            await db.project_scripts.update(activeScriptId, {
                content: code,
                updated_at: new Date()
            });
            toast.success("Script saved");
        } catch (error) {
            console.error("Failed to save script:", error);
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm('Are you sure you want to delete this script?')) {
            await db.project_scripts.delete(id);
            if (activeScriptId === id) setActiveScriptId(null);
        }
    };

    const handleEditorDidMount: OnMount = (editor, monaco) => {
        editorRef.current = editor;
    };

    const handleFormat = () => {
        if (editorRef.current) {
            editorRef.current.getAction('editor.action.formatDocument').run();
        }
    };

    const handleToggleComment = () => {
        if (editorRef.current) {
            editorRef.current.getAction('editor.action.commentLine').run();
        }
    };

    const content = (
        <div
            className={clsx(
                "flex border border-white/10 rounded-lg overflow-hidden bg-[#1e1e1e] transition-all duration-300",
                isZenMode ? "fixed inset-0 z-[99999] bg-[#1e1e1e] p-4" : "h-[600px]"
            )}
        >
            {/* Sidebar (Collapsed in Zen Mode) */}
            <div
                className={clsx(
                    "border-r border-white/10 bg-black/50 flex flex-col shrink-0 transition-all duration-300",
                    isZenMode ? "w-0 overflow-hidden opacity-0" : "w-64 opacity-100"
                )}
            >
                <div className="p-3 border-b border-white/10 flex justify-between items-center bg-[#252526]">
                    <span className="text-xs font-bold uppercase text-gray-400 flex items-center gap-2">
                        <Code size={14} /> Explorer
                    </span>
                    <Button
                        size="sm"
                        variant="ghost"
                        onClick={() => setIsCreating(!isCreating)}
                        className="h-6 w-6 p-0 hover:bg-white/10 text-gray-400 hover:text-white"
                    >
                        <Plus size={14} />
                    </Button>
                </div>

                {isCreating && (
                    <div className="p-2 bg-[#2d2d2d] space-y-2 border-b border-white/10 animate-in slide-in-from-top-2">
                        <Input
                            placeholder="Script Name..."
                            value={newScriptName}
                            onChange={e => setNewScriptName(e.target.value)}
                            className="h-7 text-xs bg-[#3c3c3c] border-transparent focus:border-accent text-white"
                            autoFocus
                        />
                        <select
                            value={newScriptLang}
                            onChange={e => setNewScriptLang(e.target.value)}
                            className="w-full h-7 text-xs bg-[#3c3c3c] text-white border-transparent rounded px-2 outline-none focus:ring-1 ring-accent"
                        >
                            <option value="javascript">JavaScript</option>
                            <option value="typescript">TypeScript</option>
                            <option value="python">Python</option>
                            <option value="json">JSON</option>
                            <option value="html">HTML</option>
                            <option value="css">CSS</option>
                            <option value="cpp">C++</option>
                            <option value="arduino">Arduino (C++)</option>
                        </select>
                        <div className="flex justify-end gap-1">
                            <Button size="sm" variant="ghost" onClick={() => setIsCreating(false)} className="h-6 text-[10px]">Cancel</Button>
                            <Button size="sm" onClick={handleCreate} className="h-6 text-[10px] bg-accent text-black hover:bg-accent/90">Create</Button>
                        </div>
                    </div>
                )}

                <div className="flex-1 overflow-y-auto">
                    {scripts?.map(script => (
                        <div
                            key={script.id}
                            onClick={() => setActiveScriptId(script.id as number)}
                            className={clsx(
                                "group flex items-center justify-between px-3 py-2 text-sm cursor-pointer border-l-2 transition-colors",
                                activeScriptId === script.id
                                    ? "bg-[#37373d] text-white border-accent"
                                    : "text-gray-400 border-transparent hover:bg-[#2a2d2e] hover:text-gray-200"
                            )}
                        >
                            <div className="flex items-center gap-2 truncate">
                                <FileCode size={14} className={activeScriptId === script.id ? "text-accent" : "text-gray-500"} />
                                <span className="truncate">{script.name}</span>
                            </div>
                        </div>
                    ))}
                    {scripts?.length === 0 && !isCreating && (
                        <div className="p-4 text-center text-xs text-gray-600 italic">
                            No scripts created.
                        </div>
                    )}
                </div>
            </div>

            {/* Main Editor Area */}
            <div className="flex-1 flex flex-col bg-[#1e1e1e] overflow-hidden">
                {activeScript ? (
                    <>
                        <div className="h-9 flex items-center justify-between px-4 bg-[#1e1e1e] border-b border-white/5 shrink-0">
                            <div className="flex items-center gap-2">
                                <span className="text-sm font-mono text-gray-300">{activeScript.name}</span>
                                <span className="text-xs text-gray-400 bg-white/5 px-2 py-0.5 rounded uppercase border border-white/5">{activeScript.language}</span>
                            </div>
                            <div className="flex items-center gap-2">
                                {/* AI & Tools */}
                                <button
                                    onClick={() => setOracleChatOpen(!isOracleChatOpen)}
                                    title="Oracle Chat"
                                    className={clsx(
                                        "flex items-center justify-center h-6 w-6 rounded hover:bg-white/10 transition-colors focus:outline-none",
                                        isOracleChatOpen ? "text-accent" : "text-gray-400 hover:text-white"
                                    )}
                                >
                                    <Bot size={14} />
                                </button>
                                <div className="h-4 w-px bg-white/10 mx-1" />

                                {/* Code Formatting Tools */}
                                <button
                                    onClick={handleFormat}
                                    title="Format Document"
                                    className="flex items-center justify-center h-6 w-6 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors focus:outline-none"
                                >
                                    <Braces size={14} />
                                </button>
                                <button
                                    onClick={handleToggleComment}
                                    title="Toggle Comment"
                                    className="flex items-center justify-center h-6 w-6 rounded hover:bg-white/10 text-gray-400 hover:text-white transition-colors focus:outline-none"
                                >
                                    <MessageSquare size={14} />
                                </button>
                                <div className="h-4 w-px bg-white/10 mx-1" />

                                <button
                                    onClick={() => handleDelete(activeScript.id as number)}
                                    className="flex items-center justify-center h-6 w-6 rounded hover:bg-white/10 text-gray-400 hover:text-red-400 transition-colors focus:outline-none"
                                >
                                    <Trash2 size={14} />
                                </button>
                                <div className="h-4 w-px bg-white/10 mx-1" />
                                <button
                                    onClick={() => setIsZenMode(!isZenMode)}
                                    className={clsx(
                                        "flex items-center justify-center h-6 w-6 rounded hover:bg-white/10 transition-colors focus:outline-none",
                                        isZenMode ? "text-accent" : "text-gray-400 hover:text-white"
                                    )}
                                    title="Toggle Zen Mode"
                                >
                                    {isZenMode ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                                </button>
                                <div className="h-4 w-px bg-white/10 mx-1" />
                                <Button
                                    size="sm"
                                    onClick={handleSave}
                                    className="h-6 text-xs bg-[#007acc] hover:bg-[#0062a3] text-white gap-1 px-3 border-none"
                                >
                                    <Save size={13} /> Save
                                </Button>
                            </div>
                        </div>
                        <div className="flex-1 relative">
                            <Editor
                                height="100%"
                                defaultLanguage={activeScript.language === 'arduino' ? 'cpp' : activeScript.language}
                                language={activeScript.language === 'arduino' ? 'cpp' : activeScript.language}
                                value={code}
                                onChange={(value) => setCode(value || '')}
                                onMount={handleEditorDidMount}
                                theme="vs-dark"
                                options={{
                                    minimap: { enabled: !isZenMode },
                                    fontSize: isZenMode ? 16 : 14,
                                    wordWrap: 'on',
                                    scrollBeyondLastLine: false,
                                    automaticLayout: true,
                                    padding: { top: 16 }
                                }}
                            />
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex flex-col items-center justify-center text-gray-500 gap-2">
                        <Code size={48} className="opacity-20" />
                        <p className="text-sm">Select a script to edit or create a new one.</p>
                        <Button
                            variant="outline"
                            onClick={() => setIsCreating(true)}
                            className="mt-2"
                        >
                            <Plus size={16} className="mr-2" /> Create Script
                        </Button>
                    </div>
                )}
            </div>
        </div>
    );

    if (isZenMode) {
        return createPortal(content, document.body);
    }

    return content;
}
