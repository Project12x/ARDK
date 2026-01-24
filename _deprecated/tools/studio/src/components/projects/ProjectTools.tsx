import { useState, useMemo } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Trash2, Plus, Check } from 'lucide-react';
import clsx from 'clsx';

export function ProjectTools({ projectId }: { projectId: number }) {
    const tools = useLiveQuery(() => db.project_tools.where('project_id').equals(projectId).toArray());
    const globalInventory = useLiveQuery(() => db.inventory.where('type').equals('tool').toArray());

    const [newItem, setNewItem] = useState('');
    const [showSuggestions, setShowSuggestions] = useState(false);

    const suggestions = useMemo(() => {
        if (!newItem || !globalInventory) return [];
        return globalInventory.filter(t => t.name.toLowerCase().includes(newItem.toLowerCase())).slice(0, 5);
    }, [newItem, globalInventory]);

    const handleAdd = async (name: string, status: 'owned' | 'borrow' | 'buy' | 'rent' = 'owned') => {
        await db.project_tools.add({
            project_id: projectId,
            name,
            status,
            is_acquired: status === 'owned'
        });
        setNewItem('');
        setShowSuggestions(false);
    };

    const toggleAcquired = (id: number, current: boolean) => {
        db.project_tools.update(id, { is_acquired: !current });
    };

    const removeTool = (id: number) => {
        db.project_tools.delete(id);
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-2 max-w-5xl mx-auto">
            <div className="flex justify-between items-end border-b border-white/10 pb-4">
                <div>
                    <h2 className="text-xl font-bold text-white">Tools & Equipment</h2>
                    <p className="text-gray-400 text-sm">Manage required tools, equipment, and resources for this project.</p>
                </div>
            </div>

            <div className="bg-black/30 p-4 rounded-lg border border-white/5 relative">
                <div className="flex gap-2">
                    <div className="relative flex-1">
                        <Input
                            placeholder="Add required tool..."
                            value={newItem}
                            onChange={e => { setNewItem(e.target.value); setShowSuggestions(true); }}
                            onKeyDown={e => { if (e.key === 'Enter') handleAdd(newItem, 'buy'); }}
                        />
                        {showSuggestions && suggestions.length > 0 && (
                            <div className="absolute top-full left-0 right-0 bg-gray-900 border border-white/20 z-20 mt-1 rounded shadow-xl">
                                {suggestions.map(s => (
                                    <div
                                        key={s.id}
                                        className="p-2 hover:bg-white/10 cursor-pointer flex justify-between items-center text-sm"
                                        onClick={() => handleAdd(s.name, 'owned')}
                                    >
                                        <span>{s.name}</span>
                                        <span className="text-xs text-green-500 font-mono">[INVENTORY]</span>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                    <Button onClick={() => handleAdd(newItem, 'buy')}><Plus size={16} /></Button>
                </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                {tools?.sort((a, b) => Number(a.is_acquired) - Number(b.is_acquired)).map(tool => (
                    <div key={tool.id} className={clsx("p-3 rounded border flex items-center justify-between group", tool.is_acquired ? "bg-green-900/10 border-green-500/30" : "bg-red-900/5 border-red-500/20")}>
                        <div className="flex items-center gap-3">
                            <button
                                onClick={() => toggleAcquired(tool.id!, tool.is_acquired)}
                                className={clsx("w-5 h-5 rounded border flex items-center justify-center transition-colors", tool.is_acquired ? "bg-green-500 border-green-500 text-black" : "border-white/20 hover:border-white/50")}
                            >
                                {tool.is_acquired && <Check size={12} strokeWidth={4} />}
                            </button>
                            <div>
                                <p className={clsx("font-bold text-sm", tool.is_acquired ? "text-gray-400 line-through" : "text-white")}>{tool.name}</p>
                                <p className="text-[10px] uppercase font-mono text-gray-500">{tool.status}</p>
                            </div>
                        </div>
                        <button onClick={() => removeTool(tool.id!)} className="opacity-0 group-hover:opacity-100 text-red-500 hover:text-red-400 transition-opacity">
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}
            </div>

            {tools?.length === 0 && (
                <div className="text-center py-10 text-gray-600 font-mono text-sm">
                    No tools required yet.
                </div>
            )}
        </div>
    );
}
