/**
 * Comment Adapter
 * Converts comments/notes attached to entities to UniversalEntity format.
 * Comments can be attached to any entity type for discussion and annotations.
 */

import type { UniversalEntity } from '../types';

// ============================================================================
// COMMENT SCHEMA
// ============================================================================

export interface CommentEntry {
    id: number;
    /** Entity type this comment is attached to */
    parent_type: string;
    /** ID of the parent entity */
    parent_id: number;
    /** Comment content (markdown supported) */
    content: string;
    /** Author of the comment */
    author?: string;
    /** Is this comment pinned/important */
    is_pinned?: boolean;
    /** Is this a reply to another comment */
    reply_to_id?: number;
    /** Reactions (emoji counts) */
    reactions?: Record<string, number>;
    /** Timestamp */
    created_at: Date;
    updated_at?: Date;
}

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalComment(comment: CommentEntry): UniversalEntity<CommentEntry> {
    // Truncate content for subtitle
    const truncatedContent = comment.content.length > 80
        ? comment.content.substring(0, 80) + '...'
        : comment.content;

    return {
        urn: `comment:${comment.id}`,
        id: comment.id,
        type: 'comment',
        title: comment.author || 'Comment',
        subtitle: truncatedContent,
        icon: 'MessageSquare',
        color: comment.is_pinned ? 'text-yellow-500' : 'text-gray-400',
        status: comment.is_pinned ? 'pinned' : 'default',
        createdAt: comment.created_at,
        updatedAt: comment.updated_at,
        data: comment,
        metadata: {
            parentType: comment.parent_type,
            parentId: comment.parent_id,
            author: comment.author,
            isPinned: comment.is_pinned,
            isReply: !!comment.reply_to_id,
            reactionCount: comment.reactions
                ? Object.values(comment.reactions).reduce((a, b) => a + b, 0)
                : 0,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Comment',
            statusStripe: comment.is_pinned ? '#eab308' : '#9ca3af',
            statusGlow: comment.is_pinned,
            collapsible: true,
            defaultCollapsed: false, // Comments usually better expanded unless very long

            metaGrid: [
                { label: 'Author', value: comment.author || 'Anonymous' },
                { label: 'Date', value: new Date(comment.created_at).toLocaleDateString() },
                { label: 'Replies', value: comment.reactions ? Object.values(comment.reactions).reduce((a, b) => a + b, 0) : 0 }
            ].filter(i => i.label !== 'Replies' || i.value as number > 0),
        }
    };
}

export function toUniversalCommentBatch(comments: CommentEntry[]): UniversalEntity<CommentEntry>[] {
    return comments.map(toUniversalComment);
}
