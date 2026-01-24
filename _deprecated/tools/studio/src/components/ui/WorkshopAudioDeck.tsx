import React, { useRef, useState, useEffect } from 'react';
import { Play, Pause, SkipForward, SkipBack, Volume2, UploadCloud, FileAudio, Shuffle, Trash2 } from 'lucide-react';
import { clsx } from 'clsx';
import { motion } from 'framer-motion';
import { useAudioPlayer } from '../../store/useAudioPlayer';

export function WorkshopAudioDeck() {
    const {
        playlist, currentTrack, isPlaying, volume, currentTime, duration,
        pause, resume, next, prev, setVolume, addFilesToPlaylist, clearPlaylist
    } = useAudioPlayer();

    const containerRef = useRef<HTMLDivElement>(null);
    const [isCompact, setIsCompact] = useState(false);
    const [isMini, setIsMini] = useState(false);

    // Detect container size for responsive layout
    useEffect(() => {
        if (!containerRef.current) return;

        const observer = new ResizeObserver((entries) => {
            const { height, width } = entries[0].contentRect;
            setIsCompact(height < 180 || width < 250);
            setIsMini(height < 120 || width < 180);
        });

        observer.observe(containerRef.current);
        return () => observer.disconnect();
    }, []);

    // Handle Drag and Drop
    const handleDrop = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();

        const files = Array.from(e.dataTransfer.files).filter(f =>
            f.type.startsWith('audio/') ||
            f.name.endsWith('.mp3') ||
            f.name.endsWith('.wav') ||
            f.name.endsWith('.ogg') ||
            f.name.endsWith('.flac') ||
            f.name.endsWith('.aac') ||
            f.name.endsWith('.m4a')
        );

        if (files.length > 0) {
            addFilesToPlaylist(files);
        }
    };

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        e.stopPropagation();
    };

    const togglePlay = () => {
        if (isPlaying) {
            pause();
        } else {
            resume();
        }
    };

    // Get current track index in playlist
    const currentIndex = currentTrack
        ? playlist.findIndex(t => t.id === currentTrack.id)
        : -1;

    // Mini layout - just controls
    if (isMini) {
        return (
            <div
                ref={containerRef}
                className="relative flex items-center justify-center gap-2 p-2 bg-black/40 h-full"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
            >
                <button onClick={prev} className="text-gray-400 hover:text-white transition-colors">
                    <SkipBack size={14} />
                </button>
                <button
                    onClick={togglePlay}
                    className="flex justify-center items-center w-8 h-8 bg-white/10 hover:bg-accent hover:text-black rounded-full text-white transition-all"
                >
                    {isPlaying ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" className="ml-0.5" />}
                </button>
                <button onClick={next} className="text-gray-400 hover:text-white transition-colors">
                    <SkipForward size={14} />
                </button>
            </div>
        );
    }

    // Compact layout - track name + controls
    if (isCompact) {
        return (
            <div
                ref={containerRef}
                className="relative flex flex-col justify-between p-3 bg-black/40 h-full"
                onDrop={handleDrop}
                onDragOver={handleDragOver}
            >
                {/* Track Info */}
                <div className="flex items-center gap-2 mb-2">
                    <FileAudio size={12} className={isPlaying ? "text-accent animate-pulse shrink-0" : "text-gray-500 shrink-0"} />
                    <span className="text-[10px] font-bold text-white truncate flex-1">
                        {currentTrack?.title || 'No Track'}
                    </span>
                    {playlist.length > 0 && (
                        <button onClick={clearPlaylist} className="text-red-500/50 hover:text-red-500 transition-colors shrink-0">
                            <Trash2 size={10} />
                        </button>
                    )}
                </div>

                {/* Progress Bar */}
                {playlist.length > 0 && (
                    <div className="w-full h-1 bg-white/10 rounded-full overflow-hidden mb-2">
                        <div
                            className="h-full bg-accent transition-all duration-100 ease-linear"
                            style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}
                        />
                    </div>
                )}

                {/* Controls Row */}
                <div className="flex items-center justify-center gap-3">
                    <button onClick={prev} className="text-gray-400 hover:text-white transition-colors">
                        <SkipBack size={16} />
                    </button>
                    <button
                        onClick={togglePlay}
                        className="flex justify-center items-center w-8 h-8 bg-white/10 hover:bg-accent hover:text-black rounded-full text-white transition-all"
                    >
                        {isPlaying ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" className="ml-0.5" />}
                    </button>
                    <button onClick={next} className="text-gray-400 hover:text-white transition-colors">
                        <SkipForward size={16} />
                    </button>
                    <Volume2 size={12} className="text-gray-500" />
                </div>
            </div>
        );
    }

    // Full layout
    return (
        <div
            ref={containerRef}
            className={clsx(
                "relative flex flex-col justify-between p-4 bg-black/40 overflow-hidden group transition-all h-full",
            )}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
        >
            {/* Background Texture/FX */}
            <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,_var(--tw-gradient-stops))] from-neutral-900/50 via-black to-black opacity-80 z-0 pointer-events-none" />

            {/* Header: Status */}
            <div className="flex justify-between items-center relative z-10 mb-2">
                <div className="flex items-center gap-2">
                    <FileAudio size={16} className={isPlaying ? "text-accent animate-pulse" : "text-gray-500"} />
                    <span className="text-xs font-bold font-mono tracking-widest text-gray-400 uppercase">WORKSHOP DECK</span>
                </div>
                {playlist.length > 0 && (
                    <button onClick={clearPlaylist} className="text-red-500/50 hover:text-red-500 transition-colors">
                        <Trash2 size={14} />
                    </button>
                )}
            </div>

            {/* Main Display Area (Drop Zone or Visualizer) */}
            <div className="flex-1 flex flex-col items-center justify-center relative z-10 py-2 min-h-0">
                {playlist.length === 0 ? (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        className="text-center border-2 border-dashed border-white/10 rounded-lg p-4 w-full h-full flex flex-col items-center justify-center text-gray-600 hover:text-accent hover:border-accent/50 transition-colors"
                    >
                        <UploadCloud size={24} className="mb-2" />
                        <span className="text-[10px] font-mono uppercase font-bold">DROP AUDIO</span>
                    </motion.div>
                ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center min-h-0">
                        {/* Track Name */}
                        <div className="w-full overflow-hidden whitespace-nowrap mb-2 relative">
                            <motion.div
                                className="inline-block"
                                animate={{ x: ["100%", "-100%"] }}
                                transition={{ repeat: Infinity, duration: 10, ease: "linear" }}
                            >
                                <h3 className="text-sm font-black text-white uppercase tracking-tighter mx-4">
                                    {currentTrack?.title}
                                </h3>
                            </motion.div>
                        </div>

                        {/* Visualizer (Fake Bars) */}
                        <div className="flex items-end justify-center gap-1 h-8 w-full px-4 mb-2">
                            {[...Array(10)].map((_, i) => (
                                <motion.div
                                    key={i}
                                    className={clsx("w-1 bg-accent/80 rounded-t-sm", isPlaying ? "opacity-100" : "opacity-20")}
                                    animate={isPlaying ? {
                                        height: [8, Math.random() * 24 + 4, 8],
                                    } : { height: 3 }}
                                    transition={{
                                        repeat: Infinity,
                                        duration: 0.2 + Math.random() * 0.3,
                                        ease: "easeInOut"
                                    }}
                                />
                            ))}
                        </div>

                        {/* Time Progress */}
                        <div className="w-full flex items-center gap-2 text-[9px] font-mono text-gray-500">
                            <span>{Math.floor(currentTime / 60)}:{Math.floor(currentTime % 60).toString().padStart(2, '0')}</span>
                            <div className="flex-1 h-1 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-accent transition-all duration-100 ease-linear"
                                    style={{ width: `${(currentTime / (duration || 1)) * 100}%` }}
                                />
                            </div>
                            <span>{Math.floor((duration || 0) / 60)}:{Math.floor((duration || 0) % 60).toString().padStart(2, '0')}</span>
                        </div>
                    </div>
                )}
            </div>

            {/* Controls */}
            <div className="relative z-10 grid grid-cols-5 gap-2 items-center mt-2 border-t border-white/5 pt-3">
                <div className="flex justify-center text-gray-600">
                    {/* Placeholder for shuffle - can implement later */}
                </div>
                <button onClick={prev} className="flex justify-center text-gray-400 hover:text-white transition-colors">
                    <SkipBack size={18} />
                </button>
                <button
                    onClick={togglePlay}
                    className="flex justify-center items-center w-10 h-10 bg-white/10 hover:bg-accent hover:text-black rounded-full text-white transition-all mx-auto"
                >
                    {isPlaying ? <Pause size={18} fill="currentColor" /> : <Play size={18} fill="currentColor" className="ml-0.5" />}
                </button>
                <button onClick={next} className="flex justify-center text-gray-400 hover:text-white transition-colors">
                    <SkipForward size={18} />
                </button>
                <div className="group/vol relative flex justify-center">
                    <Volume2 size={16} className="text-gray-500 group-hover/vol:text-white cursor-pointer" />
                    <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden group-hover/vol:block bg-black border border-white/20 p-2 rounded shadow-xl">
                        <input
                            type="range"
                            min="0" max="1" step="0.1"
                            value={volume}
                            onChange={(e) => setVolume(parseFloat(e.target.value))}
                            className="h-20 w-1 appearance-none bg-white/20 rounded outline-none"
                            style={{ writingMode: 'vertical-lr', direction: 'rtl' }}
                        />
                    </div>
                </div>
            </div>
        </div>
    );
}
