import { useNavigate } from 'react-router-dom';
import { Music, Play, Clock, BarChart3 } from 'lucide-react';
import type { Song } from '../../lib/db';
import { UniversalCard } from '../ui/UniversalCard';

interface DraggableSongCardProps {
    song: Song;
    viewMode: 'grid' | 'list';
}

const STATUS_COLORS: Record<string, string> = {
    draft: '#6b7280', // gray-500
    demo: '#3b82f6', // blue-500
    polishing: '#8b5cf6', // violet-500
    mixed: '#ec4899', // pink-500
    mastered: '#10b981', // emerald-500
    released: '#eab308' // yellow-500
};

export function DraggableSongCard({ song, viewMode }: DraggableSongCardProps) {
    const navigate = useNavigate();
    const statusColor = STATUS_COLORS[song.status] || STATUS_COLORS.draft;

    if (viewMode === 'list') {
        // ... list view code (keeping simple for now)
        return null;
    }

    // Grid View (Standard Card) - Wrapped in UniversalCard
    return (
        <UniversalCard
            entityType="song"
            entityId={song.id!}
            title={song.title}
            metadata={{ status: song.status, bpm: song.bpm, key: song.key }}
            onClick={() => navigate(`/songs/${song.id}`)}
            className="border-white/10 bg-black hover:border-accent/50 p-4 overflow-hidden h-full flex flex-col justify-between"
        >
            {/* Background Gradient & Image (Subtle) */}
            <div className="absolute inset-0 z-0 bg-gradient-to-t from-black via-black/90 to-black/40 pointer-events-none" />
            {song.cover_art_url && (
                <div className="absolute inset-0 z-0 bg-cover bg-center opacity-10 blur-sm brightness-50" style={{ backgroundImage: `url(${song.cover_art_url})` }} />
            )}

            {/* Status Stripe */}
            <div
                title={`Status: ${song.status}`}
                style={{ backgroundColor: statusColor }}
                className="absolute top-0 left-0 w-full h-1 z-10"
            />

            {/* Header: Status & Play */}
            <div className="relative z-10 flex justify-between items-start mb-2 mt-1">
                <div className="flex gap-1 flex-wrap">
                    <span
                        className="text-[9px] font-mono uppercase px-1.5 py-0.5 rounded-sm font-bold border"
                        style={{ borderColor: `${statusColor}40`, backgroundColor: `${statusColor}10`, color: statusColor }}
                    >
                        {song.status}
                    </span>
                    {song.key && (
                        <span className="text-[9px] font-mono uppercase text-gray-400 border border-white/10 px-1.5 py-0.5 rounded-sm bg-white/5">
                            {song.key}
                        </span>
                    )}
                </div>

                {/* Play Button Overhead */}
                <button
                    className="w-8 h-8 rounded-full bg-accent text-black flex items-center justify-center hover:scale-110 transition-transform shadow-lg opacity-0 group-hover:opacity-100"
                    onClick={(e) => {
                        e.stopPropagation();
                    }}
                >
                    <Play size={14} fill="currentColor" className="ml-0.5" />
                </button>
            </div>

            {/* Content Body */}
            <div className="relative z-10 flex items-end gap-3 mt-auto">
                {/* Visible Thumbnail */}
                {song.cover_art_url ? (
                    <img
                        src={song.cover_art_url}
                        alt={song.title}
                        className="w-12 h-12 rounded bg-white/5 object-cover border border-white/10 shadow-lg shrink-0"
                    />
                ) : (
                    <div className="w-12 h-12 rounded bg-white/5 flex items-center justify-center border border-white/5 text-gray-600 shrink-0">
                        <Music size={20} />
                    </div>
                )}

                <div className="min-w-0 flex-1 pb-1">
                    <h3 className="text-lg font-black text-white leading-tight truncate" title={song.title}>
                        {song.title}
                    </h3>
                    <div className="flex items-center gap-3 text-[10px] font-mono text-gray-400 mt-1">
                        <span className="flex items-center gap-1">
                            <Clock size={10} /> {song.duration || '--:--'}
                        </span>
                        <span className="flex items-center gap-1">
                            <BarChart3 size={10} /> {song.bpm || '--'} BPM
                        </span>
                    </div>
                </div>
            </div>
        </UniversalCard>
    );
}
