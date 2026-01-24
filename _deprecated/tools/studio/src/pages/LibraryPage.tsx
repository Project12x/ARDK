import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type LibraryItem } from '../lib/db';
import { Button } from '../components/ui/Button';
import { Book, FileText, Image as ImageIcon, Upload, Download, Trash2, Search, Cpu, Disc, Film, Archive, LayoutGrid, List } from 'lucide-react';
import { toast } from 'sonner';
import clsx from 'clsx';
import { AIService } from '../lib/AIService';
import { UniversalCard } from '../components/ui/UniversalCard';

type Category = 'bookshelf' | 'records' | 'photos' | 'vhs' | 'junk';
type ViewMode = 'shelf' | 'explorer';

export function LibraryPage() {
    const allItems = useLiveQuery(() => db.library_items.reverse().toArray()) || [];
    const [search, setSearch] = useState('');
    const [category, setCategory] = useState<Category>('bookshelf');
    const [viewMode, setViewMode] = useState<ViewMode>('shelf');
    const [isUploading, setIsUploading] = useState(false);

    // Filter Items
    const items = allItems.filter(i => {
        const matchesSearch = i.title.toLowerCase().includes(search.toLowerCase());
        const matchesCategory = i.category === category || (!i.category && category === 'junk'); // Legacy items -> junk
        return matchesSearch && matchesCategory;
    });

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (file.size > 20 * 1024 * 1024) { // Increased to 20MB
            toast.error("File too large. Max 20MB.");
            return;
        }

        setIsUploading(true);
        try {
            const reader = new FileReader();
            reader.onload = async (ev) => {
                const content = ev.target?.result as string;
                let type: LibraryItem['type'] = 'other';
                let itemCategory: Category = 'junk';

                // Auto-Classify
                const mime = file.type;
                if (mime.includes('pdf')) { type = 'pdf'; itemCategory = 'bookshelf'; }
                else if (mime.includes('image')) { type = 'image'; itemCategory = 'photos'; }
                else if (mime.includes('text') || mime.includes('json') || mime.includes('markdown')) { type = 'text'; itemCategory = 'bookshelf'; }
                else if (mime.includes('audio')) { type = 'audio'; itemCategory = 'records'; }
                else if (mime.includes('video')) { type = 'video'; itemCategory = 'vhs'; }

                // Default fallbacks if category selected is explicit?? No, auto-detect is better for drag-drop upload
                // But if user is IN "Records" and uploads a PDF, maybe warn? For now just auto-sort.

                await db.library_items.add({
                    title: file.name,
                    type,
                    category: itemCategory,
                    folder_path: '/',
                    content,
                    tags: [],
                    created_at: new Date(),
                    file_size: file.size,
                    mime_type: file.type
                });
                toast.success(`added to ${itemCategory.toUpperCase()}`);
            };

            if (file.type.includes('text') || file.type.includes('json') || file.type.includes('markdown')) {
                reader.readAsText(file);
            } else {
                reader.readAsDataURL(file);
            }
        } catch (err) {
            console.error(err);
            toast.error("Failed to upload");
        } finally {
            setIsUploading(false);
        }
    };

    const handleDelete = async (id: number) => {
        if (confirm("Delete this library item?")) {
            await db.library_items.delete(id);
            toast.success("Deleted");
        }
    };

    return (
        <div className="h-full flex bg-background text-white overflow-hidden">
            {/* Sidebar */}
            <div className="w-64 border-r border-white/10 flex flex-col bg-black/20">
                <div className="p-6">
                    <h1 className="text-xl font-bold font-display flex items-center gap-2">
                        <Archive className="text-indigo-400" />
                        Library
                    </h1>
                </div>

                <div className="flex-1 px-3 space-y-1">
                    <SidebarItem active={category === 'bookshelf'} icon={Book} label="Bookshelf" onClick={() => setCategory('bookshelf')} count={allItems.filter(i => i.category === 'bookshelf').length} />
                    <SidebarItem active={category === 'records'} icon={Disc} label="Record Cabinet" onClick={() => setCategory('records')} count={allItems.filter(i => i.category === 'records').length} />
                    <SidebarItem active={category === 'photos'} icon={ImageIcon} label="Photo Album" onClick={() => setCategory('photos')} count={allItems.filter(i => i.category === 'photos').length} />
                    <SidebarItem active={category === 'vhs'} icon={Film} label="VHS Collection" onClick={() => setCategory('vhs')} count={allItems.filter(i => i.category === 'vhs').length} />
                    <div className="h-px bg-white/10 my-2 mx-2" />
                    <SidebarItem active={category === 'junk'} icon={Archive} label="Junk Drawer" onClick={() => setCategory('junk')} count={allItems.filter(i => !i.category || i.category === 'junk').length} />
                </div>

                <div className="p-4 border-t border-white/10">
                    <div className="relative">
                        <input
                            type="file"
                            onChange={handleFileUpload}
                            className="absolute inset-0 opacity-0 cursor-pointer"
                            disabled={isUploading}
                        />
                        <Button className="w-full" disabled={isUploading}>
                            <Upload size={16} className="mr-2" />
                            Upload File
                        </Button>
                    </div>
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0">
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex items-center justify-between bg-black/10">
                    <div className="relative">
                        <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                        <input
                            value={search}
                            onChange={(e) => setSearch(e.target.value)}
                            placeholder={`Search ${category}...`}
                            className="bg-black/40 border border-white/10 rounded-full pl-9 pr-4 py-1.5 text-sm focus:outline-none focus:border-indigo-500 w-64"
                        />
                    </div>
                    <div className="flex bg-black/40 rounded border border-white/10 p-1 gap-1">
                        <button onClick={() => setViewMode('shelf')} className={clsx("p-1.5 rounded", viewMode === 'shelf' ? "bg-white/10 text-white" : "text-gray-500 hover:text-white")}>
                            <LayoutGrid size={16} />
                        </button>
                        <button onClick={() => setViewMode('explorer')} className={clsx("p-1.5 rounded", viewMode === 'explorer' ? "bg-white/10 text-white" : "text-gray-500 hover:text-white")}>
                            <List size={16} />
                        </button>
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto p-6 bg-dots-pattern">
                    {items.length === 0 ? (
                        <div className="h-full flex flex-col items-center justify-center text-gray-500 opacity-50">
                            <Archive size={64} className="mb-4" />
                            <p>Empty Section</p>
                        </div>
                    ) : viewMode === 'shelf' ? (
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                            {items.map(item => (
                                <DraggableLibraryItem key={item.id} item={item} onDelete={() => handleDelete(item.id!)} />
                            ))}
                        </div>
                    ) : (
                        <div className="bg-black/20 border border-white/10 rounded-lg overflow-hidden">
                            <table className="w-full text-sm text-left">
                                <thead className="bg-white/5 text-gray-400 font-mono text-xs uppercase">
                                    <tr>
                                        <th className="p-3">Name</th>
                                        <th className="p-3">Type</th>
                                        <th className="p-3">Size</th>
                                        <th className="p-3">Date</th>
                                        <th className="p-3 text-right">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-white/5">
                                    {items.map(item => (
                                        <tr key={item.id} className="hover:bg-white/5 group">
                                            <td className="p-3 font-bold">{item.title}</td>
                                            <td className="p-3 text-gray-500">{item.type}</td>
                                            <td className="p-3 text-gray-500 font-mono">{(item.file_size ? (item.file_size / 1024).toFixed(0) + ' KB' : '-')}</td>
                                            <td className="p-3 text-gray-500">{item.created_at.toLocaleDateString()}</td>
                                            <td className="p-3 text-right">
                                                <button onClick={() => handleDelete(item.id!)} className="text-red-500 opacity-0 group-hover:opacity-100"><Trash2 size={14} /></button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

function SidebarItem({ icon: Icon, label, active, onClick, count }: any) {
    return (
        <button
            onClick={onClick}
            className={clsx(
                "w-full flex items-center justify-between px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                active ? "bg-indigo-500/20 text-indigo-300" : "text-gray-400 hover:bg-white/5 hover:text-white"
            )}
        >
            <div className="flex items-center gap-3">
                <Icon size={16} />
                <span>{label}</span>
            </div>
            {count > 0 && <span className="text-xs opacity-50 bg-black/40 px-1.5 rounded-full">{count}</span>}
        </button>
    );
}

function DraggableLibraryItem({ item, onDelete }: { item: LibraryItem, onDelete: () => void }) {
    return (
        <UniversalCard
            entityType="library"
            entityId={item.id!}
            title={item.title}
            metadata={{ category: item.category, type: item.type }}
            onDelete={onDelete}
            className="bg-black/40 border-white/5 hover:border-indigo-500/50 p-3 hover:bg-white/5 hover:shadow-xl"
        >
            <div className="aspect-[3/4] bg-black/60 rounded flex items-center justify-center overflow-hidden mb-3 border border-white/5 shadow-inner">
                {item.type === 'image' && item.content ? (
                    <img src={item.content} alt={item.title} className="w-full h-full object-cover opacity-90" />
                ) : (
                    <IconForType type={item.type} />
                )}
            </div>

            <div className="px-1">
                <div className="font-bold text-xs truncate mb-1" title={item.title}>{item.title}</div>
                <div className="flex justify-between items-center text-[10px] text-gray-500">
                    <span className="uppercase">{item.type}</span>
                </div>
            </div>
        </UniversalCard>
    );
}

function IconForType({ type }: { type: string }) {
    if (type === 'pdf') return <FileText size={48} className="text-red-400/80" />;
    if (type === 'text') return <FileText size={48} className="text-gray-400/80" />;
    if (type === 'ebook') return <Book size={48} className="text-yellow-400/80" />;
    if (type === 'audio') return <Disc size={48} className="text-pink-400/80" />;
    if (type === 'video') return <Film size={48} className="text-cyan-400/80" />;
    return <Archive size={48} className="text-blue-400/80" />;
}
