/**
 * State Machines - Entity Status Transitions
 * 
 * @module lib/registry/stateMachines
 * @description
 * Defines valid status transitions for entities (e.g., todo → in_progress → done).
 * Inspired by XState but simplified for our needs with just states, events, and metadata.
 * 
 * ## Why Use This?
 * - **Valid Transitions**: Prevents invalid status changes
 * - **Consistent Styling**: Status colors/icons defined once
 * - **UI Generation**: Can auto-generate status dropdown options
 * - **Guard Rails**: `canTransition()` prevents bad state changes
 * - **Command Layer Integration (v8.1)**: `executeTransition()` uses Command Layer
 * 
 * ## Usage Examples
 * ```typescript
 * // Check if a transition is valid
 * if (canTransition('taskStatus', 'todo', 'START')) {
 *   // Transition allowed
 * }
 * 
 * // Get valid next events
 * const events = getValidEvents('taskStatus', 'in_progress');
 * // ['COMPLETE', 'BLOCK', 'RESET']
 * 
 * // Execute transition via Command Layer (v8.1)
 * await executeTransition('task', taskEntity, 'taskStatus', 'START');
 * ```
 * 
 * @see ENTITY_REGISTRY.stateMachine for entity state machine references
 */

import { UpdateEntityCommand } from '../commands';
import type { UniversalEntity } from '../universal/types';

// ============================================================================
// Type Definitions
// ============================================================================

export interface StateMetadata {
    color: string;
    icon?: string;
    label: string;
}

export interface StateTransitions {
    [event: string]: string; // event -> next state
}

export interface StateDefinition {
    on: StateTransitions;
    meta: StateMetadata;
}

export interface StateMachine {
    initial: string;
    states: Record<string, StateDefinition>;
}

// ============================================================================
// State Machine Registry (To be populated in Phase 11C)
// ============================================================================

