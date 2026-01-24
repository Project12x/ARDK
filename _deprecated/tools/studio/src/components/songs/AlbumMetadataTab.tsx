import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { SongService } from '../../services/SongService';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Plus, X, Save, Calendar } from 'lucide-react';
import { toast } from 'sonner';

interface AlbumMetadataTabProps {
    albumId: number;
}

export function AlbumMetadataTab({ albumId }: AlbumMetadataTabProps) {
    const album = useLiveQuery(() => db.albums.get(albumId), [albumId]);
    const [formData, setFormData] = useState<any>({});
    const [tagInput, setTagInput] = useState('');

    useEffect(() => {
        if (album) {
            setFormData({
                artist: album.artist || '',
                status: album.status || 'planned',
                release_date: album.release_date ? new Date(album.release_date).toISOString().split('T')[0] : '',
                tags: [] // Schema doesn't have tags on Album yet? Let's check db.ts. 
                // db.ts: albums: '++id, title, status' (v48). 
                // Ah, it seems Albums don't have tags in v48 schema.
                // I should add tags to Album schema if I want them, but for now I'll stick to existing fields.
            });
        }
    }, [album]);

    const handleChange = (field: string, value: any) => {
        setFormData((prev: any) => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        try {
            await SongService.updateAlbum(albumId, {
                artist: formData.artist,
                status: formData.status,
                release_date: formData.release_date ? new Date(formData.release_date) : undefined,
            });
            toast.success("Album Metadata saved");
        } catch (e) {
            toast.error("Failed to save");
            console.error(e);
        }
    };

    if (!album) return null;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6 text-gray-400">Album Metadata</h2>

            <Card className="p-6 space-y-6 bg-white/5 border-white/10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Status */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Status</label>
                        <select
                            className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={formData.status}
                            onChange={e => handleChange('status', e.target.value)}
                        >
                            {['planned', 'in-progress', 'released'].map(s => (
                                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                            ))}
                        </select>
                    </div>

                    {/* Artist */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Artist</label>
                        <input
                            type="text"
                            placeholder="Artist Name"
                            className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={formData.artist}
                            onChange={e => handleChange('artist', e.target.value)}
                        />
                    </div>

                    {/* Release Date */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Release Date</label>
                        <div className="relative">
                            <input
                                type="date"
                                className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                                value={formData.release_date}
                                onChange={e => handleChange('release_date', e.target.value)}
                            />
                            <Calendar className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-500 pointer-events-none" size={16} />
                        </div>
                    </div>
                </div>

                <div className="pt-4 border-t border-white/10 flex justify-end">
                    <Button onClick={handleSave} className="bg-accent text-black hover:bg-accent/90">
                        <Save size={16} className="mr-2" /> Save Changes
                    </Button>
                </div>
            </Card>
        </div>
    );
}
