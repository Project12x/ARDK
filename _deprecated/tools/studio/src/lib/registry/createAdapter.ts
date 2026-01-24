/**
 * Create Adapter Factory - UniversalEntity Builder
 * 
 * @module lib/registry/createAdapter
 * @description
 * Factory functions that transform raw database records into UniversalEntity objects.
 * Uses ENTITY_REGISTRY for field mapping, icons, colors, and card configuration.
 * 
 * ## Why Use This?
 * - **Standardization**: All entities have same structure
 * - **Registry-Driven**: Uses ENTITY_REGISTRY for configuration
 * - **Computed Fields**: Automatically applies derived values
 * - **Card Ready**: Generates cardConfig for UniversalCard rendering
 * 
 * ## Usage Examples
 * ```typescript
 * // Create a universal entity from raw DB data
 * const universal = createUniversalEntity('project', rawProject, { tasks });
 * 
 * // Create a reusable adapter function
 * const projectAdapter = createAdapter('project');
 * const entities = rawProjects.map(p => projectAdapter(p));
 * ```
 * 
 * @see ENTITY_REGISTRY for entity configuration
 * @see UniversalEntity for the output type
 */

import type { UniversalEntity, EntityType } from '../universal/types';
import { ENTITY_REGISTRY, getEntityDefinition, getStatusColor } from './entityRegistry';
import { nanoid } from 'nanoid';

// ============================================================================
// Factory Function
// ============================================================================

/**
 * Create a UniversalEntity from raw database data
 * 
 * @param type - Entity type (e.g., 'project', 'task')
 * @param raw - Raw data from database
 * @param related - Optional related entities (tasks, files, etc.)
 */
export function createUniversalEntity(
    type: string,
    raw: Record<string, unknown>,
    related?: Record<string, unknown[]>
): UniversalEntity {
    const def = getEntityDefinition(type);

    if (!def) {
        console.warn(`[createAdapter] Unknown entity type: ${type}`);
        // Return minimal entity
        return {
            urn: `${type}:${raw.id ?? nanoid()}`,
            id: (raw.id as string | number) ?? nanoid(),
            type: type as EntityType,
            title: (raw.title as string) ?? (raw.name as string) ?? 'Untitled',
            status: (raw.status as string) ?? 'unknown',
            data: raw,
        };
    }

    // Extract core fields from definition
    const entityId = (raw.id as string | number) ?? nanoid();
    const entity: UniversalEntity = {
        urn: `${type}:${entityId}`,
        id: entityId,
        type: type as EntityType,
        title: raw[def.primaryField] as string,
        subtitle: def.subtitleField ? raw[def.subtitleField] as string : undefined,
        status: (raw.status as string) ?? 'active',
        icon: def.icon,
        color: def.color,
        data: raw,
    };

    // Add tags if configured
    if (def.tags && raw[def.tags]) {
        entity.tags = raw[def.tags] as string[];
    }

    // Add thumbnail if configured
    if (def.thumbnail && raw[def.thumbnail]) {
        entity.thumbnail = raw[def.thumbnail] as string;
    }

    // Build card configuration
    entity.cardConfig = {
        statusStripe: def.statusStripe ? def.statusStripe(raw) : getStatusColor(entity.status ?? 'active'),
        statusGlow: def.statusGlow ? def.statusGlow(raw) : false,
        collapsible: def.collapsible ?? false,
        // Note: ratings and metaGrid require computed values, handled in Phase 11B
    };

    // Compute derived fields (Phase 11C)
    // TODO: Apply COMPUTED_FIELDS

    return entity;
}

// ============================================================================
// One-Liner Adapter Factory
// ============================================================================

/**
 * Create an adapter function for a specific entity type
 * 
 * Usage:
 *   export const projectAdapter = createAdapter('project');
 *   const universalProject = projectAdapter(rawProject);
 */
export function createAdapter(type: string) {
    return (raw: Record<string, unknown>, related?: Record<string, unknown[]>) =>
        createUniversalEntity(type, raw, related);
}
