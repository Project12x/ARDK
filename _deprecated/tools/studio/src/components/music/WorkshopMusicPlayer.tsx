import { useRef, useEffect, useState } from 'react';
import { Play, Pause, SkipForward, SkipBack, Disc, Volume2, Maximize2, Minimize2, X, Music } from 'lucide-react';
import clsx from 'clsx';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { useAudioPlayer } from '../../store/useAudioPlayer';

export function WorkshopMusicPlayer() {
    const {
        currentTrack, isPlaying, volume, isExpanded, currentTime, duration,
        pause, resume, next, setVolume, toggleExpand,
        setCurrentTime, setDuration, setHeaderPlayerVisible
    } = useAudioPlayer();

    const audioRef = useRef<HTMLAudioElement>(null);
    const [audioSrc, setAudioSrc] = useState<string | null>(null);

    // Fetch full song details for metadata
    const song = useLiveQuery(() =>
        currentTrack?.source === 'recording' && currentTrack.recording?.song_id
            ? db.songs.get(currentTrack.recording.song_id)
            : Promise.resolve(null)
        , [currentTrack]);

    const album = useLiveQuery(() =>
        song?.album_id ? db.albums.get(song.album_id) : Promise.resolve(null)
        , [song?.album_id]);

    // Generate audio source
    useEffect(() => {
        if (!currentTrack) {
            setAudioSrc(null);
            return;
        }

        if (currentTrack.source === 'file' && currentTrack.blobUrl) {
            setAudioSrc(currentTrack.blobUrl);
            return;
        }

        if (currentTrack.source === 'recording' && currentTrack.recording?.content) {
            const url = URL.createObjectURL(currentTrack.recording.content as Blob);
            setAudioSrc(url);
            return () => URL.revokeObjectURL(url);
        }
    }, [currentTrack]);

    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = volume;
        }
    }, [volume]);

    useEffect(() => {
        if (!audioRef.current || !audioSrc) return;

        if (isPlaying) {
            audioRef.current.play().catch(e => console.error("Playback error:", e));
        } else {
            audioRef.current.pause();
        }
    }, [isPlaying, audioSrc]);

    const handleTimeUpdate = () => {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
            setDuration(audioRef.current.duration || 0);
        }
    };

    const handleEnded = () => {
        next();
    };

    const handleSeek = (e: React.ChangeEvent<HTMLInputElement>) => {
        const time = parseFloat(e.target.value);
        if (audioRef.current) {
            audioRef.current.currentTime = time;
            setCurrentTime(time);
        }
    };

    const formatTime = (time: number) => {
        if (!time || isNaN(time)) return '0:00';
        const mins = Math.floor(time / 60);
        const secs = Math.floor(time % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    };

    if (!currentTrack) return null;

    if (!isExpanded) {
        // Minimized View (Floating Pill)
        return (
            <div className="fixed top-1/2 right-6 -translate-y-1/2 z-[100] flex items-center gap-2 animate-in fade-in slide-in-from-right-4">
                <audio
                    ref={audioRef}
                    src={audioSrc || undefined}
                    onTimeUpdate={handleTimeUpdate}
                    onEnded={handleEnded}
                />

                <div className="bg-black/80 backdrop-blur-md border border-white/10 rounded-full p-1 pl-3 pr-2 shadow-2xl flex items-center gap-3 group hover:border-accent/50 transition-colors">
                    {/* Visualizer / Spinner */}
                    <div className={clsx(
                        "w-5 h-5 rounded-full flex items-center justify-center border border-white/10",
                        isPlaying && "animate-spin border-t-accent"
                    )}>
                        <Music size={10} className="text-accent" />
                    </div>

                    <div className="flex flex-col max-w-[120px]">
                        <span className="text-xs font-bold text-white truncate">{currentTrack.title}</span>
                        <span className="text-[10px] text-gray-500 truncate">{song?.title || 'Unknown Song'}</span>
                    </div>

                    <div className="flex items-center gap-1">
                        <button
                            onClick={isPlaying ? pause : resume}
                            className="w-8 h-8 rounded-full bg-white/10 hover:bg-white/20 flex items-center justify-center text-white transition-colors"
                        >
                            {isPlaying ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
                        </button>
                        <button onClick={toggleExpand} className="p-1.5 text-gray-500 hover:text-white transition-colors">
                            <Maximize2 size={14} />
                        </button>
                    </div>
                </div>
            </div>
        );
    }

    // Expanded View (Widget)
    return (
        <div className="fixed bottom-6 right-6 z-[100] w-80 bg-black/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl p-4 animate-in fade-in slide-in-from-bottom-4 flex flex-col gap-4">
            <audio
                ref={audioRef}
                src={audioSrc || undefined}
                onTimeUpdate={handleTimeUpdate}
                onEnded={handleEnded}
            />

            {/* Header */}
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <span className="w-2 h-2 rounded-full bg-accent animate-pulse" />
                    <span className="text-xs font-mono font-bold tracking-wider text-accent">WORKSHOP.MUSIC</span>
                </div>
                <button onClick={toggleExpand} className="text-gray-500 hover:text-white transition-colors">
                    <Minimize2 size={16} />
                </button>
            </div>

            {/* Cover Art / Visual */}
            <div className="aspect-square bg-white/5 rounded-xl overflow-hidden relative group border border-white/5">
                {song?.cover_art_url || album?.cover_art_url ? (
                    <img src={song?.cover_art_url || album?.cover_art_url} alt="Cover" className="w-full h-full object-cover" />
                ) : (
                    <div className="w-full h-full flex items-center justify-center">
                        <Disc size={48} className={clsx("text-gray-700", isPlaying && "animate-spin-slow")} />
                    </div>
                )}
            </div>

            {/* Track Info */}
            <div>
                <h3 className="font-bold text-white truncate text-lg leading-tight">{currentTrack.title}</h3>
                <p className="text-sm text-gray-400 truncate">{song?.title || 'Unknown Song'}</p>
            </div>

            {/* Progress Bar */}
            <div className="space-y-1">
                <input
                    type="range"
                    min={0}
                    max={duration || 100}
                    value={currentTime}
                    onChange={handleSeek}
                    className="w-full accent-accent h-1 bg-white/10 rounded-lg appearance-none cursor-pointer"
                />
                <div className="flex justify-between text-[10px] font-mono text-gray-500">
                    <span>{formatTime(currentTime)}</span>
                    <span>{formatTime(duration)}</span>
                </div>
            </div>

            {/* Controls */}
            <div className="flex items-center justify-between mt-2">
                <div className="flex items-center gap-4">
                    <button onClick={() => { }} className="text-gray-500 hover:text-white transition-colors">
                        <SkipBack size={20} />
                    </button>
                    <button
                        onClick={isPlaying ? pause : resume}
                        className="w-12 h-12 rounded-full bg-accent text-black flex items-center justify-center hover:scale-105 transition-transform shadow-[0_0_15px_rgba(var(--accent-rgb),0.3)]"
                    >
                        {isPlaying ? <Pause size={24} fill="currentColor" /> : <Play size={24} fill="currentColor" className="ml-1" />}
                    </button>
                    <button onClick={next} className="text-gray-500 hover:text-white transition-colors">
                        <SkipForward size={20} />
                    </button>
                </div>

                {/* Volume */}
                <div className="flex items-center gap-2 group/vol">
                    <Volume2 size={16} className="text-gray-500" />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.01"
                        value={volume}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                        className="w-20 accent-white h-1 bg-white/10 rounded-lg appearance-none"
                    />
                </div>
            </div>
        </div>
    );
}
