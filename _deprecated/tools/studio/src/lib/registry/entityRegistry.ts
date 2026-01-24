/**
 * Entity Registry - Single Source of Truth for Entity Configuration
 * 
 * @module lib/registry/entityRegistry
 * @description
 * This file contains the centralized configuration for ALL entity types in the system.
 * Each entity type (project, task, goal, etc.) is defined once here, and all components
 * reference this registry for consistent rendering, actions, and behavior.
 * 
 * ## Benefits
 * - **Single edit point**: Change an icon/color/field once, updates everywhere
 * - **Type safety**: TypeScript ensures all definitions are valid
 * - **Extensibility**: Add new entity types by simply adding entries
 * - **Plugin-ready**: Future plugin system will use registerEntityType()
 * 
 * ## How to Add a New Entity Type
 * 1. Add the entity to the EntityType union in `src/lib/universal/types.ts`
 * 2. Add a new entry to ENTITY_REGISTRY below with:
 *    - table: Database table name
 *    - primaryField: Main display field (title, name, etc.)
 *    - icon: Lucide icon name (string)
 *    - color: Hex color for entity accent
 *    - actions: Array of action IDs from ACTION_REGISTRY
 *    - searchFields: Fields to index for search
 * 3. (Optional) Add state machine in `stateMachines.ts` if entity has status
 * 4. (Optional) Add computed fields in `computedFields.ts`
 * 
 * ## Architecture Notes
 * - This registry currently has 25+ built-in entity types
 * - The system is designed to scale to 100+ entity types
 * - Future: Plugins will call registerEntityType() to add custom entities
 * - All entity types share the same rendering pipeline (UniversalCard)
 * 
 * @see ACTION_REGISTRY for entity actions
 * @see STATE_MACHINES for status transitions
 * @see COMPUTED_FIELDS for derived values
 */

import type { ZodSchema } from 'zod';
import { ProjectSchema } from '../schemas';

// ============================================================================
// Type Definitions
// ============================================================================

export interface RatingConfig {
    field: string;
    label: string;
    max: number;
    color?: string;
}

export interface MetaGridItem {
    label: string;
    field: string;
    format?: 'date' | 'number' | 'currency' | 'duration' | 'text';
}

export interface FormFieldConfig {
    key: string;
    label?: string;
    widget?: 'text' | 'textarea' | 'number' | 'date' | 'select' | 'range' | 'checkbox' | 'url' | 'github';
    options?: { label: string; value: string | number }[]; // For select
    min?: number;
    max?: number;
    step?: number;
    placeholder?: string;
    description?: string;
    icon?: string; // Leading icon from Lucide
}

export interface FormSection {
    id: string;
    title: string;
    icon?: string;
    fields: (string | FormFieldConfig)[];
}

// ============================================================================
// View Configuration Types (Phase 12D)
// ============================================================================

export type ViewType = 'overview' | 'kanban' | 'table' | 'chart' | 'three_viewer' | 'timeline' | 'grid' | 'notebook' | 'custom';

export interface ViewConfig {
    id: string;
    title: string;
    icon?: string;
    type: ViewType;
    dataSource?: string;        // Related entity table (e.g., 'project_tasks')
    filterKey?: string;         // FK field (e.g., 'project_id')
    columns?: string[];         // For table views
    groupBy?: string;           // For kanban (e.g., 'status')
    component?: string;         // For 'custom' type - component name
}

export interface EntityDefinition {
    // Identity
    table: string;
    primaryField: string;
    subtitleField?: string;
    icon: string; // Lucide icon name
    color: string;

    // Display
    badges?: string[];
    tags?: string;
    thumbnail?: string;
    ratings?: RatingConfig[];
    metaGrid?: MetaGridItem[];

    // Behavior
    actions: string[]; // Action IDs from ACTION_REGISTRY
    searchFields: string[];
    computedFields?: string[];
    stateMachine?: string;

    // Card config
    collapsible?: boolean;
    defaultCollapsed?: (entity: unknown) => boolean;
    statusStripe?: (entity: unknown) => string;
    statusGlow?: (entity: unknown) => boolean;

    // Forms
    schema?: ZodSchema;
    form?: {
        sections?: FormSection[];
        fields?: (string | FormFieldConfig)[]; // Fallback if no sections
    };
    editFields?: string[]; // Legacy overrides
    createFields?: string[];

