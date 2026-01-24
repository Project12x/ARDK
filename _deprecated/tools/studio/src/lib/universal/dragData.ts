/**
 * Universal Drag Data Helper
 * Creates standardized drag data payload for Layout.tsx compatibility
 */
import type { UniversalEntity } from './types';

export interface UniversalDragData {
    type: 'universal-card';
    entityType: string;
    id: number | string;
    title: string;
    metadata: Record<string, any>;
    entity: UniversalEntity<any>;
    origin: string;
}

/**
 * Creates standardized drag data from a UniversalEntity
 * This format is expected by Layout.tsx handleDragEnd
 */
export function createUniversalDragData(
    entity: UniversalEntity<any>,
    origin: string = 'grid'
): UniversalDragData {
    return {
        type: 'universal-card',
        // Flattened fields for Layout.tsx handler
        entityType: entity.type,
        id: entity.id,
        title: entity.title,
        metadata: entity.metadata || { status: entity.status },
        // Full entity for components that need it
        entity: entity,
        origin
    };
}
