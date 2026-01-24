import { Wifi, Cpu, RefreshCw, AlertTriangle, Github } from 'lucide-react';
import { useState } from 'react';

export function StatusIndicators() {
    // Initial state from localStorage directly
    const [aiStatus] = useState<'online' | 'offline'>(() => {
        const hasGemini = !!localStorage.getItem('GEMINI_API_KEY');
        const hasOllama = !!localStorage.getItem('OLLAMA_URL');
        return (hasGemini || hasOllama) ? 'online' : 'offline';
    });

    // Placeholder for Sync Status (will implement with GitHubService later)
    const [syncStatus] = useState<'synced' | 'syncing' | 'error' | 'disconnected'>('synced');

    return (
        <div className="flex items-center gap-4 text-xs font-mono text-gray-500">
            <div className="flex items-center gap-2 border border-border px-3 py-1 rounded-sm bg-black/50">
                <Cpu size={14} className={aiStatus === 'online' ? "text-blue-400" : "text-gray-600"} />
                <span className={aiStatus === 'online' ? "text-blue-400" : "text-gray-600"}>
                    {aiStatus === 'online' ? 'AI READY' : 'AI OFFLINE'}
                </span>
            </div>

            <div className="flex items-center gap-2 border border-border px-3 py-1 rounded-sm bg-black/50">
                {syncStatus === 'synced' && <Github size={14} className="text-white" />}
                {syncStatus === 'disconnected' && <Wifi size={14} className="text-gray-600" />}

                <span className={syncStatus === 'synced' ? "text-gray-300" : "text-gray-600"}>
                    {syncStatus === 'synced' ? 'GIT CONNECTED' : 'LOCAL ONLY'}
                </span>
            </div>
        </div>
    );
}
