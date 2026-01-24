import { useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { ArrowLeft, Cpu, History, FileText, AlertTriangle, Plus, PenLine, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import { ComputerSpecsCard } from '../components/assets/ComputerSpecsCard';
import { motion } from 'framer-motion';
import { ReferencesPanel } from '../components/ui/ReferencesPanel';
import { toast } from 'sonner';

export function AssetDetail() {
    const { id } = useParams();
    const assetId = parseInt(id || '0');
    const [tab, setTab] = useState<'overview' | 'history' | 'docs'>('overview');

    const asset = useLiveQuery(() => db.assets.get(assetId), [assetId]);

    // Fetch related library docs
    const relatedDocs = useLiveQuery(async () => {
        if (!asset?.related_library_ids || asset.related_library_ids.length === 0) return [];
        return await db.library_items.where('id').anyOf(asset.related_library_ids).toArray();
    }, [asset]) || [];

    // Linking State
    const [isLinking, setIsLinking] = useState(false);
    const [linkSearch, setLinkSearch] = useState('');
    const librarySearchResults = useLiveQuery(async () => {
        if (!linkSearch) return [];
        return await db.library_items.filter(i => i.title.toLowerCase().includes(linkSearch.toLowerCase())).limit(5).toArray();
    }, [linkSearch]) || [];

    const handleLinkDoc = async (docId: number) => {
        if (!asset) return;
        const current = asset.related_library_ids || [];
        if (current.includes(docId)) return;
        await db.assets.update(asset.id!, { related_library_ids: [...current, docId] });
        setIsLinking(false);
        setLinkSearch('');
        toast.success("Document linked");
    };

    const handleUnlinkDoc = async (docId: number) => {
        if (!asset) return;
        const current = asset.related_library_ids || [];
        await db.assets.update(asset.id!, { related_library_ids: current.filter(id => id !== docId) });
        toast.success("Document unlinked");
    };

    // Fetch related projects for history
    const history = useLiveQuery(async () => {
        if (!asset?.related_project_ids) return [];
        return await db.projects.where('id').anyOf(asset.related_project_ids).toArray();
    }, [asset]);

    if (!asset) return <div className="p-12 text-center text-gray-500">Asset not found</div>;

    return (
        <div className="h-full flex flex-col bg-black text-white overflow-hidden">
            {/* Header */}
            <div className="h-16 flex items-center justify-between px-6 border-b border-white/10 shrink-0 bg-black/50 backdrop-blur">
                <div className="flex items-center gap-4">
                    <Link to="/assets" className="text-gray-500 hover:text-white transition-colors">
                        <ArrowLeft size={20} />
                    </Link>
                    <div>
                        <h1 className="text-xl font-bold tracking-tight">{asset.name}</h1>
                        <div className="flex items-center gap-2 text-xs text-gray-400">
                            <span className="bg-white/10 px-1.5 py-0.5 rounded">{asset.category}</span>
                            <span>#{asset.id}</span>
                            <span>•</span>
                            <span className={clsx(
                                "capitalize",
                                asset.status === 'active' ? "text-green-500" :
                                    asset.status === 'broken' ? "text-red-500" : "text-yellow-500"
                            )}>{asset.status}</span>
                        </div>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button className="p-2 hover:bg-white/5 rounded-lg text-gray-400 hover:text-white">
                        <PenLine size={18} />
                    </button>
                    <button className="p-2 hover:bg-red-500/10 rounded-lg text-red-500 hover:text-red-400">
                        <Trash2 size={18} />
                    </button>
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Main Content */}
                <div className="flex-1 overflow-y-auto p-8">
                    <div className="max-w-4xl mx-auto space-y-8">

                        {/* Computer Specs (Top billing if exists) */}
                        {asset.specs_computer && (
                            <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
                                <ComputerSpecsCard specs={asset.specs_computer} />
                            </motion.div>
                        )}

                        {/* Symptom Library */}
                        <div>
                            <div className="flex items-center justify-between mb-4">
                                <h3 className="text-lg font-bold flex items-center gap-2">
                                    <AlertTriangle className="text-orange-500" size={20} />
                                    Known Symptoms
                                </h3>
                                <button className="text-xs bg-white/5 hover:bg-white/10 px-2 py-1 rounded border border-white/5">
                                    + Log Issue
                                </button>
                            </div>
                            {(!asset.symptoms || asset.symptoms.length === 0) ? (
                                <div className="p-4 border border-dashed border-white/10 rounded-xl text-center text-gray-500 text-sm">
                                    No known issues logged.
                                </div>
                            ) : (
                                <div className="space-y-2">
                                    {asset.symptoms.map(sym => (
                                        <div key={sym.id} className="bg-orange-500/5 border border-orange-500/20 p-3 rounded-lg flex items-start gap-3">
                                            <AlertTriangle size={16} className="text-orange-500 mt-0.5 shrink-0" />
                                            <div>
                                                <div className="text-sm text-gray-200">{sym.description}</div>
                                                {sym.solution_ref && (
                                                    <div className="text-xs text-orange-500/60 mt-1">Ref: {sym.solution_ref}</div>
                                                )}
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Service History */}
                        <div className="pt-8 border-t border-white/5">
                            <h3 className="text-lg font-bold flex items-center gap-2 mb-6">
                                <History className="text-blue-500" size={20} />
                                service History
                            </h3>
                            <div className="relative border-l-2 border-white/10 ml-3 space-y-8 pl-8">
                                {(history || []).sort((a, b) => b.updated_at.getTime() - a.updated_at.getTime()).map(proj => (
                                    <div key={proj.id} className="relative">
                                        {/* Dot */}
                                        <div className="absolute -left-[39px] top-1 w-5 h-5 rounded-full bg-black border-2 border-blue-500/50" />

                                        <Link to={`/projects/${proj.id}`} className="block group">
                                            <div className="text-xs text-gray-500 mb-1">{proj.updated_at.toLocaleDateString()}</div>
                                            <div className="text-lg font-bold text-white group-hover:text-accent transition-colors">{proj.title}</div>
                                            <div className="text-sm text-gray-400 mt-1 line-clamp-2">{proj.status_description}</div>
                                            <div className="mt-2 flex gap-2">
                                                <span className="text-[10px] bg-white/5 px-1.5 py-0.5 rounded border border-white/5 text-gray-400">
                                                    {proj.status}
                                                </span>
                                            </div>
                                        </Link>
                                    </div>
                                ))}
                                {history?.length === 0 && (
                                    <div className="text-sm text-gray-500 italic">No linked service projects.</div>
                                )}
                            </div>
                        </div>

                    </div>
                </div>

                {/* Sidebar (Docs & Meta) */}
                <div className="w-80 border-l border-white/5 bg-black/20 p-6 space-y-6">
                    <div>
                        <h4 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider">Asset Details</h4>
                        <div className="space-y-3 text-sm">
                            <div>
                                <div className="text-gray-600 text-xs">Make</div>
                                <div className="truncate">{asset.make || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-gray-600 text-xs">Model</div>
                                <div className="truncate">{asset.model || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-gray-600 text-xs">Serial</div>
                                <div className="font-mono text-xs truncate">{asset.serial_number || 'N/A'}</div>
                            </div>
                            <div>
                                <div className="text-gray-600 text-xs">Location</div>
                                <div>{asset.location || 'Unassigned'}</div>
                            </div>
                        </div>
                    </div>

                    <div className="pt-6 border-t border-white/5">
                        <h4 className="text-sm font-bold text-gray-400 mb-4 uppercase tracking-wider flex items-center justify-between">
                            Documents
                            <button
                                onClick={() => setIsLinking(!isLinking)}
                                className="text-accent hover:text-white"
                                title="Link Library Document"
                            >
                                <Plus size={14} />
                            </button>
                        </h4>

                        {/* Linking Interface */}
                        {isLinking && (
                            <div className="mb-4 bg-black/40 p-2 rounded border border-white/10 animate-in slide-in-from-top-2">
                                <input
                                    autoFocus
                                    placeholder="Search library..."
                                    className="w-full bg-transparent text-xs border-b border-white/10 p-1 mb-2 focus:outline-none focus:border-accent"
                                    value={linkSearch}
                                    onChange={e => setLinkSearch(e.target.value)}
                                />
                                <div className="space-y-1 max-h-32 overflow-y-auto">
                                    {librarySearchResults.map(res => (
                                        <button
                                            key={res.id}
                                            onClick={() => handleLinkDoc(res.id!)}
                                            className="w-full text-left text-xs p-1 hover:bg-white/10 rounded truncate flex items-center gap-2"
                                        >
                                            <FileText size={10} className="text-gray-500" />
                                            {res.title}
                                        </button>
                                    ))}
                                    {linkSearch && librarySearchResults.length === 0 && (
                                        <div className="text-xs text-gray-500 italic p-1">No matches</div>
                                    )}
                                </div>
                            </div>
                        )}

                        <div className="space-y-2">
                            {/* Manuals (Legacy) */}
                            {asset.manuals?.map((doc, i) => (
                                <a key={i} href={doc.url} target="_blank" rel="noreferrer" className="flex items-center gap-2 p-2 hover:bg-white/5 rounded transition-colors text-sm text-gray-300">
                                    <FileText size={16} className="text-gray-500" />
                                    <span className="truncate">{doc.title}</span>
                                </a>
                            ))}

                            {/* Linked Library Items */}
                            {relatedDocs.map(doc => (
                                <div key={doc.id} className="group flex items-center gap-2 p-2 hover:bg-white/5 rounded transition-colors text-sm text-gray-300 relative">
                                    <FileText size={16} className="text-indigo-400" />
                                    <span className="truncate flex-1" title={doc.title}>{doc.title}</span>
                                    <button
                                        onClick={() => handleUnlinkDoc(doc.id!)}
                                        className="opacity-0 group-hover:opacity-100 p-1 hover:text-red-500 transition-opacity"
                                        title="Unlink"
                                    >
                                        <Trash2 size={12} />
                                    </button>
                                </div>
                            ))}

                            {(!asset.manuals?.length && relatedDocs.length === 0) && (
                                <div className="text-xs text-gray-600 italic">No documents linked.</div>
                            )}
                        </div>
                    </div>

                    {/* References / Backlinks */}
                    <div className="pt-6 border-t border-white/5">
                        <ReferencesPanel entityType="asset" entityId={assetId} />
                    </div>
                </div>
            </div>
        </div>
    );
}
