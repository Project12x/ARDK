import React from 'react';
import { useMusic } from '../../lib/MusicContext';
import { Play, Pause, SkipForward, SkipBack, Music } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export function GlobalMediaControls() {
    const { playlist, isPlaying, togglePlay, nextTrack, prevTrack, currentIndex } = useMusic();

    if (playlist.length === 0) return null;
    const currentTrack = playlist[currentIndex];

    return (
        <AnimatePresence>
            <motion.div
                initial={{ opacity: 0, y: -20 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -20 }}
                className="flex items-center gap-4 bg-black/50 border border-white/10 px-4 py-1.5 rounded-full"
            >
                {/* Marquee Title (Small) */}
                <div className="w-[120px] overflow-hidden whitespace-nowrap mask-linear-fade relative hidden sm:block">
                    <motion.div
                        className="inline-block text-[10px] font-mono text-accent uppercase tracking-wider"
                        animate={{ x: ["100%", "-100%"] }}
                        transition={{ repeat: Infinity, duration: 8, ease: "linear" }}
                    >
                        {currentTrack?.name}
                    </motion.div>
                </div>

                {/* Controls */}
                <div className="flex items-center gap-2">
                    <button onClick={prevTrack} className="text-gray-500 hover:text-white transition-colors">
                        <SkipBack size={12} />
                    </button>
                    <button onClick={togglePlay} className="text-white hover:text-accent transition-colors">
                        {isPlaying ? <Pause size={14} /> : <Play size={14} />}
                    </button>
                    <button onClick={nextTrack} className="text-gray-500 hover:text-white transition-colors">
                        <SkipForward size={12} />
                    </button>
                </div>

                {/* Status Icon */}
                <div className="flex items-center gap-1 border-l border-white/10 pl-3">
                    <Music size={10} className={isPlaying ? "text-accent animate-spin-slow" : "text-gray-600"} />
                </div>
            </motion.div>
        </AnimatePresence>
    );
}
