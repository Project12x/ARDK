import { useState } from 'react';
import { Button } from '../ui/Button';
import { SongService } from '../../services/SongService';
import { toast } from 'sonner';
import { X } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';

interface CreateSongModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated?: (songId: number) => void;
}

export function CreateSongModal({ isOpen, onClose, onCreated }: CreateSongModalProps) {
    const [title, setTitle] = useState('');
    const [albumId, setAlbumId] = useState<number | undefined>(undefined);
    const [isSubmitting, setIsSubmitting] = useState(false);

    const albums = useLiveQuery(() => db.albums.orderBy('title').toArray());

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const id = await SongService.createSong({ title, album_id: albumId, status: 'idea' });
            toast.success('Song created');
            if (onCreated) onCreated(id);
            onClose();
            setTitle('');
            setAlbumId(undefined);
        } catch (error) {
            console.error(error);
            toast.error('Failed to create song');
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm">
            <div className="bg-surface border border-border rounded-lg shadow-xl w-full max-w-md p-6 relative animate-in fade-in zoom-in-95 duration-200">
                <button onClick={onClose} className="absolute top-4 right-4 text-gray-500 hover:text-white">
                    <X size={20} />
                </button>
                <h2 className="text-xl font-bold mb-4">Create Song</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Title</label>
                        <input
                            required
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-accent"
                            placeholder="Song Title"
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Album (Optional)</label>
                        <select
                            value={albumId || ''}
                            onChange={(e) => setAlbumId(e.target.value ? parseInt(e.target.value) : undefined)}
                            className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-accent appearance-none"
                        >
                            <option value="">Select Album...</option>
                            {albums?.map(album => (
                                <option key={album.id} value={album.id}>{album.title}</option>
                            ))}
                        </select>
                    </div>
                    <div className="flex justify-end gap-2 mt-6">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? 'Creating...' : 'Create Song'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
