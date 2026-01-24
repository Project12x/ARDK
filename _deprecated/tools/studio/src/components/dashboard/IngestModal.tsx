import { useState, useRef, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { Upload, FileText, Package, Briefcase, X, Loader2, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import { IngestionService } from '../../lib/ingest';
import { toast } from 'sonner';

interface IngestModalProps {
    isOpen: boolean;
    onClose: () => void;
}

type IngestMode = 'universal' | 'project' | 'inventory' | 'portfolio';

export function IngestModal({ isOpen, onClose }: IngestModalProps) {
    const [mode, setMode] = useState<IngestMode>('universal');
    const [isDragging, setIsDragging] = useState(false);
    const [isProcessing, setIsProcessing] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // Close on Escape
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape' && !isProcessing) onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose, isProcessing]);

    if (!isOpen) return null;

    const handleFile = async (file: File) => {
        if (!file) return;

        setIsProcessing(true);
        const toastId = toast.loading(mode === 'universal' ? "Analyzing & Classifying..." : "Analyzing document...");

        try {
            let result;
            if (mode === 'universal') {
                result = await IngestionService.ingestUniversal(file);
                toast.success(result.summary || "Ingestion Complete", { id: toastId });
            } else {
                result = await IngestionService.ingestFile(file, mode);
                if (mode === 'inventory') {
                    toast.success(`Ingested ${result.count} items`, { id: toastId });
                } else if (mode === 'portfolio') {
                    toast.success(`Found ${result.count} projects`, { id: toastId });
                } else {
                    toast.success("Project updated successfully", { id: toastId });
                }
            }
            onClose();
        } catch (error: any) {
            console.error(error);
            toast.error("Ingestion failed", { id: toastId, description: error.message });
        } finally {
            setIsProcessing(false);
        }
    };

    const onDrop = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(false);
        if (e.dataTransfer.files?.[0]) {
            handleFile(e.dataTransfer.files[0]);
        }
    };

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm transition-opacity"
                onClick={() => !isProcessing && onClose()}
            />

            {/* Modal Panel */}
            <div className="relative w-full max-w-2xl bg-[#0A0A0A] border border-white/10 rounded-2xl shadow-2xl overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="p-6">
                    <div className="flex items-center justify-between mb-6">
                        <div className="flex items-center gap-2">
                            <Upload className="text-accent" size={24} />
                            <h2 className="text-xl font-bold text-white">Ingest Document</h2>
                        </div>
                        {!isProcessing && (
                            <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                                <X size={20} />
                            </button>
                        )}
                    </div>

                    {isProcessing ? (
                        <div className="flex flex-col items-center justify-center py-12 space-y-4">
                            <Loader2 size={48} className="text-accent animate-spin" />
                            <div className="text-center">
                                <h3 className="text-lg font-bold text-white">Processing...</h3>
                                <p className="text-sm text-gray-400">Gemini is analyzing your document structure.</p>
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-6">
                            {/* Mode Selection */}
                            <div className="grid grid-cols-4 gap-4">
                                <button
                                    onClick={() => setMode('universal')}
                                    className={clsx(
                                        "p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all",
                                        mode === 'universal'
                                            ? "bg-accent/10 border-accent text-white ring-1 ring-accent shadow-[0_0_15px_rgba(var(--accent-rgb),0.2)]"
                                            : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                    )}
                                >
                                    <Sparkles size={24} className={mode === 'universal' ? "text-accent" : ""} />
                                    <div className="text-center">
                                        <div className="font-bold text-sm">Auto-Detect</div>
                                        <div className="text-[10px] opacity-60 mt-1">Smart Parsing</div>
                                    </div>
                                </button>

                                <button
                                    onClick={() => setMode('project')}
                                    className={clsx(
                                        "p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all",
                                        mode === 'project'
                                            ? "bg-accent/10 border-accent text-white"
                                            : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                    )}
                                >
                                    <FileText size={24} className={mode === 'project' ? "text-accent" : ""} />
                                    <div className="text-center">
                                        <div className="font-bold text-sm">Single Project</div>
                                        <div className="text-[10px] opacity-60 mt-1">Datasheets, Sketches, Manuals</div>
                                    </div>
                                </button>

                                <button
                                    onClick={() => setMode('inventory')}
                                    className={clsx(
                                        "p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all",
                                        mode === 'inventory'
                                            ? "bg-accent/10 border-accent text-white"
                                            : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                    )}
                                >
                                    <Package size={24} className={mode === 'inventory' ? "text-accent" : ""} />
                                    <div className="text-center">
                                        <div className="font-bold text-sm">Inventory</div>
                                        <div className="text-[10px] opacity-60 mt-1">Receipts, Lists, Photos of Parts</div>
                                    </div>
                                </button>

                                <button
                                    onClick={() => setMode('portfolio')}
                                    className={clsx(
                                        "p-4 rounded-xl border flex flex-col items-center justify-center gap-3 transition-all",
                                        mode === 'portfolio'
                                            ? "bg-accent/10 border-accent text-white"
                                            : "bg-white/5 border-transparent text-gray-400 hover:bg-white/10"
                                    )}
                                >
                                    <Briefcase size={24} className={mode === 'portfolio' ? "text-accent" : ""} />
                                    <div className="text-center">
                                        <div className="font-bold text-sm">Portfolio</div>
                                        <div className="text-[10px] opacity-60 mt-1">Master Indexes, Resumes, Exports</div>
                                    </div>
                                </button>
                            </div>

                            {/* Drop Zone */}
                            <div
                                className={clsx(
                                    "border-2 border-dashed rounded-xl p-12 flex flex-col items-center justify-center transition-all cursor-pointer",
                                    isDragging ? "border-accent bg-accent/5" : "border-white/10 hover:border-white/20 hover:bg-white/5"
                                )}
                                onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
                                onDragLeave={() => setIsDragging(false)}
                                onDrop={onDrop}
                                onClick={() => fileInputRef.current?.click()}
                            >
                                <Upload className="text-gray-500 mb-4" size={32} />
                                <h3 className="text-lg font-bold text-white mb-1">Click to Upload</h3>
                                <p className="text-sm text-gray-500">or drag and drop your file here</p>
                                <input
                                    type="file"
                                    ref={fileInputRef}
                                    className="hidden"
                                    onChange={(e) => e.target.files?.[0] && handleFile(e.target.files[0])}
                                    accept=".json,.pdf,.txt,.md,image/*,.csv"
                                />
                            </div>
                        </div>
                    )}
                </div>
            </div>
        </div>,
        document.body
    );
}
