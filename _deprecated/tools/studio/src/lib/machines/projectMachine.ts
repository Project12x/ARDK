/**
 * XState Machine Definitions - Project Status
 * 
 * @module lib/machines/projectMachine
 * @description
 * XState v5 machine for project status transitions.
 * Provides formal state machine with guards, actions, and devtools support.
 * 
 * States: planning → active → on_hold/completed → archived
 */
import { createMachine, assign } from 'xstate';

// ============================================================================
// Types
// ============================================================================

export interface ProjectContext {
    projectId: number;
    previousStatus?: string;
    transitionCount: number;
}

export type ProjectEvent =
    | { type: 'START' }
    | { type: 'PAUSE' }
    | { type: 'RESUME' }
    | { type: 'COMPLETE' }
    | { type: 'REOPEN' }
    | { type: 'ARCHIVE' }
    | { type: 'RESTORE' };

// ============================================================================
// Machine Definition
// ============================================================================

export const projectStatusMachine = createMachine({
    id: 'projectStatus',
    initial: 'planning',
    context: {
        projectId: 0,
        previousStatus: undefined,
        transitionCount: 0,
    } as ProjectContext,
    states: {
        planning: {
            meta: { color: '#f59e0b', label: 'Planning', icon: 'Lightbulb' },
            on: {
                START: {
                    target: 'active',
                    actions: assign({
                        previousStatus: 'planning',
                        transitionCount: ({ context }) => context.transitionCount + 1,
                    }),
                },
                ARCHIVE: 'archived',
            },
        },
        active: {
            meta: { color: '#10b981', label: 'Active', icon: 'Play' },
            on: {
                PAUSE: {
                    target: 'on_hold',
                    actions: assign({
                        previousStatus: 'active',
                        transitionCount: ({ context }) => context.transitionCount + 1,
                    }),
                },
                COMPLETE: {
                    target: 'completed',
                    actions: assign({
                        previousStatus: 'active',
                        transitionCount: ({ context }) => context.transitionCount + 1,
                    }),
                },
                ARCHIVE: 'archived',
            },
        },
        on_hold: {
            meta: { color: '#6b7280', label: 'On Hold', icon: 'Pause' },
            on: {
                RESUME: {
                    target: 'active',
                    actions: assign({
                        previousStatus: 'on_hold',
                        transitionCount: ({ context }) => context.transitionCount + 1,
                    }),
                },
                ARCHIVE: 'archived',
            },
        },
        completed: {
            meta: { color: '#3b82f6', label: 'Completed', icon: 'CheckCircle' },
            on: {
                REOPEN: {
                    target: 'active',
                    actions: assign({
                        previousStatus: 'completed',
                        transitionCount: ({ context }) => context.transitionCount + 1,
                    }),
                },
                ARCHIVE: 'archived',
            },
        },
        archived: {
            meta: { color: '#374151', label: 'Archived', icon: 'Archive' },
            on: {
                RESTORE: {
                    target: 'planning',
                    actions: assign({
                        previousStatus: 'archived',
                        transitionCount: ({ context }) => context.transitionCount + 1,
                    }),
                },
            },
        },
    },
});

export type ProjectStatusMachine = typeof projectStatusMachine;
