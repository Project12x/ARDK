/**
 * Event Bus - Centralized Pub/Sub System
 * 
 * @module lib/registry/eventBus
 * @description
 * A typed event system using the `mitt` library for decoupled component communication.
 * Components can emit and listen to events without direct dependencies on each other.
 * 
 * ## Why Use This?
 * - **Decoupling**: Components don't need to know about each other
 * - **Type Safety**: All events are typed via EventMap
 * - **Debugging**: All events are logged in development mode
 * - **Extensibility**: Easy to add new event types
 * 
 * ## Usage Examples
 * ```typescript
 * // Listen for entity changes
 * eventBus.on('entity:created', ({ type, entity }) => {
 *   console.log(`New ${type}: ${entity.title}`);
 * });
 * 
 * // Emit an event
 * eventBus.emit('entity:updated', { type: 'project', entity, previousState });
 * 
 * // Use convenience helpers
 * showToast('Saved!', 'success');
 * openEditModal('project', '123');
 * ```
 * 
 * @see https://github.com/developit/mitt - The underlying event library
 */

import mitt from 'mitt';
import type { UniversalEntity } from '../universal/types';

// ============================================================================
// Event Type Definitions
// ============================================================================

export type EntityEventPayload = {
    type: string;
    entity: UniversalEntity;
    previousState?: UniversalEntity;
};

export type ModalEventPayload = {
    modalId: string;
    entityType?: string;
    entityId?: string;
    data?: Record<string, unknown>;
};

export type SearchEventPayload = {
    query: string;
    filters?: Record<string, unknown>;
};

export type SyncEventPayload = {
    status: 'started' | 'completed' | 'failed' | 'offline';
    entityCount?: number;
    error?: string;
};

export type ActionEventPayload = {
    actionId: string;
    entityType: string;
    entityIds: string[];
    result?: 'success' | 'error' | 'cancelled';
};

// ============================================================================
// Event Map
// ============================================================================

export type EventMap = {
    // Entity lifecycle events
    'entity:created': EntityEventPayload;
    'entity:updated': EntityEventPayload;
    'entity:deleted': EntityEventPayload;
    'entity:selected': EntityEventPayload;
    'entity:batch-selected': { type: string; entityIds: string[] };

    // Modal events
    'modal:open': ModalEventPayload;
    'modal:close': { modalId: string };
    'modal:edit': ModalEventPayload;
    'modal:confirm': ModalEventPayload;

    // Search events
    'search:query': SearchEventPayload;
    'search:clear': void;
    'search:focus': void;

    // Sync events
    'sync:started': SyncEventPayload;
    'sync:completed': SyncEventPayload;
    'sync:failed': SyncEventPayload;
    'sync:offline': SyncEventPayload;

    // Action events
    'action:started': ActionEventPayload;
    'action:completed': ActionEventPayload;
    'action:failed': ActionEventPayload;

    // Draft/autosave events
    'draft:saved': { entityType: string; entityId: string; timestamp: Date };
    'draft:restored': { entityType: string; entityId: string };

    // UI events
    'toast:show': { message: string; type?: 'success' | 'error' | 'info' | 'warning' };
    'sidebar:toggle': { open: boolean };
    'theme:changed': { theme: string };

    // Navigation events
    'navigate:entity': { type: string; id: string };
    'navigate:page': { path: string };
};

// ============================================================================
// Event Bus Instance
// ============================================================================

export const eventBus = mitt<EventMap>();

// ============================================================================
// Convenience Helpers
// ============================================================================

/**
 * Emit an entity created event
 */
export function emitEntityCreated(type: string, entity: UniversalEntity) {
    eventBus.emit('entity:created', { type, entity });
}

/**
 * Emit an entity updated event
 */
export function emitEntityUpdated(type: string, entity: UniversalEntity, previousState?: UniversalEntity) {
    eventBus.emit('entity:updated', { type, entity, previousState });
}

/**
 * Emit an entity deleted event
 */
export function emitEntityDeleted(type: string, entity: UniversalEntity) {
    eventBus.emit('entity:deleted', { type, entity });
}

/**
 * Show a toast notification
 */
export function showToast(message: string, type: 'success' | 'error' | 'info' | 'warning' = 'info') {
    eventBus.emit('toast:show', { message, type });
}

/**
 * Open an edit modal for an entity
 */
export function openEditModal(entityType: string, entityId: string) {
    eventBus.emit('modal:edit', { modalId: 'edit', entityType, entityId });
}

/**
 * Close a modal by ID
 */
export function closeModal(modalId: string = 'edit') {
    eventBus.emit('modal:close', { modalId });
}

// ============================================================================
// Debug Mode (Development Only)
// ============================================================================

if (import.meta.env.DEV) {
    // Log all events in development
    eventBus.on('*', (type, event) => {
        console.debug(`[EventBus] ${String(type)}`, event);
    });
}
