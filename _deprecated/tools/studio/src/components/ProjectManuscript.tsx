import { useState, useEffect, useCallback } from 'react';
import { createPortal } from 'react-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type ProjectDocument } from '../lib/db';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Plus, FileText, Music, Clapperboard, GripVertical, Trash2, Edit2, Save, Maximize2, Minimize2, ChevronLeft, ChevronRight, Upload, Loader2, PanelLeft, Bot, Book, Download } from 'lucide-react';
import { TipTapEditor } from './ui/TipTapEditor';
import { toast } from 'sonner';
import clsx from 'clsx';
import { useDropzone } from 'react-dropzone';
import { useUIStore } from '../store/useStore';
import { useExportFlow } from '../hooks/useExportFlow';
import { ExportDialog } from './ui/ExportComponents/ExportDialog';
import { StandardManuscriptStrategy, PublisherManuscriptStrategy } from '../lib/strategies/manuscriptStrategies';

interface ProjectManuscriptProps {
    projectId: number;
    projectCategory?: string;
}

export function ProjectManuscript({ projectId, projectCategory }: ProjectManuscriptProps) {
    const { setOracleChatOpen, isOracleChatOpen, setNotebookPanelOpen, isNotebookPanelOpen } = useUIStore();
    const documents = useLiveQuery(() =>
        db.project_documents.where('project_id').equals(projectId).sortBy('order')
    );

    const [selectedDocId, setSelectedDocId] = useState<number | null>(null);
    const [editorContent, setEditorContent] = useState('');
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [titleEditValue, setTitleEditValue] = useState('');

    // UI States
    const [isZenMode, setIsZenMode] = useState(false);
    const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);

    const { isExportOpen, openExport, closeExport, exportContext } = useExportFlow();

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
        await db.project_documents.update(selectedDocId, {
            content: editorContent,
            updated_at: new Date()
        });
        toast.success("Document saved");
    };

    const handleCreateDoc = async () => {
        const count = documents?.length || 0;
        const type = projectCategory?.toLowerCase().includes('music') ? 'song' :
            projectCategory?.toLowerCase().includes('video') ? 'scene' : 'chapter';

        const id = await db.project_documents.add({
            project_id: projectId,
            title: `Untitled ${type === 'song' ? 'Song' : type === 'scene' ? 'Scene' : 'Chapter'} ${count + 1}`,
            content: '',
            order: count,
            type: type as any,
            status: 'draft',
            updated_at: new Date()
        });

        setSelectedDocId(id as number);
        setEditorContent('');
        toast.success("New document created");
    };

    const handleDeleteDoc = async (id: number) => {
        if (confirm("Delete this document? This cannot be undone.")) {
            await db.project_documents.delete(id);
            if (selectedDocId === id) {
                setSelectedDocId(null);
                setEditorContent('');
            }
            toast.success("Document deleted");
        }
    };

    const handleUpdateTitle = async () => {
        if (!selectedDocId) return;
        await db.project_documents.update(selectedDocId, {
            title: titleEditValue
        });
        setIsEditingTitle(false);
    };

    // --- Drag & Drop Import Logic ---
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        let importedCount = 0;
        const count = documents?.length || 0;

        for (const file of acceptedFiles) {
            try {
                // 1. Read Content
                const text = await file.text();

                // 2. Determine Type
                const type = projectCategory?.toLowerCase().includes('music') ? 'song' : 'chapter';

                // 3. Create Manuscript Document
                const docId = await db.project_documents.add({
                    project_id: projectId,
                    title: file.name.replace(/\.(txt|md)$/i, ''),
                    content: text, // Simple text import for now. TipTap can handle HTML too if needed.
                    order: count + importedCount,
                    type: type as any,
                    status: 'draft',
                    updated_at: new Date()
                });

                // 4. Dual Ingestion: Store as Project Asset
                // Check if file already exists? For now, we just add it.
                await db.project_files.add({
                    project_id: projectId,
                    name: file.name,
                    type: file.type || 'text/plain',
                    content: file,
                    created_at: new Date(),
                    extracted_metadata: {}
                });

                if (importedCount === 0) setSelectedDocId(docId as number);
                importedCount++;

            } catch (err) {
                console.error("Failed to import file:", file.name, err);
                toast.error(`Failed to import ${file.name}`);
            }
        }

        if (importedCount > 0) {
            toast.success(`Imported ${importedCount} documents (and added to project assets)`);
        }
    }, [documents, projectId, projectCategory]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'text/*': ['.txt', '.md'] },
        noClick: true // Only drag drop
    });


    const activeDoc = documents?.find(d => d.id === selectedDocId);

    const getIcon = (type: string) => {
        switch (type) {
            case 'song': return <Music size={14} />;
            case 'scene': return <Clapperboard size={14} />;
            default: return <FileText size={14} />;
        }
    };

    // Auto-collapse sidebar when entering Zen Mode
    const toggleZenMode = () => {
        if (!isZenMode) {
            setIsSidebarCollapsed(true);
        }
        setIsZenMode(!isZenMode);
    };

    const [toolbarContainer, setToolbarContainer] = useState<HTMLDivElement | null>(null);

    const content = (
        <div
            className={clsx(
                "flex animate-in fade-in duration-500 transition-all ease-in-out",
                isZenMode ? "fixed inset-0 z-[99999] bg-gray-950 p-0 gap-0" : "h-[calc(100vh-200px)] gap-4"
            )}
        >
            {/* Sidebar List */}
            <div
                className={clsx(
                    "flex flex-col gap-2 transition-all duration-300 relative",
                    isZenMode && isSidebarCollapsed ? "w-0 overflow-hidden opacity-0 mr-0" : isSidebarCollapsed ? "w-12 items-center" : isZenMode ? "w-64" : "w-1/4 min-w-[200px]",
                    isZenMode && !isSidebarCollapsed && "mr-4 bg-black/20 rounded-lg p-2"
                )}
            >
                <Card
                    {...getRootProps()}
                    className={clsx(
                        "flex-1 flex flex-col p-0 overflow-hidden bg-black/20 border-white/10 relative transition-all",
                        isDragActive && "border-accent ring-2 ring-accent/20 bg-accent/5"
                    )}
                >
                    <input {...getInputProps()} />

                    {/* Sidebar Header */}
                    {!isSidebarCollapsed && (
                        <div className="p-3 border-b border-white/10 flex justify-between items-center bg-white/5">
                            <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">
                                {documents?.length} Items
                            </span>
                            <Button size="sm" variant="ghost" onClick={handleCreateDoc} className="h-6 w-6 p-0 rounded-full hover:bg-white/10">
                                <Plus size={14} />
                            </Button>
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

                    {/* Collapse Toggle (Top if collapsed, Absolute if expanded) */}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
                        className={clsx(
                            "z-20 text-gray-500 hover:text-white",
                            isSidebarCollapsed ? "my-2" : "absolute right-2 top-[3.25rem]"
                        )}
                    >
                        {isSidebarCollapsed ? <ChevronRight size={16} /> : <ChevronLeft size={16} />}
                    </Button>


                    {/* List Items */}
                    <div className={clsx("flex-1 overflow-y-auto p-2 space-y-1", isSidebarCollapsed && "scrollbar-hide")}>
                        {documents?.map(doc => (
                            <div
                                key={doc.id}
                                onClick={() => setSelectedDocId(doc.id!)}
                                className={clsx(
                                    "group flex items-center gap-2 p-2 rounded cursor-pointer transition-all border relative",
                                    selectedDocId === doc.id
                                        ? "bg-purple-900/30 border-purple-500/50 text-purple-100"
                                        : "hover:bg-white/5 border-transparent text-gray-400 hover:text-gray-200",
                                    isSidebarCollapsed && "justify-center px-1"
                                )}
                                title={isSidebarCollapsed ? doc.title : undefined}
                            >
                                {!isSidebarCollapsed && (
                                    <span className="opacity-0 group-hover:opacity-50 cursor-grab active:cursor-grabbing">
                                        <GripVertical size={12} />
                                    </span>
                                )}
                                <span className="text-purple-400/70 shrink-0">
                                    {getIcon(doc.type)}
                                </span>
                                {!isSidebarCollapsed && (
                                    <span className="text-sm truncate flex-1 font-medium">
                                        {doc.title}
                                    </span>
                                )}
                            </div>
                        ))}
                    </div>
                </Card>
            </div>

            {/* Main Editor Area */}
            <div className="flex-1 flex flex-col transition-all">
                {selectedDocId && activeDoc ? (
                    <Card className={clsx("flex-1 flex flex-col p-0 overflow-hidden shadow-2xl transition-all", isZenMode ? "bg-black border-none" : "bg-gray-900 border-white/10")}>
                        {/* Toolbar */}
                        <div className="h-12 border-b border-white/10 flex items-center justify-between px-4 bg-white/5 shrink-0">
                            <div className="flex items-center gap-2 shrink-0">
                                {isEditingTitle ? (
                                    <input
                                        className="bg-black/50 border border-white/20 rounded px-2 py-1 text-sm text-white w-full max-w-[300px] focus:outline-none focus:border-purple-500"
                                        value={titleEditValue}
                                        onChange={(e) => setTitleEditValue(e.target.value)}
                                        onBlur={handleUpdateTitle}
                                        onKeyDown={(e) => e.key === 'Enter' && handleUpdateTitle()}
                                        autoFocus
                                    />
                                ) : (
                                    <h3
                                        className="text-lg font-bold text-white cursor-pointer hover:underline decoration-dashed decoration-gray-600 underline-offset-4 truncate max-w-[200px]"
                                        onClick={() => setIsEditingTitle(true)}
                                        title="Click to rename"
                                    >
                                        {activeDoc.title}
                                    </h3>
                                )}
                                <span className="text-xs px-2 py-0.5 rounded bg-white/10 text-gray-400 font-mono shrink-0">
                                    {activeDoc.type.toUpperCase()}
                                </span>
                            </div>

                            {/* PORTAL TARGET FOR TIPTAP TOOLBAR */}
                            <div ref={setToolbarContainer} className="flex-1 flex justify-center items-center px-4" />

                            <div className="flex items-center gap-2 shrink-0">
                                {isZenMode && isSidebarCollapsed && (
                                    <>
                                        <Button
                                            size="sm"
                                            variant="ghost"
                                            onClick={() => setIsSidebarCollapsed(false)}
                                            className="text-gray-400 hover:text-white"
                                            title="Show Sidebar"
                                        >
                                            <PanelLeft size={14} />
                                        </Button>
                                        <div className="h-4 w-px bg-white/10 mx-1" />
                                    </>
                                )}
                                {/* AI & Tools */}
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => setOracleChatOpen(!isOracleChatOpen)}
                                    className={clsx("hover:bg-white/10", isOracleChatOpen ? "text-accent" : "text-gray-400")}
                                    title="Oracle Chat"
                                >
                                    <Bot size={14} />
                                </Button>
                                <div className="h-4 w-px bg-white/10 mx-1" />

                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={handleSave}
                                    className="text-green-400 hover:text-green-300 hover:bg-green-900/20"
                                >
                                    <Save size={14} className="mr-1.5" /> Save
                                </Button>
                                <div className="h-4 w-px bg-white/10 mx-1" />

                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => openExport({ projectId })}
                                    className="text-blue-400 hover:text-blue-300 hover:bg-blue-900/20"
                                    title="Export Manuscript"
                                >
                                    <Download size={14} />
                                </Button>
                                <div className="h-4 w-px bg-white/10 mx-1" />
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={toggleZenMode}
                                    className={clsx("hover:bg-white/10", isZenMode ? "text-accent" : "text-gray-400")}
                                    title="Toggle Zen Mode"
                                >
                                    {isZenMode ? <Minimize2 size={14} /> : <Maximize2 size={14} />}
                                </Button>
                                <div className="h-4 w-px bg-white/10 mx-1" />
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    onClick={() => handleDeleteDoc(selectedDocId)}
                                    className="text-red-400 hover:text-red-300 hover:bg-red-900/20"
                                >
                                    <Trash2 size={14} />
                                </Button>
                            </div>
                        </div>

                        {/* Editor */}
                        <div className="flex-1 overflow-hidden relative bg-gray-950/50">
                            <div className="h-full overflow-y-auto custom-scrollbar">
                                <TipTapEditor
                                    key={selectedDocId}
                                    value={editorContent}
                                    onChange={setEditorContent}
                                    onSave={handleSave}
                                    placeholder="Start writing..."
                                    toolbarContainer={toolbarContainer}
                                    className={clsx(
                                        "min-h-full !border-none !rounded-none focus-within:ring-0 !bg-transparent !shadow-none text-lg leading-relaxed mx-auto py-12 transition-all duration-300",
                                        isZenMode ? "max-w-none w-full px-12" : "max-w-3xl px-8"
                                    )}
                                />
                                <div className="h-20" /> {/* Bottom spacer */}
                            </div>
                        </div>
                    </Card>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-500 flex-col gap-4">
                        <FileText size={48} className="opacity-20" />
                        <p>Select a document or drag files here to start.</p>
                        <Button
                            variant="outline"
                            onClick={handleCreateDoc}
                            className="mt-2"
                        >
                            <Plus size={16} className="mr-2" /> Create Document
                        </Button>
                    </div>
                )}
            </div>
            <ExportDialog
                isOpen={isExportOpen}
                onClose={closeExport}
                strategies={[StandardManuscriptStrategy, PublisherManuscriptStrategy]}
                context={exportContext}
            />
        </div>
    );

    if (isZenMode) {
        return createPortal(content, document.body);
    }

    return content;
}
