import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { SongService } from '../../services/SongService';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Mic, Upload, Trash2, Play, Pause, FileAudio, Clock } from 'lucide-react';
import { Button } from '../ui/Button';
import { toast } from 'sonner';
import clsx from 'clsx';
import { Card } from '../ui/Card';
import { useAudioPlayer } from '../../store/useAudioPlayer';

interface SongRecordingsTabProps {
    songId: number;
}

export function SongRecordingsTab({ songId }: SongRecordingsTabProps) {
    const recordings = useLiveQuery(() =>
        db.recordings.where('song_id').equals(songId).reverse().sortBy('created_at')
        , [songId]);

    const { playRecording, currentTrack, isPlaying, pause, resume } = useAudioPlayer();

    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        for (const file of acceptedFiles) {
            try {
                // Determine type based on name or user input? Default to 'demo'
                let type: 'demo' | 'voice_memo' | 'stem' | 'master' = 'demo';
                if (file.name.toLowerCase().includes('shred')) type = 'voice_memo';
                if (file.name.toLowerCase().includes('master')) type = 'master';

                await SongService.addRecording({
                    song_id: songId,
                    content: file,
                    filename: file.name,
                    title: file.name.replace(/\.[^/.]+$/, ""), // remove extension
                    type,
                    file_type: file.type
                });
                toast.success(`Uploaded ${file.name}`);
            } catch (e) {
                console.error(e);
                toast.error("Upload failed");
            }
        }
    }, [songId]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'audio/*': [], 'video/*': [] } // Allow video for memos?
    });

    const handleDelete = async (id: number) => {
        if (confirm("Delete recording?")) {
            await SongService.deleteRecording(id);
            toast.success("Deleted");
        }
    };

    const getTypeColor = (type: string) => {
        switch (type) {
            case 'master': return 'text-purple-400 bg-purple-500/10 border-purple-500/20';
            case 'stem': return 'text-blue-400 bg-blue-500/10 border-blue-500/20';
            case 'voice_memo': return 'text-orange-400 bg-orange-500/10 border-orange-500/20';
            default: return 'text-green-400 bg-green-500/10 border-green-500/20'; // demo
        }
    };

    const handlePlayClick = (rec: any) => {
        const isCurrentTrack = currentTrack?.source === 'recording' && currentTrack.recording?.id === rec.id;

        if (isCurrentTrack) {
            if (isPlaying) {
                pause();
            } else {
                resume();
            }
        } else {
            playRecording(rec);
        }
    };

    const isTrackPlaying = (rec: any) => {
        return currentTrack?.source === 'recording' && currentTrack.recording?.id === rec.id && isPlaying;
    };

    const isCurrentTrackId = (rec: any) => {
        return currentTrack?.source === 'recording' && currentTrack.recording?.id === rec.id;
    };

    return (
        <div className="p-8 max-w-5xl mx-auto h-full overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <Mic className="text-accent" /> Recordings & Assets
            </h2>

            {/* Drop Zone */}
            <div
                {...getRootProps()}
                className={clsx(
                    "border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all mb-8",
                    isDragActive ? "border-accent bg-accent/10" : "border-white/10 hover:border-white/30 hover:bg-white/5"
                )}
            >
                <input {...getInputProps()} />
                <Upload size={32} className="mb-4 text-gray-400" />
                <p className="font-medium">Upload Audio Files</p>
                <p className="text-sm text-gray-500 mt-1">Demos, Voice Memos, Stems</p>
            </div>

            {/* List */}
            <div className="space-y-4">
                {recordings?.map(rec => (
                    <Card key={rec.id} className={clsx("p-4 flex items-center gap-4 hover:bg-white/5 transition-colors border-white/5", isCurrentTrackId(rec) && "bg-white/10 border-accent/20")}>
                        <button
                            onClick={() => handlePlayClick(rec)}
                            className={clsx(
                                "w-10 h-10 rounded-full flex items-center justify-center transition-colors shrink-0",
                                isTrackPlaying(rec) ? "bg-accent text-black" : "bg-white/10 text-accent hover:bg-white/20"
                            )}
                        >
                            {isTrackPlaying(rec) ? <Pause size={16} fill="currentColor" /> : <Play size={16} className="ml-0.5" fill="currentColor" />}
                        </button>

                        <div className="flex-1 min-w-0">
                            <h3 className="font-bold text-white truncate">{rec.title}</h3>
                            <div className="flex items-center gap-2 text-xs text-gray-400 mt-1">
                                <span>{new Date(rec.created_at).toLocaleDateString()}</span>
                                <span>•</span>
                                <span className={clsx("px-1.5 py-0.5 rounded uppercase font-bold text-[10px] border", getTypeColor(rec.type))}>
                                    {rec.type.replace('_', ' ')}
                                </span>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            <div className="text-xs font-mono text-gray-500 flex items-center gap-1">
                                <Clock size={12} /> --:--
                            </div>
                            <Button size="sm" variant="ghost" className="text-gray-500 hover:text-red-400" onClick={() => handleDelete(rec.id!)}>
                                <Trash2 size={16} />
                            </Button>
                        </div>
                    </Card>
                ))}

                {recordings?.length === 0 && (
                    <div className="text-center text-gray-500 py-12">
                        No recordings yet.
                    </div>
                )}
            </div>
        </div>
    );
}
