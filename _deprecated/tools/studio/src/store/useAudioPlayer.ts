import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Recording } from '../lib/db';

// Unified Track Type - supports both DB recordings and file uploads
export interface UnifiedTrack {
    id: string;
    title: string;
    source: 'recording' | 'file';

    // For DB recordings
    recording?: Recording;

    // For file uploads
    file?: File;
    blobUrl?: string;
}

interface AudioPlayerState {
    // Current playback
    currentTrack: UnifiedTrack | null;
    isPlaying: boolean;
    volume: number;
    currentTime: number;
    duration: number;

    // Queue/Playlist
    queue: UnifiedTrack[];
    playlist: UnifiedTrack[];

    // UI State
    isExpanded: boolean;
    isHeaderPlayerVisible: boolean;

    // Actions
    play: (track: UnifiedTrack) => void;
    playRecording: (recording: Recording) => void;
    playFile: (file: File) => void;
    pause: () => void;
    resume: () => void;
    stop: () => void;
    setVolume: (v: number) => void;
    seek: (time: number) => void;
    setCurrentTime: (time: number) => void;
    setDuration: (duration: number) => void;

    // Queue management
    addToQueue: (track: UnifiedTrack) => void;
    addRecordingToQueue: (recording: Recording) => void;
    addFileToQueue: (file: File) => void;
    addFilesToPlaylist: (files: File[]) => void;
    playNext: (track: UnifiedTrack) => void;
    next: () => void;
    prev: () => void;
    clearQueue: () => void;
    clearPlaylist: () => void;
    setPlaylist: (tracks: UnifiedTrack[]) => void;

    // UI
    toggleExpand: () => void;
    setHeaderPlayerVisible: (visible: boolean) => void;
}

// Helper to create UnifiedTrack from Recording
const recordingToTrack = (recording: Recording): UnifiedTrack => ({
    id: `rec-${recording.id}`,
    title: recording.title || recording.filename || 'Unknown',
    source: 'recording',
    recording
});

// Helper to create UnifiedTrack from File
const fileToTrack = (file: File): UnifiedTrack => ({
    id: `file-${Date.now()}-${Math.random().toString(36).slice(2)}`,
    title: file.name.replace(/\.[^/.]+$/, ""),
    source: 'file',
    file,
    blobUrl: URL.createObjectURL(file)
});

export const useAudioPlayer = create<AudioPlayerState>()(
    persist(
        (set, get) => ({
            currentTrack: null,
            isPlaying: false,
            volume: 0.8,
            currentTime: 0,
            duration: 0,
            queue: [],
            playlist: [],
            isExpanded: false,
            isHeaderPlayerVisible: true,

            // Play a unified track
            play: (track) => {
                // Clean up old blob URL if any
                const oldTrack = get().currentTrack;
                if (oldTrack?.blobUrl && oldTrack.source === 'file') {
                    URL.revokeObjectURL(oldTrack.blobUrl);
                }

                set({
                    currentTrack: track,
                    isPlaying: true,
                    isHeaderPlayerVisible: true,
                    currentTime: 0
                });
            },

            // Convenience: Play a DB recording
            playRecording: (recording) => {
                get().play(recordingToTrack(recording));
            },

            // Convenience: Play a file
            playFile: (file) => {
                get().play(fileToTrack(file));
            },

            pause: () => set({ isPlaying: false }),
            resume: () => set({ isPlaying: true }),
            stop: () => {
                const track = get().currentTrack;
                if (track?.blobUrl) URL.revokeObjectURL(track.blobUrl);
                set({ isPlaying: false, currentTrack: null, currentTime: 0 });
            },

            setVolume: (volume) => set({ volume }),
            seek: (time) => set({ currentTime: time }),
            setCurrentTime: (currentTime) => set({ currentTime }),
            setDuration: (duration) => set({ duration }),

            // Queue management
            addToQueue: (track) => set((state) => ({ queue: [...state.queue, track] })),
            addRecordingToQueue: (recording) => get().addToQueue(recordingToTrack(recording)),
            addFileToQueue: (file) => get().addToQueue(fileToTrack(file)),

            addFilesToPlaylist: (files) => {
                const tracks = files.map(fileToTrack);
                set((state) => {
                    const newPlaylist = [...state.playlist, ...tracks];
                    // If nothing playing, start playing first track
                    if (!state.currentTrack && tracks.length > 0) {
                        return {
                            playlist: newPlaylist,
                            currentTrack: tracks[0],
                            isPlaying: true,
                            isHeaderPlayerVisible: true
                        };
                    }
                    return { playlist: newPlaylist };
                });
            },

            playNext: (track) => set((state) => ({ queue: [track, ...state.queue] })),

            setPlaylist: (playlist) => set({ playlist }),
            clearQueue: () => set({ queue: [] }),
            clearPlaylist: () => {
                const { playlist } = get();
                playlist.forEach(t => {
                    if (t.blobUrl) URL.revokeObjectURL(t.blobUrl);
                });
                set({ playlist: [], currentTrack: null, isPlaying: false });
            },

            next: () => {
                const { queue, playlist, currentTrack } = get();

                // First check queue
                if (queue.length > 0) {
                    const [nextTrack, ...remaining] = queue;
                    if (currentTrack?.blobUrl) URL.revokeObjectURL(currentTrack.blobUrl);
                    set({ currentTrack: nextTrack, queue: remaining, isPlaying: true, currentTime: 0 });
                    return;
                }

                // Then check playlist
                if (playlist.length > 0 && currentTrack) {
                    const currentIdx = playlist.findIndex(t => t.id === currentTrack.id);
                    if (currentIdx !== -1 && currentIdx < playlist.length - 1) {
                        if (currentTrack.blobUrl) URL.revokeObjectURL(currentTrack.blobUrl);
                        set({
                            currentTrack: playlist[currentIdx + 1],
                            isPlaying: true,
                            currentTime: 0
                        });
                        return;
                    }
                }

                // Nothing more to play
                set({ isPlaying: false });
            },

            prev: () => {
                const { playlist, currentTrack, currentTime } = get();

                // If more than 3 seconds in, restart current track
                if (currentTime > 3) {
                    set({ currentTime: 0 });
                    return;
                }

                // Go to previous in playlist
                if (playlist.length > 0 && currentTrack) {
                    const currentIdx = playlist.findIndex(t => t.id === currentTrack.id);
                    if (currentIdx > 0) {
                        if (currentTrack.blobUrl) URL.revokeObjectURL(currentTrack.blobUrl);
                        set({
                            currentTrack: playlist[currentIdx - 1],
                            isPlaying: true,
                            currentTime: 0
                        });
                    }
                }
            },

            toggleExpand: () => set((state) => ({ isExpanded: !state.isExpanded })),
            setHeaderPlayerVisible: (visible) => set({ isHeaderPlayerVisible: visible })
        }),
        {
            name: 'workshop-audio-player',
            partialize: (state) => ({
                volume: state.volume,
                isExpanded: state.isExpanded,
                isHeaderPlayerVisible: state.isHeaderPlayerVisible
            }),
        }
    )
);

// Export for backward compatibility
export type { Recording };
