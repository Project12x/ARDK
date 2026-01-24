/**
 * Entity Command - Base Command for Entity Mutations
 * 
 * @module lib/commands/EntityCommand
 * @description
 * Abstract base class for all entity mutation commands.
 * Handles validation, DB writes, activity logging, and event emission.
 * 
 * ## Architecture (v8.1 Hardening)
 * Pattern: UI -> useCommand -> EntityCommand -> DB + ActivityLog + EventBus
 * 
 * ## Usage
 * ```typescript
 * const command = new CreateEntityCommand('project', { title: 'New Project' });
 * const result = await command.execute();
 * if (result.success) {
 *   console.log('Created:', result.data);
 * }
 * ```
 */

import { db, type ActivityLogEntry } from '../db';
import { ENTITY_REGISTRY, getEntityDefinition } from '../registry/entityRegistry';
import { eventBus, emitEntityCreated, emitEntityUpdated, emitEntityDeleted } from '../registry/eventBus';
import { createUniversalEntity } from '../registry/createAdapter';
import { createId } from '../utils/id';
import type { CommandResult, CommandContext } from './types';
import type { UniversalEntity } from '../universal/types';

// ============================================================================
// Create Entity Command
// ============================================================================

/**
 * Command to create a new entity
 */
export class CreateEntityCommand {
    constructor(
        private entityType: string,
        private data: Record<string, unknown>,
        private context: CommandContext = { actor: 'user', timestamp: new Date() }
    ) { }

    async execute(): Promise<CommandResult<UniversalEntity>> {
        const def = getEntityDefinition(this.entityType);
        if (!def) {
            return { success: false, error: `Unknown entity type: ${this.entityType}` };
        }

        try {
            // 1. Prepare data with defaults
            const now = new Date();
            const entityData = {
                ...this.data,
                created_at: now,
                updated_at: now,
            };

            // 2. Write to DB
            const table = db.table(def.table);
            const id = await table.add(entityData);

            // 3. Get the created entity
            const raw = await table.get(id);
            const entity = createUniversalEntity(this.entityType, raw as Record<string, unknown>);

            // 4. Log to activity_log
            const logEntry: ActivityLogEntry = {
                entity_type: this.entityType,
                entity_id: id as number,
                action_type: 'create',
                actor: this.context.actor,
                timestamp: this.context.timestamp,
                metadata: this.context.metadata,
            };
            const activityLogId = await db.activity_log.add(logEntry);

            // 5. Emit event
            emitEntityCreated(this.entityType, entity);

            return { success: true, data: entity, activityLogId: activityLogId as number };
        } catch (error) {
            console.error('[CreateEntityCommand] Error:', error);
            return { success: false, error: (error as Error).message };
        }
    }
}

// ============================================================================
// Update Entity Command
// ============================================================================

/**
 * Command to update an existing entity
 */
export class UpdateEntityCommand {
    constructor(
        private entityType: string,
        private entityId: number | string,
        private changes: Record<string, unknown>,
        private context: CommandContext = { actor: 'user', timestamp: new Date() }
    ) { }

    async execute(): Promise<CommandResult<UniversalEntity>> {
        const def = getEntityDefinition(this.entityType);
        if (!def) {
            return { success: false, error: `Unknown entity type: ${this.entityType}` };
        }

        try {
            const table = db.table(def.table);

            // 1. Get previous state for diff
            const previousRaw = await table.get(this.entityId);
            if (!previousRaw) {
                return { success: false, error: `Entity not found: ${this.entityType}:${this.entityId}` };
            }
            const previousEntity = createUniversalEntity(this.entityType, previousRaw as Record<string, unknown>);

            // 2. Calculate diff
            const diff: Record<string, { before: unknown; after: unknown }> = {};
            for (const [key, value] of Object.entries(this.changes)) {
                if ((previousRaw as Record<string, unknown>)[key] !== value) {
                    diff[key] = {
                        before: (previousRaw as Record<string, unknown>)[key],
                        after: value,
                    };
                }
            }

            // 3. Update in DB
            const updateData = {
                ...this.changes,
                updated_at: new Date(),
            };
            await table.update(this.entityId, updateData);

            // 4. Get updated entity
            const updatedRaw = await table.get(this.entityId);
            const entity = createUniversalEntity(this.entityType, updatedRaw as Record<string, unknown>);

            // 5. Log to activity_log
            const logEntry: ActivityLogEntry = {
                entity_type: this.entityType,
                entity_id: this.entityId as number,
                action_type: 'update',
                actor: this.context.actor,
                timestamp: this.context.timestamp,
                changes: diff,
                metadata: this.context.metadata,
            };
            const activityLogId = await db.activity_log.add(logEntry);

            // 6. Emit event
            emitEntityUpdated(this.entityType, entity, previousEntity);

            return { success: true, data: entity, activityLogId: activityLogId as number };
        } catch (error) {
            console.error('[UpdateEntityCommand] Error:', error);
            return { success: false, error: (error as Error).message };
        }
    }
}

// ============================================================================
// Delete Entity Command
// ============================================================================

/**
 * Command to delete an entity
 */
export class DeleteEntityCommand {
    private snapshot?: Record<string, unknown>;

    constructor(
        private entityType: string,
        private entityId: number | string,
        private context: CommandContext = { actor: 'user', timestamp: new Date() }
    ) { }

    async execute(): Promise<CommandResult<void>> {
        const def = getEntityDefinition(this.entityType);
        if (!def) {
            return { success: false, error: `Unknown entity type: ${this.entityType}` };
        }

        try {
            const table = db.table(def.table);

            // 1. Snapshot for undo
            const raw = await table.get(this.entityId);
            if (!raw) {
                return { success: false, error: `Entity not found: ${this.entityType}:${this.entityId}` };
            }
            this.snapshot = raw as Record<string, unknown>;
            const entity = createUniversalEntity(this.entityType, this.snapshot);

            // 2. Delete from DB
            await table.delete(this.entityId);

            // 3. Log to activity_log
            const logEntry: ActivityLogEntry = {
                entity_type: this.entityType,
                entity_id: this.entityId as number,
                action_type: 'delete',
                actor: this.context.actor,
                timestamp: this.context.timestamp,
                metadata: { snapshot: this.snapshot }, // Store for undo
            };
            const activityLogId = await db.activity_log.add(logEntry);

            // 4. Emit event
            emitEntityDeleted(this.entityType, entity);

            return { success: true, activityLogId: activityLogId as number };
        } catch (error) {
            console.error('[DeleteEntityCommand] Error:', error);
            return { success: false, error: (error as Error).message };
        }
    }

    async undo(): Promise<CommandResult<void>> {
        if (!this.snapshot) {
            return { success: false, error: 'No snapshot available for undo' };
        }

        const def = getEntityDefinition(this.entityType);
        if (!def) {
            return { success: false, error: `Unknown entity type: ${this.entityType}` };
        }

        try {
            const table = db.table(def.table);
            await table.add(this.snapshot);

            const entity = createUniversalEntity(this.entityType, this.snapshot);
            emitEntityCreated(this.entityType, entity);

            return { success: true };
        } catch (error) {
            console.error('[DeleteEntityCommand.undo] Error:', error);
            return { success: false, error: (error as Error).message };
        }
    }
}
