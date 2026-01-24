/**
 * InventoryEntityAdapter
 * Transforms raw InventoryItem objects into UniversalEntity<InventoryItem>
 * Zero data loss - original object preserved in data payload
 */

import type { InventoryItem } from '../../db';
import type { UniversalEntity, UniversalFile } from '../types';

export interface InventoryRelatedData {
    // Future: linked projects, BOM entries, etc.
    linkedProjects?: number[];
}

/**
 * Convert InventoryItem to UniversalEntity with full fidelity
 */
export function toUniversalInventory(
    item: InventoryItem,
    related?: InventoryRelatedData
): UniversalEntity<InventoryItem> {
    return {
        // Core Identity
        urn: `inventory:${item.id}`,
        id: item.id!,
        type: item.type || 'part',

        // Presentation
        title: item.name,
        subtitle: item.category ? `${item.domain || 'General'} › ${item.category}` : item.domain,
        icon: getInventoryIcon(item.type),
        color: getInventoryColor(item),

        // Context
        status: getStockStatus(item),
        tags: [], // Inventory doesn't have tags currently
        createdAt: undefined,
        updatedAt: item.updated_at,

        // Full Payload (Zero Data Loss)
        data: item,

        // Extended Fields
        progress: undefined, // Not applicable
        thumbnail: item.image_url,
        metadata: {
            location: item.location,
            quantity: item.quantity,
            min_stock: item.min_stock,
            unit_cost: item.unit_cost,
            units: item.units,
            mpn: item.mpn,
            manufacturer: item.manufacturer,
            barcode: item.barcode,
            specs: item.specs,
            properties: item.properties,
        },
        relatedData: {
            linkedProjects: related?.linkedProjects || [],
        },
        cardConfig: {
            label: item.type ? item.type.charAt(0).toUpperCase() + item.type.slice(1) : 'Item',
            backgroundImage: item.image_url,
            statusStripe: getInventoryColor(item),
            statusGlow: item.quantity <= item.min_stock,
            collapsible: true,
            metaGrid: [
                { label: 'MPN', value: item.mpn || 'N/A' },
                { label: 'Loc', value: item.location || 'Unknown' },
                { label: 'Qty', value: `${item.quantity} ${item.units}` }
            ].filter(i => i.value !== 'N/A' && i.value !== 'Unknown'),
            ratings: [
                { label: 'Stock', value: item.quantity, max: Math.max(item.quantity, item.min_stock * 2 || 10), color: getInventoryColor(item) }
            ]
        }

    };
}

/**
 * Get icon based on inventory type
 */
function getInventoryIcon(type?: string): string {
    switch (type) {
        case 'tool': return 'Wrench';
        case 'consumable': return 'Droplet';
        case 'equipment': return 'Monitor';
        default: return 'Package';
    }
}

/**
 * Get color based on stock status
 */
function getInventoryColor(item: InventoryItem): string {
    if (item.quantity <= 0) return '#ef4444'; // red
    if (item.quantity <= item.min_stock) return '#f59e0b'; // amber
    return '#22c55e'; // green
}

/**
 * Get stock status string
 */
function getStockStatus(item: InventoryItem): string {
    if (item.quantity <= 0) return 'out-of-stock';
    if (item.quantity <= item.min_stock) return 'low-stock';
    return 'in-stock';
}

/**
 * Batch convert multiple inventory items
 */
export function toUniversalInventoryBatch(
    items: InventoryItem[]
): UniversalEntity<InventoryItem>[] {
    return items.map(item => toUniversalInventory(item));
}
