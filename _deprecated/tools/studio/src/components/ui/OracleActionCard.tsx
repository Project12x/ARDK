import { Button } from './Button';
import { X, ArrowRight } from 'lucide-react';

interface OracleActionCardProps {
    title: string;
    description: string;
    proposedData: Record<string, any>; // The new data structure
    onConfirm: () => void;
    onCancel: () => void;
    isSubmitting?: boolean;
}

export function OracleActionCard({ title, description, proposedData, onConfirm, onCancel, isSubmitting }: OracleActionCardProps) {
    return (
        <div className="bg-black/80 border border-neon/50 rounded-xl overflow-hidden shadow-[0_0_30px_rgba(59,130,246,0.15)] animate-in fade-in zoom-in-95 duration-300 backdrop-blur-sm">
            {/* Header */}
            <div className="bg-neon/10 border-b border-neon/20 px-4 py-3 flex items-center justify-between">
                <div className="flex items-center gap-2 text-neon">
                    <div className="w-2 h-2 bg-neon rounded-full animate-pulse shadow-[0_0_10px_#00f]" />
                    <span className="font-bold uppercase tracking-wider text-xs">Oracle Proposal</span>
                </div>
            </div>

            <div className="p-5 space-y-4">
                <div>
                    <h3 className="text-xl font-bold text-white mb-1">{title}</h3>
                    <p className="text-gray-400 text-sm">{description}</p>
                </div>

                {/* Content Preview */}
                <div className="bg-white/5 rounded-lg border border-white/10 p-4 font-mono text-sm overflow-hidden text-gray-300">

                    {/* Generic Key-Value Render (for simple actions) */}
                    {Object.entries(proposedData).map(([k, v]) => {
                        if (k === 'tasks' || k === 'name') return null; // Skip handled fields

                        let valueDisplay = v;
                        if (Array.isArray(v)) {
                            valueDisplay = v.join(', ');
                        } else if (typeof v === 'object' && v !== null) {
                            return null; // Still skip complex nested objects
                        }

                        return (
                            <div key={k} className="flex justify-between border-b border-white/5 last:border-0 py-1">
                                <span className="text-gray-500 uppercase text-xs font-bold">{k}:</span>
                                <span className="text-white text-right font-bold break-all pl-4">{String(valueDisplay)}</span>
                            </div>
                        );
                    })}

                    {/* Heuristic Visualization based on data shape (Blueprints/Complex) */}
                    {proposedData.name && proposedData.category && (
                        <div className="mt-4 pt-4 border-t border-white/10">
                            <div className="text-gray-500 text-xs uppercase font-bold mb-1">Blueprint Header</div>
                            <div className="grid grid-cols-2 gap-2">
                                <div><span className="text-gray-500">Name:</span> <span className="text-white font-bold">{proposedData.name}</span></div>
                                <div><span className="text-gray-500">Category:</span> <span className="text-accent">{proposedData.category}</span></div>
                            </div>
                            <div className="mt-2"><span className="text-gray-500">Description:</span> <span className="text-gray-300 italic">{proposedData.description}</span></div>
                        </div>
                    )}

                    {proposedData.tasks && Array.isArray(proposedData.tasks) && (
                        <div className="mt-4">
                            <div className="text-gray-500 text-xs uppercase font-bold mb-2 flex items-center justify-between">
                                <span>Proposed Protocol ({proposedData.tasks.length} steps)</span>
                            </div>
                            <div className="space-y-1 max-h-[200px] overflow-y-auto pr-2">
                                {proposedData.tasks.map((t: Record<string, any>, i: number) => (
                                    <div key={i} className="flex items-center gap-3 text-xs bg-black/30 p-2 rounded">
                                        <span className="text-gray-600 w-4">{i + 1}</span>
                                        <span className="flex-1 text-gray-200">{t.title}</span>
                                        <span className="text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">{t.phase}</span>
                                        {t.estimated_time && <span className="text-gray-500">{t.estimated_time}</span>}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* Actions */}
                <div className="flex gap-3 pt-2">
                    <Button
                        variant="ghost"
                        onClick={onCancel}
                        className="flex-1 border border-red-500/20 hover:bg-red-900/20 text-red-400 hover:text-red-300"
                    >
                        <X size={16} className="mr-2" /> REJECT
                    </Button>
                    <Button
                        variant="primary"
                        onClick={onConfirm}
                        disabled={isSubmitting}
                        className="flex-1 bg-neon text-black hover:bg-white hover:text-black font-bold shadow-[0_0_20px_rgba(59,130,246,0.3)]"
                    >
                        {isSubmitting ? 'APPLYING...' : 'CONFIRM & APPLY'} <ArrowRight size={16} className="ml-2" />
                    </Button>
                </div>
            </div>
        </div>
    );
}
