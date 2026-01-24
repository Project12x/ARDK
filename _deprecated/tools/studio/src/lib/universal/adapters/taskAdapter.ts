/**
 * TaskEntityAdapter
 * Transforms raw ProjectTask objects into UniversalEntity<ProjectTask>
 * Zero data loss - original object preserved in data payload
 */

import type { ProjectTask } from '../../db';
import type { UniversalEntity } from '../types';

export interface TaskRelatedData {
    projectTitle?: string;
    upstreamTasks?: ProjectTask[];
}

/**
 * Convert ProjectTask to UniversalEntity with full fidelity
 */
export function toUniversalTask(
    task: ProjectTask,
    related?: TaskRelatedData
): UniversalEntity<ProjectTask> {
    return {
        // Core Identity
        urn: `task:${task.id}`,
        id: task.id!,
        type: 'task',

        // Presentation
        title: task.title,
        subtitle: related?.projectTitle || (task.phase ? `Phase: ${task.phase}` : undefined),
        icon: getTaskIcon(task),
        color: getTaskColor(task),

        // Context
        status: task.status,
        tags: task.caution_flags || [],
        createdAt: undefined,
        updatedAt: undefined,

        // Full Payload (Zero Data Loss)
        data: task,

        // Extended Fields
        progress: getTaskProgress(task),
        metadata: {
            priority: task.priority,
            phase: task.phase,
            estimated_time: task.estimated_time,
            calendar_duration: task.calendar_duration,
            blockers: task.blockers,
            materials_needed: task.materials_needed,
            energy_level: task.energy_level,
            sensory_load: task.sensory_load,
            scheduled_date: task.scheduled_date,
            scheduled_time: task.scheduled_time,
            is_high_priority: task.is_high_priority,
            recurrence: task.recurrence,
            goal_id: task.goal_id,
        },
        relatedData: {
            upstreamTasks: related?.upstreamTasks || [],
        },
        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Task',
            statusStripe: getTaskColor(task),
            statusGlow: task.status === 'in-progress',
            collapsible: true,
            defaultCollapsed: task.status === 'completed',
            metaGrid: [
                { label: 'Due', value: task.scheduled_date ? new Date(task.scheduled_date).toLocaleDateString() : 'No Date' },
                { label: 'Phase', value: task.phase || 'N/A' },
                { label: 'Priority', value: task.priority || 'Normal' }
            ].filter(i => i.value !== 'N/A' && i.value !== 'No Date'),
            ratings: [
                { label: 'Energy', value: task.energy_level || 0, max: 10, color: '#f59e0b' }
            ]
        }
    };
}

/**
 * Get icon based on task status
 */
function getTaskIcon(task: ProjectTask): string {
    switch (task.status) {
        case 'completed': return 'CheckCircle';
        case 'in-progress': return 'PlayCircle';
        case 'blocked': return 'AlertCircle';
        default: return 'Circle';
    }
}

/**
 * Get color based on priority and status
 */
function getTaskColor(task: ProjectTask): string {
    if (task.status === 'blocked') return '#ef4444'; // red
    if (task.status === 'completed') return '#22c55e'; // green
    if (task.is_high_priority || task.priority >= 4) return '#f59e0b'; // amber
    if (task.status === 'in-progress') return '#3b82f6'; // blue
    return '#6b7280'; // gray
}

/**
 * Get progress percentage
 */
function getTaskProgress(task: ProjectTask): number {
    switch (task.status) {
        case 'completed': return 100;
        case 'in-progress': return 50;
        case 'blocked': return 25;
        default: return 0;
    }
}

/**
 * Batch convert multiple tasks
 */
export function toUniversalTaskBatch(
    tasks: ProjectTask[],
    projectTitle?: string
): UniversalEntity<ProjectTask>[] {
    return tasks.map(task => toUniversalTask(task, { projectTitle }));
}
