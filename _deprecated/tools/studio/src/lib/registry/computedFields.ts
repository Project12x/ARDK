/**
 * Computed Fields - Derived Entity Values
 * 
 * @module lib/registry/computedFields
 * @description
 * Computes derived values from entity data and related records.
 * For example: progress % from task counts, overdue status from deadlines.
 * 
 * ## Why Use This?
 * - **DRY**: Calculate once, use everywhere
 * - **Consistency**: Same formula across all views
 * - **Performance**: Can be cached (future enhancement)
 * - **Declarative**: Just specify what data is needed
 * 
 * ## Usage Examples
 * ```typescript
 * // Compute a single field
 * const progress = computeField('progress', project, { tasks });
 * 
 * // Compute multiple fields
 * const computed = computeAllFields(['progress', 'isOverdue'], project, { tasks });
 * ```
 * 
 * ## Adding a New Computed Field
 * Add to COMPUTED_FIELDS with:
 * - `id`: Unique field identifier
 * - `requires`: Array of related data keys needed
 * - `compute`: Function that returns the computed value
 * 
 * @see ENTITY_REGISTRY.computedFields for entity field references
 */

// ============================================================================
// Type Definitions
// ============================================================================

export interface ComputedFieldDefinition {
    id: string;
    requires: string[]; // Related data needed (e.g., ['tasks', 'files'])
    compute: (entity: Record<string, unknown>, related?: Record<string, unknown[]>) => unknown;
    cache?: boolean; // Whether to cache the result
}

// ============================================================================
// Computed Fields Registry (To be populated in Phase 11C)
// ============================================================================

export const COMPUTED_FIELDS: Record<string, ComputedFieldDefinition> = {
    progress: {
        id: 'progress',
        requires: ['tasks'],
        compute: (entity, related) => {
            const tasks = related?.tasks ?? [];
            if (!tasks.length) return 0;

            const completed = tasks.filter((t: Record<string, unknown>) =>
                t.status === 'completed' || t.status === 'done'
            ).length;

            return Math.round((completed / tasks.length) * 100);
        },
    },

    isOverdue: {
        id: 'isOverdue',
        requires: [],
        compute: (entity) => {
            const deadline = entity.target_completion_date ?? entity.due_date ?? entity.deadline;
            if (!deadline) return false;
            return new Date(deadline as string) < new Date();
        },
    },

    daysUntilDeadline: {
        id: 'daysUntilDeadline',
        requires: [],
        compute: (entity) => {
            const deadline = entity.target_completion_date ?? entity.due_date ?? entity.deadline;
            if (!deadline) return null;

            const diff = new Date(deadline as string).getTime() - Date.now();
            return Math.ceil(diff / (1000 * 60 * 60 * 24));
        },
    },

    nextTask: {
        id: 'nextTask',
        requires: ['tasks'],
        compute: (entity, related) => {
            const tasks = related?.tasks ?? [];
            return tasks.find((t: Record<string, unknown>) =>
                t.status !== 'completed' && t.status !== 'done'
            );
        },
    },

    taskCount: {
        id: 'taskCount',
        requires: ['tasks'],
        compute: (entity, related) => {
            return related?.tasks?.length ?? 0;
        },
    },

    completedTaskCount: {
        id: 'completedTaskCount',
        requires: ['tasks'],
        compute: (entity, related) => {
            const tasks = related?.tasks ?? [];
            return tasks.filter((t: Record<string, unknown>) =>
                t.status === 'completed' || t.status === 'done'
            ).length;
        },
    },
};

// ============================================================================
// Helper Functions
// ============================================================================

export function computeField(
    fieldId: string,
    entity: Record<string, unknown>,
    related?: Record<string, unknown[]>
): unknown {
    const field = COMPUTED_FIELDS[fieldId];
    if (!field) {
        console.warn(`[ComputedFields] Unknown field: ${fieldId}`);
        return undefined;
    }

    return field.compute(entity, related);
}

export function computeAllFields(
    fieldIds: string[],
    entity: Record<string, unknown>,
    related?: Record<string, unknown[]>
): Record<string, unknown> {
    const result: Record<string, unknown> = {};

    for (const fieldId of fieldIds) {
        result[fieldId] = computeField(fieldId, entity, related);
    }

    return result;
}
