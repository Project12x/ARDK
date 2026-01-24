/**
 * XState Machine Definitions - Goal Status
 * 
 * @module lib/machines/goalMachine
 * @description
 * XState v5 machine for goal status transitions.
 * 
 * States: not_started → working → paused/achieved/abandoned
 */
import { createMachine, assign } from 'xstate';

// ============================================================================
// Types
// ============================================================================

export interface GoalContext {
    goalId: number;
    previousStatus?: string;
    achievedAt?: Date;
}

export type GoalEvent =
    | { type: 'START' }
    | { type: 'ACHIEVE' }
    | { type: 'ABANDON' }
    | { type: 'PAUSE' }
    | { type: 'RESUME' }
    | { type: 'REOPEN' };

// ============================================================================
// Machine Definition
// ============================================================================

export const goalStatusMachine = createMachine({
    id: 'goalStatus',
    initial: 'not_started',
    context: {
        goalId: 0,
        previousStatus: undefined,
        achievedAt: undefined,
    } as GoalContext,
    states: {
        not_started: {
            meta: { color: '#6b7280', label: 'Not Started', icon: 'Circle' },
            on: {
                START: {
                    target: 'working',
                    actions: assign({ previousStatus: 'not_started' }),
                },
            },
        },
        working: {
            meta: { color: '#f59e0b', label: 'Working', icon: 'Target' },
            on: {
                ACHIEVE: {
                    target: 'achieved',
                    actions: assign({
                        previousStatus: 'working',
                        achievedAt: () => new Date(),
                    }),
                },
                ABANDON: {
                    target: 'abandoned',
                    actions: assign({ previousStatus: 'working' }),
                },
                PAUSE: {
                    target: 'paused',
                    actions: assign({ previousStatus: 'working' }),
                },
            },
        },
        paused: {
            meta: { color: '#6b7280', label: 'Paused', icon: 'Pause' },
            on: {
                RESUME: {
                    target: 'working',
                    actions: assign({ previousStatus: 'paused' }),
                },
                ABANDON: {
                    target: 'abandoned',
                    actions: assign({ previousStatus: 'paused' }),
                },
            },
        },
        achieved: {
            meta: { color: '#10b981', label: 'Achieved', icon: 'Trophy' },
            on: {
                REOPEN: {
                    target: 'working',
                    actions: assign({
                        previousStatus: 'achieved',
                        achievedAt: undefined,
                    }),
                },
            },
        },
        abandoned: {
            meta: { color: '#374151', label: 'Abandoned', icon: 'X' },
            on: {
                REOPEN: {
                    target: 'not_started',
                    actions: assign({ previousStatus: 'abandoned' }),
                },
            },
        },
    },
});

export type GoalStatusMachine = typeof goalStatusMachine;
