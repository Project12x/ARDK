import { useState, useEffect, useRef, useCallback } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { GlobalSearch } from '../../lib/search';
import { Search, Folder, Box, Wrench, Package, Command, ArrowRight, CheckSquare, Book, History as HistoryIcon, Zap, Sparkles, Target, DatabaseBackup, Palette } from 'lucide-react';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';
import { useUIStore } from '../../store/useStore';
import { toast } from 'sonner';

export function CommandBar() {
    const [isOpen, setIsOpen] = useState(false);
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<any[]>([]);
    const [selectedIndex, setSelectedIndex] = useState(0);
    const inputRef = useRef<HTMLInputElement>(null);
    const listRef = useRef<HTMLDivElement>(null);
    const navigate = useNavigate();
    const location = useLocation();

    // Toggle with Cmd+K
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.metaKey || e.ctrlKey) && e.key === 'k') {
                e.preventDefault();
                setIsOpen(prev => !prev);
            }
            if (e.key === 'Escape') {
                setIsOpen(false);
            }
        };

        const handleCustomOpen = (e: CustomEvent) => {
            setIsOpen(true);
            if (e.detail?.query) {
                setQuery(e.detail.query);
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        window.addEventListener('open-command-multiverse' as any, handleCustomOpen);
        return () => {
            window.removeEventListener('keydown', handleKeyDown);
            window.removeEventListener('open-command-multiverse' as any, handleCustomOpen);
        };
    }, []);

    // Subscribe to global search store (for tag clicks etc.)
    useEffect(() => {
        const unsubscribe = useUIStore.subscribe((state, prevState) => {
            if (state.isGlobalSearchOpen && !prevState.isGlobalSearchOpen) {
                setIsOpen(true);
                if (state.globalSearchQuery) {
                    setQuery(state.globalSearchQuery);
                }
                // Reset the store state after consuming
                useUIStore.getState().setGlobalSearchOpen(false);
            }
        });
        return () => unsubscribe();
    }, []);

    // Index on mount/interaction
    useEffect(() => {
        if (isOpen) {
            GlobalSearch.indexAll();
            setTimeout(() => inputRef.current?.focus(), 50);
        }
    }, [isOpen]);

    // Search
    useEffect(() => {
        // Clear results immediately to prevent stale selection during debounce
        setResults([]);
        setSelectedIndex(0);

        const runSearch = async () => {
            let hits = [];

            // 1. Actions (if query matches basic intent)
            const lowerQ = query.toLowerCase();
            const actions = [];
            // ... (rest of logic is same, implied)

            // Oracle Fallback
            if (query.startsWith('?') || query.startsWith('/')) {
                const cleanQuery = query.slice(1).trim();
                actions.push({
                    id: 'oracle-ask',
                    type: 'action',
                    title: `Ask Oracle: "${cleanQuery}"`,
                    subtitle: 'AI Assistant',
                    icon: <Sparkles size={14} className="text-neon" />,
                    action: () => {
                        useUIStore.getState().setOraclePendingMessage(cleanQuery);
                        useUIStore.getState().setOracleChatOpen(true);
                    }
                });
            }

            if (!query || lowerQ.includes('create') || lowerQ.includes('project') || lowerQ.includes('new')) {
                actions.push({
                    id: 'action-create-project',
                    type: 'action',
                    title: 'Create New Project',
                    subtitle: 'Quick Action',
                    icon: <Box size={14} className="text-accent" />,
                    action: () => useUIStore.getState().setCreateProjectOpen(true)
                });
            }


            if ('goals'.includes(lowerQ) || 'strategy'.includes(lowerQ) || 'plan'.includes(lowerQ)) {
                actions.push({
                    id: 'nav-goals',
                    type: 'action',
                    title: 'Go to Goals / Strategy',
                    subtitle: 'Navigation',
                    icon: <Target size={14} className="text-neon" />,
                    action: () => navigate('/goals')
                });
            }

            if ('backup'.includes(lowerQ) || 'export'.includes(lowerQ) || 'save'.includes(lowerQ)) {
                actions.push({
                    id: 'nav-backup',
                    type: 'action',
                    title: 'System Backup / Export',
                    subtitle: 'Settings',
                    icon: <DatabaseBackup size={14} className="text-amber-500" />,
                    action: () => navigate('/settings')
                });
            }

            if (lowerQ.includes('theme') || lowerQ.includes('color') || lowerQ.includes('style')) {
                const themes = ['default', 'music', 'synthwave', 'light'];
                themes.forEach(t => {
                    actions.push({
                        id: `theme-${t}`,
                        type: 'action',
                        title: `Theme: ${t.charAt(0).toUpperCase() + t.slice(1)}`,
                        subtitle: 'Appearance',
                        icon: <Palette size={14} className="text-purple-500" />,
                        action: () => {
                            useUIStore.getState().setMainTheme(t);
                            toast.success(`Theme set to ${t}`);
                        }
                    });
                });
            }


            if (query) {
                const searchHits = await GlobalSearch.search(query);
                hits = [...actions, ...searchHits];
            } else {
                hits = actions;
            }

            setResults(hits);
            setSelectedIndex(0);
        };
        const debounce = setTimeout(runSearch, 150);
        return () => clearTimeout(debounce);
    }, [query]);

    const handleSelect = useCallback((item: any) => {
        if (item.type === 'action' && item.action) {
            item.action();
        } else if (item.url) {
            navigate(item.url);
        }
        setIsOpen(false);
        setQuery('');
    }, [navigate]);

    // Navigation
    useEffect(() => {
        const handleNav = (e: KeyboardEvent) => {
            if (!isOpen) return;

            if (e.key === 'ArrowDown') {
                e.preventDefault();
                setSelectedIndex(prev => (prev + 1) % results.length);
            } else if (e.key === 'ArrowUp') {
                e.preventDefault();
                setSelectedIndex(prev => (prev - 1 + results.length) % results.length);
            } else if (e.key === 'Enter') {
                e.preventDefault();
                if (results[selectedIndex]) {
                    handleSelect(results[selectedIndex]);
                }
            }
        };

        window.addEventListener('keydown', handleNav);
        return () => window.removeEventListener('keydown', handleNav);
    }, [isOpen, results, selectedIndex, handleSelect]);

    if (!isOpen) return null;

    return (
        <AnimatePresence>
            <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
                {/* Backdrop */}
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    onClick={() => setIsOpen(false)}
                    className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                />

                {/* Modal */}
                <motion.div
                    initial={{ opacity: 0, scale: 0.95, y: -20 }}
                    animate={{ opacity: 1, scale: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95, y: -20 }}
                    className="relative w-full max-w-2xl bg-neutral-900 border border-white/10 rounded-xl shadow-2xl overflow-hidden flex flex-col"
                >
                    {/* Header / Input */}
                    <div className="flex items-center gap-3 p-4 border-b border-white/10">
                        <Search className="text-gray-500" size={20} />
                        <input
                            ref={inputRef}
                            value={query}
                            onChange={e => setQuery(e.target.value)}
                            placeholder="Type a command or search..."
                            className="flex-1 bg-transparent text-lg text-white placeholder-gray-600 focus:outline-none font-mono"
                        />
                        <div className="flex gap-2">
                            <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-gray-500 font-mono">ESC</span>
                        </div>
                    </div>

                    {/* Results */}
                    <div className="max-h-[50vh] overflow-y-auto p-2" ref={listRef}>
                        {results.length === 0 ? (
                            <div className="py-12 text-center text-gray-600">
                                {query ? (
                                    <p>No results found.</p>
                                ) : (
                                    <div className="flex flex-col items-center gap-2">
                                        <Command size={32} className="opacity-20" />
                                        <p className="text-sm font-mono uppercase tracking-widest opacity-50">Global Command Active</p>
                                    </div>
                                )}
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {results.map((item, index) => (
                                    <button
                                        key={item.id}
                                        onClick={() => handleSelect(item)}
                                        onMouseEnter={() => setSelectedIndex(index)}
                                        className={clsx(
                                            "w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-colors group",
                                            index === selectedIndex ? "bg-accent/10" : "hover:bg-white/5"
                                        )}
                                    >
                                        <div className={clsx(
                                            "p-2 rounded-md",
                                            index === selectedIndex ? "bg-accent text-black" : "bg-white/5 text-gray-400"
                                        )}>
                                            {item.type === 'project' && <Folder size={18} />}
                                            {item.type === 'filament' && <Box size={18} />}
                                            {item.type === 'tool' && <Wrench size={18} />}
                                            {(item.type === 'part' || item.type === 'inventory') && <Package size={18} />}
                                            {item.type === 'task' && <CheckSquare size={18} />}
                                            {item.type === 'note' && <Book size={18} />}
                                            {item.type === 'log' && <HistoryIcon size={18} />}
                                            {item.type === 'action' && <Zap size={18} />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center justify-between">
                                                <span className={clsx("font-bold truncate", index === selectedIndex ? "text-accent" : "text-white")}>{item.title}</span>
                                                {index === selectedIndex && <ArrowRight size={14} className="text-accent" />}
                                            </div>
                                            <div className="flex items-center gap-2 text-xs text-gray-500 font-mono">
                                                <span className="uppercase">{item.type}</span>
                                                <span>•</span>
                                                <span className="truncate">{item.subtitle}</span>
                                            </div>
                                        </div>
                                    </button>
                                ))}
                            </div>
                        )}
                    </div>

                    {/* Footer */}
                    <div className="bg-black/50 p-2 text-[10px] text-gray-600 font-mono flex justify-between px-4 border-t border-white/5">
                        <span>Search powered by Orama</span>
                        <div className="flex gap-2">
                            <span>Select ↵</span>
                            <span>Navigate ↑↓</span>
                        </div>
                    </div>
                </motion.div>
            </div>
        </AnimatePresence>
    );
}
