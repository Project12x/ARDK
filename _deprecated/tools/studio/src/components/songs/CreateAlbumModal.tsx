import { useState } from 'react';
import { Button } from '../ui/Button';
import { SongService } from '../../services/SongService';
import { toast } from 'sonner';
import { X } from 'lucide-react';

interface CreateAlbumModalProps {
    isOpen: boolean;
    onClose: () => void;
    onCreated?: (albumId: number) => void;
}

export function CreateAlbumModal({ isOpen, onClose, onCreated }: CreateAlbumModalProps) {
    const [title, setTitle] = useState('');
    const [artist, setArtist] = useState('');
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!isOpen) return null;

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsSubmitting(true);
        try {
            const id = await SongService.createAlbum({ title, artist, status: 'planned' });
            toast.success('Album created');
            if (onCreated) onCreated(id);
            onClose();
            setTitle('');
            setArtist('');
        } catch (error) {
            console.error(error);
            toast.error('Failed to create album');
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
                <h2 className="text-xl font-bold mb-4">Create Album</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Title</label>
                        <input
                            required
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-accent"
                            placeholder="Album Title"
                            autoFocus
                        />
                    </div>
                    <div>
                        <label className="block text-sm font-medium text-gray-400 mb-1">Artist</label>
                        <input
                            value={artist}
                            onChange={(e) => setArtist(e.target.value)}
                            className="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-white focus:outline-none focus:border-accent"
                            placeholder="Artist Name"
                        />
                    </div>
                    <div className="flex justify-end gap-2 mt-6">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                        <Button type="submit" disabled={isSubmitting}>
                            {isSubmitting ? 'Creating...' : 'Create Album'}
                        </Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
