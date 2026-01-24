/**
 * Relationship Adapter
 * Converts entity relationships to UniversalEntity format.
 * First-class representation of relationships between any entities.
 */

import type { UniversalEntity } from '../types';

// ============================================================================
// RELATIONSHIP SCHEMA
// ============================================================================

export interface RelationshipEntry {
    id: number;
    /** Source entity type */
    source_type: string;
    /** Source entity ID */
    source_id: number;
    /** Source entity title (for display) */
    source_title?: string;
    /** Target entity type */
    target_type: string;
    /** Target entity ID */
    target_id: number;
    /** Target entity title (for display) */
    target_title?: string;
    /** Relationship type */
    relationship: 'blocks' | 'depends_on' | 'related' | 'parent' | 'child' | 'supports' | 'references' | 'custom';
    /** Custom relationship label */
    custom_label?: string;
    /** Strength/weight of relationship (1-10) */
    strength?: number;
    /** Is this relationship bidirectional */
    bidirectional?: boolean;
    /** Additional metadata */
    metadata?: Record<string, any>;
    /** Timestamp */
    created_at: Date;
}

// ============================================================================
// RELATIONSHIP CONFIG
// ============================================================================

const RELATIONSHIP_CONFIG: Record<string, { color: string; icon: string; verb: string; hex: string }> = {
    'blocks': { color: 'text-red-500', icon: 'Ban', verb: 'blocks', hex: '#ef4444' },
    'depends_on': { color: 'text-orange-500', icon: 'ArrowRight', verb: 'depends on', hex: '#f97316' },
    'related': { color: 'text-blue-500', icon: 'Link', verb: 'related to', hex: '#3b82f6' },
    'parent': { color: 'text-purple-500', icon: 'FolderUp', verb: 'parent of', hex: '#a855f7' },
    'child': { color: 'text-purple-400', icon: 'FolderDown', verb: 'child of', hex: '#c084fc' },
    'supports': { color: 'text-green-500', icon: 'HeartHandshake', verb: 'supports', hex: '#22c55e' },
    'references': { color: 'text-cyan-500', icon: 'FileText', verb: 'references', hex: '#06b6d4' },
    'custom': { color: 'text-gray-400', icon: 'Link2', verb: 'linked to', hex: '#9ca3af' },
};

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalRelationship(rel: RelationshipEntry): UniversalEntity<RelationshipEntry> {
    const config = RELATIONSHIP_CONFIG[rel.relationship] || RELATIONSHIP_CONFIG['custom'];
    const verb = rel.custom_label || config.verb;

    const sourceLabel = rel.source_title || `${rel.source_type}#${rel.source_id}`;
    const targetLabel = rel.target_title || `${rel.target_type}#${rel.target_id}`;

    return {
        urn: `relationship:${rel.id}`,
        id: rel.id,
        type: 'relationship',
        title: `${sourceLabel} ${verb} ${targetLabel}`,
        subtitle: `${rel.source_type} → ${rel.target_type}`,
        icon: config.icon,
        color: config.color,
        status: rel.relationship,
        createdAt: rel.created_at,
        data: rel,
        metadata: {
            sourceType: rel.source_type,
            sourceId: rel.source_id,
            targetType: rel.target_type,
            targetId: rel.target_id,
            relationship: rel.relationship,
            bidirectional: rel.bidirectional,
            strength: rel.strength,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Relationship',
            statusStripe: config.hex,
            statusGlow: rel.relationship === 'blocks',
            collapsible: true, // Collapsible to see full metadata if needed

            metaGrid: [
                { label: 'Source', value: sourceLabel },
                { label: 'Rel', value: verb },
                { label: 'Target', value: targetLabel }
            ],

            ratings: rel.strength ? [
                { label: 'Strength', value: rel.strength, max: 10, color: config.hex }
            ] : undefined
        }
    };
}

export function toUniversalRelationshipBatch(relationships: RelationshipEntry[]): UniversalEntity<RelationshipEntry>[] {
    return relationships.map(toUniversalRelationship);
}

export { RELATIONSHIP_CONFIG };
