/**
 * VendorEntityAdapter
 * Transforms raw Vendor objects into UniversalEntity<Vendor>
 */

import type { Vendor } from '../../db';
import type { UniversalEntity } from '../types';

export function toUniversalVendor(vendor: Vendor): UniversalEntity<Vendor> {
    return {
        urn: `vendor:${vendor.id}`,
        id: vendor.id!,
        type: 'vendor',

        title: vendor.name,
        subtitle: vendor.website || 'No website',
        icon: 'Store',
        color: vendor.api_integration !== 'none' ? '#22c55e' : '#6b7280',

        status: vendor.api_integration || 'manual',
        tags: [],
        createdAt: undefined,
        updatedAt: undefined,

        data: vendor,

        metadata: {
            website: vendor.website,
            api_integration: vendor.api_integration,
            has_api: vendor.api_integration !== 'none',
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Vendor',
            statusStripe: vendor.api_integration !== 'none' ? '#22c55e' : '#6b7280',
            statusGlow: vendor.api_integration === 'full',
            collapsible: true,

            metaGrid: [
                { label: 'API', value: vendor.api_integration || 'None' },
                { label: 'Website', value: vendor.website ? new URL(vendor.website).hostname : 'None' }
            ].filter(i => i.value !== 'None'),

            externalLinks: vendor.website ? [
                { label: 'Website', url: vendor.website }
            ] : undefined
        }
    };
}

export function toUniversalVendorBatch(vendors: Vendor[]): UniversalEntity<Vendor>[] {
    return vendors.map(vendor => toUniversalVendor(vendor));
}
