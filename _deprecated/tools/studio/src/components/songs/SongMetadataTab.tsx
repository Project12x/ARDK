import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { SongService } from '../../services/SongService';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input'; // Assuming Input exists or use native
import { Plus, X, Save } from 'lucide-react';
import { toast } from 'sonner';

interface SongMetadataTabProps {
    songId: number;
}

export function SongMetadataTab({ songId }: SongMetadataTabProps) {
    const song = useLiveQuery(() => db.songs.get(songId), [songId]);
    const [formData, setFormData] = useState<any>({});
    const [tagInput, setTagInput] = useState('');

    useEffect(() => {
        if (song) {
            setFormData({
                status: song.status,
                bpm: song.bpm || '',
                key: song.key || '',
                duration: song.duration || '',
                tags: song.tags || []
            });
        }
    }, [song]);

    const handleChange = (field: string, value: any) => {
        setFormData((prev: any) => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        try {
            await SongService.updateSong(songId, {
                status: formData.status,
                bpm: formData.bpm ? parseInt(formData.bpm) : undefined,
                key: formData.key,
                duration: formData.duration,
                tags: formData.tags
            });
            toast.success("Metadata saved");
        } catch (e) {
            toast.error("Failed to save");
            console.error(e);
        }
    };

    const addTag = () => {
        if (tagInput.trim() && !formData.tags.includes(tagInput.trim())) {
            setFormData((prev: any) => ({ ...prev, tags: [...prev.tags, tagInput.trim()] }));
            setTagInput('');
        }
    };

    const removeTag = (tag: string) => {
        setFormData((prev: any) => ({ ...prev, tags: prev.tags.filter((t: string) => t !== tag) }));
    };

    if (!song) return null;

    return (
        <div className="p-8 max-w-4xl mx-auto h-full overflow-y-auto">
            <h2 className="text-2xl font-bold mb-6 text-gray-400">Song Metadata</h2>

            <Card className="p-6 space-y-6 bg-white/5 border-white/10">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Status */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Status</label>
                        <select
                            className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={formData.status || 'draft'}
                            onChange={e => handleChange('status', e.target.value)}
                        >
                            {['draft', 'idea', 'demo', 'recording', 'mixing', 'mastering', 'released'].map(s => (
                                <option key={s} value={s}>{s.charAt(0).toUpperCase() + s.slice(1)}</option>
                            ))}
                        </select>
                    </div>

                    {/* Key */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Key</label>
                        <input
                            type="text"
                            placeholder="e.g. Cm, F# Major"
                            className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={formData.key || ''}
                            onChange={e => handleChange('key', e.target.value)}
                        />
                    </div>

                    {/* BPM */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">BPM</label>
                        <input
                            type="number"
                            placeholder="e.g. 120"
                            className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={formData.bpm || ''}
                            onChange={e => handleChange('bpm', e.target.value)}
                        />
                    </div>

                    {/* Duration */}
                    <div className="space-y-2">
                        <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Duration</label>
                        <input
                            type="text"
                            placeholder="e.g. 3:45"
                            className="w-full bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={formData.duration || ''}
                            onChange={e => handleChange('duration', e.target.value)}
                        />
                    </div>
                </div>

                {/* Tags */}
                <div className="space-y-2">
                    <label className="text-xs uppercase text-gray-500 font-bold tracking-wider">Tags</label>
                    <div className="flex flex-wrap gap-2 mb-2">
                        {formData.tags?.map((tag: string) => (
                            <span key={tag} className="px-2 py-1 bg-white/10 rounded text-sm flex items-center gap-1 group">
                                {tag}
                                <button onClick={() => removeTag(tag)} className="text-gray-500 hover:text-red-400"><X size={12} /></button>
                            </span>
                        ))}
                    </div>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            placeholder="Add tag..."
                            className="flex-1 bg-black/50 border border-white/10 rounded-lg p-2 text-white focus:border-accent outline-none"
                            value={tagInput}
                            onChange={e => setTagInput(e.target.value)}
                            onKeyDown={e => e.key === 'Enter' && addTag()}
                        />
                        <Button variant="outline" onClick={addTag}><Plus size={16} /></Button>
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
