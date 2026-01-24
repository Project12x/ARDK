/**
 * PurchaseEntityAdapter
 * Transforms raw PurchaseItem objects into UniversalEntity<PurchaseItem>
 */

import type { PurchaseItem } from '../../db';
import type { UniversalEntity } from '../types';

const STATUS_CONFIG = {
    'planned': { icon: 'ShoppingCart', color: '#6b7280' },
    'ordered': { icon: 'Package', color: '#3b82f6' },
    'shipped': { icon: 'Truck', color: '#8b5cf6' },
    'arrived': { icon: 'PackageCheck', color: '#22c55e' },
    'installed': { icon: 'CheckCircle', color: '#10b981' },
};

export function toUniversalPurchase(item: PurchaseItem): UniversalEntity<PurchaseItem> {
    const config = STATUS_CONFIG[item.status] || STATUS_CONFIG.planned;

    return {
        urn: `purchase:${item.id}`,
        id: item.id!,
        type: 'purchase',

        title: item.name,
        subtitle: `${item.quantity_needed}× • ${item.status}`,
        icon: config.icon,
        color: config.color,

        status: item.status,
        tags: [],
        createdAt: item.created_at,
        updatedAt: item.updated_at,

        data: item,

        progress: getPurchaseProgress(item.status),
        metadata: {
            quantity_needed: item.quantity_needed,
            estimated_unit_cost: item.estimated_unit_cost,
            actual_unit_cost: item.actual_unit_cost,
            priority: item.priority,
            vendor_id: item.vendor_id,
            tracking_number: item.tracking_number,
            expected_arrival: item.expected_arrival,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Purchase',
            statusStripe: config.color,
            statusGlow: item.status === 'arrived' || item.status === 'shipped',
            collapsible: true,

            metaGrid: [
                { label: 'Qty', value: `${item.quantity_needed}` },
                { label: 'Cost', value: item.estimated_unit_cost ? `$${item.estimated_unit_cost}` : 'TBD' },
                { label: item.actual_unit_cost ? 'Actual' : 'Est', value: item.actual_unit_cost ? `$${item.actual_unit_cost}` : (item.estimated_unit_cost ? `$${item.estimated_unit_cost}` : '-') }
            ].filter(i => i.value !== 'TBD' && i.value !== '-'),

            ratings: [
                { label: 'Status', value: getPurchaseProgress(item.status), max: 100, color: config.color }
            ],

            externalLinks: item.tracking_number ? [
                { label: 'Track', url: `https://www.google.com/search?q=${item.tracking_number}` } // Generic tracking search
            ] : undefined
        }
    };
}

function getPurchaseProgress(status: string): number {
    switch (status) {
        case 'planned': return 0;
        case 'ordered': return 25;
        case 'shipped': return 50;
        case 'arrived': return 75;
        case 'installed': return 100;
        default: return 0;
    }
}

export function toUniversalPurchaseBatch(items: PurchaseItem[]): UniversalEntity<PurchaseItem>[] {
    return items.map(item => toUniversalPurchase(item));
}
