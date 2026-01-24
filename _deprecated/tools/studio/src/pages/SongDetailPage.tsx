import React, { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useParams, useNavigate } from 'react-router-dom';
import { db } from '../lib/db';
import { SongService } from '../services/SongService';
import { ArrowLeft, Edit2, Play, Save, Mic, Image as ImageIcon, FileText, Music, LayoutTemplate } from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

import { SongManuscript } from '../components/SongManuscript';
import { SongRecordingsTab } from '../components/songs/SongRecordingsTab';
import { SongArtworkTab } from '../components/songs/SongArtworkTab';
import { SongMetadataTab } from '../components/songs/SongMetadataTab';
import { SongFlowchart } from '../components/songs/flow/SongFlowchart';

export default function SongDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const songId = parseInt(id || '0');

    const song = useLiveQuery(() => db.songs.get(songId), [songId]);
    const [activeTab, setActiveTab] = useState<'lyrics' | 'structure' | 'recordings' | 'artwork' | 'metadata'>('lyrics');
    const [isEditingTitle, setIsEditingTitle] = useState(false);
    const [titleDraft, setTitleDraft] = useState('');

    if (!song) return <div className="p-10 text-center text-gray-500">Loading song...</div>;

    const handleSaveTitle = async () => {
        if (titleDraft) {
            await SongService.updateSong(songId, { title: titleDraft });
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
                            <h1 className="text-xl font-bold">{song.title}</h1>
                            <button
                                onClick={() => { setTitleDraft(song.title); setIsEditingTitle(true); }}
                                className="opacity-0 group-hover:opacity-100 text-gray-500 hover:text-accent transition-opacity"
                            >
                                <Edit2 size={14} />
                            </button>
                        </div>
                    )}

                    <span className="px-2 py-0.5 rounded bg-white/10 text-xs text-gray-400 border border-white/5 uppercase tracking-wider">
                        {song.status}
                    </span>
                </div>

                <div className="flex items-center gap-2">
                    {/* Tab Navigation */}
                    <nav className="flex bg-white/5 rounded-lg p-1 border border-white/5 mr-4">
                        {[
                            { id: 'lyrics', icon: FileText, label: 'Lyrics' },
                            { id: 'structure', icon: LayoutTemplate, label: 'Flow' },
                            { id: 'recordings', icon: Mic, label: 'Recordings' },
                            { id: 'artwork', icon: ImageIcon, label: 'Artwork' },
                            { id: 'metadata', icon: Music, label: 'Metadata' },
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
                {activeTab === 'lyrics' && (
                    <div className="h-full max-w-[1920px] mx-auto p-4">
                        <SongManuscript songId={songId} />
                    </div>
                )}

                {activeTab === 'structure' && (
                    <SongFlowchart songId={songId} />
                )}

                {activeTab === 'recordings' && (
                    <SongRecordingsTab songId={songId} />
                )}

                {activeTab === 'artwork' && (
                    <SongArtworkTab songId={songId} />
                )}

                {activeTab === 'metadata' && (
                    <SongMetadataTab songId={songId} />
                )}
            </div>
        </div>
    );
}
