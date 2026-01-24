/**
 * XState Machine Definitions - Task Status
 * 
 * @module lib/machines/taskMachine
 * @description
 * XState v5 machine for task status transitions.
 * 
 * States: todo → in_progress → blocked/done
 */
import { createMachine, assign } from 'xstate';

// ============================================================================
// Types
// ============================================================================

export interface TaskContext {
    taskId: number;
    projectId?: number;
    previousStatus?: string;
    blockedReason?: string;
}

export type TaskEvent =
    | { type: 'START' }
    | { type: 'COMPLETE' }
    | { type: 'BLOCK'; reason?: string }
    | { type: 'UNBLOCK' }
    | { type: 'RESET' }
    | { type: 'REOPEN' };

// ============================================================================
// Machine Definition
// ============================================================================

export const taskStatusMachine = createMachine({
    id: 'taskStatus',
    initial: 'todo',
    context: {
        taskId: 0,
        projectId: undefined,
        previousStatus: undefined,
        blockedReason: undefined,
    } as TaskContext,
    states: {
        todo: {
            meta: { color: '#6b7280', label: 'To Do', icon: 'Circle' },
            on: {
                START: {
                    target: 'in_progress',
                    actions: assign({ previousStatus: 'todo' }),
                },
            },
        },
        in_progress: {
            meta: { color: '#f59e0b', label: 'In Progress', icon: 'Clock' },
            on: {
                COMPLETE: {
                    target: 'done',
                    actions: assign({ previousStatus: 'in_progress' }),
                },
                BLOCK: {
                    target: 'blocked',
                    actions: assign({
                        previousStatus: 'in_progress',
                        blockedReason: ({ event }) => event.reason,
                    }),
                },
                RESET: {
                    target: 'todo',
                    actions: assign({ previousStatus: 'in_progress' }),
                },
            },
        },
        blocked: {
            meta: { color: '#ef4444', label: 'Blocked', icon: 'AlertCircle' },
            on: {
                UNBLOCK: {
                    target: 'in_progress',
                    actions: assign({
                        previousStatus: 'blocked',
                        blockedReason: undefined,
                    }),
                },
                COMPLETE: {
                    target: 'done',
                    actions: assign({
                        previousStatus: 'blocked',
                        blockedReason: undefined,
                    }),
                },
            },
        },
        done: {
            meta: { color: '#10b981', label: 'Done', icon: 'CheckCircle' },
            on: {
                REOPEN: {
                    target: 'todo',
                    actions: assign({ previousStatus: 'done' }),
                },
            },
        },
    },
});

export type TaskStatusMachine = typeof taskStatusMachine;
