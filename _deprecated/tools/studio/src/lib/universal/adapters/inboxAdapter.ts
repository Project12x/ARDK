/**
 * InboxEntityAdapter
 * Transforms raw InboxItem objects into UniversalEntity<InboxItem>
 */

import type { InboxItem } from '../../db';
import type { UniversalEntity } from '../types';

/**
 * Convert InboxItem to UniversalEntity with full fidelity
 */
export function toUniversalInbox(
    item: InboxItem
): UniversalEntity<InboxItem> {
    return {
        // Core Identity
        urn: `inbox:${item.id}`,
        id: item.id!,
        type: 'inbox',

        // Presentation
        title: item.content?.substring(0, 100) || 'Untitled Item',
        subtitle: item.suggested_action || item.type,
        icon: getInboxIcon(item.type),
        color: item.triaged_at ? '#22c55e' : '#f59e0b',

        // Context
        status: item.triaged_at ? 'triaged' : 'pending',
        tags: [],
        createdAt: item.created_at,
        updatedAt: undefined,

        // Full Payload
        data: item,

        // Extended
        metadata: {
            type: item.type,
            suggested_action: item.suggested_action,
            triaged_to: item.triaged_to,
            triaged_at: item.triaged_at,
            ai_analysis: item.ai_analysis,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Inbox Item',
            statusStripe: item.triaged_at ? '#22c55e' : '#f59e0b',
            statusGlow: !item.triaged_at, // Glow if pending
            collapsible: false,

            metaGrid: [
                { label: 'Type', value: item.type },
                { label: 'Action', value: item.suggested_action || 'Review' }
            ],

            ratings: item.ai_analysis?.priority ? [
                { label: 'AI Priority', value: item.ai_analysis.priority, max: 10, color: '#8b5cf6' }
            ] : undefined
        }
    };
}

function getInboxIcon(type: string): string {
    switch (type) {
        case 'note': return 'StickyNote';
        case 'link': return 'Link';
        case 'idea': return 'Lightbulb';
        case 'task': return 'CheckSquare';
        case 'file': return 'File';
        default: return 'Inbox';
    }
}

export function toUniversalInboxBatch(items: InboxItem[]): UniversalEntity<InboxItem>[] {
    return items.map(item => toUniversalInbox(item));
}
