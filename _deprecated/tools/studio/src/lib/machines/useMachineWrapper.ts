/**
 * XState Machine Wrapper Hook
 * 
 * @module lib/machines/useMachineWrapper
 * @description
 * Wraps XState's useMachine hook to integrate with the app's eventBus system.
 * Automatically publishes state transitions to eventBus for cross-component sync.
 * 
 * @example
 * ```typescript
 * const { state, send } = useMachineWithEventBus(projectStatusMachine, {
 *   entityType: 'project',
 *   entityId: project.id,
 *   initialState: project.status,
 * });
 * 
 * // When you call send({ type: 'START' }), it will:
 * // 1. Transition the XState machine
 * // 2. Emit 'entity:statusChanged' to eventBus
 * ```
 */
import { useEffect, useCallback } from 'react';
import { useMachine } from '@xstate/react';
import type { AnyStateMachine, SnapshotFrom } from 'xstate';
import { eventBus } from '../eventBus';

// ============================================================================
// Types
// ============================================================================

export interface UseMachineOptions {
    /** Entity type for eventBus notifications */
    entityType: string;
    /** Entity ID for eventBus notifications */
    entityId: number;
    /** Initial state to hydrate from (e.g., from database) */
    initialState?: string;
    /** Whether to emit events to eventBus (default: true) */
    emitToEventBus?: boolean;
}

export interface MachineWrapperResult<TMachine extends AnyStateMachine> {
    /** Current state snapshot */
    state: SnapshotFrom<TMachine>;
    /** Send function for dispatching events */
    send: (event: Parameters<ReturnType<typeof useMachine<TMachine>>[1]>[0]) => void;
    /** Current state value as string */
    currentState: string;
    /** Whether currently in a final state */
    isFinal: boolean;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * XState machine hook with eventBus integration.
 * Publishes state transitions so other components can react.
 */
export function useMachineWithEventBus<TMachine extends AnyStateMachine>(
    machine: TMachine,
    options: UseMachineOptions
): MachineWrapperResult<TMachine> {
    const { entityType, entityId, initialState, emitToEventBus = true } = options;

    // Create machine with initial state if provided
    const machineWithContext = machine.provide({
        // Could add custom actions/services here
    });

    const [state, baseSend] = useMachine(machineWithContext);

    // Wrapped send that emits to eventBus
    const send = useCallback(
        (event: Parameters<typeof baseSend>[0]) => {
            const previousState = state.value;

            // Execute the transition
            baseSend(event);

            // Emit to eventBus after transition
            if (emitToEventBus) {
                // Note: State will update on next render, so we emit the event info
                eventBus.emit('entity:statusChanged', {
                    entityType,
                    entityId,
                    event: typeof event === 'string' ? event : event.type,
                    previousState: String(previousState),
                    machineId: machine.id,
                });
            }
        },
        [baseSend, state.value, entityType, entityId, emitToEventBus, machine.id]
    );

    // Hydrate from initial state if provided
    useEffect(() => {
        if (initialState && state.value !== initialState) {
            // XState v5: We can't directly set state, but we can track mismatch
            // The component should ensure it creates the machine with correct initial state
            console.debug(`[XState] Machine ${machine.id} initialized. DB state: ${initialState}, Machine state: ${String(state.value)}`);
        }
    }, [initialState, state.value, machine.id]);

    // Current state as string (handles compound states)
    const currentState = typeof state.value === 'string'
        ? state.value
        : JSON.stringify(state.value);

    return {
        state,
        send,
        currentState,
        isFinal: state.done ?? false,
    };
}
