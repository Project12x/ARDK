/**
 * Command Layer Types
 * 
 * @module lib/commands/types
 * @description
 * Defines the core interfaces for the Command Layer architecture.
 * Commands are the ONLY way to mutate data in the system.
 * 
 * ## Architecture (v8.1 Hardening)
 * - UI -> useCommand hook -> CommandLayer -> DB + ActivityLog + EventBus
 * - No direct db.table.add() calls from components
 * - All mutations are tracked and reversible
 */

import type { UniversalEntity } from '../universal/types';

// ============================================================================
// Command Interfaces
// ============================================================================

/**
 * Result of executing a command
 */
export interface CommandResult<T = unknown> {
    success: boolean;
    data?: T;
    error?: string;
    /** Activity log entry ID for undo */
    activityLogId?: number;
}

/**
 * Base command interface
 */
export interface Command<T = unknown> {
    /** Unique command type identifier */
    type: string;
    /** Execute the command */
    execute(): Promise<CommandResult<T>>;
    /** Undo the command (Tier 2 Undo) */
    undo?(): Promise<CommandResult<void>>;
}

/**
 * Entity mutation command payload
 */
export interface EntityMutationPayload {
    entityType: string;
    entityId?: number | string;
    data: Record<string, unknown>;
}

/**
 * Command execution context
 */
export interface CommandContext {
    actor: 'user' | 'system' | 'sync' | 'ai';
    timestamp: Date;
    metadata?: Record<string, unknown>;
}

// ============================================================================
// Entity Command Types
// ============================================================================

export type EntityCommandType =
    | 'create'
    | 'update'
    | 'delete'
    | 'archive'
    | 'restore'
    | 'move';

export interface CreateEntityPayload extends EntityMutationPayload {
    commandType: 'create';
}

export interface UpdateEntityPayload extends EntityMutationPayload {
    commandType: 'update';
    entityId: number | string;
    changes: Record<string, { before: unknown; after: unknown }>;
}

export interface DeleteEntityPayload extends EntityMutationPayload {
    commandType: 'delete';
    entityId: number | string;
    /** Snapshot for undo */
    snapshot?: Record<string, unknown>;
}
