/**
 * Action Registry - Centralized Entity Actions
 * 
 * @module lib/registry/actionRegistry
 * @description
 * Defines all actions that can be performed on entities (edit, delete, archive, etc.).
 * Actions are referenced by ID in entity definitions and rendered in context menus.
 * 
 * ## Why Use This?
 * - **Consistency**: Same action behavior across all entity types
 * - **Reusability**: Define once, use everywhere
 * - **Extensibility**: Plugins can register custom actions
 * - **Safety**: Actions can have confirm dialogs and visibility predicates
 * 
 * ## Usage Examples
 * ```typescript
 * // Get actions for an entity
 * const actions = getEntityActions('project', ['edit', 'delete', 'archive']);
 * 
 * // Execute an action
 * executeAction('edit', myEntity);
 * ```
 * 
 * ## Adding a New Action
 * Add to ACTION_REGISTRY with id, icon, label, and handler.
 * Optional: visible, enabled, confirm, destructive, batch.
 * 
 * @see ENTITY_REGISTRY for action references
 */

import type { UniversalEntity } from '../universal/types';
import { eventBus } from './eventBus';
import { UpdateEntityCommand, DeleteEntityCommand } from '../commands';
import { getEntityDefinition } from './entityRegistry';

// ============================================================================
// Type Definitions
// ============================================================================

export interface ActionDefinition {
    id: string;
    icon: string; // Lucide icon name
    label: string;
    shortcut?: string;

    // Handler
    handler: (entity: UniversalEntity) => void | Promise<void>;

    // Predicates
    visible?: (entity: UniversalEntity) => boolean;
    enabled?: (entity: UniversalEntity) => boolean;

    // Options
    confirm?: string; // Confirmation message
    destructive?: boolean;
    batch?: boolean; // Supports batch operations
}

// ============================================================================
// Action Registry - All Entity Actions
// ============================================================================

/**
 * ACTION_REGISTRY contains all available entity actions.
 * 
 * Categories:
 * - **CRUD**: edit, delete, duplicate
 * - **Lifecycle**: archive, complete, start, pause, resume
 * - **Organization**: pin, reorder, link
 * - **View**: view, preview
 * - **Media**: play (for songs/recordings)
 */
