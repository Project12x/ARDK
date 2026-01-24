import { Search } from 'lucide-react';
import { useState } from 'react';

export function GlobalSearchInput() {
    const [localQuery, setLocalQuery] = useState('');

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && localQuery.trim()) {
            e.preventDefault();
            e.stopPropagation();
            window.dispatchEvent(new CustomEvent('open-command-multiverse', { detail: { query: localQuery } }));
        }
    };

    return (
        <div className="relative group max-w-md w-64 mx-2">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-5 h-5 group-focus-within:text-accent transition-colors" />
            <input
                type="text"
                value={localQuery}
                onChange={(e) => setLocalQuery(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Search..."
                className="bg-black/20 border border-white/10 rounded-full pl-11 pr-12 py-2 text-sm font-mono text-white placeholder-gray-500 focus:border-accent focus:bg-black/50 outline-none w-full transition-all"
            />
            <div className="absolute right-3 top-1/2 -translate-y-1/2 flex items-center gap-1 pointer-events-none">
                <span className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded text-gray-600 font-mono">⌘K</span>
            </div>
        </div>
    );
}
