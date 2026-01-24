/**
 * AssetEntityAdapter
 * Transforms raw Asset objects into UniversalEntity<Asset>
 * Zero data loss - original object preserved in data payload
 */

import type { Asset } from '../../db';
import type { UniversalEntity, UniversalFile } from '../types';

export interface AssetRelatedData {
    linkedProjects?: { id: number; title: string }[];
    libraryItems?: { id: number; title: string }[];
}

/**
 * Convert Asset to UniversalEntity with full fidelity
 */
export function toUniversalAsset(
    asset: Asset,
    related?: AssetRelatedData
): UniversalEntity<Asset> {
    return {
        // Core Identity
        urn: `asset:${asset.id}`,
        id: asset.id!,
        type: 'asset',

        // Presentation
        title: asset.name,
        subtitle: [asset.make, asset.model].filter(Boolean).join(' ') || asset.category,
        icon: getAssetIcon(asset.category),
        color: getAssetColor(asset.status),

        // Context
        status: asset.status,
        tags: [], // Assets don't have tags currently
        createdAt: asset.created_at,
        updatedAt: asset.updated_at,

        // Full Payload (Zero Data Loss)
        data: asset,

        // Extended Fields
        thumbnail: asset.images?.[0],
        files: mapAssetFiles(asset),
        metadata: {
            serial_number: asset.serial_number,
            location: asset.location,
            value: asset.value,
            description: asset.description,
            purchaseDate: asset.purchaseDate,
            specs_computer: asset.specs_computer,
            symptoms: asset.symptoms,
        },
        relatedData: {
            linkedProjects: related?.linkedProjects || [],
            libraryItems: related?.libraryItems || [],
            manuals: asset.manuals || [],
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: asset.category || 'Asset',
            backgroundImage: asset.images?.[0], // Use first image as background
            statusStripe: getAssetColor(asset.status),
            statusGlow: asset.status === 'breakdown' || asset.status === 'broken',
            collapsible: true,

            metaGrid: [
                { label: 'Make', value: asset.make || '' },
                { label: 'Model', value: asset.model || '' },
                { label: 'Serial', value: asset.serial_number || '' }
            ].filter(i => !!i.value),

            ratings: [
                {
                    label: 'Health',
                    value: asset.status === 'active' ? 10 : (asset.status === 'broken' ? 2 : 6),
                    max: 10,
                    color: getAssetColor(asset.status)
                }
            ],

            externalLinks: asset.manuals?.map(m => ({ label: m.title, url: m.url }))
        }
    };
}

/**
 * Map asset files (images, manuals) to UniversalFile format
 */
function mapAssetFiles(asset: Asset): UniversalFile[] {
    const files: UniversalFile[] = [];

    // Add images
    asset.images?.forEach((url, index) => {
        files.push({
            id: `img-${index}`,
            name: `Image ${index + 1}`,
            type: 'image',
            url: url,
            thumbnailUrl: url,
        });
    });

    // Add manuals
    asset.manuals?.forEach((manual, index) => {
        files.push({
            id: `manual-${index}`,
            name: manual.title,
            type: 'document',
            url: manual.url,
        });
    });

    return files;
}

/**
 * Get icon based on asset category
 */
function getAssetIcon(category: string): string {
    switch (category.toLowerCase()) {
        case 'computer': return 'Monitor';
        case 'test equipment': return 'Activity';
        case 'power tools': return 'Zap';
        case 'hand tools': return 'Wrench';
        case 'audio': return 'Volume2';
        case 'camera': return 'Camera';
        default: return 'Box';
    }
}

/**
 * Get color based on asset status
 */
function getAssetColor(status: string): string {
    switch (status) {
        case 'active': return '#22c55e'; // green
        case 'maintenance': return '#f59e0b'; // amber
        case 'broken': return '#ef4444'; // red
        case 'retired': return '#6b7280'; // gray
        default: return '#6b7280';
    }
}

/**
 * Batch convert multiple assets
 */
export function toUniversalAssetBatch(
    assets: Asset[]
): UniversalEntity<Asset>[] {
    return assets.map(asset => toUniversalAsset(asset));
}
