/**
 * XState Machine Definitions - Sync Status
 * 
 * @module lib/machines/syncMachine
 * @description
 * XState v5 machine for sync/offline status.
 * Used for tracking data synchronization state.
 * 
 * States: idle → syncing → synced/error
 */
import { createMachine, assign } from 'xstate';

// ============================================================================
// Types
// ============================================================================

export interface SyncContext {
    lastSyncAt?: Date;
    lastError?: string;
    retryCount: number;
    pendingChanges: number;
}

export type SyncEvent =
    | { type: 'SYNC' }
    | { type: 'SYNC_SUCCESS'; timestamp: Date }
    | { type: 'SYNC_ERROR'; error: string }
    | { type: 'RETRY' }
    | { type: 'RESET' }
    | { type: 'QUEUE_CHANGE' }
    | { type: 'CLEAR_QUEUE' };

// ============================================================================
// Machine Definition
// ============================================================================

export const syncStatusMachine = createMachine({
    id: 'syncStatus',
    initial: 'idle',
    context: {
        lastSyncAt: undefined,
        lastError: undefined,
        retryCount: 0,
        pendingChanges: 0,
    } as SyncContext,
    states: {
        idle: {
            meta: { color: '#6b7280', label: 'Idle', icon: 'Cloud' },
            on: {
                SYNC: 'syncing',
                QUEUE_CHANGE: {
                    target: 'idle',
                    actions: assign({
                        pendingChanges: ({ context }) => context.pendingChanges + 1,
                    }),
                },
            },
        },
        syncing: {
            meta: { color: '#f59e0b', label: 'Syncing', icon: 'RefreshCw' },
            on: {
                SYNC_SUCCESS: {
                    target: 'synced',
                    actions: assign({
                        lastSyncAt: ({ event }) => event.timestamp,
                        lastError: undefined,
                        retryCount: 0,
                        pendingChanges: 0,
                    }),
                },
                SYNC_ERROR: {
                    target: 'error',
                    actions: assign({
                        lastError: ({ event }) => event.error,
                        retryCount: ({ context }) => context.retryCount + 1,
                    }),
                },
            },
        },
        synced: {
            meta: { color: '#10b981', label: 'Synced', icon: 'CheckCircle' },
            on: {
                QUEUE_CHANGE: {
                    target: 'idle',
                    actions: assign({
                        pendingChanges: ({ context }) => context.pendingChanges + 1,
                    }),
                },
                SYNC: 'syncing',
            },
        },
        error: {
            meta: { color: '#ef4444', label: 'Error', icon: 'AlertCircle' },
            on: {
                RETRY: 'syncing',
                RESET: {
                    target: 'idle',
                    actions: assign({
                        lastError: undefined,
                        retryCount: 0,
                    }),
                },
            },
        },
    },
});

export type SyncStatusMachine = typeof syncStatusMachine;
