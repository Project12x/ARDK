/**
 * Command Layer - Public API
 * 
 * @module lib/commands
 * @description
 * Entry point for the Command Layer. All entity mutations should go through these exports.
 * 
 * ## Usage
 * ```typescript
 * import { CreateEntityCommand, UpdateEntityCommand, DeleteEntityCommand } from '../lib/commands';
 * 
 * // Create
 * const createCmd = new CreateEntityCommand('project', { title: 'New Project' });
 * const result = await createCmd.execute();
 * 
 * // Update
 * const updateCmd = new UpdateEntityCommand('project', 1, { title: 'Updated' });
 * await updateCmd.execute();
 * 
 * // Delete
 * const deleteCmd = new DeleteEntityCommand('project', 1);
 * await deleteCmd.execute();
 * ```
 */

// Command Classes
export { CreateEntityCommand, UpdateEntityCommand, DeleteEntityCommand } from './EntityCommand';

// Repository (Read-only access)
export {
    getEntityById,
    getAllEntities,
    queryEntities,
    entityExists,
    getRawEntity,
    type EntityQuery
} from './EntityRepository';

// Types
export type {
    CommandResult,
    Command,
    CommandContext,
    EntityMutationPayload,
    CreateEntityPayload,
    UpdateEntityPayload,
    DeleteEntityPayload,
} from './types';
