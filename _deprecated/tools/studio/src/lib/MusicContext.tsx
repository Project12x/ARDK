import { createContext, useContext, useState, useRef, useEffect, type ReactNode } from 'react';

// Types
export interface AudioTrack {
    file: File;
    name: string;
    url: string;
}

interface MusicContextType {
    playlist: AudioTrack[];
    currentIndex: number;
    isPlaying: boolean;
    currentTime: number;
    duration: number;
    volume: number;
    isShuffled: boolean;

    // Actions
    togglePlay: () => void;
    nextTrack: () => void;
    prevTrack: () => void;
    setVolume: (v: number) => void;
    toggleShuffle: () => void;
    loadPlaylist: (tracks: AudioTrack[]) => void;
    addToPlaylist: (tracks: AudioTrack[]) => void;
    clearPlaylist: () => void;
    seek: (time: number) => void;
}

const MusicContext = createContext<MusicContextType | undefined>(undefined);

export function MusicProvider({ children }: { children: ReactNode }) {
    const audioRef = useRef<HTMLAudioElement | null>(null);

    const [playlist, setPlaylist] = useState<AudioTrack[]>([]);
    const [currentIndex, setCurrentIndex] = useState(0);
    const [isPlaying, setIsPlaying] = useState(false);
    const [volume, setVolume] = useState(0.5);
    const [isShuffled, setIsShuffled] = useState(false);

    const [currentTime, setCurrentTime] = useState(0);
    const [duration, setDuration] = useState(0);

    // Audio Element Logic
    useEffect(() => {
        if (!audioRef.current || playlist.length === 0) return;

        const track = playlist[currentIndex];

        const currentSrc = audioRef.current.src;
        if (currentSrc !== track.url) {
            audioRef.current.src = track.url;
            audioRef.current.load();
            if (isPlaying) {
                audioRef.current.play().catch(e => {
                    console.error("Autoplay prevention or error", e);
                    setIsPlaying(false);
                });
            }
        }
    }, [currentIndex, playlist]);

    // Volume effect
    useEffect(() => {
        if (audioRef.current) {
            audioRef.current.volume = volume;
        }
    }, [volume]);

    // Play/Pause effect
    useEffect(() => {
        if (!audioRef.current || playlist.length === 0) return;

        if (isPlaying && audioRef.current.paused) {
            audioRef.current.play().catch(() => setIsPlaying(false));
        } else if (!isPlaying && !audioRef.current.paused) {
            audioRef.current.pause();
        }
    }, [isPlaying]);

    // Persistence
    useEffect(() => {
        const state = {
            volume,
            isShuffled,
            // We can persist playlist but Blob URLs die. 
            // We can only persist metadata and try to recover? 
            // Or just persist volume/shuffle for now.
            // Actually, if we want playlist persistence, we need real file handles or IDs.
            // For now, let's persist UI settings.
        };
        localStorage.setItem('MUSIC_PLAYER_STATE', JSON.stringify(state));
    }, [volume, isShuffled]);

    useEffect(() => {
        const saved = localStorage.getItem('MUSIC_PLAYER_STATE');
        if (saved) {
            try {
                const parsed = JSON.parse(saved);
                if (parsed.volume !== undefined) setVolume(parsed.volume);
                if (parsed.isShuffled !== undefined) setIsShuffled(parsed.isShuffled);
            } catch (e) {
                console.error("Failed to load music persistence", e);
            }
        }
    }, []);

    const togglePlay = () => {
        if (playlist.length === 0) return;
        setIsPlaying(!isPlaying);
    };

    const nextTrack = () => {
        if (playlist.length === 0) return;
        if (isShuffled) {
            // Simple random for now
            const next = Math.floor(Math.random() * playlist.length);
            setCurrentIndex(next);
        } else {
            setCurrentIndex(prev => (prev + 1) % playlist.length);
        }
    };

    const prevTrack = () => {
        if (playlist.length === 0) return;
        setCurrentIndex(prev => (prev - 1 + playlist.length) % playlist.length);
    };

    const loadPlaylist = (tracks: AudioTrack[]) => {
        // Clear old
        playlist.forEach(t => URL.revokeObjectURL(t.url));
        setPlaylist(tracks);
        setCurrentIndex(0);
        setIsPlaying(true);
    };

    const addToPlaylist = (tracks: AudioTrack[]) => {
        setPlaylist(prev => [...prev, ...tracks]);
        if (playlist.length === 0) {
            setCurrentIndex(0);
            setIsPlaying(true);
        }
    };

    const clearPlaylist = () => {
        playlist.forEach(t => URL.revokeObjectURL(t.url));
        setPlaylist([]);
        setIsPlaying(false);
        setCurrentIndex(0);
    };

    const toggleShuffle = () => setIsShuffled(!isShuffled);
    const seek = (time: number) => {
        if (audioRef.current) {
            audioRef.current.currentTime = time;
            setCurrentTime(time);
        }
    }

    // Events
    const onTimeUpdate = () => {
        if (audioRef.current) {
            setCurrentTime(audioRef.current.currentTime);
            setDuration(audioRef.current.duration || 0);
        }
    };

    const onEnded = () => {
        nextTrack();
    };

    return (
        <MusicContext.Provider value={{
            playlist,
            currentIndex,
            isPlaying,
            currentTime,
            duration,
            volume,
            isShuffled,
            togglePlay,
            nextTrack,
            prevTrack,
            setVolume,
            toggleShuffle,
            loadPlaylist,
            addToPlaylist,
            clearPlaylist,
            seek
        }}>
            <audio
                ref={audioRef}
                onTimeUpdate={onTimeUpdate}
                onEnded={onEnded}
                className="hidden"
            />
            {children}
        </MusicContext.Provider>
    );
}

export const useMusic = () => {
    const context = useContext(MusicContext);
    if (!context) throw new Error("useMusic must be used within MusicProvider");
    return context;
};
