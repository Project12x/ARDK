import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Asset } from '../../lib/db';
import { useDroppable } from '@dnd-kit/core';
import { clsx } from 'clsx';
import { Box, Monitor, Plus } from 'lucide-react';
import { AssetCard } from '../assets/AssetCard';
import { AssetModal } from '../assets/AssetModal';
import { toast } from 'sonner';

interface ProjectAssetsProps {
    projectId: number;
}

export function ProjectAssets({ projectId }: ProjectAssetsProps) {
    const [showModal, setShowModal] = useState(false);
    const [editingAsset, setEditingAsset] = useState<Asset | undefined>(undefined);
    const [defaultCategory, setDefaultCategory] = useState<string | undefined>(undefined);

    const { setNodeRef, isOver } = useDroppable({
        id: `project-assets-dropzone-${projectId}`,
        data: { type: 'project-assets-zone', projectId }
    });

    const assets = useLiveQuery(() =>
        db.assets.where('related_project_ids').equals(projectId).toArray()
        , [projectId]);

    const handleEdit = (asset: Asset) => {
        setEditingAsset(asset);
        setDefaultCategory(undefined);
        setShowModal(true);
    };

    const handleCreate = (category?: string) => {
        setEditingAsset(undefined);
        setDefaultCategory(category);
        setShowModal(true);
    };

    const handleDelete = async (id: number) => {
        if (confirm("Are you sure you want to remove this asset? It will be deleted permanently.")) {
            await db.assets.delete(id);
            toast.success("Asset deleted");
        }
    };

    const handleCloseModal = () => {
        setShowModal(false);
        setEditingAsset(undefined);
        setDefaultCategory(undefined);
    };

    return (
        <div className="space-y-4">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <Box className="text-accent" size={20} />
                    Project Assets
                </h3>
                <div className="flex gap-2">
                    <button
                        onClick={() => handleCreate('computer')}
                        className="flex items-center gap-2 px-3 py-1.5 bg-accent/10 hover:bg-accent/20 text-accent font-bold text-xs rounded-lg transition-colors border border-accent/20"
                    >
                        <Monitor size={14} />
                        <span>Register Computer</span>
                    </button>
                    <button
                        onClick={() => handleCreate()}
                        className="flex items-center gap-2 px-3 py-1.5 bg-white/5 hover:bg-white/10 text-white font-bold text-xs rounded-lg transition-colors border border-white/10"
                    >
                        <Plus size={14} />
                        <span>Add Asset</span>
                    </button>
                </div>
            </div>

            <div
                ref={setNodeRef}
                className={clsx(
                    "min-h-[200px] bg-black/20 border-2 border-dashed rounded-xl p-6 transition-all",
                    isOver ? "border-accent bg-accent/5 scale-[1.01]" : "border-white/10 hover:border-white/20"
                )}
            >
                {assets && assets.length > 0 ? (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {assets.map(asset => (
                            <AssetCard
                                key={asset.id}
                                asset={asset}
                                onEdit={() => handleEdit(asset)}
                                onDelete={() => asset.id && handleDelete(asset.id)}
                            />
                        ))}
                    </div>
                ) : (
                    <div className="flex flex-col items-center justify-center h-48 text-gray-500 gap-4 pointer-events-none">
                        <Box size={32} className="opacity-20" />
                        <p className="text-xs font-mono uppercase tracking-widest">Drop assets here or register new</p>
                    </div>
                )}
            </div>

            <AssetModal
                isOpen={showModal}
                onClose={handleCloseModal}
                assetToEdit={editingAsset}
                defaultProjectId={projectId}
                defaultCategory={defaultCategory}
            />
        </div>
    );
}
