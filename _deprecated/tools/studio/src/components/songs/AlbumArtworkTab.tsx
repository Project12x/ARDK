import { useState, useCallback, useEffect } from 'react';
import { useDropzone } from 'react-dropzone';
import { SongService } from '../../services/SongService';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Image as ImageIcon, Upload, Sparkles, Trash2, Link as LinkIcon } from 'lucide-react';
import { Button } from '../ui/Button';
import { toast } from 'sonner';
import clsx from 'clsx';
import { Card } from '../ui/Card';

interface AlbumArtworkTabProps {
    albumId: number;
}

export function AlbumArtworkTab({ albumId }: AlbumArtworkTabProps) {
    const artworkFiles = useLiveQuery(() =>
        db.album_files.where({ album_id: albumId, category: 'artwork' }).toArray()
        , [albumId]);

    const album = useLiveQuery(() => db.albums.get(albumId), [albumId]);

    // Set as Cover
    const handleSetCover = async (urlOrId: string | number) => {
        let finalUrl = '';
        if (typeof urlOrId === 'number') {
            finalUrl = `internal://album_file/${urlOrId}`;
        } else {
            finalUrl = urlOrId;
        }

        await SongService.updateAlbum(albumId, { cover_art_url: finalUrl });
        toast.success("Album cover updated");
    };

    // Resolve displayed cover
    const [resolvedCover, setResolvedCover] = useState<string | null>(null);

    useEffect(() => {
        let activeObjUrl: string | null = null;

        const loadCover = async () => {
            if (album?.cover_art_url?.startsWith('internal://album_file/')) {
                const id = parseInt(album.cover_art_url.split('/').pop() || '0');
                const file = await db.album_files.get(id);
                if (file) {
                    activeObjUrl = URL.createObjectURL(file.content as Blob);
                    setResolvedCover(activeObjUrl);
                }
            } else {
                setResolvedCover(album?.cover_art_url || null);
            }
        };

        loadCover();

        return () => {
            if (activeObjUrl) URL.revokeObjectURL(activeObjUrl);
        };
    }, [album?.cover_art_url]);

    // Upload
    const onDrop = useCallback(async (acceptedFiles: File[]) => {
        for (const file of acceptedFiles) {
            try {
                await SongService.addAlbumFile(albumId, file, 'artwork');
                toast.success(`Uploaded ${file.name}`);
            } catch (e) {
                console.error(e);
                toast.error("Upload failed");
            }
        }
    }, [albumId]);

    const { getRootProps, getInputProps, isDragActive } = useDropzone({
        onDrop,
        accept: { 'image/*': [] }
    });

    const handleDelete = async (id: number) => {
        if (confirm("Delete artwork?")) {
            await SongService.deleteAlbumFile(id);
            toast.success("Deleted");
        }
    };

    return (
        <div className="p-8 max-w-5xl mx-auto h-full overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6 flex items-center gap-2">
                <ImageIcon className="text-accent" /> Album Artwork
            </h2>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Active Cover */}
                <Card className="p-6 bg-white/5 border-white/10 flex flex-col items-center justify-center text-center gap-4">
                    <h3 className="text-sm font-bold text-gray-400 uppercase tracking-wider">Current Cover</h3>
                    <div className="aspect-square w-64 bg-black/50 rounded-xl overflow-hidden shadow-2xl relative group">
                        {resolvedCover ? (
                            <img src={resolvedCover} alt="Cover" className="w-full h-full object-cover" />
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
                                const prompt = encodeURIComponent(`${album?.title} album cover art artistic high quality`);
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
                                <Button size="sm" onClick={() => handleSetCover(file.id!)}>
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
