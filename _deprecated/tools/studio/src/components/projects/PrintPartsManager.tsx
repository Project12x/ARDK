import React, { useState } from 'react';
import { type PrintPart } from '../../lib/db';
import { Printer, Check, Trash2, ExternalLink, Box, Plus, Layers, Image as ImageIcon, Loader2 } from 'lucide-react';
import clsx from 'clsx';

interface PrintPartsManagerProps {
    parts: PrintPart[];
    onChange: (parts: PrintPart[]) => void;
}

export function PrintPartsManager({ parts, onChange }: PrintPartsManagerProps) {
    const [newPartName, setNewPartName] = useState('');
    const [newPartCount, setNewPartCount] = useState(1);
    const [newPartUrl, setNewPartUrl] = useState('');
    const [isFetching, setIsFetching] = useState(false);

    const handleAdd = async () => {
        // Allow adding if URL is present OR name is present
        if (!newPartName.trim() && !newPartUrl.trim()) return;

        setIsFetching(true);
        let finalName = newPartName;
        let finalThumbnail = '';

        if (newPartUrl.trim()) {
            try {
                // Attempt to fetch metadata for Thingiverse or other sites
                const apiUrl = `https://api.microlink.io?url=${encodeURIComponent(newPartUrl)}`;
                const res = await fetch(apiUrl);
                const data = await res.json();

                if (data.status === 'success') {
                    if (!finalName && data.data.title) {
                        finalName = data.data.title;
                    }
                    if (data.data.image && data.data.image.url) {
                        finalThumbnail = data.data.image.url;
                    }
                }
            } catch (e) {
                console.error("Failed to fetch metadata", e);
            }
        }

        // Fallback name if still empty
        if (!finalName) finalName = "Untitled Part";

        const newPart: PrintPart = {
            id: crypto.randomUUID(),
            name: finalName,
            count: newPartCount,
            source_url: newPartUrl,
            thumbnail_url: finalThumbnail,
            status: 'stl'
        };
        onChange([...parts, newPart]);
        setNewPartName('');
        setNewPartUrl('');
        setNewPartCount(1);
        setIsFetching(false);
    };

    const handleDelete = (id: string) => {
        onChange(parts.filter(p => p.id !== id));
    };

    const handleStatusChange = (id: string, newStatus: PrintPart['status']) => {
        onChange(parts.map(p => p.id === id ? { ...p, status: newStatus } : p));
    };

    const statuses: PrintPart['status'][] = ['stl', 'sliced', 'printing', 'done'];
    const statusIcons = {
        stl: Box,
        sliced: Layers,
        printing: Printer,
        done: Check
    };
    const statusColors = {
        stl: 'text-gray-400 bg-gray-900',
        sliced: 'text-blue-400 bg-blue-900/20',
        printing: 'text-amber-400 bg-amber-900/20 animate-pulse',
        done: 'text-green-400 bg-green-900/20'
    };

    return (
        <div className="space-y-4">
            <h3 className="text-xs font-bold uppercase text-gray-400 flex items-center gap-2 mb-2">
                <Printer size={14} /> Fabrication Assets
            </h3>

            {/* List */}
            <div className="space-y-2">
                {parts.map(part => (
                    <div key={part.id} className="flex items-center gap-3 bg-black/40 border border-white/10 p-2 rounded group hover:border-white/20 transition-all">
                        {/* Thumbnail (if exists) */}
                        {part.thumbnail_url ? (
                            <div className="w-10 h-10 rounded overflow-hidden border border-white/10 shrink-0">
                                <img src={part.thumbnail_url} className="w-full h-full object-cover" alt="Thumbnail" />
                            </div>
                        ) : (
                            <div className="w-10 h-10 rounded border border-white/10 bg-white/5 flex items-center justify-center shrink-0">
                                <Box size={16} className="text-gray-600" />
                            </div>
                        )}

                        {/* Status Stepper */}
                        <div className="flex flex-col gap-1 items-center">
                            {/* We can make stepper horizontal or compact */}
                            <div className="flex bg-black rounded p-0.5 border border-white/10">
                                {statuses.map((s) => {
                                    const isActive = part.status === s;
                                    const Icon = statusIcons[s];
                                    return (
                                        <button
                                            key={s}
                                            onClick={() => handleStatusChange(part.id, s)}
                                            title={s.toUpperCase()}
                                            className={clsx(
                                                "p-1 rounded transition-all",
                                                isActive ? statusColors[s] : "text-gray-700 hover:text-gray-500"
                                            )}
                                        >
                                            <Icon size={10} />
                                        </button>
                                    );
                                })}
                            </div>
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0 flex flex-col justify-center">
                            <div className="flex items-baseline gap-2">
                                <span className="text-sm font-mono text-white truncate font-bold">{part.name}</span>
                                <span className="text-[10px] text-gray-500 font-mono bg-white/10 px-1 rounded">x{part.count}</span>
                            </div>
                            <div className="flex gap-2 mt-0.5">
                                {part.source_url && (
                                    <a
                                        href={part.source_url}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        className="text-[9px] text-blue-400 hover:underline flex items-center gap-1 uppercase tracking-wider"
                                    >
                                        <ExternalLink size={8} />
                                        {part.source_url.includes('thingiverse') ? 'Thingiverse' : 'Source'}
                                    </a>
                                )}
                            </div>
                        </div>

                        {/* Actions */}
                        <button
                            onClick={() => handleDelete(part.id)}
                            className="text-gray-600 hover:text-red-500 transition-colors p-2"
                        >
                            <Trash2 size={12} />
                        </button>
                    </div>
                ))}

                {/* Empty State */}
                {parts.length === 0 && (
                    <div className="text-center py-4 border border-dashed border-white/10 rounded text-[10px] text-gray-600 uppercase">
                        No Printed Parts Tracked
                    </div>
                )}
            </div>

            {/* Add New */}
            <div className="grid grid-cols-[1fr_60px_auto] gap-2 items-center bg-black/20 p-2 rounded border border-white/5 relative">
                {isFetching && <div className="absolute inset-0 bg-black/50 z-10 flex items-center justify-center backdrop-blur-sm rounded"><Loader2 className="animate-spin text-accent" size={16} /></div>}

                <div className="space-y-1">
                    <input
                        className="w-full bg-transparent text-xs text-white placeholder-gray-600 focus:outline-none placeholder:italic"
                        placeholder="Part Name (Optional if URL provided)"
                        value={newPartName}
                        onChange={e => setNewPartName(e.target.value)}
                        onKeyDown={e => e.key === 'Enter' && handleAdd()}
                    />
                    <div className="flex items-center gap-1 border-t border-white/5 pt-1">
                        <ImageIcon size={10} className="text-gray-600" />
                        <input
                            className="w-full bg-transparent text-[10px] text-blue-300 placeholder-gray-700 focus:outline-none"
                            placeholder="Paste Link (Thingiverse / STL)..."
                            value={newPartUrl}
                            onChange={e => setNewPartUrl(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && handleAdd()}
                        />
                    </div>
                </div>
                <input
                    type="number"
                    min="1"
                    className="bg-black border border-white/10 text-xs text-center text-white p-1 rounded h-full"
                    value={newPartCount}
                    onChange={e => setNewPartCount(parseInt(e.target.value))}
                />
                <button
                    onClick={handleAdd}
                    disabled={isFetching}
                    className="p-2 bg-accent/10 hover:bg-accent/20 text-accent rounded transition-colors h-full flex items-center justify-center border border-accent/20"
                >
                    <Plus size={16} />
                </button>
            </div>
        </div>
    );
}
