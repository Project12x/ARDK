
import { useUIStore } from '../store/useStore';
import { Loader2 } from 'lucide-react';

export function GlobalProgressBar() {
    const { isIngesting, ingestMessage } = useUIStore();

    if (!isIngesting) return null;

    return (
        <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-4 fade-in duration-300">
            <div className="bg-black/90 border border-accent/20 text-white px-4 py-3 rounded-md shadow-2xl flex items-center gap-3 backdrop-blur-md">
                <Loader2 className="animate-spin text-accent" size={18} />
                <div className="flex flex-col">
                    <span className="text-xs font-bold text-accent uppercase tracking-wider">System Processing</span>
                    <span className="text-xs font-mono text-gray-300">{ingestMessage || 'Ingesting data...'}</span>
                </div>
            </div>
            {/* Ambient Glow */}
            <div className="absolute inset-0 bg-accent/20 blur-xl -z-10 rounded-full" />
        </div>
    );
}
