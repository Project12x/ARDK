/**
 * XState Machine Definitions - Purchase Status
 * 
 * @module lib/machines/purchaseMachine
 * @description
 * XState v5 machine for purchase/wishlist status transitions.
 * 
 * States: wishlist → considering → approved → ordered → received/returned
 */
import { createMachine, assign } from 'xstate';

// ============================================================================
// Types
// ============================================================================

export interface PurchaseContext {
    purchaseId: number;
    previousStatus?: string;
    orderedAt?: Date;
    receivedAt?: Date;
}

export type PurchaseEvent =
    | { type: 'CONSIDER' }
    | { type: 'APPROVE' }
    | { type: 'REJECT' }
    | { type: 'DEFER' }
    | { type: 'ORDER' }
    | { type: 'RECEIVE' }
    | { type: 'RETURN' }
    | { type: 'CANCEL' }
    | { type: 'REORDER' }
    | { type: 'REMOVE' }
    | { type: 'RESTORE' };

// ============================================================================
// Machine Definition
// ============================================================================

export const purchaseStatusMachine = createMachine({
    id: 'purchaseStatus',
    initial: 'wishlist',
    context: {
        purchaseId: 0,
        previousStatus: undefined,
        orderedAt: undefined,
        receivedAt: undefined,
    } as PurchaseContext,
    states: {
        wishlist: {
            meta: { color: '#8b5cf6', label: 'Wishlist', icon: 'Star' },
            on: {
                CONSIDER: { target: 'considering', actions: assign({ previousStatus: 'wishlist' }) },
                APPROVE: { target: 'approved', actions: assign({ previousStatus: 'wishlist' }) },
                REMOVE: { target: 'removed', actions: assign({ previousStatus: 'wishlist' }) },
            },
        },
        considering: {
            meta: { color: '#f59e0b', label: 'Considering', icon: 'HelpCircle' },
            on: {
                APPROVE: { target: 'approved', actions: assign({ previousStatus: 'considering' }) },
                REJECT: { target: 'removed', actions: assign({ previousStatus: 'considering' }) },
                DEFER: { target: 'wishlist', actions: assign({ previousStatus: 'considering' }) },
            },
        },
        approved: {
            meta: { color: '#10b981', label: 'Approved', icon: 'ThumbsUp' },
            on: {
                ORDER: {
                    target: 'ordered',
                    actions: assign({
                        previousStatus: 'approved',
                        orderedAt: () => new Date(),
                    }),
                },
                CANCEL: { target: 'removed', actions: assign({ previousStatus: 'approved' }) },
            },
        },
        ordered: {
            meta: { color: '#3b82f6', label: 'Ordered', icon: 'Truck' },
            on: {
                RECEIVE: {
                    target: 'received',
                    actions: assign({
                        previousStatus: 'ordered',
                        receivedAt: () => new Date(),
                    }),
                },
                CANCEL: { target: 'removed', actions: assign({ previousStatus: 'ordered' }) },
            },
        },
        received: {
            meta: { color: '#10b981', label: 'Received', icon: 'PackageCheck' },
            on: {
                RETURN: { target: 'returned', actions: assign({ previousStatus: 'received' }) },
            },
        },
        returned: {
            meta: { color: '#ef4444', label: 'Returned', icon: 'RotateCcw' },
            on: {
                REORDER: {
                    target: 'ordered',
                    actions: assign({
                        previousStatus: 'returned',
                        orderedAt: () => new Date(),
                        receivedAt: undefined,
                    }),
                },
            },
        },
        removed: {
            meta: { color: '#374151', label: 'Removed', icon: 'Trash2' },
            on: {
                RESTORE: { target: 'wishlist', actions: assign({ previousStatus: 'removed' }) },
            },
        },
    },
});

export type PurchaseStatusMachine = typeof purchaseStatusMachine;
