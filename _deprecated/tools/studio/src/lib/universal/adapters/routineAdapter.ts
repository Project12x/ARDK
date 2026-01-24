/**
 * RoutineEntityAdapter
 * Transforms raw Routine objects into UniversalEntity<Routine>
 */

import type { Routine } from '../../db';
import type { UniversalEntity } from '../types';

/**
 * Convert Routine to UniversalEntity with full fidelity
 */
export function toUniversalRoutine(
    routine: Routine
): UniversalEntity<Routine> {
    const isOverdue = routine.next_due && new Date(routine.next_due) < new Date();

    return {
        // Core Identity
        urn: `routine:${routine.id}`,
        id: routine.id!,
        type: 'routine',

        // Presentation
        title: routine.title,
        subtitle: `${routine.frequency}${routine.season ? ` (${routine.season})` : ''}`,
        icon: 'RefreshCw',
        color: isOverdue ? '#ef4444' : '#3b82f6',

        // Context
        status: isOverdue ? 'overdue' : 'scheduled',
        tags: routine.category ? [routine.category] : [],
        createdAt: routine.created_at,
        updatedAt: undefined,

        // Full Payload
        data: routine,

        // Extended
        metadata: {
            frequency: routine.frequency,
            season: routine.season,
            last_completed: routine.last_completed,
            next_due: routine.next_due,
            category: routine.category,
            google_event_id: routine.google_event_id,
            linked_project_ids: routine.linked_project_ids,
            linked_goal_ids: routine.linked_goal_ids,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Routine',
            statusStripe: isOverdue ? '#ef4444' : '#3b82f6',
            statusGlow: isOverdue,
            collapsible: true,

            metaGrid: [
                { label: 'Freq', value: routine.frequency || 'Ad-hoc' },
                { label: 'Next', value: routine.next_due ? new Date(routine.next_due).toLocaleDateString() : 'None' },
                { label: 'Season', value: routine.season || 'All' }
            ].filter(i => !!i.value && i.value !== 'None' && i.value !== 'All'),

            nextAction: isOverdue || new Date(routine.next_due || '') <= new Date() ? {
                label: 'Complete',
                icon: undefined, // Will default to Circle/Check
            } : undefined
        }
    };
}

export function toUniversalRoutineBatch(routines: Routine[]): UniversalEntity<Routine>[] {
    return routines.map(routine => toUniversalRoutine(routine));
}