    // Views (Phase 12D)
    views?: ViewConfig[];
}

// ============================================================================
// Status Colors (Shared across entities)
// ============================================================================

export const STATUS_COLORS: Record<string, string> = {
    // Project statuses
    planning: '#f59e0b',
    active: '#10b981',
    on_hold: '#6b7280',
    completed: '#3b82f6',
    archived: '#374151',

    // Task statuses
    todo: '#6b7280',
    in_progress: '#f59e0b',
    done: '#10b981',
    blocked: '#ef4444',

    // Goal statuses
    not_started: '#6b7280',
    working: '#f59e0b',
    achieved: '#10b981',
    abandoned: '#374151',

    // Purchase statuses
    wishlist: '#8b5cf6',
    considering: '#f59e0b',
    approved: '#10b981',
    ordered: '#3b82f6',
    received: '#10b981',
    returned: '#ef4444',
};

// ============================================================================
// Entity Registry (All 25 Entity Types)
// ============================================================================

export const ENTITY_REGISTRY: Record<string, EntityDefinition> = {
    // === Core Entities ===
    project: {
        table: 'projects',
        primaryField: 'title',
        subtitleField: 'status_description',
        icon: 'FolderKanban',
        color: '#3b82f6',
        badges: ['status', 'priority'],
        tags: 'tags',
        thumbnail: 'image_url',
        ratings: [
            { field: 'priority', label: 'Priority', max: 5 },
            { field: 'intrusiveness', label: 'Intrusiveness', max: 5 },
        ],
        metaGrid: [
            { field: 'target_completion_date', label: 'Due', format: 'date' },
            { field: 'status', label: 'Status', format: 'text' },
        ],
        actions: ['edit', 'delete', 'archive', 'duplicate'],
        searchFields: ['title', 'status_description', 'tags', 'project_code'],
        computedFields: ['progress', 'isOverdue', 'nextTask', 'taskCount'],
        stateMachine: 'projectStatus',
        collapsible: true,
        schema: ProjectSchema,
    },

    task: {
        table: 'project_tasks',
        primaryField: 'title',
        subtitleField: 'phase',
        icon: 'CheckSquare',
        color: '#10b981',
        badges: ['status', 'priority'],
        ratings: [{ field: 'priority', label: 'Priority', max: 5 }],
        metaGrid: [
            { field: 'estimated_time', label: 'Est.', format: 'text' },
            { field: 'scheduled_date', label: 'Scheduled', format: 'date' },
        ],
        actions: ['edit', 'delete', 'complete', 'reschedule'],
        searchFields: ['title', 'phase'],
        stateMachine: 'taskStatus',
        form: {
            sections: [
                {
                    id: 'general',
                    title: 'General',
                    icon: 'CheckSquare',
                    fields: [
                        'title',
                        'phase',
                        {
                            key: 'status',
                            widget: 'select',
                            options: [
                                { label: 'To Do', value: 'todo' },
                                { label: 'In Progress', value: 'in_progress' },
                                { label: 'Done', value: 'done' },
                                { label: 'Blocked', value: 'blocked' }
                            ]
                        },
                        {
                            key: 'priority',
                            widget: 'range',
                            min: 1,
                            max: 5
                        }
                    ]
                },
                {
                    id: 'schedule',
                    title: 'Schedule',
                    icon: 'Calendar',
                    fields: [
                        { key: 'scheduled_date', widget: 'date', label: 'Start Date' },
                        { key: 'estimated_time', widget: 'text', placeholder: 'e.g. 2h 30m' }
                    ]
                }
            ]
        }
    },

    goal: {
        table: 'goals',
        primaryField: 'title',
        subtitleField: 'description',
        icon: 'Target',
        color: '#8b5cf6',
        badges: ['status', 'level'],
        tags: 'tags',
        ratings: [{ field: 'priority', label: 'Priority', max: 5 }],
        metaGrid: [
            { field: 'target_date', label: 'Target', format: 'date' },
            { field: 'level', label: 'Level', format: 'text' },
        ],
        actions: ['edit', 'delete', 'archive'],
        searchFields: ['title', 'description', 'tags'],
        computedFields: ['progress'],
        views: [
            { id: 'overview', title: 'Overview', icon: 'Target', type: 'overview' },
            { id: 'timeline', title: 'Timeline', icon: 'Clock', type: 'timeline' }
        ]
    },

    routine: {
        table: 'routines',
        primaryField: 'title',
        subtitleField: 'frequency',
        icon: 'RefreshCw',
        color: '#f59e0b',
        badges: ['category'],
        metaGrid: [
            { field: 'next_due', label: 'Next Due', format: 'date' },
            { field: 'frequency', label: 'Frequency', format: 'text' },
        ],
        actions: ['edit', 'delete', 'complete', 'skip'],
        searchFields: ['title', 'category'],
    },

    // === Inventory Entities ===
    inventory: {
        table: 'inventory',
        primaryField: 'name',
        subtitleField: 'category',
        icon: 'Package',
        color: '#06b6d4',
        badges: ['type'],
        thumbnail: 'image_url',
        metaGrid: [
            { field: 'quantity', label: 'Qty', format: 'number' },
            { field: 'location', label: 'Location', format: 'text' },
        ],
        actions: ['edit', 'delete', 'adjust_quantity'],
        searchFields: ['name', 'category', 'mpn', 'manufacturer', 'barcode'],
    },

    part: {
        table: 'inventory',
        primaryField: 'name',
        subtitleField: 'mpn',
        icon: 'Cpu',
        color: '#0ea5e9',
        metaGrid: [
            { field: 'quantity', label: 'Qty', format: 'number' },
            { field: 'unit_cost', label: 'Cost', format: 'currency' },
        ],
        actions: ['edit', 'delete', 'order'],
        searchFields: ['name', 'mpn', 'manufacturer'],
    },

    tool: {
        table: 'inventory',
        primaryField: 'name',
        subtitleField: 'location',
        icon: 'Wrench',
        color: '#64748b',
        actions: ['edit', 'delete'],
        searchFields: ['name', 'location'],
    },

    filament: {
        table: 'inventory',
        primaryField: 'name',
        subtitleField: 'properties.material',
        icon: 'Cylinder',
        color: '#ec4899',
        metaGrid: [
            { field: 'properties.color_hex', label: 'Color', format: 'text' },
            { field: 'quantity', label: 'Weight', format: 'number' },
        ],
        actions: ['edit', 'delete', 'adjust_quantity'],
        searchFields: ['name', 'properties.brand', 'properties.material'],
    },

    consumable: {
        table: 'inventory',
        primaryField: 'name',
        icon: 'Droplet',
        color: '#22c55e',
        metaGrid: [{ field: 'quantity', label: 'Qty', format: 'number' }],
        actions: ['edit', 'delete', 'reorder'],
        searchFields: ['name', 'category'],
    },

    equipment: {
        table: 'inventory',
        primaryField: 'name',
        subtitleField: 'location',
        icon: 'HardDrive',
        color: '#78716c',
        actions: ['edit', 'delete'],
        searchFields: ['name', 'location'],
    },

    // === Asset Management ===
    asset: {
        table: 'assets',
        primaryField: 'name',
        subtitleField: 'category',
        icon: 'Server',
        color: '#6366f1',
        badges: ['status'],
        metaGrid: [
            { field: 'value', label: 'Value', format: 'currency' },
            { field: 'location', label: 'Location', format: 'text' },
        ],
        actions: ['edit', 'delete', 'service'],
        searchFields: ['name', 'category', 'serial_number', 'make', 'model'],
    },

    // === Media Entities ===
    song: {
        table: 'songs',
        primaryField: 'title',
        subtitleField: 'status',
        icon: 'Music',
        color: '#ec4899',
        badges: ['status'],
        thumbnail: 'cover_art_url',
        tags: 'tags',
        metaGrid: [
            { field: 'duration', label: 'Duration', format: 'text' },
            { field: 'bpm', label: 'BPM', format: 'number' },
        ],
        actions: ['edit', 'delete', 'play', 'archive'],
        searchFields: ['title', 'tags'],
    },

    album: {
        table: 'albums',
        primaryField: 'title',
        subtitleField: 'artist',
        icon: 'Disc',
        color: '#a855f7',
        badges: ['status'],
        thumbnail: 'cover_art_url',
        metaGrid: [{ field: 'release_date', label: 'Release', format: 'date' }],
        actions: ['edit', 'delete'],
        searchFields: ['title', 'artist'],
    },

    recording: {
        table: 'recordings',
        primaryField: 'title',
        subtitleField: 'type',
        icon: 'Mic',
        color: '#ef4444',
        badges: ['type'],
        metaGrid: [{ field: 'duration', label: 'Duration', format: 'text' }],
        actions: ['edit', 'delete', 'play'],
        searchFields: ['title', 'notes'],
    },

    // === Workflow Entities ===
    inbox: {
        table: 'inbox_items',
        primaryField: 'content',
        subtitleField: 'type',
        icon: 'Inbox',
        color: '#f97316',
        badges: ['type'],
        metaGrid: [{ field: 'created_at', label: 'Added', format: 'date' }],
        actions: ['edit', 'delete', 'triage', 'convert'],
        searchFields: ['content'],
    },

    purchase: {
        table: 'purchase_items',
        primaryField: 'name',
        subtitleField: 'status',
        icon: 'ShoppingCart',
        color: '#14b8a6',
        badges: ['status', 'priority'],
        ratings: [{ field: 'priority', label: 'Priority', max: 5 }],
        metaGrid: [
            { field: 'estimated_price', label: 'Est. Price', format: 'currency' },
            { field: 'vendor_id', label: 'Vendor', format: 'text' },
        ],
        actions: ['edit', 'delete', 'order', 'received'],
        searchFields: ['name', 'notes'],
    },

    vendor: {
        table: 'vendors',
        primaryField: 'name',
        subtitleField: 'category',
        icon: 'Store',
        color: '#0d9488',
        metaGrid: [{ field: 'website', label: 'Website', format: 'text' }],
        actions: ['edit', 'delete'],
        searchFields: ['name', 'category'],
    },

    reminder: {
        table: 'reminders',
        primaryField: 'title',
        subtitleField: 'due_date',
        icon: 'Bell',
        color: '#eab308',
        badges: ['priority'],
        ratings: [{ field: 'priority', label: 'Priority', max: 5 }],
        metaGrid: [{ field: 'due_date', label: 'Due', format: 'date' }],
        actions: ['edit', 'delete', 'complete', 'snooze'],
        searchFields: ['title', 'notes'],
    },

    // === Knowledge Entities ===
    library: {
        table: 'library',
        primaryField: 'title',
        subtitleField: 'type',
        icon: 'BookOpen',
        color: '#84cc16',
        badges: ['type', 'category'],
        tags: 'tags',
        metaGrid: [
            { field: 'author', label: 'Author', format: 'text' },
            { field: 'file_size', label: 'Size', format: 'number' },
        ],
        actions: ['edit', 'delete', 'view'],
        searchFields: ['title', 'author', 'tags', 'summary'],
    },

    note: {
        table: 'global_notes',
        primaryField: 'title',
        subtitleField: 'category',
        icon: 'StickyNote',
        color: '#fbbf24',
        badges: ['category'],
        metaGrid: [{ field: 'updated_at', label: 'Updated', format: 'date' }],
        actions: ['edit', 'delete', 'pin'],
        searchFields: ['title', 'content'],
    },

    document: {
        table: 'project_documents',
        primaryField: 'title',
        subtitleField: 'type',
        icon: 'FileText',
        color: '#60a5fa',
        badges: ['status', 'type'],
        metaGrid: [{ field: 'order', label: 'Order', format: 'number' }],
        actions: ['edit', 'delete', 'reorder'],
        searchFields: ['title', 'content'],
    },

    notebook: {
        table: 'notebook',
        primaryField: 'title',
        subtitleField: 'date',
        icon: 'Book',
        color: '#f472b6',
        tags: 'tags',
        metaGrid: [{ field: 'date', label: 'Date', format: 'date' }],
        actions: ['edit', 'delete'],
        searchFields: ['title', 'content', 'tags'],
    },

    // === Relationship/Meta Entities ===
    bom: {
        table: 'project_bom',
        primaryField: 'part_name',
        icon: 'List',
        color: '#94a3b8',
        badges: ['status'],
        metaGrid: [
            { field: 'quantity_required', label: 'Qty', format: 'number' },
            { field: 'est_unit_cost', label: 'Cost', format: 'currency' },
        ],
        actions: ['edit', 'delete', 'link_inventory'],
        searchFields: ['part_name'],
    },

    branch: {
        table: 'branches',
        primaryField: 'name',
        icon: 'GitBranch',
        color: '#a78bfa',
        badges: ['is_active'],
        actions: ['edit', 'delete', 'activate'],
        searchFields: ['name'],
    },

    log: {
        table: 'logs',
        primaryField: 'summary',
        subtitleField: 'version',
        icon: 'Clock',
        color: '#9ca3af',
        badges: ['type'],
        metaGrid: [{ field: 'date', label: 'Date', format: 'date' }],
        actions: ['view', 'delete'],
        searchFields: ['summary'],
    },

    link: {
        table: 'links',
        primaryField: 'relationship',
        icon: 'Link',
        color: '#6b7280',
        metaGrid: [
            { field: 'source_type', label: 'From', format: 'text' },
            { field: 'target_type', label: 'To', format: 'text' },
        ],
        actions: ['edit', 'delete'],
        searchFields: ['relationship'],
    },

    template: {
        table: 'project_templates',
        primaryField: 'name',
        subtitleField: 'category',
        icon: 'Copy',
        color: '#8b5cf6',
        badges: ['category'],
        metaGrid: [{ field: 'is_custom', label: 'Custom', format: 'text' }],
        actions: ['edit', 'delete', 'use'],
        searchFields: ['name', 'category'],
    },

    // === New Universal Abstractions ===
    activity: {
        table: 'activities',
        primaryField: 'message',
        subtitleField: 'action',
        icon: 'Activity',
        color: '#4ade80',
        badges: ['action'],
        metaGrid: [{ field: 'timestamp', label: 'Time', format: 'date' }],
        actions: ['view'],
        searchFields: ['message'],
    },

    comment: {
        table: 'comments',
        primaryField: 'content',
        subtitleField: 'author',
        icon: 'MessageCircle',
        color: '#60a5fa',
        metaGrid: [{ field: 'created_at', label: 'Posted', format: 'date' }],
        actions: ['edit', 'delete', 'reply'],
        searchFields: ['content'],
    },

    metric: {
        table: 'metrics',
        primaryField: 'name',
        icon: 'BarChart3',
        color: '#f472b6',
        metaGrid: [
            { field: 'value', label: 'Value', format: 'number' },
            { field: 'unit', label: 'Unit', format: 'text' },
        ],
        actions: ['edit', 'delete'],
        searchFields: ['name'],
    },

    relationship: {
        table: 'links',
        primaryField: 'type',
        icon: 'GitMerge',
        color: '#a855f7',
        actions: ['edit', 'delete'],
        searchFields: ['type', 'label'],
    },

    process: {
        table: 'processes',
        primaryField: 'name',
        subtitleField: 'type',
        icon: 'Workflow',
        color: '#06b6d4',
        badges: ['type', 'difficulty'],
        tags: 'tags',
        metaGrid: [{ field: 'totalDuration', label: 'Duration', format: 'text' }],
        actions: ['edit', 'delete', 'start'],
        searchFields: ['name', 'description', 'tags'],
    },

    collection: {
        table: 'collections',
        primaryField: 'name',
        subtitleField: 'description',
        icon: 'Folder',
        color: '#f59e0b',
        metaGrid: [{ field: 'members', label: 'Items', format: 'number' }],
        actions: ['edit', 'delete', 'add_member'],
        searchFields: ['name', 'description'],
    },

    widget: {
        table: 'widgets',
        primaryField: 'title',
        subtitleField: 'type',
        icon: 'LayoutGrid',
        color: '#2dd4bf',
        badges: ['type'],
        actions: ['edit', 'delete', 'configure'],
        searchFields: ['title'],
    },
};

// ============================================================================
// Helper Functions
// ============================================================================

export function getEntityDefinition(type: string): EntityDefinition | undefined {
    return ENTITY_REGISTRY[type];
}

export function getEntityIcon(type: string): string {
    return ENTITY_REGISTRY[type]?.icon ?? 'Box';
}

export function getEntityColor(type: string): string {
    return ENTITY_REGISTRY[type]?.color ?? '#6b7280';
}

export function getStatusColor(status: string): string {
    return STATUS_COLORS[status] ?? '#6b7280';
}

export function getAllEntityTypes(): string[] {
    return Object.keys(ENTITY_REGISTRY);
}
