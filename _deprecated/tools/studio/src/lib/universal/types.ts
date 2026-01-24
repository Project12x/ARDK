// import type { Project, InventoryItem, ProjectTask, Log } from '../db';
// Broken Cycle: Converted to any for now. TODO: Move Schema types to shared file.

// Complete EntityType enum covering ALL database entities + new abstractions
export type EntityType =
    // Core Entities
    | 'project'
    | 'inventory'
    | 'task'
    | 'asset'
    // Legacy inventory subtypes
    | 'part'
    | 'tool'
    | 'filament'
    | 'consumable'
    | 'equipment'
    // Media Entities
    | 'song'
    | 'album'
    | 'recording'
    // Planning Entities
    | 'goal'
    | 'routine'
    // Workflow Entities
    | 'inbox'
    | 'purchase'
    | 'vendor'
    | 'reminder'
    // Knowledge Entities
    | 'library'
    | 'note'
    | 'document'
    | 'notebook'
    // Relationship/Meta Entities
    | 'bom'
    | 'branch'
    | 'log'
    | 'link'
    | 'template'
    // New Universal Abstractions
    | 'activity'
    | 'comment'
    | 'metric'
    | 'relationship'
    | 'process'
    | 'collection'
    | 'widget';

export interface UniversalEntity<T = any> {
    // Core Identity
    urn: string;         // 'project:15', 'part:402' (Uniform Resource Name)
    id: string | number; // Original DB ID
    type: EntityType;

    // Universal Presentation
    title: string;
    subtitle?: string;
    icon?: string;       // Lucide icon name (we can use dynamic imports or a map later)
    color?: string;      // Tailwind class or Hex

    // Context
    status?: string;     // 'active', 'archived', 'completed', etc.
    tags?: string[];
    createdAt?: Date;
    updatedAt?: Date;

    // The Payload (Full granular data)
    // This strictly preserves the original DB object for full-fidelity rendering
    data: T;

    // Extended Fidelity Fields (v2)
    progress?: number;                      // 0-100 completion percentage
    links?: any[];                          // EntityLink[] for universal linkage
    relatedData?: Record<string, any[]>;    // Aggregated relations (tasks, BOM, logs)
    metadata?: Record<string, any>;         // Specs, configs, etc.
    actions?: UniversalAction[];            // Context-specific actions
    thumbnail?: string;                     // Preview image URL
    files?: UniversalFile[];                // Attached documents, images, videos, etc.

    // NEW: Configuration for UniversalCard rendering (Phase 11c)
    cardConfig?: {
        label?: string;                     // e.g. "Project" vs "Initiative"
        backgroundImage?: string;           // URL
        statusStripe?: string;              // Hex color (overrides status mapping)
        statusGlow?: boolean;

        // Layout
        collapsible?: boolean;
        defaultCollapsed?: boolean;

        // Visual Features
        ratings?: { label: string; value: number; max: number; color?: string; readonly?: boolean; onChange?: (value: number) => void }[];
        metaGrid?: { label: string; value: string | number | { text: string; color?: string } }[];
        badges?: { label: string | any; icon?: string; color?: string; onClick?: () => void }[];
        externalLinks?: { label: string; url: string; icon?: any }[];

        // Media Features
        media?: {
            playAction?: () => void;
            duration?: string;
            progress?: number; // 0-1 for playback
        };

        // Interactives
        nextAction?: {
            label: string;
            subtitle?: string;
            icon?: any;
            onClick?: () => void
        };

        // Editing
        editSchema?: any; // Zod schema
    };
}

// Universal File Attachment
export interface UniversalFile {
    id: string | number;
    name: string;
    type: 'document' | 'image' | 'video' | 'audio' | 'archive' | 'other';
    mimeType?: string;         // e.g. 'application/pdf', 'image/png'
    size?: number;             // Bytes
    url?: string;              // Direct link or blob URL
    thumbnailUrl?: string;     // Preview for images/videos
    createdAt?: Date;
    metadata?: Record<string, any>; // Extracted data (dimensions, duration, etc.)
}

// Wrapper for Drag and Drop payloads
export interface UniversalDragPayload {
    entity: UniversalEntity;
    origin: 'kanban' | 'list' | 'grid' | 'sidebar' | 'transporter';
}

// Universal Action (Button/Command abstract)
export interface UniversalAction {
    id: string;
    label: string;
    icon?: any; // Lucide icon
    action: () => void;

    // Context
    variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline';
    disabled?: boolean;
    hidden?: boolean;
    tooltip?: string;
    shortcut?: string; // e.g. "Cmd+N"
}

// Universal Widget Definition (Dashboard compatible)
export interface UniversalWidgetDefinition<T = any> {
    id: string;
    type: 'chart' | 'list' | 'stat' | 'interactive' | 'container' | 'calendar' | 'progress' | 'timeline';
    title: string;

    // Behavior
    data: T;
    refreshInterval?: number;

