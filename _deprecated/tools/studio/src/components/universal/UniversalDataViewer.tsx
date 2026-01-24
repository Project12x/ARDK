
import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Search, Plus, Save, Trash2, ArrowLeft } from 'lucide-react';
import { Link } from 'react-router-dom';
import { AIService } from '../../lib/AIService';
import { toast } from 'sonner';

/**
 * WORKSHOP.OS UNIVERSAL VIEWER
 * 
 * Automatically renders ANY table in the database.
 * Provides:
 * - Search / Filtering
 * - JSON / Form Editing
 * - AI Action context
 */
export function UniversalDataViewer() {
    const { tableName } = useParams<{ tableName: string }>();
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editData, setEditData] = useState<string>(''); // JSON string for editing

    // 1. Dynamic Data Fetch
    const data = useLiveQuery(async () => {
        if (!tableName) return [];
        if (!tableName) return [];
        const table = (db as any).table(tableName);
        if (!table) return [];
        return await table.toArray();
    }, [tableName]) || [];

    // 2. Filter
    const filtered = data.filter(item => {
        if (!searchQuery) return true;
        return JSON.stringify(item).toLowerCase().includes(searchQuery.toLowerCase());
    });

    // 3. Selection
    const selectedItem = data.find(d => d.id === selectedId);

    // 4. Handlers
    const handleSave = async () => {
        try {
            const parsed = JSON.parse(editData);
            await (db as any).table(tableName).put(parsed);
            setIsEditing(false);
            toast.success("Record saved");
        } catch (e) {
            toast.error("Invalid JSON");
        }
    };

    const handleDelete = async () => {
        if (!selectedId || !confirm("Delete this record?")) return;
        await (db as any).table(tableName).delete(selectedId);
        setSelectedId(null);
        toast.success("Record deleted");
    };

    const handleCreate = async () => {
        // 1. Try to find a template for this collection
        // @ts-ignore
        const template = await db.item_templates.where('collection_name').equals(tableName).first();

        let initialData = { name: "New Item" };

        if (template && template.default_schema) {
            initialData = { ...template.default_schema };
        } else if (data.length > 0) {
            // Fallback: Clone structure of first item
            initialData = { ...data[0], id: undefined };
            // Clear string values
            for (const key in initialData) {
                // @ts-ignore
                if (typeof initialData[key] === 'string') initialData[key] = "";
            }
        }

        const id = await (db as any).table(tableName).add(initialData);
        setSelectedId(id as number);
        setIsEditing(true);
        setEditData(JSON.stringify(initialData, null, 2));
    };

    const handleAIAction = async (prompt: string) => {
        if (!selectedItem) return;
        toast.promise(
            async () => {
                const response = await AIService.chatWithProject(prompt, selectedItem);
                // Assuming chatWithProject is generalized enough (it uses title/status/desc)
                // If not, we might need a generic 'chatWithEntity'
                return response;
            },
            {
                loading: 'Thinking...',
                success: (data) => {
                    // Try to parse generic message
                    try {
                        const parsed = JSON.parse(data);
                        return parsed.message || JSON.stringify(parsed);
                    } catch {
                        return data;
                    }
                },
                error: 'AI Failed'
            }
        );
    }

    if (!tableName) return <div className="p-8 text-red-500">No Collection Specified</div>;

    return (
        <div className="flex h-full bg-black/90 text-white font-mono">
            {/* LEFT: LIST */}
            <div className="w-1/3 border-r border-white/10 flex flex-col">
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-white/5">
                    <div className='flex items-center gap-2'>
                        <Link to="/" className='text-gray-500 hover:text-white'><ArrowLeft size={16} /></Link>
                        <h1 className="font-bold text-lg uppercase tracking-wider text-accent">{tableName.replace(/_/g, ' ')}</h1>
                    </div>
                    <button onClick={handleCreate} className="p-1 hover:text-green-400"><Plus size={20} /></button>
                </div>
                <div className="p-2">
                    <div className="relative">
                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 w-4 h-4" />
                        <input
                            value={searchQuery}
                            onChange={(e) => setSearchQuery(e.target.value)}
                            placeholder="Filter..."
                            className="w-full bg-black/50 border border-white/10 rounded px-9 py-2 text-xs focus:border-accent outline-none"
                        />
                    </div>
                </div>
                <div className="flex-1 overflow-y-auto p-2 space-y-1">
                    {filtered.map(item => (
                        <div
                            key={item.id}
                            onClick={() => { setSelectedId(item.id); setIsEditing(false); }}
                            className={`p-3 rounded cursor-pointer border hover:border-white/20 transition-all ${selectedId === item.id ? 'bg-accent/10 border-accent' : 'bg-transparent border-transparent'}`}
                        >
                            <div className="font-bold text-sm truncate">{item.title || item.name || `ID #${item.id}`}</div>
                            <div className="text-xs text-gray-500 truncate">{JSON.stringify(item).slice(0, 50)}...</div>
                        </div>
                    ))}
                </div>
            </div>

            {/* RIGHT: DETAIL */}
            <div className="flex-1 flex flex-col bg-neutral-900/50">
                {selectedItem ? (
                    <>
                        <div className="h-16 border-b border-white/10 flex items-center justify-between px-6">
                            <div className="text-xs text-gray-500">ID: {selectedItem.id}</div>
                            <div className="flex gap-2">
                                {isEditing ? (
                                    <>
                                        <button onClick={() => setIsEditing(false)} className="text-gray-400 hover:text-white text-xs px-3">CANCEL</button>
                                        <button onClick={handleSave} className="flex items-center gap-2 bg-green-500/20 text-green-400 px-4 py-1.5 rounded text-xs hover:bg-green-500/30">
                                            <Save size={14} /> SAVE
                                        </button>
                                    </>
                                ) : (
                                    <>
                                        <button onClick={handleDelete} className="text-gray-600 hover:text-red-500 p-2"><Trash2 size={16} /></button>
                                        <button onClick={() => { setEditData(JSON.stringify(selectedItem, null, 2)); setIsEditing(true); }} className="bg-white/10 hover:bg-white/20 px-4 py-1.5 rounded text-xs">
                                            EDIT RAW
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>

                        <div className="flex-1 overflow-y-auto p-6">
                            {isEditing ? (
                                <textarea
                                    value={editData}
                                    onChange={e => setEditData(e.target.value)}
                                    className="w-full h-full bg-black border border-white/10 rounded p-4 font-mono text-xs text-green-300 outline-none focus:border-accent"
                                    spellCheck={false}
                                />
                            ) : (
                                <div className="space-y-6 max-w-3xl mx-auto">
                                    {/* AI HEADER */}
                                    <div className="bg-gradient-to-r from-indigo-900/20 to-purple-900/20 border border-white/5 rounded-xl p-6 relative overflow-hidden group">
                                        <div className="absolute top-0 right-0 p-4 opacity-50 group-hover:opacity-100 transition-opacity">
                                            <button
                                                onClick={() => handleAIAction("Analyze this record and suggest improvements.")}
                                                className="text-xs bg-indigo-500/20 hover:bg-indigo-500/40 text-indigo-300 px-3 py-1 rounded-full border border-indigo-500/30"
                                            >
                                                ✨ AI Analyze
                                            </button>
                                        </div>
                                        <h2 className="text-2xl font-bold mb-2">{selectedItem.title || selectedItem.name || 'Untitled'}</h2>
                                        <p className="text-gray-400 text-sm max-w-xl">{selectedItem.description || selectedItem.summary || "No description."}</p>
                                    </div>

                                    {/* DYNAMIC FIELDS */}
                                    <div className="grid grid-cols-2 gap-4">
                                        {Object.entries(selectedItem).map(([key, value]) => {
                                            if (['id', 'title', 'name', 'description'].includes(key)) return null;
                                            return (
                                                <div key={key} className="bg-white/5 rounded p-4 border border-white/5">
                                                    <div className="text-[10px] uppercase text-gray-500 mb-1 tracking-wider">{key.replace(/_/g, ' ')}</div>
                                                    <div className="text-sm font-mono text-gray-300 break-words">
                                                        {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                                                    </div>
                                                </div>
                                            )
                                        })}
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-gray-700 font-mono tracking-widest text-sm">
                        SELECT A RECORD FROM {tableName}
                    </div>
                )}
            </div>
        </div>
    );
}
