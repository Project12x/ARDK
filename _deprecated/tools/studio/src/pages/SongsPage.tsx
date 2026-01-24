import React, { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useNavigate } from 'react-router-dom';
import { db } from '../lib/db';
import { Plus, Music, Disc, Mic, Search, Filter, Play, Clock, MoreVertical, LayoutGrid, List as ListIcon, Palette } from 'lucide-react';
import clsx from 'clsx';
import { CreateSongModal } from '../components/songs/CreateSongModal';
import { CreateAlbumModal } from '../components/songs/CreateAlbumModal';
import { DraggableSongCard } from '../components/songs/DraggableSongCard';
import { DndContext, DragOverlay, useSensor, useSensors, PointerSensor, useDroppable, type DragEndEvent } from '@dnd-kit/core';
import { toast } from 'sonner';
import { useUIStore } from '../store/useStore';

// Helper component for droppable album sidebar item
function DroppableAlbumItem({
    album,
    isSelected,
    onSelect,
    onEdit
}: {
    album: any,
    isSelected: boolean,
    onSelect: () => void,
    onEdit: (e: React.MouseEvent) => void
}) {
    const { setNodeRef, isOver } = useDroppable({
        id: `album-${album.id}`,
        data: { type: 'album', albumId: album.id }
    });

    return (
        <div
            ref={setNodeRef}
            className={clsx(
                "flex items-center gap-1 group/item rounded transition-all pr-2 mb-1 border border-transparent",
                isSelected ? "bg-white/10" : "hover:bg-white/5",
                isOver && "bg-accent/20 border-accent scale-105 shadow-lg z-10"
            )}
        >
            <button
                onClick={onSelect}
                className={clsx(
                    "flex-1 text-left px-3 py-2 text-sm flex items-center gap-2",
                    isSelected ? "text-accent font-bold" : "text-gray-400 group-hover/item:text-white",
                    isOver && "text-white"
                )}
            >
                <Disc size={16} className={isOver ? "animate-spin" : ""} />
                <span className="truncate">{album.title}</span>
                {isOver && <span className="text-[9px] uppercase bg-accent text-black px-1 rounded ml-auto font-bold">Drop</span>}
            </button>
            <button
                onClick={onEdit}
                className="opacity-0 group-hover/item:opacity-100 p-1.5 text-gray-500 hover:text-white transition-opacity"
                title="Edit Album"
            >
                <MoreVertical size={14} />
            </button>
        </div>
    );
}

