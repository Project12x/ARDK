/**
 * UniversalCollectionCard
 * Displays collections/groups of entities.
 */

import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, Folder, FolderOpen, ListMusic, LayoutDashboard, Users, Pin, Sparkles } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { CollectionEntry } from '../../lib/universal/adapters/collectionAdapter';

interface UniversalCollectionCardProps {
    entity: UniversalEntity<CollectionEntry>;
    onClick?: () => void;
    className?: string;
}

const CATEGORY_ICONS: Record<string, typeof Folder> = {
    'folder': Folder,
    'playlist': ListMusic,
    'board': LayoutDashboard,
    'group': Users,
};

export function UniversalCollectionCard({ entity, onClick, className }: UniversalCollectionCardProps) {
    const collection = entity.data;
    const CategoryIcon = CATEGORY_ICONS[collection.category || 'folder'] || FolderOpen;
    const memberCount = collection.members.length;

    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'grid' }
    });

    // Group members by type
    const memberTypes = collection.members.reduce((acc, m) => {
        acc[m.entity_type] = (acc[m.entity_type] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative p-4 rounded-xl border border-white/5 bg-black/40 hover:border-white/20 transition-all",
                collection.is_pinned && "border-yellow-500/20",
                isDragging && "opacity-50 scale-95",
                className
            )}
        >
            {/* Drag Handle */}
            <div
                {...attributes}
                {...listeners}
                className="absolute top-2 right-2 p-1 rounded cursor-grab text-gray-500 hover:text-white opacity-0 group-hover:opacity-100"
            >
                <GripVertical size={14} />
            </div>

            {/* Header */}
            <div className="flex items-center gap-3 mb-3">
                <div
                    className={clsx("p-2 rounded-lg bg-white/5", collection.color || 'text-blue-500')}
                    style={collection.color?.startsWith('#') ? { color: collection.color } : undefined}
                >
                    <CategoryIcon size={20} />
                </div>
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-white truncate">{collection.name}</h3>
                        {collection.is_pinned && <Pin size={12} className="text-yellow-500" />}
                        {collection.is_smart && <Sparkles size={12} className="text-purple-500" />}
                    </div>
                    <div className="text-[10px] text-gray-500">
                        {memberCount} item{memberCount !== 1 ? 's' : ''}
                    </div>
                </div>
            </div>

            {/* Description */}
            {collection.description && (
                <p className="text-xs text-gray-400 line-clamp-2 mb-3">
                    {collection.description}
                </p>
            )}

            {/* Member Type Breakdown */}
            {memberCount > 0 && (
                <div className="flex flex-wrap gap-1">
                    {Object.entries(memberTypes).slice(0, 4).map(([type, count]) => (
                        <span
                            key={type}
                            className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-400"
                        >
                            {count} {type}
                        </span>
                    ))}
                    {Object.keys(memberTypes).length > 4 && (
                        <span className="text-[9px] px-1.5 py-0.5 rounded bg-white/5 text-gray-500">
                            +{Object.keys(memberTypes).length - 4} more
                        </span>
                    )}
                </div>
            )}

            {/* Empty State */}
            {memberCount === 0 && (
                <div className="text-center py-4 text-gray-500 text-xs">
                    Empty collection
                </div>
            )}
        </div>
    );
}
