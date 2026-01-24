/**
 * GoalEntityAdapter
 * Transforms raw Goal objects into UniversalEntity<Goal>
 * Zero data loss - original object preserved in data payload
 */

import type { Goal } from '../../db';
import type { UniversalEntity } from '../types';

export interface GoalRelatedData {
    linkedProjects?: { id: number; title: string }[];
    linkedTasks?: { id: number; title: string }[];
    childGoals?: Goal[];
    parentGoal?: Goal;
}

/**
 * Convert Goal to UniversalEntity with full fidelity
 */
export function toUniversalGoal(
    goal: Goal,
    related?: GoalRelatedData
): UniversalEntity<Goal> {
    return {
        // Core Identity
        urn: `goal:${goal.id}`,
        id: goal.id!,
        type: 'goal',

        // Presentation
        title: goal.title,
        subtitle: getLevelLabel(goal.level),
        icon: goal.icon || getDefaultGoalIcon(goal.level),
        color: goal.label_color || getGoalColor(goal.status),

        // Context
        status: goal.status,
        tags: goal.tags || [],
        createdAt: goal.created_at,
        updatedAt: goal.updated_at,

        // Full Payload (Zero Data Loss)
        data: goal,

        // Extended Fields
        progress: goal.progress,
        thumbnail: undefined,
        metadata: {
            level: goal.level,
            parent_id: goal.parent_id,
            priority: goal.priority,
            target_date: goal.target_date,
            started_at: goal.started_at,
            achieved_at: goal.achieved_at,
            motivation: goal.motivation,
            success_criteria: goal.success_criteria,
            review_cadence: goal.review_cadence,
            notes: goal.notes,
            children_count: goal.children_count,
            flow_x: goal.flow_x,
            flow_y: goal.flow_y,
        },
        relatedData: {
            linkedProjects: related?.linkedProjects || [],
            linkedTasks: related?.linkedTasks || [],
            childGoals: related?.childGoals || [],
            parentGoal: related?.parentGoal ? [related.parentGoal] : [],
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: getLevelLabel(goal.level),
            statusStripe: getGoalColor(goal.status),
            statusGlow: goal.status === 'achieved',
            collapsible: true,

            metaGrid: [
                { label: 'Priority', value: goal.priority || 'Normal' },
                { label: 'Deadline', value: goal.target_date ? new Date(goal.target_date).toLocaleDateString() : 'None' },
                { label: 'Cadence', value: goal.review_cadence || 'Ad-hoc' }
            ].filter(i => i.value !== 'None' && i.value !== 'Ad-hoc'),

            ratings: [
                { label: 'Progress', value: goal.progress, max: 100, color: getGoalColor(goal.status) }
            ]
        }
    };
}

/**
 * Get level display label
 */
function getLevelLabel(level: string): string {
    switch (level) {
        case 'vision': return '🌟 Vision';
        case 'year': return '📅 Annual Goal';
        case 'quarter': return '📊 Quarterly Goal';
        case 'objective': return '🎯 Objective';
        default: return level;
    }
}

/**
 * Get default icon based on goal level
 */
function getDefaultGoalIcon(level: string): string {
    switch (level) {
        case 'vision': return 'Star';
        case 'year': return 'Calendar';
        case 'quarter': return 'BarChart2';
        case 'objective': return 'Target';
        default: return 'Circle';
    }
}

/**
 * Get color based on goal status
 */
function getGoalColor(status: string): string {
    switch (status) {
        case 'active': return '#3b82f6'; // blue
        case 'achieved': return '#22c55e'; // green
        case 'paused': return '#f59e0b'; // amber
        case 'abandoned': return '#6b7280'; // gray
        default: return '#6b7280';
    }
}

/**
 * Batch convert multiple goals
 */
export function toUniversalGoalBatch(
    goals: Goal[]
): UniversalEntity<Goal>[] {
    return goals.map(goal => toUniversalGoal(goal));
}
