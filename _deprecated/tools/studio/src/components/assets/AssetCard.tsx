
import type { Asset } from '../../lib/db';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { motion } from 'framer-motion';
import { Box, PenLine, FileText, Trash2 } from 'lucide-react';
import clsx from 'clsx';
import { Link } from 'react-router-dom';

interface AssetCardProps {
    asset: Asset;
    onEdit?: () => void;
    onDelete?: () => void;
}

export function AssetCard({ asset, onEdit, onDelete }: AssetCardProps) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `asset-${asset.id}`,
        data: {
            type: 'asset-item',
            item: asset
        }
    });

    const style = transform ? {
        transform: CSS.Translate.toString(transform),
        zIndex: isDragging ? 999 : undefined,
    } : undefined;

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'active': return 'bg-green-500/10 text-green-500 border-green-500/20';
            case 'maintenance': return 'bg-yellow-500/10 text-yellow-500 border-yellow-500/20';
            case 'retired': return 'bg-red-500/10 text-red-500 border-red-500/20';
            default: return 'bg-gray-500/10 text-gray-500 border-gray-500/20';
        }
    };

    const getIcon = (cat: string) => {
        return <Box size={24} />;
    };

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={clsx(
                "group relative bg-white/5 border border-white/10 rounded-lg p-4 hover:border-white/20 transition-all cursor-grab active:cursor-grabbing hover:shadow-[0_0_15px_rgba(59,130,246,0.1)]",
                isDragging && "opacity-50"
            )}
        >
            <motion.div
                layoutId={`asset-${asset.id}`}
                className="bg-[#0A0A0A] border border-white/10 rounded-xl overflow-hidden hover:border-accent/50 transition-colors group h-full flex flex-col"
            >
                {/* Image / Icon Header */}
                <div className="h-40 bg-white/5 flex items-center justify-center relative overflow-hidden">
                    {asset.images?.[0] ? (
                        <img src={asset.images[0]} alt={asset.name} className="w-full h-full object-cover opacity-80 group-hover:scale-105 transition-transform duration-500" />
                    ) : (
                        <div className="text-white/20 group-hover:text-white/40 transition-colors">
                            {getIcon(asset.category)}
                        </div>
                    )}
                    <div className={clsx("absolute top-3 right-3 px-2 py-0.5 rounded text-xs font-bold uppercase border backdrop-blur-md", getStatusColor(asset.status))}>
                        {asset.status}
                    </div>
                </div>

                {/* Content */}
                <div className="p-5 flex-1 flex flex-col">
                    <h3 className="text-lg font-bold text-white mb-1">{asset.name}</h3>
                    <div className="text-sm text-gray-500 mb-4 flex items-center gap-2">
                        <span>{asset.category}</span>
                        {asset.model && <span>• {asset.model}</span>}
                    </div>

                    {/* Computer Badge */}
                    {asset.specs_computer && (
                        <div className="mb-4 bg-accent/5 border border-accent/10 rounded p-2 text-xs font-mono text-accent/80">
                            PC: {asset.specs_computer.cpu.split(' ')[0]} / {asset.specs_computer.ram}
                        </div>
                    )}

                    <div className="mt-auto pt-4 border-t border-white/5 flex items-center justify-between text-xs text-gray-600">
                        <span>ID: #{asset.id}</span>
                        <div className="flex gap-2">
                            {onEdit && (
                                <button
                                    onPointerDown={(e) => { e.stopPropagation(); }}
                                    onClick={(e) => { e.stopPropagation(); onEdit(); }}
                                    className="hover:text-accent transition-colors"
                                >
                                    <PenLine size={14} />
                                </button>
                            )}
                            <Link to={`/assets/${asset.id}`} className="hover:text-white transition-colors" onPointerDown={e => e.stopPropagation()}>
                                <FileText size={14} />
                            </Link>
                            {onDelete && (
                                <button
                                    onPointerDown={(e) => { e.stopPropagation(); }}
                                    onClick={(e) => { e.stopPropagation(); onDelete(); }}
                                    className="hover:text-red-500 transition-colors"
                                >
                                    <Trash2 size={14} />
                                </button>
                            )}
                        </div>
                    </div>
                </div>
            </motion.div>
        </div>
    );
}
