
import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Asset } from '../lib/db';
import { Link } from 'react-router-dom';
import { Box, Search, Plus, Trash2, Filter, Tag, DollarSign, Calendar, MapPin, FileText, Image as ImageIcon, PenLine, Monitor } from 'lucide-react';
import clsx from 'clsx';
import { useDraggable } from '@dnd-kit/core';
import { motion } from 'framer-motion';
import { AssetCard } from '../components/assets/AssetCard';
import { AssetModal } from '../components/assets/AssetModal';
import { toast } from 'sonner';

export function AssetRegistry() {
    const [search, setSearch] = useState('');
    const [showAddModal, setShowAddModal] = useState(false);
    const [editingAsset, setEditingAsset] = useState<Asset | undefined>(undefined);
    const [defaultCategory, setDefaultCategory] = useState<string | undefined>(undefined);

    const assets = useLiveQuery(() =>
        db.assets
            .filter(a => a.name.toLowerCase().includes(search.toLowerCase()) || a.category.toLowerCase().includes(search.toLowerCase()))
            .toArray()
        , [search]);

    const getIcon = (cat: string) => {
        return <Box size={24} />;
    };

    const handleEdit = (asset: Asset) => {
        setEditingAsset(asset);
        setShowAddModal(true);
    };

    const handleDelete = async (id: number) => {
        if (confirm("Are you sure you want to delete this asset?")) {
            await db.assets.delete(id);
            toast.success("Asset deleted");
        }
    };

    const handleCloseModal = () => {
        setShowAddModal(false);
        setEditingAsset(undefined);
        setDefaultCategory(undefined);
    };

    return (
        <div className="h-full flex flex-col p-8 overflow-y-auto">
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-accent/10 rounded-xl">
                        <Box size={28} className="text-accent" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-white uppercase tracking-tight">Asset Registry</h1>
                        <p className="text-gray-400 text-sm font-mono">
                            Hardware, software licenses, and physical equipment
                        </p>
                    </div>
                </div>
                <div className="flex gap-2">
                    <button
                        onClick={() => { setDefaultCategory('computer'); setShowAddModal(true); }}
                        className="flex items-center gap-2 px-4 py-2 bg-accent/10 hover:bg-accent/20 text-accent font-bold rounded-lg transition-colors border border-accent/20"
                    >
                        <Monitor size={18} />
                        <span>Register Computer</span>
                    </button>
                    <button
                        onClick={() => { setDefaultCategory(undefined); setShowAddModal(true); }}
                        className="flex items-center gap-2 px-4 py-2 bg-accent hover:bg-accent/90 text-white font-bold rounded-lg transition-colors"
                    >
                        <Plus size={18} />
                        <span>Register Asset</span>
                    </button>
                </div>
            </div>

            {/* Quick Stats */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white/5 border border-white/10 p-4 rounded-xl flex items-center justify-between group hover:border-accent/50 transition-colors">
                    <div>
                        <div className="text-gray-500 text-xs font-mono uppercase">Total Assets</div>
                        <div className="text-2xl font-bold text-white mt-1">{assets?.length || 0}</div>
                    </div>
                    <Box className="text-gray-600 group-hover:text-accent transition-colors" />
                </div>
                <div className="bg-white/5 border border-white/10 p-4 rounded-xl flex items-center justify-between group hover:border-blue-500/50 transition-colors">
                    <div>
                        <div className="text-gray-500 text-xs font-mono uppercase">Total Value</div>
                        <div className="text-2xl font-bold text-white mt-1">
                            ${(assets || []).reduce((acc, curr) => acc + (curr.value || 0), 0).toLocaleString()}
                        </div>
                    </div>
                    <DollarSign className="text-gray-600 group-hover:text-blue-500 transition-colors" />
                </div>
            </div>

            {/* Filters */}
            <div className="flex gap-4 mb-6">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" size={16} />
                    <input
                        type="text"
                        placeholder="Search assets..."
                        value={search}
                        onChange={e => setSearch(e.target.value)}
                        className="w-full bg-black border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm focus:outline-none focus:border-accent"
                    />
                </div>
                <button className="px-4 py-2 bg-white/5 border border-white/10 rounded-lg flex items-center gap-2 text-sm hover:bg-white/10 transition-colors">
                    <Filter size={16} />
                    <span>Filter</span>
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {(assets || []).map(asset => (
                    <AssetCard
                        key={asset.id}
                        asset={asset}
                        onEdit={() => handleEdit(asset)}
                        onDelete={() => asset.id && handleDelete(asset.id)}
                    />
                ))}
            </div>

            <AssetModal
                isOpen={showAddModal}
                onClose={handleCloseModal}
                assetToEdit={editingAsset}
                defaultCategory={defaultCategory}
            />
        </div>
    );
}
