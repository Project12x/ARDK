/**
 * LibraryEntityAdapter
 * Transforms raw LibraryItem objects into UniversalEntity<LibraryItem>
 * Zero data loss - original object preserved in data payload
 */

import type { LibraryItem } from '../../db';
import type { UniversalEntity } from '../types';

/**
 * Convert LibraryItem to UniversalEntity with full fidelity
 */
export function toUniversalLibrary(
    item: LibraryItem
): UniversalEntity<LibraryItem> {
    return {
        // Core Identity
        urn: `library:${item.id}`,
        id: item.id!,
        type: 'library',

        // Presentation
        title: item.title,
        subtitle: getCategoryLabel(item.category),
        icon: getLibraryIcon(item.type),
        color: getLibraryColor(item.type),

        // Context
        status: item.category || 'junk',
        tags: item.tags || [],
        createdAt: item.created_at,
        updatedAt: undefined,

        // Full Payload
        data: item,

        // Extended
        thumbnail: item.type === 'image' ? item.content : undefined,
        metadata: {
            type: item.type,
            category: item.category,
            folder_path: item.folder_path,
            file_size: item.file_size,
            mime_type: item.mime_type,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Library Item',
            statusStripe: getLibraryColor(item.type),
            statusGlow: false,
            collapsible: true,

            metaGrid: [
                { label: 'Type', value: item.type },
                { label: 'Size', value: item.file_size ? `${Math.round(item.file_size / 1024)} KB` : ' - ' },
                { label: 'Folder', value: item.folder_path || 'Root' }
            ].filter(i => !!i.value && i.value !== ' - '),

            externalLinks: item.content && (item.type === 'link' || item.type === 'pdf') ? [
                { label: 'Open', url: item.content }
            ] : undefined
        }
    };
}

function getCategoryLabel(category?: string): string {
    switch (category) {
        case 'bookshelf': return '📚 Bookshelf';
        case 'records': return '💿 Records';
        case 'photos': return '📷 Photos';
        case 'vhs': return '📼 VHS';
        case 'junk': return '📦 Junk Drawer';
        default: return '📦 Uncategorized';
    }
}

function getLibraryIcon(type: string): string {
    switch (type) {
        case 'pdf': return 'FileText';
        case 'text': return 'FileText';
        case 'ebook': return 'Book';
        case 'image': return 'Image';
        case 'audio': return 'Disc';
        case 'video': return 'Film';
        default: return 'Archive';
    }
}

function getLibraryColor(type: string): string {
    switch (type) {
        case 'pdf': return '#ef4444'; // red
        case 'text': return '#6b7280'; // gray
        case 'ebook': return '#f59e0b'; // amber
        case 'image': return '#22c55e'; // green
        case 'audio': return '#ec4899'; // pink
        case 'video': return '#06b6d4'; // cyan
        default: return '#3b82f6'; // blue
    }
}

export function toUniversalLibraryBatch(items: LibraryItem[]): UniversalEntity<LibraryItem>[] {
    return items.map(item => toUniversalLibrary(item));
}
