import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type SongDocument } from '../lib/db';
import { SongService } from '../services/SongService'; // Use Service
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Plus, FileText, Music, Clapperboard, GripVertical, Trash2, Edit2, Save, Maximize2, Minimize2, ChevronLeft, ChevronRight, Upload, Loader2, PanelLeft, Bot, Book } from 'lucide-react';
import { TipTapEditor } from './ui/TipTapEditor';
import { toast } from 'sonner';
import clsx from 'clsx';
import { useDropzone } from 'react-dropzone';
import { useUIStore } from '../store/useStore';

interface SongManuscriptProps {
    songId: number;
}

export function SongManuscript({ songId }: SongManuscriptProps) {
    const { setOracleChatOpen, isOracleChatOpen } = useUIStore();

    // Live Query for Documents
    const documents = useLiveQuery(() =>
        db.song_documents.where('song_id').equals(songId).sortBy('order')
    );

    const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
    const [editorContent, setEditorContent] = useState('');
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [titleEditValue, setTitleEditValue] = useState('');

    // UI States
    const [isZenMode, setIsZenMode] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
    const [toolbarContainer, setToolbarContainer] = useState<HTMLDivElement | null>(null);

    // Initial Selection
    useEffect(() => {
        if (documents && documents.length > 0 && selectedDocId === null) {
            setSelectedDocId(documents[0].id!);
            setEditorContent(documents[0].content);
            setTitleEditValue(documents[0].title);
        }
    }, [documents]);

    // Sync Editor State on Selection Change
    useEffect(() => {
        if (selectedDocId && documents) {
            const doc = documents.find(d => d.id === selectedDocId);
            if (doc) {
                setEditorContent(doc.content);
                setTitleEditValue(doc.title);
            }
        }
    }, [selectedDocId]);

    const handleSave = async () => {
        if (!selectedDocId) return;
        await SongService.updateDocument(selectedDocId, {
            content: editorContent
        });
        toast.success("Saved");
    };

    const handleCreateDoc = async () => {
        const count = documents?.length || 0;
        const id = await SongService.createDocument(songId, `Version ${count + 1}`, 'lyrics');
        setSelectedDocId(id as number);
        setEditorContent('');
        toast.success("New lyric sheet created");
    };

    const handleDeleteDoc = async (id: number) => {
        if (confirm("Delete this document?")) {
            await SongService.deleteDocument(id);
            if (selectedDocId === id) {
                setSelectedDocId(null);
                setEditorContent('');
            }
            toast.success("Deleted");
        }
    };

    const handleUpdateTitle = async () => {
        if (!selectedDocId) return;
        await SongService.updateDocument(selectedDocId, {
            title: titleEditValue
        });
        setIsEditingTitle(false);
    };

    // --- Drag & Drop Import Logic ---
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        let importedCount = 0;
        for (const file of acceptedFiles) {
            try {
                const text = await file.text();
                // Create Lyric Doc
                const docId = await SongService.createDocument(songId, file.name.replace(/\.(txt|md)$/i, ''), 'lyrics');
                await SongService.updateDocument(docId as number, { content: text });

                // Also add as File Asset
                await SongService.addFile(songId, file, 'attachment');

                if (importedCount === 0) setSelectedDocId(docId as number);
                importedCount++;
            } catch (err) {
                console.error("Import failed", err);
                toast.error(`Failed to import ${file.name}`);
            }
        }
        if (importedCount > 0) toast.success(`Imported ${importedCount} files`);
    }, [songId]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'text/*': ['.txt', '.md'] },
        noClick: true
    });

    const activeDoc = documents?.find(d => d.id === selectedDocId);

    const toggleZenMode = () => {
        if (!isZenMode) setIsSidebarCollapsed(true);
        setIsZenMode(!isZenMode);
    };

    const content = (
        <div className={clsx(
            "flex animate-in fade-in duration-300",
            isZenMode ? "fixed inset-0 z-[99999] bg-gray-950 p-0" : "h-full gap-4"
        )}>
            {/* Sidebar */}
            <div className={clsx(
                "flex flex-col gap-2 transition-all duration-300 relative",
                isZenMode && isSidebarCollapsed ? "w-0 overflow-hidden opacity-0" : isSidebarCollapsed ? "w-12 items-center" : isZenMode ? "w-64" : "w-1/4 min-w-[200px]",
                isZenMode && "bg-black/20"
            )}>
                <Card
                    {...getRootProps()}
                    className={clsx(
                        "flex-1 flex flex-col p-0 overflow-hidden bg-black/20 border-white/10 relative transition-all",
                        isDragActive && "border-accent ring-2 ring-accent/20 bg-accent/5"
                    )}
                >
                    <input {...getInputProps()} />

                    {!isSidebarCollapsed && (
                        <div className="p-3 border-b border-white/10 flex justify-between items-center bg-white/5">
                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Versions</span>
                            <Button size="sm" variant="ghost" onClick={handleCreateDoc}><Plus size={14} /></Button>
                        </div>
                    )}

                    {/* Drag Overlay */}
                    {isDragActive && !isSidebarCollapsed && (
                        <div className="absolute inset-0 z-10 flex items-center justify-center bg-black/60 backdrop-blur-sm">
                            <div className="text-center text-accent">
                                <Upload size={32} className="mx-auto mb-2 animate-bounce" />
                                <span className="text-xs font-bold uppercase">Drop to Import</span>
                            </div>
                        </div>
                    )}

                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                        className={clsx("z-20 text-gray-500 hover:text-white", isSidebarCollapsed ? "my-2" : "absolute right-2 top-[3.25rem]")}
                    >
                        {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </Button>

                    <div className="flex-1 overflow-y-auto p-2 space-y-1">
                        {documents?.map(doc => (
                            <div
                                key={doc.id}
                                onClick={() => setSelectedDocId(doc.id!)}
                                className={clsx(
                                    "group flex items-center gap-2 p-2 rounded cursor-pointer transition-all border",
                                    selectedDocId === doc.id ? "bg-accent/10 border-accent/50 text-accent" : "hover:bg-white/5 border-transparent text-gray-400",
                                    isSidebarCollapsed && "justify-center px-1"
                                )}
                            >
                                <FileText size={14} className="shrink-0" />
                                {!isSidebarCollapsed && <span className="text-sm truncate flex-1">{doc.title}</span>}
                            </div>
                        ))}
                    </div>
                </Card>
            </div>

            {/* Editor Area */}
            <div className="flex-1 flex flex-col min-w-0 transition-all">
                {selectedDocId && activeDoc ? (
                    <Card className={clsx("flex-1 flex flex-col p-0 overflow-hidden shadow-2xl", isZenMode ? "bg-black border-none" : "bg-gray-900 border-white/10")}>
                        {/* Toolbar */}
                        <div className="h-12 border-b border-white/10 flex items-center justify-between px-4 bg-white/5 shrink-0">
                            <div className="flex items-center gap-2">
                                {isEditingTitle ? (
                                    <input
                                        className="bg-black/50 border border-white/20 rounded px-2 py-1 text-sm text-white focus:outline-none focus:border-accent"
                                        value={titleEditValue}
                                        onChange={(e) => setTitleEditValue(e.target.value)}
                                        onBlur={handleUpdateTitle}
                                        onKeyDown={(e) => e.key === 'Enter' && handleUpdateTitle()}
                                        autoFocus
                                    />
                                ) : (
                                    <h3 onClick={() => setIsEditingTitle(true)} className="text-sm font-bold text-white cursor-pointer hover:underline truncate max-w-[200px]">{activeDoc.title}</h3>
                                )}
                            </div>

                            <div ref={setToolbarContainer} className="flex-1 flex justify-center px-4" />

                            <div className="flex items-center gap-2">
                                {isZenMode && isSidebarCollapsed && <Button size="sm" variant="ghost" onClick={() => setIsSidebarCollapsed(false)}><PanelLeft size={14} /></Button>}
                                <Button size="sm" variant="ghost" onClick={() => setOracleChatOpen(!isOracleChatOpen)} className={isOracleChatOpen ? "text-accent" : "text-gray-400"}><Bot size={14} /></Button>
                                <Button size="sm" variant="ghost" onClick={handleSave} className="text-green-400"><Save size={14} /></Button>
                                <Button size="sm" variant="ghost" onClick={toggleZenMode}>{isZenMode ? <Minimize2 size={14} /> : <Maximize2 size={14} />}</Button>
                                <Button size="sm" variant="ghost" onClick={() => handleDeleteDoc(selectedDocId)} className="text-red-400"><Trash2 size={14} /></Button>
                            </div>
                        </div>

                        <div className="flex-1 overflow-hidden relative bg-gray-950/50">
                            <div className="h-full overflow-y-auto custom-scrollbar">
                                <TipTapEditor
                                    key={selectedDocId}
                                    value={editorContent}
                                    onChange={setEditorContent}
                                    onSave={handleSave}
                                    toolbarContainer={toolbarContainer}
                                    className={clsx(
                                        "min-h-full !border-none !rounded-none focus-within:ring-0 !bg-transparent !shadow-none text-lg leading-relaxed mx-auto py-12 transition-all",
                                        isZenMode ? "max-w-3xl" : "max-w-2xl px-8"
                                    )}
                                />
                                <div className="h-20" />
                            </div>
                        </div>
                    </Card>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-500 flex-col gap-4">
                        <FileText size={48} className="opacity-20" />
                        <p>Select or create a version to start writing.</p>
                        <Button variant="outline" onClick={handleCreateDoc}><Plus size={16} className="mr-2" /> Create Version</Button>
                    </div>
                )}
            </div>
        </div>
    );

    if (isZenMode) return createPortal(content, document.body);
    return content;
}