export default function SongsPage() {
    const navigate = useNavigate();
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [filter, setFilter] = useState<'all' | 'recordings'>('all');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedAlbumId, setSelectedAlbumId] = useState<number | null>(null);

    // Theme
    const { musicTheme, setMusicTheme } = useUIStore();
    const availableThemes = ['default', 'music', 'synthwave', 'light', 'midnight', 'forest'];

    // Modals
    const [isCreateSongOpen, setIsCreateSongOpen] = useState(false);
    const [isCreateAlbumOpen, setIsCreateAlbumOpen] = useState(false);

    // DND Sensors
    const sensors = useSensors(useSensor(PointerSensor, {
        activationConstraint: { distance: 8 } // Prevent accidental drags
    }));

    // Fetch Data
    const songs = useLiveQuery(async () => {
        const collection = db.songs.orderBy('title');
        if (selectedAlbumId) {
            return await collection.filter(s => s.album_id === selectedAlbumId).toArray();
        }
        return await collection.toArray();
    }, [selectedAlbumId]) || [];

    const albums = useLiveQuery(() => db.albums.toArray()) || [];

    // Filter Logic
    const filteredSongs = songs.filter(song => {
        if (searchQuery && !song.title.toLowerCase().includes(searchQuery.toLowerCase())) return false;
        return true;
    });

    const handleCreateSong = () => setIsCreateSongOpen(true);
    const handleCreateAlbum = () => setIsCreateAlbumOpen(true);

    const handleDragEnd = async (event: DragEndEvent) => {
        const { active, over } = event;

        if (!over || !active) return;

        const activeId = active.id as string;
        const overId = over.id as string;

        // Check if dragging song -> album
        if (activeId.startsWith('song-') && overId.startsWith('album-')) {
            const songId = parseInt(activeId.replace('song-', ''));
            const albumId = parseInt(overId.replace('album-', ''));

            if (!songId || !albumId) return;

            try {
                // Determine target album title for toast
                const targetAlbum = albums.find(a => a.id === albumId);

                await db.songs.update(songId, {
                    album_id: albumId,
                    updated_at: new Date()
                });
                toast.success(`Song added to ${targetAlbum?.title || 'Album'}`);
            } catch (e) {
                console.error("Failed to move song to album", e);
                toast.error("Failed to move song");
            }
        }
    };

    return (
        <DndContext sensors={sensors} onDragEnd={handleDragEnd}>
            <div className="flex h-full bg-background text-white">
                {/* Left Rail: Albums & Filters */}
                <aside className="w-64 border-r border-white/10 flex flex-col bg-black/20">
                    <div className="p-4 border-b border-white/10 flex items-center justify-between">
                        <h2 className="font-mono text-sm font-bold text-gray-400 tracking-wider">LIBRARY</h2>
                        <button onClick={handleCreateSong} className="text-gray-500 hover:text-accent transition-colors" title="Quick Add Song"><Plus size={16} /></button>
                    </div>
                    <div className="p-2 space-y-1 flex-1 overflow-y-auto">
                        <button
                            onClick={() => setSelectedAlbumId(null)}
                            className={clsx(
                                "w-full text-left px-3 py-2 rounded text-sm flex items-center gap-2 transition-colors",
                                selectedAlbumId === null ? "bg-white/10 text-accent font-bold" : "text-gray-400 hover:bg-white/5 hover:text-white"
                            )}
                        >
                            <Music size={16} />
                            <span>All Songs</span>
                        </button>

                        <div className="h-px bg-white/10 my-2" />
                        <div className="px-3 py-1 flex items-center justify-between group">
                            <span className="text-xs text-gray-600 font-mono font-bold">ALBUMS</span>
                            <button onClick={handleCreateAlbum} className="text-gray-600 hover:text-white opacity-0 group-hover:opacity-100 transition-opacity"><Plus size={12} /></button>
                        </div>

                        {albums.map(album => (
                            <DroppableAlbumItem
                                key={album.id}
                                album={album}
                                isSelected={selectedAlbumId === album.id}
                                onSelect={() => setSelectedAlbumId(album.id!)}
                                onEdit={(e) => { e.stopPropagation(); navigate(`/albums/${album.id}`); }}
                            />
                        ))}
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 flex flex-col relative overflow-hidden">
                    {/* Header */}
                    <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-black/40 backdrop-blur-sm sticky top-0 z-10">
                        <div className="flex items-center gap-4 flex-1">
                            <div className="relative group">
                                <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 group-focus-within:text-accent transition-colors" size={16} />
                                <input
                                    type="text"
                                    placeholder="Search library..."
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    className="bg-black/50 border border-white/10 rounded-full pl-10 pr-4 py-1.5 text-sm text-white focus:border-accent outline-none w-64 focus:w-80 transition-all placeholder:text-gray-600"
                                />
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            {/* Theme Selector */}
                            <div className="hidden md:flex bg-white/5 rounded-lg border border-white/5 items-center px-3 py-1.5 hover:border-white/20 transition-colors">
                                <Palette size={14} className="text-gray-500 mr-2" />
                                <select
                                    value={musicTheme}
                                    onChange={(e) => setMusicTheme(e.target.value)}
                                    className="bg-transparent text-xs text-gray-300 outline-none uppercase font-bold tracking-wider cursor-pointer active:text-accent"
                                >
                                    {availableThemes.map(t => <option key={t} value={t} className="bg-neutral-900 text-white hover:bg-accent">{t}</option>)}
                                </select>
                            </div>

                            <div className="flex bg-white/5 rounded-lg p-1 border border-white/5">
                                <button
                                    onClick={() => setViewMode('grid')}
                                    className={clsx("p-1.5 rounded transition-all", viewMode === 'grid' ? "bg-accent/20 text-accent shadow-sm" : "text-gray-500 hover:text-white")}
                                >
                                    <LayoutGrid size={16} />
                                </button>
                                <button
                                    onClick={() => setViewMode('list')}
                                    className={clsx("p-1.5 rounded transition-all", viewMode === 'list' ? "bg-accent/20 text-accent shadow-sm" : "text-gray-500 hover:text-white")}
                                >
                                    <ListIcon size={16} />
                                </button>
                            </div>
                            <button
                                onClick={handleCreateSong}
                                className="bg-accent text-black px-4 py-1.5 rounded-full text-sm font-bold hover:bg-accent/90 transition-all flex items-center gap-2 shadow-[0_0_15px_rgba(var(--accent-rgb),0.3)]"
                            >
                                <Plus size={16} />
                                <span>New Song</span>
                            </button>
                        </div>
                    </header>

                    <div className="flex-1 p-6 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                        {filteredSongs.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500">
                                <div className="w-16 h-16 rounded-full bg-white/5 flex items-center justify-center mb-4">
                                    <Music className="text-gray-600" size={32} />
                                </div>
                                <h3 className="text-lg font-bold text-gray-300">Library Empty</h3>
                                <p className="text-sm max-w-xs mt-2 mb-6">Start your musical journey by creating your first song or album.</p>
                                <button onClick={handleCreateSong} className="px-6 py-2 bg-white/10 hover:bg-white/20 text-white rounded font-medium transition-colors border border-white/5">
                                    Create Song
                                </button>
                            </div>
                        ) : (
                            viewMode === 'grid' ? (
                                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
                                    {filteredSongs.map(song => (
                                        <DraggableSongCard key={song.id} song={song} viewMode="grid" />
                                    ))}
                                </div>
                            ) : (
                                <div className="flex flex-col gap-1">
                                    {filteredSongs.map(song => (
                                        <DraggableSongCard key={song.id} song={song} viewMode="list" />
                                    ))}
                                </div>
                            )
                        )}
                    </div>
                </main>

                <CreateSongModal isOpen={isCreateSongOpen} onClose={() => setIsCreateSongOpen(false)} onCreated={(id) => navigate(`/songs/${id}`)} />
                <CreateAlbumModal isOpen={isCreateAlbumOpen} onClose={() => setIsCreateAlbumOpen(false)} onCreated={(id) => navigate(`/albums/${id}`)} />
            </div>
        </DndContext>
    );
}
