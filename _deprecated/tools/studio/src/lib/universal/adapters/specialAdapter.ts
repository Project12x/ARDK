/**
 * UniversalSpecial Adapter
 * Handles bespoke, legacy, or unknown entity types that need
 * to fit into the Universal system without a dedicated adapter.
 */

import type { UniversalEntity } from '../types';

export interface SpecialEntityConfig {
    type: string;
    titleKey?: string;
    subtitleKey?: string;
    icon?: string;
    color?: string;
    idKey?: string;
}

export function toUniversalSpecial(
    data: any,
    config: SpecialEntityConfig
): UniversalEntity<any> {
    const id = data[config.idKey || 'id'] || Math.random();
    const title = data[config.titleKey || 'title'] || data.name || data.label || 'Unknown Entity';
    const subtitle = config.subtitleKey ? data[config.subtitleKey] : undefined;

    return {
        urn: `special:${config.type}:${id}`,
        id: id,
        type: config.type,

        title: title,
        subtitle: subtitle,
        icon: config.icon || 'Box',
        color: config.color || '#6b7280', // gray default

        status: data.status || 'active',
        tags: data.tags || [],
        createdAt: data.created_at || data.date || new Date(),
        updatedAt: data.updated_at,

        data: data,

        metadata: {
            isSpecial: true,
            originalType: config.type
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: config.type.charAt(0).toUpperCase() + config.type.slice(1),
            statusStripe: config.color || '#6b7280',
            statusGlow: false,
            collapsible: true,

            metaGrid: Object.entries(data)
                .filter(([k, v]) =>
                    typeof v === 'string' ||
                    typeof v === 'number' ||
                    typeof v === 'boolean'
                )
                .slice(0, 3) // Show first 3 primitive fields
                .map(([key, value]) => ({
                    label: key.slice(0, 5).toUpperCase(),
                    value: String(value)
                }))
        }
    };
}

export function toUniversalSpecialBatch(
    items: any[],
    config: SpecialEntityConfig
): UniversalEntity<any>[] {
    return items.map(item => toUniversalSpecial(item, config));
}
