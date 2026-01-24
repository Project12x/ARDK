/**
 * ReminderEntityAdapter
 * Transforms raw Reminder objects into UniversalEntity<Reminder>
 */

import type { Reminder } from '../../db';
import type { UniversalEntity } from '../types';

export function toUniversalReminder(reminder: Reminder): UniversalEntity<Reminder> {
    return {
        urn: `reminder:${reminder.id}`,
        id: reminder.id!,
        type: 'reminder',

        title: reminder.content,
        subtitle: reminder.is_completed ? '✓ Completed' : `Priority ${reminder.priority}`,
        icon: reminder.is_completed ? 'CheckCircle' : 'Bell',
        color: reminder.is_completed ? '#22c55e' : getPriorityColor(reminder.priority),

        status: reminder.is_completed ? 'completed' : 'pending',
        tags: [],
        createdAt: reminder.created_at,
        updatedAt: undefined,

        data: reminder,

        metadata: {
            priority: reminder.priority,
            is_completed: reminder.is_completed,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Reminder',
            statusStripe: reminder.is_completed ? '#22c55e' : getPriorityColor(reminder.priority),
            statusGlow: !reminder.is_completed && reminder.priority >= 3,
            collapsible: false,

            metaGrid: [
                { label: 'Priority', value: reminder.priority },
                { label: 'Created', value: new Date(reminder.created_at).toLocaleDateString() }
            ],

            nextAction: !reminder.is_completed ? {
                label: 'Complete',
                icon: undefined // CheckCircle default
            } : undefined
        }
    };
}

function getPriorityColor(priority: number): string {
    if (priority >= 4) return '#ef4444'; // red
    if (priority >= 3) return '#f59e0b'; // amber
    if (priority >= 2) return '#3b82f6'; // blue
    return '#6b7280'; // gray
}

export function toUniversalReminderBatch(reminders: Reminder[]): UniversalEntity<Reminder>[] {
    return reminders.map(reminder => toUniversalReminder(reminder));
}