export const STATE_MACHINES: Record<string, StateMachine> = {
    projectStatus: {
        initial: 'planning',
        states: {
            planning: {
                on: { START: 'active', ARCHIVE: 'archived' },
                meta: { color: '#f59e0b', label: 'Planning', icon: 'Lightbulb' },
            },
            active: {
                on: { PAUSE: 'on_hold', COMPLETE: 'completed', ARCHIVE: 'archived' },
                meta: { color: '#10b981', label: 'Active', icon: 'Play' },
            },
            on_hold: {
                on: { RESUME: 'active', ARCHIVE: 'archived' },
                meta: { color: '#6b7280', label: 'On Hold', icon: 'Pause' },
            },
            completed: {
                on: { REOPEN: 'active', ARCHIVE: 'archived' },
                meta: { color: '#3b82f6', label: 'Completed', icon: 'CheckCircle' },
            },
            archived: {
                on: { RESTORE: 'planning' },
                meta: { color: '#374151', label: 'Archived', icon: 'Archive' },
            },
        },
    },

    taskStatus: {
        initial: 'todo',
        states: {
            todo: {
                on: { START: 'in_progress' },
                meta: { color: '#6b7280', label: 'To Do', icon: 'Circle' },
            },
            in_progress: {
                on: { COMPLETE: 'done', BLOCK: 'blocked', RESET: 'todo' },
                meta: { color: '#f59e0b', label: 'In Progress', icon: 'Clock' },
            },
            blocked: {
                on: { UNBLOCK: 'in_progress', COMPLETE: 'done' },
                meta: { color: '#ef4444', label: 'Blocked', icon: 'AlertCircle' },
            },
            done: {
                on: { REOPEN: 'todo' },
                meta: { color: '#10b981', label: 'Done', icon: 'CheckCircle' },
            },
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Goal Status
    // ─────────────────────────────────────────────────────────────────────────
    goalStatus: {
        initial: 'not_started',
        states: {
            not_started: {
                on: { START: 'working' },
                meta: { color: '#6b7280', label: 'Not Started', icon: 'Circle' },
            },
            working: {
                on: { ACHIEVE: 'achieved', ABANDON: 'abandoned', PAUSE: 'paused' },
                meta: { color: '#f59e0b', label: 'Working', icon: 'Target' },
            },
            paused: {
                on: { RESUME: 'working', ABANDON: 'abandoned' },
                meta: { color: '#6b7280', label: 'Paused', icon: 'Pause' },
            },
            achieved: {
                on: { REOPEN: 'working' },
                meta: { color: '#10b981', label: 'Achieved', icon: 'Trophy' },
            },
            abandoned: {
                on: { REOPEN: 'not_started' },
                meta: { color: '#374151', label: 'Abandoned', icon: 'X' },
            },
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Purchase Status
    // ─────────────────────────────────────────────────────────────────────────
    purchaseStatus: {
        initial: 'wishlist',
        states: {
            wishlist: {
                on: { CONSIDER: 'considering', APPROVE: 'approved', REMOVE: 'removed' },
                meta: { color: '#8b5cf6', label: 'Wishlist', icon: 'Star' },
            },
            considering: {
                on: { APPROVE: 'approved', REJECT: 'removed', DEFER: 'wishlist' },
                meta: { color: '#f59e0b', label: 'Considering', icon: 'HelpCircle' },
            },
            approved: {
                on: { ORDER: 'ordered', CANCEL: 'removed' },
                meta: { color: '#10b981', label: 'Approved', icon: 'ThumbsUp' },
            },
            ordered: {
                on: { RECEIVE: 'received', CANCEL: 'removed' },
                meta: { color: '#3b82f6', label: 'Ordered', icon: 'Truck' },
            },
            received: {
                on: { RETURN: 'returned' },
                meta: { color: '#10b981', label: 'Received', icon: 'PackageCheck' },
            },
            returned: {
                on: { REORDER: 'ordered' },
                meta: { color: '#ef4444', label: 'Returned', icon: 'RotateCcw' },
            },
            removed: {
                on: { RESTORE: 'wishlist' },
                meta: { color: '#374151', label: 'Removed', icon: 'Trash2' },
            },
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Routine Status (for recurring tasks)
    // ─────────────────────────────────────────────────────────────────────────
    routineStatus: {
        initial: 'pending',
        states: {
            pending: {
                on: { COMPLETE: 'completed', SKIP: 'skipped' },
                meta: { color: '#f59e0b', label: 'Pending', icon: 'Clock' },
            },
            completed: {
                on: { RESET: 'pending' },
                meta: { color: '#10b981', label: 'Completed', icon: 'CheckCircle' },
            },
            skipped: {
                on: { RESET: 'pending' },
                meta: { color: '#6b7280', label: 'Skipped', icon: 'SkipForward' },
            },
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Song/Recording Status
    // ─────────────────────────────────────────────────────────────────────────
    songStatus: {
        initial: 'idea',
        states: {
            idea: {
                on: { START_WRITING: 'writing' },
                meta: { color: '#6b7280', label: 'Idea', icon: 'Lightbulb' },
            },
            writing: {
                on: { START_RECORDING: 'recording', ARCHIVE: 'archived' },
                meta: { color: '#f59e0b', label: 'Writing', icon: 'Pencil' },
            },
            recording: {
                on: { START_MIXING: 'mixing', ARCHIVE: 'archived' },
                meta: { color: '#3b82f6', label: 'Recording', icon: 'Mic' },
            },
            mixing: {
                on: { START_MASTERING: 'mastering', ARCHIVE: 'archived' },
                meta: { color: '#8b5cf6', label: 'Mixing', icon: 'Sliders' },
            },
            mastering: {
                on: { FINISH: 'finished', ARCHIVE: 'archived' },
                meta: { color: '#ec4899', label: 'Mastering', icon: 'Disc' },
            },
            finished: {
                on: { RELEASE: 'released', REOPEN: 'mastering' },
                meta: { color: '#10b981', label: 'Finished', icon: 'CheckCircle' },
            },
            released: {
                on: { ARCHIVE: 'archived' },
                meta: { color: '#10b981', label: 'Released', icon: 'Rocket' },
            },
            archived: {
                on: { RESTORE: 'idea' },
                meta: { color: '#374151', label: 'Archived', icon: 'Archive' },
            },
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Inbox Status (capture → triage → process)
    // ─────────────────────────────────────────────────────────────────────────
    inboxStatus: {
        initial: 'captured',
        states: {
            captured: {
                on: { TRIAGE: 'triaging', DELETE: 'deleted' },
                meta: { color: '#f97316', label: 'Captured', icon: 'Inbox' },
            },
            triaging: {
                on: { CONVERT: 'converted', DEFER: 'deferred', DELETE: 'deleted' },
                meta: { color: '#f59e0b', label: 'Triaging', icon: 'Filter' },
            },
            deferred: {
                on: { TRIAGE: 'triaging', DELETE: 'deleted' },
                meta: { color: '#6b7280', label: 'Deferred', icon: 'Clock' },
            },
            converted: {
                on: {}, // Terminal state (item converted to another entity)
                meta: { color: '#10b981', label: 'Converted', icon: 'ArrowRight' },
            },
            deleted: {
                on: { RESTORE: 'captured' },
                meta: { color: '#374151', label: 'Deleted', icon: 'Trash2' },
            },
        },
    },
};

// ============================================================================
// Helper Functions
// ============================================================================

export function getStateMachine(machineId: string): StateMachine | undefined {
    return STATE_MACHINES[machineId];
}

export function getStateMeta(machineId: string, state: string): StateMetadata | undefined {
    return STATE_MACHINES[machineId]?.states[state]?.meta;
}

export function canTransition(machineId: string, currentState: string, event: string): boolean {
    const machine = STATE_MACHINES[machineId];
    if (!machine) return false;

    const stateConfig = machine.states[currentState];
    if (!stateConfig) return false;

    return event in stateConfig.on;
}

export function getValidEvents(machineId: string, currentState: string): string[] {
    const machine = STATE_MACHINES[machineId];
    if (!machine) return [];

    const stateConfig = machine.states[currentState];
    if (!stateConfig) return [];

    return Object.keys(stateConfig.on);
}

export function getNextState(machineId: string, currentState: string, event: string): string | undefined {
    const machine = STATE_MACHINES[machineId];
    if (!machine) return undefined;

    const stateConfig = machine.states[currentState];
    if (!stateConfig) return undefined;

    return stateConfig.on[event];
}

// ============================================================================
// Command Layer Integration (v8.1 Hardening)
// ============================================================================

export interface TransitionResult {
    success: boolean;
    newState?: string;
    error?: string;
}

/**
 * Execute a state transition using the Command Layer.
 * Validates the transition is allowed, then persists via UpdateEntityCommand.
 * 
 * @param entityType - Entity type (e.g., 'task', 'project')
 * @param entity - The universal entity to transition
 * @param machineId - State machine ID (e.g., 'taskStatus')
 * @param event - Transition event (e.g., 'START', 'COMPLETE')
 */
export async function executeTransition(
    entityType: string,
    entity: UniversalEntity,
    machineId: string,
    event: string
): Promise<TransitionResult> {
    const currentState = entity.status ?? '';

    // 1. Validate transition is allowed
    if (!canTransition(machineId, currentState, event)) {
        return {
            success: false,
            error: `Invalid transition: ${currentState} --[${event}]--> ? (not allowed in ${machineId})`,
        };
    }

    // 2. Get the next state
    const nextState = getNextState(machineId, currentState, event);
    if (!nextState) {
        return {
            success: false,
            error: `No target state found for event: ${event}`,
        };
    }

    // 3. Execute via Command Layer
    const command = new UpdateEntityCommand(
        entityType,
        entity.id,
        { status: nextState },
        { actor: 'user', timestamp: new Date(), metadata: { event, machineId } }
    );

    const result = await command.execute();

    if (!result.success) {
        return {
            success: false,
            error: result.error,
        };
    }

    return {
        success: true,
        newState: nextState,
    };
}

/**
 * Get all possible states for a state machine
 */
export function getAllStates(machineId: string): string[] {
    const machine = STATE_MACHINES[machineId];
    if (!machine) return [];
    return Object.keys(machine.states);
}

/**
 * Get all state metadata for a state machine (useful for rendering status selectors)
 */
export function getAllStateMeta(machineId: string): Array<{ state: string; meta: StateMetadata }> {
    const machine = STATE_MACHINES[machineId];
    if (!machine) return [];

    return Object.entries(machine.states).map(([state, def]) => ({
        state,
        meta: def.meta,
    }));
}
