import { createFixture } from 'zod-fixture';
import { ENTITY_REGISTRY } from '../lib/registry/entityRegistry';
import { z } from 'zod';

/**
 * Generates a mock entity based on its Zod schema in the registry.
 * @param entityType The key of the entity in ENTITY_REGISTRY (e.g. 'project')
 */
export function generateMockEntity(entityType: string) {
    const def = ENTITY_REGISTRY[entityType];
    if (!def) throw new Error(`Unknown entity type: ${entityType}`);
    if (!def.schema) throw new Error(`Entity type ${entityType} has no Zod schema defined`);

    return createFixture(def.schema);
}

/**
 * Generates a specific Zod schema fixture (useful for non-registry types)
 */
export function generateMock<T extends z.ZodTypeAny>(schema: T): z.infer<T> {
    return createFixture(schema);
}
