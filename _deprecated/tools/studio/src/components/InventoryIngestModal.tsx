import { useState, useEffect } from 'react';
import { toast } from 'sonner';
import { db, type InventoryItem } from '../lib/db';
import { AIService } from '../lib/AIService';
import { Button } from './ui/Button';
import { Input } from './ui/Input';
import { Loader2, Plus, Trash2, FileText, Upload, CheckCircle, ScanBarcode } from 'lucide-react';
import clsx from 'clsx';
import { useUIStore } from '../store/useStore';
import { BarcodeScanner } from './mobile/BarcodeScanner';

interface InventoryIngestModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialData?: Partial<InventoryItem>[];
}

export function InventoryIngestModal({ isOpen, onClose, initialData }: InventoryIngestModalProps) {
    const [mode, setMode] = useState<'text' | 'file' | 'scan'>('text');
    const [isScanning, setIsScanning] = useState(false);
    const [inputText, setInputText] = useState('');
    const [isAnalyzing, setIsAnalyzing] = useState(false);
    const [candidates, setCandidates] = useState<Partial<InventoryItem>[]>([]);
    const { setIngesting } = useUIStore();

    // Initialize from props if provided
    useEffect(() => {
        if (initialData && initialData.length > 0) {
            setCandidates(initialData);
        }
    }, [initialData]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;
        await handleAnalyze(file);
    };

    const updateCandidate = (index: number, field: keyof InventoryItem, value: any) => {
        const newCandidates = [...candidates];
        newCandidates[index] = { ...newCandidates[index], [field]: value };
        setCandidates(newCandidates);
    };

    const removeCandidate = (index: number) => {
        setCandidates(candidates.filter((_, i) => i !== index));
    };

    const handleSaveAll = async () => {
        if (candidates.length === 0) return;

        try {
            await db.inventory.bulkAdd(candidates.map(c => ({
                name: c.name || 'Unknown Item',
                category: c.category || 'Unsorted',
                domain: c.domain || 'General',
                quantity: Number(c.quantity) || 1,
                location: c.location || 'TBD',
                units: c.units || 'pcs',
                type: c.type || 'part', // Default to part
                min_stock: 0,
                // New fields
                mpn: c.mpn || undefined,
                manufacturer: c.manufacturer,
                barcode: c.barcode,
                datasheet_url: c.datasheet_url,
                unit_cost: Number(c.unit_cost) || 0
            })));

            onClose();
            // Reset
            setCandidates([]);
            setInputText('');
            setMode('text');
        } catch (e) {
            console.error(e);
            toast.error("Failed to save items");
        }
    };

    const handleScanResult = (code: string) => {
        setIsScanning(false);
        // Treat code as input for analysis
        setInputText(`Product with UPC/EAN: ${code}`);
        // Auto-analyze?
        handleAnalyze(undefined, `Product with UPC/EAN: ${code}`);
    };

    // Modified analyze handle to accept direct text override
    const handleAnalyze = async (file?: File, overrideText?: string) => {
        setIsAnalyzing(true);
        setIngesting(true, "Scanning for Inventory...");
        try {
            const input = file || overrideText || inputText;
            const results = await AIService.analyzeInventory(input);
            setCandidates(prev => [...prev, ...results]);
        } catch (e) {
            console.error(e);
            toast.error("Analysis failed. Try again.");
        } finally {
            setIsAnalyzing(false);
            setIngesting(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            {/* Scanner Overlay */}
            {isScanning && (
                <BarcodeScanner
                    onScan={handleScanResult}
                    onClose={() => setIsScanning(false)}
                />
            )}

            <div className="bg-neutral-900 border border-white/10 rounded-xl w-full max-w-5xl max-h-[90vh] flex flex-col shadow-2xl animate-in fade-in zoom-in-95 overflow-hidden">

                {/* Header ... */}
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-black/40 rounded-t-xl">
                    {/* ... */}
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden flex flex-col md:flex-row">

                    {/* Left Panel: Input */}
                    <div className="w-full md:w-1/3 p-6 border-r border-white/10 flex flex-col gap-6 bg-white/5">
                        <div className="flex bg-black/50 p-1 rounded border border-white/10">
                            <button onClick={() => setMode('text')} className={clsx("flex-1 py-2 text-xs font-bold uppercase rounded-sm transition-colors", mode === 'text' ? "bg-accent text-black" : "text-gray-400 hover:text-white")}>Text / URL</button>
                            <button onClick={() => setMode('file')} className={clsx("flex-1 py-2 text-xs font-bold uppercase rounded-sm transition-colors", mode === 'file' ? "bg-accent text-black" : "text-gray-400 hover:text-white")}>File</button>
                            <button onClick={() => { setMode('scan'); setIsScanning(true); }} className={clsx("flex-1 py-2 text-xs font-bold uppercase rounded-sm transition-colors", mode === 'scan' ? "bg-accent text-black" : "text-gray-400 hover:text-white")}>
                                <ScanBarcode size={14} className="inline mr-1" /> Scan
                            </button>
                        </div>

                        {mode === 'text' || mode === 'scan' ? (
                            <div className="flex-1 flex flex-col gap-2">
                                <textarea
                                    className="flex-1 bg-black border border-white/10 rounded-lg p-3 text-sm font-mono text-gray-300 focus:border-accent outline-none resize-none"
                                    placeholder="Paste product page text, URL, or shopping cart list here..."
                                    value={inputText}
                                    onChange={e => setInputText(e.target.value)}
                                />
                                <Button onClick={() => handleAnalyze()} disabled={!inputText || isAnalyzing} className="w-full">
                                    {isAnalyzing ? <Loader2 className="animate-spin mr-2" /> : <FileText className="mr-2" />}
                                    Analyze
                                </Button>
                            </div>
                        ) : (
                            // ... file upload UI
                            <div className="flex-1 border-2 border-dashed border-white/10 rounded-lg flex flex-col items-center justify-center gap-4 text-gray-500 hover:border-accent/50 hover:bg-accent/5 transition-colors relative">
                                <Upload size={48} className="opacity-50" />
                                <p className="text-sm font-mono uppercase">Drop Invoice / Image</p>
                                <input type="file" className="absolute inset-0 opacity-0 cursor-pointer" onChange={handleFileUpload} disabled={isAnalyzing} />
                                {isAnalyzing && <div className="absolute inset-0 bg-black/60 flex items-center justify-center"><Loader2 className="animate-spin text-accent" /></div>}
                            </div>
                        )}
                    </div>

                    {/* ... rest of UI ... */}
                    <div className="flex-1 flex flex-col bg-black">
                        <div className="flex-1 overflow-auto p-6 space-y-4">
                            {/* ... Content ... */}
                            {candidates.length === 0 ? (
                                <div className="h-full flex flex-col items-center justify-center text-gray-600">
                                    <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                                        <FileText size={24} />
                                    </div>
                                    <p className="font-mono text-sm uppercase">Waiting for Input...</p>
                                </div>
                            ) : (
                                candidates.map((item, i) => (
                                    <div key={i} className="bg-white/5 border border-white/10 rounded-lg p-4 group hover:border-accent/30 transition-colors">
                                        <div className="flex justify-between items-start mb-3">
                                            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-4">
                                                {/* Added MPN field */}
                                                <div>
                                                    <Input label="Name" value={item.name} onChange={e => updateCandidate(i, 'name', e.target.value)} className="font-bold border-transparent bg-transparent p-0 focus:bg-black focus:border-accent focus:p-2 transition-all w-full" />
                                                    <div className="flex gap-2 mt-1">
                                                        <input
                                                            placeholder="MPN..."
                                                            value={item.mpn || ''}
                                                            onChange={e => updateCandidate(i, 'mpn', e.target.value)}
                                                            className="bg-transparent text-[10px] font-mono text-gray-500 border-b border-white/10 focus:border-accent outline-none w-20"
                                                        />
                                                        <input
                                                            placeholder="Mfr..."
                                                            value={item.manufacturer || ''}
                                                            onChange={e => updateCandidate(i, 'manufacturer', e.target.value)}
                                                            className="bg-transparent text-[10px] font-mono text-gray-500 border-b border-white/10 focus:border-accent outline-none w-20"
                                                        />
                                                    </div>
                                                </div>

                                                <div className="flex gap-2">
                                                    <Input label="Type" value={item.type} onChange={e => updateCandidate(i, 'type', e.target.value)} className="text-xs font-mono text-gray-400" />
                                                    <Input label="Category" value={item.category} onChange={e => updateCandidate(i, 'category', e.target.value)} className="text-xs font-mono text-gray-400" />
                                                </div>
                                            </div>
                                            <button onClick={() => removeCandidate(i)} className="text-red-500 opacity-0 group-hover:opacity-100 p-2 hover:bg-red-900/20 rounded"><Trash2 size={16} /></button>
                                        </div>
                                        {/* ... Rest of fields */}
                                        <div className="grid grid-cols-4 gap-4">
                                            <Input label="Qty" type="number" value={item.quantity} onChange={e => updateCandidate(i, 'quantity', e.target.value)} />
                                            <Input label="Cost ($)" type="number" value={item.unit_cost} onChange={e => updateCandidate(i, 'unit_cost', e.target.value)} />
                                            <Input label="Loc" value={item.location} onChange={e => updateCandidate(i, 'location', e.target.value)} />
                                            <Input label="Bar/Link" value={item.barcode || item.datasheet_url} onChange={e => updateCandidate(i, 'barcode', e.target.value)} placeholder="UPC/EAN" />
                                        </div>
                                    </div>
                                ))
                            )}
                        </div>

                        <div className="p-6 border-t border-white/10 bg-neutral-900 flex justify-between items-center">
                            <div className="text-sm font-mono text-gray-400">
                                {candidates.length} candidate(s) detected
                            </div>
                            <Button variant="primary" onClick={handleSaveAll} disabled={candidates.length === 0}>
                                <CheckCircle size={16} className="mr-2" />
                                Confirm & Add {candidates.length} Items
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
