import { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { SongService } from '../../services/SongService';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Image as ImageIcon, Upload, Sparkles, Trash2, Link as LinkIcon, ExternalLink } from 'lucide-react';
import { Button } from '../ui/Button';
import { toast } from 'sonner';
import clsx from 'clsx';
import { Card } from '../ui/Card';

interface SongArtworkTabProps {
    songId: number;
}

export function SongArtworkTab({ songId }: SongArtworkTabProps) {
    const artworkFiles = useLiveQuery(() =>
        db.song_files.where({ song_id: songId, category: 'artwork' }).toArray()
        , [songId]);

    const song = useLiveQuery(() => db.songs.get(songId), [songId]);

    // Set as Cover
    const handleSetCover = async (url: string) => {
        await SongService.updateSong(songId, { cover_art_url: url });
        toast.success("Cover art updated");
    };

    // Upload
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        for (const file of acceptedFiles) {
            try {
                // In real app, we'd upload to blob storage/IPFS and get a URL.
                // Here we store blob in DB (not recommended for large files but ok for demo)
                // OR we just create a blob URL? Blob URLs are ephemeral.
                // We'll store the objectURL for the session or store base64? 
                // Dexie can store Blobs.

                await SongService.addFile(songId, file, 'artwork');
                toast.success(`Uploaded ${file.name}`);
            } catch (e) {
                console.error(e);
                toast.error("Upload failed");
            }
        }
    }, [songId]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': [] }
    });

    const handleDelete = async (id: number) => {
        if (confirm("Delete artwork?")) {
            await SongService.deleteFile(id);
            toast.success("Deleted");
        }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto h-full overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <ImageIcon className="text-accent" /> Artwork
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Active Cover */}
                <Card className="p-6 bg-white/5 border-white/10 flex flex-col items-center justify-center text-center gap-4">
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Current Cover</h3>
                    <div className="aspect-square w-64 bg-black/50 rounded-xl overflow-hidden shadow-2xl relative group">
                        {song?.cover_art_url ? (
                            <img src={song.cover_art_url} alt="Cover" className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex items-center justify-center text-gray-600">
                                <ImageIcon size={48} />
                            </div>
                        )}
                    </div>
                </Card>

                {/* Actions */}
                <div className="space-y-4">
                    <div
                        {...getRootProps()}
                        className={clsx(
                            "border-2 border-dashed rounded-xl p-8 flex flex-col items-center justify-center text-center cursor-pointer transition-all h-48",
                            isDragActive ? "border-accent bg-accent/10" : "border-white/10 hover:border-white/30 hover:bg-white/5"
                        )}
                    >
                        <input {...getInputProps()} />
                        <Upload size={32} className="mb-4 text-gray-400" />
                        <p className="font-medium">Drag & Drop Image</p>
                        <p className="text-sm text-gray-500 mt-1">or click to browse</p>
                    </div>

                    <div className="flex flex-col gap-4">
                        {/* URL Input */}
                        <div className="flex gap-2">
                            <input
                                type="text"
                                placeholder="Paste Image URL..."
                                className="flex-1 bg-black border border-white/20 p-2 text-sm text-white rounded"
                                onKeyDown={(e) => {
                                    if (e.key === 'Enter') handleSetCover(e.currentTarget.value);
                                }}
                            />
                            <Button variant="outline" onClick={(e) => {
                                const input = e.currentTarget.previousSibling as HTMLInputElement;
                                if (input.value) handleSetCover(input.value);
                            }}>
                                <LinkIcon size={16} />
                            </Button>
                        </div>

                        <Button
                            variant="outline"
                            className="h-12 border-dashed hover:border-accent hover:text-accent w-full"
                            onClick={() => {
                                const prompt = encodeURIComponent(`${song?.title} ${song?.status || ''} album cover art artistic high quality`);
                                const url = `https://image.pollinations.ai/prompt/${prompt}?width=1024&height=1024&nologo=true`;
                                handleSetCover(url);
                            }}
                        >
                            <Sparkles size={16} className="mr-2" /> AI Generate Cover Art
                        </Button>
                    </div>
                </div>
            </div>

            {/* Gallery */}
            <div className="mt-12">
                <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider mb-4 border-b border-white/10 pb-2">Library</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-4">
                    {artworkFiles?.map(file => (
                        <div key={file.id} className="group relative aspect-square bg-white/5 rounded-lg overflow-hidden border border-white/10 hover:border-accent transition-all">
                            {/* We need to create a URL for the blob */}
                            <img
                                src={URL.createObjectURL(file.content as Blob)}
                                alt={file.name}
                                className="w-full h-full object-cover"
                                onLoad={(e) => URL.revokeObjectURL(e.currentTarget.src)}
                            />

                            <div className="absolute inset-0 bg-black/80 opacity-0 group-hover:opacity-100 transition-opacity flex flex-col items-center justify-center gap-2">
                                <Button size="sm" onClick={() => handleSetCover(URL.createObjectURL(file.content as Blob))}>
                                    Set as Cover
                                </Button>
                                <Button size="sm" variant="ghost" className="text-red-400 hover:bg-red-900/20" onClick={() => handleDelete(file.id!)}>
                                    <Trash2 size={16} />
                                </Button>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
