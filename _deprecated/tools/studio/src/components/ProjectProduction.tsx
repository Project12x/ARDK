
import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type ProjectProductionItem } from '../lib/db';
import { Button } from './ui/Button';
import { Card } from './ui/Card';
import { Plus, ListMusic, Film, GripVertical, Trash2 } from 'lucide-react';
import { toast } from 'sonner';

interface ProjectProductionProps {
    projectId: number;
    projectCategory?: string;
}

export function ProjectProduction({ projectId, projectCategory }: ProjectProductionProps) {
    const items = useLiveQuery(() =>
        db.project_production_items.where('project_id').equals(projectId).sortBy('order')
    );

    const isMusic = projectCategory?.toLowerCase().includes('music') || false;
    const isVideo = projectCategory?.toLowerCase().includes('video') || false;

    // Define columns based on context
    const getColumns = () => {
        if (isMusic) {
            return [
                { key: 'bpm', label: 'BPM', width: 'w-16' },
                { key: 'key', label: 'Key', width: 'w-16' },
                { key: 'length', label: 'Length', width: 'w-20' },
                { key: 'demo', label: 'Demo', width: 'w-24', type: 'checkbox' }, // Has Demo?
                { key: 'lyrics', label: 'Lyrics', width: 'w-24', type: 'checkbox' },
                { key: 'lead_vocal', label: 'Vocals', width: 'w-24', type: 'checkbox' },
                { key: 'assignee', label: 'Assignee', width: 'w-32' },
                { key: 'status_note', label: 'Status Note', width: 'flex-1' },
            ];
        }
        if (isVideo) {
            return [
                { key: 'scene_no', label: 'Scene #', width: 'w-20' },
                { key: 'location', label: 'Location', width: 'w-32' },
                { key: 'day_time', label: 'Day/Time', width: 'w-24' },
                { key: 'cast', label: 'Cast', width: 'w-32' },
                { key: 'equipment', label: 'Equipment', width: 'w-32' }, // Camera/Lens
                { key: 'shot_type', label: 'Shot', width: 'w-24' }, // Wide, Close-up
                { key: 'assignee', label: 'Assignee', width: 'w-32' },
            ];
        }
        // Default / Generic
        return [
            { key: 'priority', label: 'Priority', width: 'w-24' },
            { key: 'assignee', label: 'Assignee', width: 'w-32' },
            { key: 'note', label: 'Note', width: 'flex-1' }
        ];
    };

    const columns = getColumns();

    const handleCreateItem = async () => {
        const count = items?.length || 0;
        const type = isMusic ? 'song' : isVideo ? 'scene' : 'shot';

        await db.project_production_items.add({
            project_id: projectId,
            name: `Untitled ${type === 'song' ? 'Song' : type === 'scene' ? 'Scene' : 'Item'} ${count + 1}`,
            type: type as any,
            metadata: {},
            status: 'planned',
            order: count
        });
        toast.success("Item added");
    };

    const updateMetadata = async (id: number, key: string, value: any, currentMeta: any) => {
        await db.project_production_items.update(id, {
            metadata: {
                ...currentMeta,
                [key]: value
            }
        });
    };

    const updateName = async (id: number, name: string) => {
        await db.project_production_items.update(id, { name });
    };

    const updateStatus = async (id: number, status: any) => {
        await db.project_production_items.update(id, { status });
    };

    const handleDelete = async (id: number) => {
        if (confirm("Delete this item?")) {
            db.project_production_items.delete(id);
        }
    };

    return (
        <div className="space-y-4 animate-in fade-in duration-500">
            <div className="flex justify-between items-center">
                <h2 className="text-xl font-bold text-white uppercase tracking-tight flex items-center gap-2">
                    {isMusic ? <ListMusic size={24} className="text-purple-400" /> :
                        isVideo ? <Film size={24} className="text-blue-400" /> : null}
                    {isMusic ? 'Album Tracker' : isVideo ? 'Shot List' : 'Production List'}
                </h2>
                <Button size="sm" onClick={handleCreateItem}>
                    <Plus size={16} className="mr-2" /> Add Item
                </Button>
            </div>

            <Card className="p-0 overflow-hidden bg-gray-900 border-white/10">
                {/* Header */}
                <div className="flex items-center gap-4 p-3 bg-white/5 border-b border-white/10 text-xs font-bold text-gray-400 uppercase tracking-wider">
                    <div className="w-8 text-center">#</div>
                    <div className="flex-1">Title</div>
                    <div className="w-24">Status</div>
                    {columns.map(col => (
                        <div key={col.key} className={col.width}>{col.label}</div>
                    ))}
                    <div className="w-8"></div>
                </div>

                {/* Rows */}
                <div className="divide-y divide-white/5">
                    {items?.map((item, index) => (
                        <div key={item.id} className="flex items-center gap-4 p-3 group hover:bg-white/5 transition-colors">
                            <div className="w-8 text-center text-gray-600 font-mono text-xs">{index + 1}</div>

                            {/* Title Editable */}
                            <div className="flex-1">
                                <input
                                    className="bg-transparent border border-transparent hover:border-white/10 rounded px-2 py-1 text-sm text-white w-full focus:outline-none focus:border-purple-500 transition-all font-medium"
                                    value={item.name}
                                    onChange={(e) => updateName(item.id!, e.target.value)}
                                />
                            </div>

                            {/* Status */}
                            <div className="w-24">
                                <select
                                    className="bg-black/30 border border-white/10 rounded px-1 py-1 text-xs text-gray-300 w-full focus:outline-none"
                                    value={item.status}
                                    onChange={(e) => updateStatus(item.id!, e.target.value)}
                                >
                                    <option value="planned">Planned</option>
                                    <option value="in-progress">WIP</option>
                                    <option value="blocked">Blocked</option>
                                    <option value="done">Done</option>
                                </select>
                            </div>

                            {/* Dynamic Columns */}
                            {columns.map(col => (
                                <div key={col.key} className={col.width}>
                                    {col.type === 'checkbox' ? (
                                        <input
                                            type="checkbox"
                                            checked={!!item.metadata[col.key]}
                                            onChange={(e) => updateMetadata(item.id!, col.key, e.target.checked, item.metadata)}
                                            className="ml-2 accent-purple-500"
                                        />
                                    ) : (
                                        <input
                                            className="bg-transparent border border-transparent hover:border-white/10 focus:bg-black/40 rounded px-2 py-1 text-xs text-gray-300 w-full focus:outline-none focus:border-purple-500 placeholder-gray-700"
                                            placeholder="--"
                                            value={item.metadata[col.key] || ''}
                                            onChange={(e) => updateMetadata(item.id!, col.key, e.target.value, item.metadata)}
                                        />
                                    )}
                                </div>
                            ))}

                            <div className="w-8 flex justify-end">
                                <button
                                    onClick={() => handleDelete(item.id!)}
                                    className="text-gray-600 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-all p-1"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        </div>
                    ))}

                    {items?.length === 0 && (
                        <div className="p-8 text-center text-gray-500 text-sm">
                            No items yet. Add one to track your production.
                        </div>
                    )}
                </div>
            </Card>
        </div>
    );
}