export const ACTION_REGISTRY: Record<string, ActionDefinition> = {
    // ─────────────────────────────────────────────────────────────────────────
    // CRUD Actions
    // ─────────────────────────────────────────────────────────────────────────

    edit: {
        id: 'edit',
        icon: 'Pencil',
        label: 'Edit',
        shortcut: 'e',
        handler: (entity) => {
            eventBus.emit('modal:edit', {
                modalId: 'edit',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    delete: {
        id: 'delete',
        icon: 'Trash2',
        label: 'Delete',
        shortcut: 'd',
        destructive: true,
        confirm: 'Are you sure you want to delete this item?',
        batch: true,
        handler: async (entity) => {
            // Use Command Layer for deletion (v8.1 Hardening)
            const command = new DeleteEntityCommand(
                entity.type,
                entity.id,
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:delete] Failed:', result.error);
            }
        },
    },

    duplicate: {
        id: 'duplicate',
        icon: 'Copy',
        label: 'Duplicate',
        shortcut: 'shift+d',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'duplicate',
                entityType: entity.type,
                entityId: String(entity.id),
                data: { sourceEntity: entity }
            });
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Lifecycle Actions
    // ─────────────────────────────────────────────────────────────────────────

    archive: {
        id: 'archive',
        icon: 'Archive',
        label: 'Archive',
        shortcut: 'a',
        batch: true,
        // Only show for non-archived entities
        visible: (entity) => entity.status !== 'archived',
        handler: async (entity) => {
            // Use Command Layer for archive (v8.1 Hardening)
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: 'archived' },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:archive] Failed:', result.error);
            }
        },
    },

    restore: {
        id: 'restore',
        icon: 'ArchiveRestore',
        label: 'Restore',
        // Only show for archived entities
        visible: (entity) => entity.status === 'archived',
        handler: async (entity) => {
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: 'active' },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:restore] Failed:', result.error);
            }
        },
    },

    complete: {
        id: 'complete',
        icon: 'CheckCircle',
        label: 'Complete',
        shortcut: 'c',
        // Only show for completable entities
        visible: (entity) => {
            const completableStatuses = ['todo', 'in_progress', 'active', 'planning'];
            return completableStatuses.includes(entity.status ?? '');
        },
        handler: async (entity) => {
            const newStatus = entity.type === 'task' ? 'done' : 'completed';
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: newStatus },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:complete] Failed:', result.error);
            }
        },
    },

    start: {
        id: 'start',
        icon: 'Play',
        label: 'Start',
        visible: (entity) => entity.status === 'todo' || entity.status === 'planning',
        handler: async (entity) => {
            const newStatus = entity.type === 'project' ? 'active' : 'in_progress';
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: newStatus },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:start] Failed:', result.error);
            }
        },
    },

    pause: {
        id: 'pause',
        icon: 'Pause',
        label: 'Pause',
        visible: (entity) => entity.status === 'active' || entity.status === 'in_progress',
        handler: async (entity) => {
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: 'on_hold' },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:pause] Failed:', result.error);
            }
        },
    },

    resume: {
        id: 'resume',
        icon: 'PlayCircle',
        label: 'Resume',
        visible: (entity) => entity.status === 'on_hold' || entity.status === 'blocked',
        handler: async (entity) => {
            const newStatus = entity.type === 'project' ? 'active' : 'in_progress';
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: newStatus },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:resume] Failed:', result.error);
            }
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Organization Actions
    // ─────────────────────────────────────────────────────────────────────────

    pin: {
        id: 'pin',
        icon: 'Pin',
        label: 'Pin',
        // Toggle pin state
        handler: async (entity) => {
            const isPinned = entity.data?.is_pinned as boolean ?? false;
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { is_pinned: !isPinned },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:pin] Failed:', result.error);
            }
        },
    },

    reorder: {
        id: 'reorder',
        icon: 'GripVertical',
        label: 'Reorder',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'reorder',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    link: {
        id: 'link',
        icon: 'Link',
        label: 'Link to...',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'link',
                entityType: entity.type,
                entityId: String(entity.id),
                data: { sourceEntity: entity }
            });
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // View Actions
    // ─────────────────────────────────────────────────────────────────────────

    view: {
        id: 'view',
        icon: 'Eye',
        label: 'View Details',
        shortcut: 'Enter',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'detail',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Media Actions (for songs, recordings)
    // ─────────────────────────────────────────────────────────────────────────

    play: {
        id: 'play',
        icon: 'Play',
        label: 'Play',
        visible: (entity) => entity.type === 'song' || entity.type === 'recording',
        handler: (entity) => {
            // Emit action started instead of custom media:play
            eventBus.emit('action:started', {
                actionId: 'play',
                entityType: entity.type,
                entityIds: [String(entity.id)]
            });
        },
    },

    // ─────────────────────────────────────────────────────────────────────────
    // Workflow Actions
    // ─────────────────────────────────────────────────────────────────────────

    triage: {
        id: 'triage',
        icon: 'ArrowRight',
        label: 'Triage',
        // Only for inbox items
        visible: (entity) => entity.type === 'inbox',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'triage',
                entityType: 'inbox',
                entityId: String(entity.id)
            });
        },
    },

    convert: {
        id: 'convert',
        icon: 'RefreshCw',
        label: 'Convert to...',
        visible: (entity) => entity.type === 'inbox' || entity.type === 'note',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'convert',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    snooze: {
        id: 'snooze',
        icon: 'Clock',
        label: 'Snooze',
        visible: (entity) => entity.type === 'reminder' || entity.type === 'inbox',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'snooze',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    order: {
        id: 'order',
        icon: 'ShoppingCart',
        label: 'Order',
        visible: (entity) => entity.type === 'purchase' || entity.type === 'part',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'order',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    received: {
        id: 'received',
        icon: 'PackageCheck',
        label: 'Mark Received',
        visible: (entity) => entity.type === 'purchase' && entity.status === 'ordered',
        handler: async (entity) => {
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { status: 'received' },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:received] Failed:', result.error);
            }
        },
    },

    skip: {
        id: 'skip',
        icon: 'SkipForward',
        label: 'Skip',
        visible: (entity) => entity.type === 'routine',
        handler: async (entity) => {
            // Mark routine as skipped (store in metadata or dedicated field)
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { last_completed: new Date() }, // Treat skip as a "soft complete"
                { actor: 'user', timestamp: new Date(), metadata: { skipped: true } }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:skip] Failed:', result.error);
            }
        },
    },

    reschedule: {
        id: 'reschedule',
        icon: 'Calendar',
        label: 'Reschedule',
        visible: (entity) => entity.type === 'task' || entity.type === 'reminder',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'reschedule',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    adjust_quantity: {
        id: 'adjust_quantity',
        icon: 'Calculator',
        label: 'Adjust Quantity',
        visible: (entity) => ['inventory', 'filament', 'consumable', 'part'].includes(entity.type),
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'adjust_quantity',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    service: {
        id: 'service',
        icon: 'Wrench',
        label: 'Log Service',
        visible: (entity) => entity.type === 'asset' || entity.type === 'equipment',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'service',
                entityType: entity.type,
                entityId: String(entity.id)
            });
        },
    },

    activate: {
        id: 'activate',
        icon: 'CheckSquare',
        label: 'Activate',
        visible: (entity) => entity.type === 'branch' && !entity.data?.is_active,
        handler: async (entity) => {
            const command = new UpdateEntityCommand(
                entity.type,
                entity.id,
                { is_active: true },
                { actor: 'user', timestamp: new Date() }
            );
            const result = await command.execute();
            if (!result.success) {
                console.error('[Action:activate] Failed:', result.error);
            }
        },
    },

    use: {
        id: 'use',
        icon: 'Play',
        label: 'Use Template',
        visible: (entity) => entity.type === 'template',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'use_template',
                entityType: 'template',
                entityId: String(entity.id)
            });
        },
    },

    link_inventory: {
        id: 'link_inventory',
        icon: 'Link',
        label: 'Link Inventory',
        visible: (entity) => entity.type === 'bom',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'link_inventory',
                entityType: 'bom',
                entityId: String(entity.id)
            });
        },
    },

    configure: {
        id: 'configure',
        icon: 'Settings',
        label: 'Configure',
        visible: (entity) => entity.type === 'widget',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'configure_widget',
                entityType: 'widget',
                entityId: String(entity.id)
            });
        },
    },

    add_member: {
        id: 'add_member',
        icon: 'Plus',
        label: 'Add Member',
        visible: (entity) => entity.type === 'collection',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'add_member',
                entityType: 'collection',
                entityId: String(entity.id)
            });
        },
    },

    reply: {
        id: 'reply',
        icon: 'Reply',
        label: 'Reply',
        visible: (entity) => entity.type === 'comment',
        handler: (entity) => {
            eventBus.emit('modal:open', {
                modalId: 'reply',
                entityType: 'comment',
                entityId: String(entity.id)
            });
        },
    },
};

// ============================================================================
// Helper Functions
// ============================================================================

export function getAction(actionId: string): ActionDefinition | undefined {
    return ACTION_REGISTRY[actionId];
}

export function getEntityActions(entityType: string, actionIds: string[]): ActionDefinition[] {
    return actionIds
        .map(id => ACTION_REGISTRY[id])
        .filter((action): action is ActionDefinition => action !== undefined);
}

export function executeAction(actionId: string, entity: UniversalEntity): void | Promise<void> {
    const action = ACTION_REGISTRY[actionId];
    if (!action) {
        console.warn(`[ActionRegistry] Unknown action: ${actionId}`);
        return;
    }

    // Check if visible and enabled
    if (action.visible && !action.visible(entity)) return;
    if (action.enabled && !action.enabled(entity)) return;

    eventBus.emit('action:started', {
        actionId,
        entityType: entity.type,
        entityIds: [String(entity.id)]
    });

    return action.handler(entity);
}
