import React, { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useParams, useNavigate } from 'react-router-dom';
import { db } from '../lib/db';
import { SongService } from '../services/SongService';
import { ArrowLeft, Edit2, Play, Save, Image as ImageIcon, Disc, Music } from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';
import { AlbumArtworkTab } from '../components/songs/AlbumArtworkTab';
import { AlbumMetadataTab } from '../components/songs/AlbumMetadataTab';
import { useExportFlow } from '../hooks/useExportFlow';
import { ExportDialog } from '../components/ui/ExportComponents/ExportDialog';
import { AlbumZipStrategy } from '../lib/strategies/albumStrategies';
import { Download } from 'lucide-react';
import { Button } from '../components/ui/Button';

export default function AlbumDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const albumId = parseInt(id || '0');

    // Export Flow
    const { isExportOpen, openExport, closeExport, exportContext } = useExportFlow();

    const album = useLiveQuery(() => db.albums.get(albumId), [albumId]);
    const [activeTab, setActiveTab] = useState<'tracks' | 'artwork' | 'metadata'>('artwork'); // Default to artwork as requested
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [titleDraft, setTitleDraft] = useState('');

    if (!album) return <div className="p-10 text-center text-gray-500">Loading album...</div>;

    const handleSaveTitle = async () => {
        if (titleDraft) {
            await SongService.updateAlbum(albumId, { title: titleDraft });
            setIsEditingTitle(false);
        }
    };

    return (
        <div className="flex flex-col h-full bg-background text-white">
            {/* Header */}
            <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-black/40 backdrop-blur-sm">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate('/songs')} className="text-gray-500 hover:text-white transition-colors">
                        <ArrowLeft size={20} />
                    </button>

                    {isEditingTitle ? (
                        <input
                            autoFocus
                            className="bg-black/50 border border-accent/50 text-xl font-bold text-white px-2 py-1 rounded outline-none"
                            value={titleDraft}
                            onChange={e => setTitleDraft(e.target.value)}
                            onBlur={handleSaveTitle}
                            onKeyDown={e => e.key === 'Enter' && handleSaveTitle()}
                        />
                    ) : (
                        <div className="flex items-center gap-2 group">
                            <h1 className="text-xl font-bold">{album.title}</h1>
                            <button
                                onClick={() => { setTitleDraft(album.title); setIsEditingTitle(true); }}
                                className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-accent transition-opacity"
                            >
                                <Edit2 size={14} />
                            </button>
                        </div>
                    )}

                    <span className="px-2 py-0.5 rounded bg-white/10 text-xs text-gray-400 border border-white/5 uppercase tracking-wider">
                        {album.status}
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        onClick={() => openExport({ albumId })}
                        className="bg-black/50 border border-white/10 text-white hover:bg-black/70 mr-2"
                        size="sm"
                    >
                        <Download size={14} className="mr-2" />
                        Export
                    </Button>
                    <nav className="flex bg-white/5 rounded-lg p-1 border border-white/5 mr-4">
                        {[
                            { id: 'tracks', icon: Music, label: 'Tracks' },
                            { id: 'artwork', icon: ImageIcon, label: 'Artwork' },
                            { id: 'metadata', icon: Disc, label: 'Metadata' },
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={clsx(
                                    "px-3 py-1.5 rounded-md flex items-center gap-2 text-sm font-medium transition-all",
                                    activeTab === tab.id
                                        ? "bg-accent/20 text-accent shadow-sm"
                                        : "text-gray-400 hover:text-white hover:bg-white/5"
                                )}
                            >
                                <tab.icon size={14} />
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </nav>
                </div>
            </header>

            {/* Content Area */}
            <div className="flex-1 overflow-hidden relative">
                {activeTab === 'artwork' && (
                    <AlbumArtworkTab albumId={albumId} />
                )}

                {activeTab === 'tracks' && (
                    <div className="p-8 text-center text-gray-500">
                        <Music size={48} className="mx-auto mb-4 opacity-20" />
                        <p>Tracklist management coming in next update.</p>
                        {/* Future: Re-use DraggableSongList here filtered by album */}
                    </div>
                )}

                {activeTab === 'metadata' && (
                    <AlbumMetadataTab albumId={albumId} />
                )}
            </div>

            <ExportDialog
                isOpen={isExportOpen}
                onClose={closeExport}
                strategies={[AlbumZipStrategy]}
                context={exportContext}
            />
        </div>
    );
}
