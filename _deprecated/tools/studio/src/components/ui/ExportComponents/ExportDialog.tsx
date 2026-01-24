import { useState } from 'react';
import { Dialog } from '@headlessui/react';
import { X, FileText, Download, Wand2, AlertTriangle, CheckCircle, ChevronRight, FileJson, FileSpreadsheet } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import type { ExportStrategy, ExportFormat } from '../../../types/export';
import { toast } from 'sonner';
import { saveAs } from 'file-saver';

interface ExportDialogProps<T> {
    isOpen: boolean;
    onClose: () => void;
    strategies: ExportStrategy<T>[];
    context?: any; // Context to pass to getData
}

type Step = 'STRATEGY' | 'FORMAT' | 'ENRICH' | 'VALIDATE' | 'RESOLVING';

export function ExportDialog<T>({ isOpen, onClose, strategies, context }: ExportDialogProps<T>) {
    const [step, setStep] = useState<Step>('STRATEGY');
    const [selectedStrategy, setSelectedStrategy] = useState<ExportStrategy<T> | null>(null);
    const [selectedFormat, setSelectedFormat] = useState<ExportFormat | null>(null);
    const [data, setData] = useState<T[]>([]);
    const [isProcessing, setIsProcessing] = useState(false);
    const [validationIssues, setValidationIssues] = useState<string[]>([]);
    const [invalidItems, setInvalidItems] = useState<any[]>([]);

    const handleStrategySelect = async (strategy: ExportStrategy<T>) => {
        setIsProcessing(true);
        try {
            // 1. Fetch Data
            const items = await strategy.getData(context);
            setData(items);
            setSelectedStrategy(strategy);

            // Auto-advance if only one format
            if (strategy.supportedFormats.length === 1) {
                setSelectedFormat(strategy.supportedFormats[0].id);
                setStep('ENRICH'); // Go to enrich if available, else validate
            } else {
                setStep('FORMAT');
            }
        } catch (error) {
            console.error(error);
            toast.error("Failed to fetch data for export");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleEnrich = async () => {
        if (!selectedStrategy?.enrichData) {
            handleValidate(); // Skip if no enrichment
            return;
        }

        setIsProcessing(true);
        try {
            // Run AI Enrichment
            const enriched = await selectedStrategy.enrichData(data);
            setData(enriched);
            toast.success("AI Enrichment Complete");
            handleValidate(enriched);
        } catch (error) {
            toast.error("Enrichment failed");
        } finally {
            setIsProcessing(false);
        }
    };

    const handleValidate = (currentData = data) => {
        if (!selectedStrategy?.validate) {
            handleExport(currentData);
            return;
        }

        const result = selectedStrategy.validate(currentData);
        if (result.isValid) {
            handleExport(currentData);
        } else {
            setValidationIssues(result.missingFields);
            setInvalidItems(result.invalidItems || []);
            setStep('VALIDATE'); // Show validation errors
        }
    };

    const handleExport = async (finalData = data) => {
        if (!selectedStrategy || !selectedFormat) return;

        setIsProcessing(true);
        try {
            const blob = await selectedStrategy.transform(finalData, selectedFormat);
            const formatInfo = selectedStrategy.supportedFormats.find(f => f.id === selectedFormat);
            const extension = formatInfo?.extension || 'txt';

            // Handle string vs blob
            const fileToSave = typeof blob === 'string'
                ? new Blob([blob], { type: 'text/plain;charset=utf-8' })
                : blob;

            saveAs(fileToSave, `${selectedStrategy.id}_export.${extension}`);
            toast.success("Export Downloaded");
            onClose();
        } catch (error) {
            console.error(error);
            toast.error("Export generation failed");
        } finally {
            setIsProcessing(false);
        }
    };

    // Reset on open
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
            <div className="bg-neutral-900 border border-white/10 rounded-xl w-full max-w-2xl overflow-hidden shadow-2xl flex flex-col max-h-[80vh]">

                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Download size={20} className="text-accent" />
                        Export Wizard
                    </h2>
                    <button onClick={onClose} className="p-1 hover:bg-white/10 rounded-full transition-colors">
                        <X size={20} className="text-gray-400" />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6">
                    <AnimatePresence mode='wait'>
                        {/* STEP 1: STRATEGY SELECTION */}
                        {step === 'STRATEGY' && (
                            <motion.div
                                key="strategy"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-4"
                            >
                                <h3 className="text-sm font-mono text-gray-500 uppercase">Select Export Goal</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {strategies.map(strategy => (
                                        <button
                                            key={strategy.id}
                                            onClick={() => handleStrategySelect(strategy)}
                                            className="flex flex-col items-start p-4 bg-white/5 border border-white/5 hover:border-accent/50 hover:bg-accent/5 rounded-lg transition-all text-left group"
                                        >
                                            <div className="font-bold text-white mb-1 group-hover:text-accent transition-colors">
                                                {strategy.name}
                                            </div>
                                            <div className="text-xs text-gray-400">
                                                {strategy.description}
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* STEP 2: FORMAT SELECTION (If needed) */}
                        {step === 'FORMAT' && selectedStrategy && (
                            <motion.div
                                key="format"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-4"
                            >
                                <h3 className="text-sm font-mono text-gray-500 uppercase">Select Format</h3>
                                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                    {selectedStrategy.supportedFormats.map(format => (
                                        <button
                                            key={format.id}
                                            onClick={() => {
                                                setSelectedFormat(format.id);
                                                setStep('ENRICH');
                                            }}
                                            className="flex items-center gap-3 p-4 bg-white/5 border border-white/5 hover:border-accent/50 hover:bg-accent/5 rounded-lg transition-all text-left"
                                        >
                                            <div className="p-2 bg-black/30 rounded">
                                                {format.id.includes('csv') ? <FileSpreadsheet size={20} className="text-green-400" /> :
                                                    format.id.includes('json') ? <FileJson size={20} className="text-yellow-400" /> :
                                                        <FileText size={20} className="text-blue-400" />}
                                            </div>
                                            <div>
                                                <div className="font-bold text-white">{format.label}</div>
                                                <div className="text-xs text-gray-500">.{format.extension}</div>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            </motion.div>
                        )}

                        {/* STEP 3: ENRICHMENT (Optional) */}
                        {step === 'ENRICH' && (
                            <motion.div
                                key="enrich"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-6 text-center py-8"
                            >
                                <Wand2 size={48} className="mx-auto text-accent mb-4 animate-pulse" />
                                <div>
                                    <h3 className="text-xl font-bold text-white mb-2">Enhance Data?</h3>
                                    <p className="text-gray-400 max-w-sm mx-auto text-sm">
                                        We can use Gemini to clean up names, extract missing metadata, or format text before exporting.
                                    </p>
                                </div>

                                <div className="flex justify-center gap-4">
                                    <button
                                        onClick={() => handleEnrich()} // Run AI
                                        className="px-6 py-2 bg-accent text-black font-bold rounded-lg hover:bg-accent/90 transition-colors flex items-center gap-2"
                                        disabled={isProcessing}
                                    >
                                        <Wand2 size={16} />
                                        {isProcessing ? 'Enhancing...' : 'Yes, Enhance Data'}
                                    </button>
                                    <button
                                        onClick={() => handleValidate()} // Skip
                                        className="px-6 py-2 bg-white/5 text-gray-300 font-bold rounded-lg hover:bg-white/10 transition-colors"
                                        disabled={isProcessing}
                                    >
                                        Skip
                                    </button>
                                </div>
                            </motion.div>
                        )}

                        {/* STEP 4: VALIDATION ISSUES */}
                        {step === 'VALIDATE' && (
                            <motion.div
                                key="validate"
                                initial={{ opacity: 0, x: 20 }}
                                animate={{ opacity: 1, x: 0 }}
                                exit={{ opacity: 0, x: -20 }}
                                className="space-y-4"
                            >
                                <div className="p-4 bg-red-500/10 border border-red-500/20 rounded-lg flex gap-3 text-red-200">
                                    <AlertTriangle size={24} className="shrink-0" />
                                    <div>
                                        <h4 className="font-bold">Items Missing Required Data</h4>
                                        <p className="text-sm opacity-80 mt-1">
                                            The chosen format requires the following fields: <b>{validationIssues.join(', ')}</b>.
                                        </p>
                                    </div>
                                </div>

                                <div className="p-4 bg-black/30 rounded-lg border border-white/5 max-h-60 overflow-y-auto">
                                    {invalidItems.length > 0 ? (
                                        <ul className="space-y-2">
                                            {invalidItems.map((item, i) => (
                                                <li key={i} className="flex items-center gap-2 text-sm text-gray-400 border-b border-white/5 pb-2 last:border-0 last:pb-0">
                                                    <AlertTriangle size={12} className="text-yellow-500 shrink-0" />
                                                    <span className="font-mono text-white">{item.part_name || item.name || 'Unknown Item'}</span>
                                                    <span className="text-xs opacity-50 ml-auto">Missing ID/MPN</span>
                                                </li>
                                            ))}
                                        </ul>
                                    ) : (
                                        <div className="text-center text-gray-500 py-8">
                                            No specific items identified, but global validation failed.
                                        </div>
                                    )}
                                </div>

                                <div className="flex justify-end gap-3 pt-4">
                                    <button
                                        onClick={onClose}
                                        className="px-4 py-2 text-gray-400 hover:text-white"
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        onClick={() => handleExport(data)} // Export anyway
                                        className="px-4 py-2 bg-red-900/50 text-red-200 border border-red-500/30 rounded hover:bg-red-900/80"
                                    >
                                        Export Anyway (Incomplete)
                                    </button>
                                </div>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Progress Footer */}
                {isProcessing && (
                    <div className="p-2 bg-accent/10 border-t border-accent/20">
                        <div className="h-1 w-full bg-accent/20 rounded overflow-hidden">
                            <div className="h-full bg-accent w-1/3 animate-[progress_1s_ease-in-out_infinite]" />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
