/**
 * EntityLinkAdapter
 * Transforms raw EntityLink objects into UniversalEntity<EntityLink>
 * Used for representing relationships between entities
 */

import type { EntityLink } from '../../db';
import type { UniversalEntity } from '../types';

const RELATIONSHIP_CONFIG: Record<string, { icon: string; color: string; label: string }> = {
    'blocks': { icon: 'Ban', color: '#ef4444', label: 'Blocks' },
    'blocked-by': { icon: 'Lock', color: '#f59e0b', label: 'Blocked By' },
    'depends-on': { icon: 'ArrowDownToLine', color: '#3b82f6', label: 'Depends On' },
    'related': { icon: 'Link', color: '#8b5cf6', label: 'Related' },
    'child-of': { icon: 'GitBranch', color: '#06b6d4', label: 'Child Of' },
    'parent-of': { icon: 'GitMerge', color: '#10b981', label: 'Parent Of' },
};

export function toUniversalEntityLink(link: EntityLink): UniversalEntity<EntityLink> {
    const config = RELATIONSHIP_CONFIG[link.relationship] || RELATIONSHIP_CONFIG.related;

    return {
        urn: `entity-link:${link.id}`,
        id: link.id!,
        type: 'link',

        title: `${link.source_type}:${link.source_id} → ${link.target_type}:${link.target_id}`,
        subtitle: config.label,
        icon: config.icon,
        color: config.color,

        status: link.relationship,
        tags: [],
        createdAt: link.created_at,
        updatedAt: undefined,

        data: link,

        metadata: {
            source_type: link.source_type,
            source_id: link.source_id,
            target_type: link.target_type,
            target_id: link.target_id,
            relationship: link.relationship,
            ...link.metadata,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Link',
            statusStripe: config.color,
            statusGlow: link.relationship === 'blocks' || link.relationship === 'blocked-by',
            collapsible: true, // Collapsible content

            metaGrid: [
                { label: 'Source', value: link.source_type },
                { label: 'Relation', value: config.label },
                { label: 'Target', value: link.target_type }
            ],
        }
    };
}

export function toUniversalEntityLinkBatch(links: EntityLink[]): UniversalEntity<EntityLink>[] {
    return links.map(link => toUniversalEntityLink(link));
}
