// Hardened: Allow any string to support dynamic tables, but keep suggestions for core types
export type EntityType = 'project' | 'goal' | 'routine' | 'asset' | 'note' | 'task' | string;

export type LinkType = 'blocks' | 'supports' | 'maintains' | 'relates_to' | 'sub_task_of';

export interface UniversalEntity {
    id: string; // Composite ID: "project-123"
    dbId: number; // Original DB ID
    type: EntityType;
    title: string;
    description?: string;
    flow_x?: number;
    flow_y?: number;
    color?: string; // For UI consistency
    tags?: string[];
    // Generic metadata bag for things like "frequency" or "status"
    metadata?: Record<string, any>;
}

// "One Ring to rule them all" - The Drag Payload
export interface UniversalDragPayload {
    type: 'universal-card';
    entityType: EntityType;
    id: number; // dbId
    title: string;
}

// Registry for mapping DB types to EntityType
export const TYPE_MAP: Record<string, EntityType> = {
    'projects': 'project',
    'goals': 'goal',
    'routines': 'routine',
    'assets': 'asset',
    'notebook': 'note',
    'project_tasks': 'task',
    'library_items': 'library',
    'inventory': 'inventory'
};

// Icon mapping for DragPreview (import icons where used)
export const ENTITY_ICON_NAMES: Record<EntityType, string> = {
    project: 'Folder',
    goal: 'Target',
    routine: 'Repeat',
    asset: 'Box',
    note: 'FileText',
    task: 'CheckSquare',
    library: 'Book',
    inventory: 'Package'
};
