/**
 * GlobalNoteEntityAdapter
 * Transforms raw GlobalNote objects into UniversalEntity<GlobalNote>
 */

import type { GlobalNote } from '../../db';
import type { UniversalEntity } from '../types';

export function toUniversalGlobalNote(note: GlobalNote): UniversalEntity<GlobalNote> {
    return {
        urn: `global-note:${note.id}`,
        id: note.id!,
        type: 'note',

        title: note.title,
        subtitle: note.category ? `📁 ${note.category}` : 'General',
        icon: note.pinned ? 'Pin' : 'StickyNote',
        color: note.pinned ? '#f59e0b' : '#6b7280',

        status: note.pinned ? 'pinned' : 'normal',
        tags: [],
        createdAt: note.created_at,
        updatedAt: note.updated_at,

        data: note,

        metadata: {
            pinned: note.pinned,
            content_preview: note.content?.substring(0, 100),
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Note',
            statusStripe: note.pinned ? '#f59e0b' : '#6b7280',
            statusGlow: note.pinned,
            collapsible: true, // Collapsible content
            defaultCollapsed: false,

            metaGrid: [
                { label: 'Category', value: note.category || 'General' },
                { label: 'Updated', value: note.updated_at ? new Date(note.updated_at).toLocaleDateString() : 'Never' }
            ],
        }
    };
}

export function toUniversalGlobalNoteBatch(notes: GlobalNote[]): UniversalEntity<GlobalNote>[] {
    return notes.map(note => toUniversalGlobalNote(note));
}