    // Layout hints
    span?: 1 | 2 | 3;          // Grid columns
    height?: 'sm' | 'md' | 'lg';
    defaultSize?: { w: number; h: number };
    minSize?: { w: number; h: number };
    maxSize?: { w: number; h: number };
}

// ============================================================================
// NEW UNIVERSAL ABSTRACTIONS (v2 - Gap Analysis)
// ============================================================================

/**
 * UniversalActivity - Track changes, events, and history across all entities
 */
export interface UniversalActivity {
    id: string;
    entityUrn: string;        // "project:15", "inventory:42"
    action: 'created' | 'updated' | 'deleted' | 'moved' | 'linked' | 'commented' | 'status_changed' | 'custom';
    actor?: string;           // User ID or "system"
    timestamp: Date;
    changes?: {
        field: string;
        oldValue: any;
        newValue: any;
    }[];
    message?: string;         // Human-readable summary
    metadata?: Record<string, any>;
}

/**
 * UniversalComment - Attach notes, comments, or discussions to ANY entity
 */
export interface UniversalComment {
    id: string;
    entityUrn: string;        // What this is attached to
    content: string;          // Markdown
    author?: string;
    createdAt: Date;
    updatedAt?: Date;
    parentId?: string;        // For threaded replies
    tags?: string[];
    attachments?: UniversalFile[];
    isPinned?: boolean;
    reactions?: { emoji: string; count: number }[];
}

/**
 * UniversalMetric - Standardized numeric/statistical data for dashboards
 */
export interface UniversalMetric {
    id: string;
    name: string;
    value: number;
    unit?: string;            // "hours", "items", "%", "$"
    trend?: 'up' | 'down' | 'stable';
    previousValue?: number;
    entityUrn?: string;       // Optional: scoped to entity
    category?: 'time' | 'cost' | 'progress' | 'health' | 'count' | 'custom';
    format?: 'number' | 'percentage' | 'currency' | 'duration';
    updatedAt: Date;
    sparkline?: number[];     // Mini chart data
}

/**
 * UniversalRelationship - First-class edges for entity graphs
 */
export interface UniversalRelationship {
    id: string;
    sourceUrn: string;
    targetUrn: string;
    type: 'blocks' | 'requires' | 'relates' | 'contains' | 'triggers' | 'follows' | 'uses' | 'custom';
    label?: string;
    strength?: number;        // 0-1, for weighted graphs
    bidirectional: boolean;
    metadata?: Record<string, any>;
    createdAt: Date;
    validUntil?: Date;        // For temporary relationships
}

/**
 * UniversalStep - A single step in a process/recipe
 */
export interface UniversalStep {
    id: string;
    order: number;
    title: string;
    description?: string;
    duration?: string;        // "15 min", "2 hours"
    inputs?: string[];        // Required items/conditions
    outputs?: string[];       // Produced items/results
    warnings?: string[];
    media?: UniversalFile[];
    isCheckpoint?: boolean;   // Critical verification point
    status?: 'pending' | 'in-progress' | 'completed' | 'skipped';
}

/**
 * UniversalProcess - Multi-step workflows, recipes, procedures
 */
export interface UniversalProcess {
    id: string;
    name: string;
    type: 'recipe' | 'procedure' | 'checklist' | 'workflow' | 'assembly';
    description?: string;
    steps: UniversalStep[];
    totalDuration?: string;
    difficulty?: 'easy' | 'medium' | 'hard' | 'expert';
    tags: string[];
    entityUrn?: string;       // Optional: attached to entity
    category?: string;
    icon?: string;
}

/**
 * UniversalTemplate - Reusable blueprints for creating new entities
 */
export interface UniversalTemplate<T = any> {
    id: string;
    name: string;
    entityType: EntityType;
    description?: string;
    defaultValues: Partial<T>;
    requiredFields: string[];
    icon?: string;
    category?: string;
    createdAt: Date;
    usageCount?: number;
}

/**
 * UniversalCollection - Arbitrary groupings of entities across types
 */
export interface UniversalCollection {
    id: string;
    name: string;
    description?: string;
    icon?: string;
    color?: string;
    members: string[];        // Array of URNs
    sortOrder: string[];      // Custom ordering
    isSmartCollection?: boolean;
    query?: {                 // For smart collections
        entityTypes: EntityType[];
        filters: Record<string, any>;
        sort?: { field: string; direction: 'asc' | 'desc' };
    };
    createdAt: Date;
    updatedAt: Date;
}

// ============================================================================
// TYPE ALIASES FOR CONVENIENCE
// ============================================================================

export type ProjectEntity = UniversalEntity<any>;
export type InventoryEntity = UniversalEntity<any>;
export type TaskEntity = UniversalEntity<any>;
export type AssetEntity = UniversalEntity<any>;
export type SongEntity = UniversalEntity<any>;
export type GoalEntity = UniversalEntity<any>;
