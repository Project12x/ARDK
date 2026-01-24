/**
 * Entity Repository - Read-Only Data Access Layer
 * 
 * @module lib/commands/EntityRepository
 * @description
 * Read-only abstraction for fetching entities from the database.
 * All reads go through this layer to ensure consistent access patterns.
 * 
 * ## Architecture (v8.1 Hardening)
 * - Components use EntityRepository for reads
 * - Commands use EntityRepository to validate before mutations
 * - This layer is the single source of truth for data access
 */

import { db } from '../db';
import { ENTITY_REGISTRY, getEntityDefinition } from '../registry/entityRegistry';
import { createUniversalEntity } from '../registry/createAdapter';
import type { UniversalEntity } from '../universal/types';

// ============================================================================
// Repository Interface
// ============================================================================

export interface EntityQuery {
    entityType: string;
    id?: number | string;
    where?: Record<string, unknown>;
    orderBy?: string;
    limit?: number;
}

// ============================================================================
// Repository Functions
// ============================================================================

/**
 * Get a single entity by ID
 */
export async function getEntityById(
    entityType: string,
    id: number | string
): Promise<UniversalEntity | null> {
    const def = getEntityDefinition(entityType);
    if (!def) {
        console.warn(`[EntityRepository] Unknown entity type: ${entityType}`);
        return null;
    }

    const table = db.table(def.table);

    // Auto-cast ID if table uses numeric PK but string was passed
    let lookupId = id;
    if (typeof id === 'string' && !isNaN(Number(id))) {
        lookupId = Number(id);
    }

    const raw = await table.get(lookupId);

    if (!raw) return null;

    return createUniversalEntity(entityType, raw as Record<string, unknown>);
}

/**
 * Get all entities of a type
 */
export async function getAllEntities(entityType: string): Promise<UniversalEntity[]> {
    const def = getEntityDefinition(entityType);
    if (!def) {
        console.warn(`[EntityRepository] Unknown entity type: ${entityType}`);
        return [];
    }

    const table = db.table(def.table);
    const rawItems = await table.toArray();

    return rawItems.map((raw) =>
        createUniversalEntity(entityType, raw as Record<string, unknown>)
    );
}

/**
 * Query entities with filters
 */
export async function queryEntities(query: EntityQuery): Promise<UniversalEntity[]> {
    const def = getEntityDefinition(query.entityType);
    if (!def) {
        console.warn(`[EntityRepository] Unknown entity type: ${query.entityType}`);
        return [];
    }

    const table = db.table(def.table);
    let collection = table.toCollection();

    // Apply where clause if provided
    if (query.where) {
        const [key, value] = Object.entries(query.where)[0];
        collection = table.where(key).equals(value);
    }

    // Apply limit
    if (query.limit) {
        collection = collection.limit(query.limit);
    }

    const rawItems = await collection.toArray();

    return rawItems.map((raw) =>
        createUniversalEntity(query.entityType, raw as Record<string, unknown>)
    );
}

/**
 * Check if an entity exists
 */
export async function entityExists(
    entityType: string,
    id: number | string
): Promise<boolean> {
    const entity = await getEntityById(entityType, id);
    return entity !== null;
}

/**
 * Get raw database record (for internal use only)
 */
export async function getRawEntity(
    entityType: string,
    id: number | string
): Promise<Record<string, unknown> | null> {
    const def = getEntityDefinition(entityType);
    if (!def) return null;

    const table = db.table(def.table);
    const raw = await table.get(id);

    return raw as Record<string, unknown> | null;
}
