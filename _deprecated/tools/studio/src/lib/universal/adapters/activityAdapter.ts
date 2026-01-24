/**
 * Activity Adapter
 * Converts activity/timeline entries to UniversalEntity format.
 * Activities track changes, events, and history across all entity types.
 */

import type { UniversalEntity } from '../types';
import {
    Activity, Edit, Plus, Trash2, Link, CheckCircle,
    MessageSquare, Upload, Download, Settings, RefreshCw
} from 'lucide-react';

// ============================================================================
// ACTIVITY SCHEMA
// ============================================================================

export interface ActivityEntry {
    id: number;
    /** Type of activity */
    action: 'create' | 'update' | 'delete' | 'link' | 'complete' | 'comment' | 'upload' | 'download' | 'archive' | 'restore' | 'sync';
    /** Entity type that was acted upon */
    entity_type: string;
    /** ID of the entity */
    entity_id: number;
    /** Title of the entity at time of action */
    entity_title: string;
    /** User or system that performed the action */
    actor?: string;
    /** Additional context/changes */
    details?: Record<string, any>;
    /** Previous value (for updates) */
    old_value?: any;
    /** New value (for updates) */
    new_value?: any;
    /** Timestamp */
    created_at: Date;
}

// ============================================================================
// ACTION CONFIG
// ============================================================================

const ACTION_CONFIG: Record<string, { icon: typeof Activity; color: string; label: string; hex: string }> = {
    'create': { icon: Plus, color: 'text-green-500', label: 'Created', hex: '#22c55e' },
    'update': { icon: Edit, color: 'text-blue-500', label: 'Updated', hex: '#3b82f6' },
    'delete': { icon: Trash2, color: 'text-red-500', label: 'Deleted', hex: '#ef4444' },
    'link': { icon: Link, color: 'text-purple-500', label: 'Linked', hex: '#a855f7' },
    'complete': { icon: CheckCircle, color: 'text-green-500', label: 'Completed', hex: '#22c55e' },
    'comment': { icon: MessageSquare, color: 'text-yellow-500', label: 'Commented', hex: '#eab308' },
    'upload': { icon: Upload, color: 'text-cyan-500', label: 'Uploaded', hex: '#06b6d4' },
    'download': { icon: Download, color: 'text-cyan-500', label: 'Downloaded', hex: '#06b6d4' },
    'archive': { icon: Settings, color: 'text-gray-500', label: 'Archived', hex: '#6b7280' },
    'restore': { icon: RefreshCw, color: 'text-orange-500', label: 'Restored', hex: '#f97316' },
    'sync': { icon: RefreshCw, color: 'text-accent', label: 'Synced', hex: '#10b981' },
};

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalActivity(activity: ActivityEntry): UniversalEntity<ActivityEntry> {
    const config = ACTION_CONFIG[activity.action] || ACTION_CONFIG['update'];

    return {
        urn: `activity:${activity.id}`,
        id: activity.id,
        type: 'activity',
        title: `${config.label} ${activity.entity_title}`,
        subtitle: `${activity.entity_type} #${activity.entity_id}`,
        icon: config.icon.name || 'Activity',
        color: config.color,
        status: activity.action,
        createdAt: activity.created_at,
        data: activity,
        metadata: {
            action: activity.action,
            actor: activity.actor,
            entityType: activity.entity_type,
            entityId: activity.entity_id,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Activity',
            statusStripe: config.hex,
            statusGlow: false,
            collapsible: true,

            metaGrid: [
                { label: 'Action', value: config.label },
                { label: 'Actor', value: activity.actor || 'System' },
                { label: 'Entity', value: activity.entity_type }
            ]
        }
    };
}

export function toUniversalActivityBatch(activities: ActivityEntry[]): UniversalEntity<ActivityEntry>[] {
    return activities.map(toUniversalActivity);
}

export { ACTION_CONFIG as ACTIVITY_ACTION_CONFIG };
