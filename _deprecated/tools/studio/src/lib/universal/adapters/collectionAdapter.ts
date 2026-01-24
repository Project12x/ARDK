/**
 * Collection Adapter
 * Converts collections/groups to UniversalEntity format.
 * Collections are arbitrary groupings of entities across types.
 */

import type { UniversalEntity } from '../types';

// ============================================================================
// COLLECTION SCHEMA
// ============================================================================

export interface CollectionMember {
    entity_type: string;
    entity_id: number;
    order?: number;
    added_at?: Date;
}

export interface CollectionEntry {
    id: number;
    /** Collection name */
    name: string;
    /** Description */
    description?: string;
    /** Collection type/category */
    category?: 'folder' | 'playlist' | 'board' | 'group' | 'custom';
    /** Collection icon */
    icon?: string;
    /** Collection color */
    color?: string;
    /** Members of this collection */
    members: CollectionMember[];
    /** Is this collection pinned/favorited */
    is_pinned?: boolean;
    /** Is this a smart/dynamic collection */
    is_smart?: boolean;
    /** Smart collection filter rules */
    filter_rules?: Record<string, any>;
    /** Parent collection (for nesting) */
    parent_id?: number;
    /** Timestamps */
    created_at: Date;
    updated_at?: Date;
}

// ============================================================================
// HELPERS
// ============================================================================

function getCollectionIcon(category?: CollectionEntry['category']): string {
    switch (category) {
        case 'folder': return 'Folder';
        case 'playlist': return 'ListMusic';
        case 'board': return 'LayoutDashboard';
        case 'group': return 'Users';
        default: return 'FolderOpen';
    }
}

function getMemberTypesSummary(members: CollectionMember[]): string {
    const typeCounts = members.reduce((acc, m) => {
        acc[m.entity_type] = (acc[m.entity_type] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    return Object.entries(typeCounts)
        .map(([type, count]) => `${count} ${type}${count > 1 ? 's' : ''}`)
        .join(', ');
}

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalCollection(collection: CollectionEntry): UniversalEntity<CollectionEntry> {
    const memberSummary = getMemberTypesSummary(collection.members);

    return {
        urn: `collection:${collection.id}`,
        id: collection.id,
        type: 'collection',
        title: collection.name,
        subtitle: memberSummary || 'Empty collection',
        icon: collection.icon || getCollectionIcon(collection.category),
        color: collection.color || (collection.is_smart ? 'text-purple-500' : 'text-blue-500'),
        status: collection.is_pinned ? 'pinned' : 'default',
        createdAt: collection.created_at,
        updatedAt: collection.updated_at,
        data: collection,
        metadata: {
            memberCount: collection.members.length,
            category: collection.category,
            isPinned: collection.is_pinned,
            isSmart: collection.is_smart,
            parentId: collection.parent_id,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Collection',
            statusStripe: collection.color || (collection.is_smart ? '#a855f7' : '#3b82f6'), // Hex colors
            statusGlow: collection.is_smart,
            collapsible: true,
            defaultCollapsed: true,

            metaGrid: [
                { label: 'Items', value: collection.members.length },
                { label: 'Type', value: collection.is_smart ? 'Smart' : 'Static' },
                { label: 'Category', value: collection.category || 'General' }
            ],

            nextAction: {
                label: 'View Items',
                icon: undefined
            }
        }
    };
}

export function toUniversalCollectionBatch(collections: CollectionEntry[]): UniversalEntity<CollectionEntry>[] {
    return collections.map(toUniversalCollection);
}
