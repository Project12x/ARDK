import { useRef, useEffect } from 'react';
import { Play, Pause, SkipForward, SkipBack, Volume2, ChevronDown, ChevronUp, Music, X } from 'lucide-react';
import clsx from 'clsx';
import { useAudioPlayer } from '../../store/useAudioPlayer';
import { db } from '../../lib/db';
import { useLiveQuery } from 'dexie-react-hooks';

export function HeaderMiniPlayer() {
    const {
        currentTrack, isPlaying, volume, currentTime, duration,
        isExpanded, isHeaderPlayerVisible,
        pause, resume, next, prev, setVolume, toggleExpand,
        setCurrentTime, setDuration, setHeaderPlayerVisible
    } = useAudioPlayer();

    const audioRef = useRef<HTMLAudioElement>(null);

    // Get song info for recordings
    const song = useLiveQuery(async () => {
        if (currentTrack?.source === 'recording' && currentTrack.recording?.song_id) {
            return await db.songs.get(currentTrack.recording.song_id);
        }
        return null;
    }, [currentTrack]);

    // Generate audio source URL
    const audioSrc = (() => {
        if (!currentTrack) return undefined;

        if (currentTrack.source === 'file' && currentTrack.blobUrl) {
            return currentTrack.blobUrl;
        }

        if (currentTrack.source === 'recording' && currentTrack.recording?.content) {
            // Create blob URL from recording content
            return URL.createObjectURL(currentTrack.recording.content as Blob);
        }

        return undefined;
    })();

    // Audio element effects
    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = volume;
        }
    }, [volume]);

    useEffect(() => {
        if (!audioRef.current || !audioSrc) return;

        if (isPlaying) {
            audioRef.current.play().catch(e => {
                console.error("Playback error:", e);
                pause();
            });
        } else {
            audioRef.current.pause();
        }
    }, [isPlaying, audioSrc, pause]);

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

    // Don't render if no track or hidden
    if (!currentTrack || !isHeaderPlayerVisible) return null;

    return (
        <>
            {/* Hidden audio element */}
            <audio
                ref={audioRef}
                src={audioSrc}
                onTimeUpdate={handleTimeUpdate}
                onEnded={handleEnded}
                onLoadedMetadata={() => {
                    if (audioRef.current) {
                        setDuration(audioRef.current.duration);
                        if (isPlaying) audioRef.current.play();
                    }
                }}
            />

            {/* Mini Player Bar - Compact */}
            <div className={clsx(
                "flex items-center gap-2 px-2 py-1.5 bg-black/60 backdrop-blur-md border-b border-white/5 transition-all",
                isExpanded && "border-b-0"
            )}>
                {/* Play/Pause */}
                <button
                    onClick={isPlaying ? pause : resume}
                    className="w-6 h-6 rounded-full bg-accent text-black flex items-center justify-center hover:scale-105 transition-transform shrink-0"
                >
                    {isPlaying ? <Pause size={10} fill="currentColor" /> : <Play size={10} fill="currentColor" className="ml-0.5" />}
                </button>

                {/* Prev/Next */}
                <div className="flex items-center gap-1">
                    <button onClick={prev} className="p-1 text-gray-500 hover:text-white transition-colors">
                        <SkipBack size={14} />
                    </button>
                    <button onClick={next} className="p-1 text-gray-500 hover:text-white transition-colors">
                        <SkipForward size={14} />
                    </button>
                </div>

                {/* Track Info */}
                <div className="flex-1 min-w-0 flex items-center gap-2">
                    <Music size={12} className="text-accent shrink-0" />
                    <div className="min-w-0">
                        <div className="text-xs font-bold text-white truncate">{currentTrack.title}</div>
                        {song && <div className="text-[10px] text-gray-500 truncate">{song.title}</div>}
                    </div>
                </div>

                {/* Progress */}
                <div className="hidden sm:flex items-center gap-2 text-[10px] font-mono text-gray-500 w-48">
                    <span>{formatTime(currentTime)}</span>
                    <input
                        type="range"
                        min={0}
                        max={duration || 100}
                        value={currentTime}
                        onChange={handleSeek}
                        className="flex-1 h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-accent"
                    />
                    <span>{formatTime(duration)}</span>
                </div>

                {/* Volume */}
                <div className="hidden md:flex items-center gap-1 group/vol">
                    <Volume2 size={14} className="text-gray-500" />
                    <input
                        type="range"
                        min="0"
                        max="1"
                        step="0.01"
                        value={volume}
                        onChange={(e) => setVolume(parseFloat(e.target.value))}
                        className="w-16 h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-white"
                    />
                </div>

                {/* Expand/Collapse */}
                <button
                    onClick={toggleExpand}
                    className="p-1 text-gray-500 hover:text-white transition-colors"
                    title={isExpanded ? "Collapse" : "Expand"}
                >
                    {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                </button>

                {/* Close */}
                <button
                    onClick={() => setHeaderPlayerVisible(false)}
                    className="p-1 text-gray-500 hover:text-red-400 transition-colors"
                    title="Hide player"
                >
                    <X size={14} />
                </button>
            </div>

            {/* Expanded Panel */}
            {isExpanded && (
                <div className="bg-neutral-900/95 backdrop-blur-xl border-b border-white/10 p-4 animate-in slide-in-from-top-2">
                    <div className="max-w-2xl mx-auto">
                        {/* Large Progress Bar */}
                        <div className="mb-4">
                            <input
                                type="range"
                                min={0}
                                max={duration || 100}
                                value={currentTime}
                                onChange={handleSeek}
                                className="w-full h-2 bg-white/10 rounded-lg appearance-none cursor-pointer accent-accent"
                            />
                            <div className="flex justify-between text-xs font-mono text-gray-500 mt-1">
                                <span>{formatTime(currentTime)}</span>
                                <span>{formatTime(duration)}</span>
                            </div>
                        </div>

                        {/* Full Controls */}
                        <div className="flex items-center justify-between">
                            <div className="flex items-center gap-3">
                                <div className="w-12 h-12 rounded-lg bg-white/5 flex items-center justify-center">
                                    <Music size={20} className="text-accent" />
                                </div>
                                <div>
                                    <h4 className="font-bold text-white">{currentTrack.title}</h4>
                                    <p className="text-sm text-gray-400">{song?.title || 'Unknown Song'}</p>
                                </div>
                            </div>

                            <div className="flex items-center gap-4">
                                <button onClick={prev} className="text-gray-400 hover:text-white transition-colors">
                                    <SkipBack size={24} />
                                </button>
                                <button
                                    onClick={isPlaying ? pause : resume}
                                    className="w-14 h-14 rounded-full bg-accent text-black flex items-center justify-center hover:scale-105 transition-transform shadow-lg"
                                >
                                    {isPlaying ? <Pause size={28} fill="currentColor" /> : <Play size={28} fill="currentColor" className="ml-1" />}
                                </button>
                                <button onClick={next} className="text-gray-400 hover:text-white transition-colors">
                                    <SkipForward size={24} />
                                </button>
                            </div>

                            <div className="flex items-center gap-2">
                                <Volume2 size={18} className="text-gray-500" />
                                <input
                                    type="range"
                                    min="0"
                                    max="1"
                                    step="0.01"
                                    value={volume}
                                    onChange={(e) => setVolume(parseFloat(e.target.value))}
                                    className="w-24 h-1.5 bg-white/10 rounded-lg appearance-none cursor-pointer accent-white"
                                />
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </>
    );
}
