import Dexie, { type Table } from 'dexie';
import type { EntityType, LinkType } from './universal';

// Force Cache Bust
export const _DB_CACHE_BUST = 1;
export interface ProjectDocument {
    id?: number;
    project_id: number;
    title: string;
    content: string; // HTML or Markdown
    order: number;
    type: 'chapter' | 'song' | 'scene' | 'article' | 'research';
    status: 'draft' | 'review' | 'final';
    updated_at: Date;
}

export interface ProjectProductionItem {
    id?: number;
    project_id: number;
    name: string;
    type: 'song' | 'scene' | 'shot';
    // Metadata is specific to type
    // Song: { bpm: 120, key: 'Cm', length: '3:30' }
    // Video: { location: 'EXT', time: 'DAY', cast: [] }
    metadata: Record<string, any>;
    status: 'planned' | 'in-progress' | 'blocked' | 'done';
    order: number;
}


export interface ActivityLogEntry {
    id?: number;
    entity_type: string;
    entity_id: number;
    action_type: 'create' | 'update' | 'delete' | 'move' | 'archive';
    actor: string; // 'user' | 'system' | 'sync' | 'ai'
    timestamp: Date;
    changes?: Record<string, { before: any; after: any }>; // Diff snapshot
    metadata?: Record<string, any>;
}

export interface EntityLink {
    id?: number;
    source_type: EntityType;
    source_id: number;
    target_type: EntityType;
    target_id: number;
    relationship: LinkType;
    created_at: Date;
    metadata?: Record<string, any>;
}

export interface Project {
    id?: number;
    title: string;
    project_code?: string; // e.g. "PE-LT"
    status: 'active' | 'on-hold' | 'completed' | 'archived' | 'legacy' | 'rnd_long' | 'dropped' | 'someday';
    design_status?: string; // e.g. 'idea', 'draft', 'planted', 'sketch'
    build_status?: string; // e.g. 'unbuilt', 'wip', 'fruiting', 'framed'
    exp_cv_usage?: string;
    // v17: Robustness
    time_estimate_active?: number; // Hours
    time_estimate_passive?: number; // Hours (drying, waiting)
    financial_budget?: number; // USD
    financial_spend?: number; // USD
    rationale?: string; // "Why" / Motivation
    risk_level?: 'low' | 'medium' | 'high';
    external_links?: Array<{ label: string; url: string }>;
    priority?: number; // 1-5
    status_description?: string; // Narrative
    next_step?: string;
    blockers?: string[];
    est_active_time?: string;
    est_calendar_time?: string;
    version: string;
    // v5 Fields
    intrusiveness?: number; // 1-5
    role?: string; // e.g. "Live-safe noise instrument"
    io_spec?: string[]; // e.g. ["EXP In", "CV Out"]
    target_completion_date?: Date;
    // v7 Fields
    parent_id?: number; // For tree structure
    category?: string; // e.g. "Music", "Home"
    kingdom?: string; // e.g. "Electronics", "Woodworking"
    phylum?: string; // e.g. "Synths", "Furniture"
    taxonomy_path?: string; // e.g. "Electronics>Music>Guitar>Pedal"
    label_color?: string; // e.g. "#ff0000" or "red-500"
    total_theorized_hours?: number; // Numeric estimate
    // v8 Fields
    design_philosophy?: string; // Core ethos
    golden_voltages?: string; // Debugging reference text/markdown

    created_at: Date;
    updated_at: Date;
    tags: string[];
    current_branch_id?: number;
    is_archived?: boolean; // v9
    deleted_at?: Date; // v14 (Trash)
    // v18: MDBD & Hybrid Domains
    domains?: string[]; // e.g. ['Electronics', 'Software']
    specs_technical?: Record<string, any>; // JSON: Power, Dimensions, Materials
    specs_performance?: Record<string, any>; // JSON: Headroom, Noise, Latency
    market_context?: Record<string, any>; // JSON: Target User, Scenarios
    signal_chain?: Record<string, any>; // JSON: Signal flow context

    // v19: Universal Support
    hazards?: string[]; // e.g. ['Fumes', 'Biohazard', 'High Voltage']
    specs_environment?: Record<string, any>; // JSON: Temp, Humidity, Drying Times

    // v20: MDBD & Deep Data
    universal_data?: Record<string, any>; // JSON: Full mapped structure ("Blueprint")

    // v21: Chaining & Drag-Drop
    upstream_dependencies?: number[]; // IDs of projects that block this one
    sort_order?: number; // For manual visual ordering

    // v22: Generic Linking
    related_projects?: number[]; // IDs of "related" projects (no direction)

    // v23: Flowchart Positioning
    flow_x?: number;
    flow_y?: number;
    image_url?: string;
    github_repo?: string;
    print_parts?: PrintPart[];
    // v35: Safety & Assets
    safety_data?: SafetyData;
    linked_asset_id?: number;

    // v42: Life Goals
    goal_id?: number; // Link to parent goal

    // v52: AI Extracted Data
    specs_custom?: Record<string, any>;

    // v56: UI Settings
    settings?: {
        hidden_tabs?: string[];
    };

    // v57: Feature Badges
    has_ai_content?: boolean;
    has_3d_models?: boolean;
    has_pcb?: boolean;
}

// --- Safety & Assets ---
export type HazardClass = 'mains' | 'high_current' | 'chemicals' | 'blades' | 'fumes' | 'lead' | 'esd';

export interface SafetyData {
    hazards: HazardClass[];
    controls: SafetyControl[];
    is_ready: boolean; // "Bench Ready" gate
    approved_at?: Date;
}

export interface SafetyControl {
    id: string; // uuid
    hazard: HazardClass;
    description: string; // e.g. "Isolation transformer connected"
    is_checked: boolean;
}

export interface Asset {
    id?: number;
    name: string;
    make?: string;
    model?: string;
    serial_number?: string;
    location?: string;
    category: string; // e.g. "Test Equipment", "Power Tools", "Computer"
    status: 'active' | 'maintenance' | 'broken' | 'retired';

    // v3 Assets Update
    value?: number;
    description?: string;
    purchaseDate?: Date;

    images: string[];
    manuals: AssetDoc[];
    symptoms: AssetSymptom[];

    related_project_ids: number[]; // Service history
    created_at: Date;
    updated_at: Date;

    // Specialized Specs
    specs_computer?: ComputerSpecs;

    // v53: Knowledge Base
    related_library_ids?: number[];
}

export interface LibraryItem {
    id?: number;
    title: string;
    type: 'pdf' | 'image' | 'text' | 'ebook' | 'other' | 'audio' | 'video'; // Added audio/video
    content?: string; // Base64 or Text
    summary?: string; // AI Summary
    tags: string[];
    created_at: Date;
    file_size?: number;
    mime_type?: string;

    // v54: Organization
    category: 'bookshelf' | 'records' | 'photos' | 'vhs' | 'junk';
    author?: string; // or Artist/Director
    genre?: string;
    folder_path: string; // e.g. "/" or "/Manuals/Old"
}

export interface ComputerSpecs {
    cpu: string;
    gpu: string;
    ram: string; // "32GB DDR4"
    storage_drives: Drive[];
    os: string;
    hostname: string;
    network_interfaces: Array<{ name: string, ip?: string, mac?: string }>;
    peripherals?: string[];
}

export interface Drive {
    name: string; // "C:" or "nvme0n1"
    type: 'ssd' | 'hdd' | 'nvme';
    capacity: string;
    usage?: string;
}

export interface AssetDoc {
    title: string;
    url: string;
}

export interface AssetSymptom {
    id: string; // uuid
    description: string;
    solution_ref?: string;
}

export interface PrintPart {
    id: string; // uuid
    name: string;
    status: 'stl' | 'sliced' | 'printing' | 'done';
    source_url?: string;
    thumbnail_url?: string;
    count: number;
}

export interface Branch {
    id?: number;
    project_id: number;
    name: string;
    is_active: boolean;
}

export interface Log {
    id?: number;
    project_id: number;
    branch_id?: number;
    version: string;
    date: Date;
    summary: string;
    type: 'auto' | 'manual';
}

export interface InventoryItem {
    id?: number;
    name: string;
    category: string;
    domain?: string; // Kingdom (e.g. Electronics)
    quantity: number;
    location: string;
    min_stock: number;
    updated_at?: Date; // Added for tracking
    unit_cost?: number; // Estimated street price
    units?: string; // e.g. "kg", "m", "pcs"
    datasheet_url?: string;
    type?: 'part' | 'tool' | 'equipment' | 'consumable'; // v19 added consumable
    properties?: {
        color_hex?: string;
        material?: 'PLA' | 'PETG' | 'ABS' | 'TPU' | 'ASA' | 'Resin';
        brand?: string;
        temp_nozzle?: number;
        temp_bed?: number;
        diameter?: number; // 1.75 or 2.85
        weight_total?: number; // Initial weight (e.g. 1000g)
    };
    // v24: MPN & Barcode
    mpn?: string;
    manufacturer?: string;
    barcode?: string;
    upc?: string; // Legacy/Alias

    // v36: Enhanced BOM
    description?: string;
    image_url?: string;
    specs?: Record<string, any>; // { "Resistance": "10k", "Power": "0.1W" }
    market_data?: Record<string, any>; // { best_price: 0.05, availability: 'In Stock' }
    last_api_fetch?: Date;
    supplier_api_source?: 'digikey' | 'trustedparts' | 'manual';
}

// ... existing interfaces ...

export interface ProjectFile {
    id?: number;
    project_id: number;
    associated_branch_id?: number;
    name: string;
    type: string;
    content: Blob;
    extracted_metadata?: Record<string, any>;
    created_at: Date;
}

export interface ProjectBOM {
    id?: number;
    project_id: number;
    branch_id?: number;
    part_name: string;
    inventory_item_id?: number;
    quantity_required: number;
    status: 'missing' | 'in-stock';
    est_unit_cost?: number;
    purchase_url?: string;
    // v17
    is_ordered?: boolean;
    is_received?: boolean;
    // v36
    manual_match_notes?: string;
}

export interface ProjectTask {
    id?: number;
    project_id: number;
    title: string;
    status: 'pending' | 'in-progress' | 'completed' | 'blocked';
    phase?: string; // e.g. "Planning", "Assembly", "Testing"
    priority: 1 | 2 | 3 | 4 | 5; // 1 = Lowest, 5 = Highest
    estimated_time?: string; // e.g. "2h"
    calendar_duration?: string; // e.g. "2 days"
    blockers?: string[];
    materials_needed?: string[];
    // v24: Task Flowchart
    upstream_task_ids?: number[];
    flow_x?: number;
    flow_y?: number;
    // v31
    is_high_priority?: boolean;
    caution_flags?: string[];
    // v37: Energy & Sensory
    energy_level?: 'low' | 'medium' | 'high';
    sensory_load?: string[]; // e.g. "loud", "bright", "smell"
    // v40: Calendar scheduling
    scheduled_date?: Date;
    scheduled_time?: string; // e.g. "14:00" or null for "anytime"
    // v41: Recurrence
    recurrence?: {
        pattern: string; // e.g. "every Monday"
        nextDue: Date;
        fromCompletion: boolean; // if true, next instance created on completion. If false, fixed schedule.
    };

    // v42: Life Goals
    goal_id?: number; // Link to parent goal
}

export interface NotebookEntry {
    id?: number;
    project_id: number;
    title?: string;
    date: Date;
    content: string; // Markdown/HTML
    images?: Blob[];
    tags?: string[];
}

export interface ProjectTool {
    id?: number;
    project_id: number;
    name: string;
    status: 'owned' | 'borrow' | 'buy' | 'rent';
    is_acquired: boolean;
}

export interface ProjectMeasurement {
    id?: number;
    project_id: number;
    label: string;
    value: string;
    unit: string;
    is_verified: boolean;
}

export interface ProjectTest {
    id?: number;
    project_id: number;
    test_case: string;
    expected_value: string;
    actual_value: string;
    status: 'pending' | 'pass' | 'fail';
    notes: string;
}

export interface ProjectScript {
    id?: number;
    project_id: number;
    name: string;
    content: string;
    language: string; // 'javascript', 'python', 'json', etc.
    created_at: Date;
    updated_at: Date;
}

// v48: Songs & Albums System
export interface Song {
    id?: number;
    title: string;
    status: 'draft' | 'idea' | 'demo' | 'recording' | 'mixing' | 'mastering' | 'released';
    lyrics: string; // HTML/Markdown
    lyrics_structure?: Record<string, any>; // JSON Nodes/Edges
    duration: string; // "3:45"
    bpm?: number;
    key?: string;
    tags: string[];
    album_id?: number;
    track_number?: number;
    cover_art_url?: string;
    thumbnail_url?: string;
    created_at: Date;
    updated_at: Date;
    is_archived: boolean;
}

export interface Album {
    id?: number;
    title: string;
    artist?: string;
    status: 'planned' | 'in-progress' | 'released';
    release_date?: Date;
    cover_art_url?: string;
    created_at: Date;
    updated_at: Date;
}

// v49: Enhanced Songs System
export interface SongDocument {
    id?: number;
    song_id: number;
    title: string;
    content: string;
    order: number;
    type: 'lyrics' | 'notes' | 'concept';
    status: 'draft' | 'final';
    updated_at: Date;
}

export interface SongFile {
    id?: number;
    song_id: number;
    name: string;
    type: string; // mime type
    content: Blob;
    category: 'artwork' | 'attachment' | 'other';
    created_at: Date;
}

export interface AlbumFile {
    id?: number;
    album_id: number;
    name: string;
    type: string; // mime type
    content: Blob;
    category: 'artwork' | 'attachment' | 'other';
    created_at: Date;
}

export interface Recording {
    id?: number;
    song_id?: number; // Optional now for global recordings
    title: string;
    type: 'demo' | 'voice_memo' | 'stem' | 'master';
    file_path?: string;
    filename?: string;
    duration?: string;
    notes?: string;
    created_at: Date;
    content?: Blob;
    file_type?: string; // mime type
}

// v47: Dynamic Item Templates
export interface ItemTemplate {
    id?: number;
    name: string; // "Recipe", "Plant"
    collection_name: string; // "recipes", "plants"
    default_schema: Record<string, any>; // { ingredients: [], cook_time: 0 }
    icon?: string; // lucide icon name
    description_prompt?: string; // Prompt for AI to describe this item
}

export class ProjectManagerDB extends Dexie {
    projects!: Table<Project>;
    branches!: Table<Branch>;
    logs!: Table<Log>;
    inventory!: Table<InventoryItem>;
    project_files!: Table<ProjectFile>;
    project_bom!: Table<ProjectBOM>;
    project_tasks!: Table<ProjectTask>;
    notebook!: Table<NotebookEntry>;
    project_tools!: Table<ProjectTool>;
    project_measurements!: Table<ProjectMeasurement>;
    project_tests!: Table<ProjectTest>;
    project_scripts!: Table<ProjectScript>;
    system_config!: Table<SystemConfig>;
    inbox_items!: Table<InboxItem>;
    global_notes!: Table<GlobalNote>;
    purchase_items!: Table<PurchaseItem>;
    vendors!: Table<Vendor>;
    reminders!: Table<Reminder>;
    assets!: Table<Asset>;
    part_cache!: Table<PartCacheEntry>;
    project_templates!: Table<ProjectTemplate>;
    llm_instructions!: Table<LLMInstruction>;
    goals!: Table<Goal>;
    routines!: Table<Routine>; // v43

    links!: Table<EntityLink>; // v45: Universal Linkage
    project_documents!: Table<ProjectDocument>; // v46
    project_production_items!: Table<ProjectProductionItem>; // v46

    // v48: Songs & Albums
    songs!: Table<Song>;
    albums!: Table<Album>;
    recordings!: Table<Recording>;
    song_documents!: Table<SongDocument>; // v49
    song_files!: Table<SongFile>; // v49
    song_files!: Table<SongFile>; // v49
    album_files!: Table<AlbumFile>; // v50

    // v47-revisit: Activity Log (Hardening)
    activity_log!: Table<ActivityLogEntry>; // v47

    constructor() {
        super('ProjectManagerDB');
        console.log("[db] Constructor started");

        // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
        // CRITICAL DEVELOPER NOTE:
        // When adding new tables to this schema, you MUST also add them to 
        // `src/lib/sync-registry.ts`.
        //
        // Failure to do so will result in the new table being EXCLUDED from 
        // Backups, Snapshots, and Vault Sync.
        //
        // The codebase has a safety check in `SnapshotService` that will warn you,
        // but please don't rely on it. Update the registry immediately!
        // !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

        this.version(5).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness',
            branches: '++id, project_id, name, is_active',
            logs: '++id, project_id, branch_id, version, date, type',
            inventory: '++id, name, category, domain, quantity, location',
            project_files: '++id, project_id, associated_branch_id, name, type',
            project_bom: '++id, project_id, branch_id, part_name, inventory_item_id, status',
            project_tasks: '++id, project_id, status, phase, priority',

            notebook: '++id, project_id, date, *tags'
        });

        this.version(6).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date',
        });

        this.version(7).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category'
        });

        this.version(8).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, design_philosophy, golden_voltages'
        });

        this.version(9).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, design_philosophy, golden_voltages, is_archived'
        });

        this.version(10).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, design_philosophy, golden_voltages, is_archived, updated_at, priority'
        });

        this.version(11).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority'
        });

        this.version(12).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path'
        });

        this.version(13).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color'
        });

        this.version(14).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at'
        });

        this.version(15).stores({
            inventory: '++id, name, category, domain, quantity, location, units'
        });

        this.version(16).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage'
        });

        this.version(17).stores({
            inventory: '++id, name, category, domain, quantity, location, units, type', // Added type
            project_bom: '++id, project_id, branch_id, part_name, inventory_item_id, status, is_ordered, is_received', // Added procurement flags
            project_tools: '++id, project_id, status, is_acquired',
            project_measurements: '++id, project_id',
            project_tests: '++id, project_id, status'
        });

        this.version(18).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains'
        });

        this.version(19).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards'
        });

        this.version(20).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards'
        });

        this.version(21).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order'
        });

        this.version(22).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects'
        });
        this.version(23).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y'
        });
        this.version(25).stores({
            project_tasks: '++id, project_id, status, phase, priority, *upstream_task_ids, flow_x, flow_y'
        });
        this.version(26).stores({
            project_scripts: '++id, project_id, name, language'
        });
        this.version(27).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y, image_url'
        });

        this.version(28).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y, image_url, github_repo'
        });

        this.version(29).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y, image_url, github_repo, *print_parts'
        });

        this.version(30).stores({
            inventory: '++id, name, category, domain, quantity, location, units, type, mpn, manufacturer, barcode'
        });

        this.version(31).stores({
            project_tasks: '++id, project_id, status, phase, priority, *upstream_task_ids, flow_x, flow_y, is_high_priority, *caution_flags'
        });

        this.version(32).stores({
            system_config: 'key' // Key-value store for app settings (e.g. Vault Handle)
        });

        this.version(33).stores({
            inbox_items: '++id, type, created_at, suggested_action, triaged_at, triaged_to',
            global_notes: '++id, title, category, created_at, updated_at, pinned'
        });

        this.version(34).stores({
            purchase_items: '++id, name, status, priority, vendor_id, *project_ids, created_at',
            vendors: '++id, name',
            reminders: '++id, created_at, is_completed, priority'
        });

        this.version(35).stores({
            assets: '++id, name, category, status, *related_project_ids'
        });

        this.version(36).stores({
            inventory: '++id, name, category, domain, quantity, location, units, type, mpn, manufacturer, barcode', // No index change needed for new fields unless searched
            project_bom: '++id, project_id, branch_id, part_name, inventory_item_id, status, is_ordered, is_received',
            part_cache: '[provider+proxied_id], expires_at' // Composite key
        });

        this.version(37).stores({
            project_tasks: '++id, project_id, status, phase, priority, *upstream_task_ids, flow_x, flow_y, is_high_priority, *caution_flags, energy_level, *sensory_load'
        });

        this.version(38).stores({
            project_templates: '++id, name, category, is_custom' // New table for user templates
        });
        this.version(39).stores({
            project_templates: '++id, name, category, is_custom' // Schema unchanged, just field types update
        });

        this.version(40).stores({
            project_tasks: '++id, project_id, status, phase, priority, *upstream_task_ids, flow_x, flow_y, is_high_priority, *caution_flags, energy_level, *sensory_load'
        });

        // v41: LLM Instructions Management
        this.version(41).stores({
            llm_instructions: '++id, name, *tags, category, created_at, updated_at'
        });

        // v42: Life Goals System
        this.version(42).stores({
            goals: '++id, title, parent_id, level, status, priority, target_date, *tags',
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y, image_url, github_repo, *print_parts, goal_id',
            project_tasks: '++id, project_id, status, phase, priority, *upstream_task_ids, flow_x, flow_y, is_high_priority, *caution_flags, energy_level, *sensory_load, goal_id'
        });

        // v43: Routine Maintenance System
        this.version(43).stores({
            routines: '++id, title, frequency, season, last_completed, next_due, category, *google_event_id'
        });

        // v44: Universal Card System Integration (Routines)
        this.version(44).stores({
            routines: '++id, title, frequency, season, last_completed, next_due, category, *google_event_id, flow_x, flow_y, *linked_project_ids, *linked_goal_ids'
        });

        // v45: Universal Linkage System
        this.version(45).stores({
            links: '++id, source_type, source_id, target_type, target_id, relationship, [source_type+source_id], [target_type+target_id]'
        }).upgrade(async tx => {
            // == MIGRATION: Convert Legacy Project Dependencies to Universal Links ==
            console.log("[Migration v45] Starting Universal Link Migration...");

            // 1. Projects
            const projects = await tx.table('projects').toArray();
            const newLinks = [];

            for (const p of projects) {
                // Migrate Blockers (upstream_dependencies)
                if (p.upstream_dependencies && p.upstream_dependencies.length > 0) {
                    for (const blockerId of p.upstream_dependencies) {
                        newLinks.push({
                            source_type: 'project',
                            source_id: blockerId, // Blocker is source (blocks target)
                            target_type: 'project',
                            target_id: p.id!,
                            relationship: 'blocks',
                            created_at: new Date()
                        });
                    }
                }

                // Migrate Goal Links (goal_id)
                if (p.goal_id) {
                    newLinks.push({
                        source_type: 'goal',
                        source_id: p.goal_id,
                        target_type: 'project',
                        target_id: p.id!,
                        relationship: 'supports', // Goal supports Project (or Project supports Goal? Let's say Goal->Project supports relation)
                        // Actually, semantically "Project SUPPORTS Goal". 
                        // So Project is Source, Goal is Target. 
                        // Let's stick to: Project(Source) -> Goal(Target) = Supports
                        // Wait, usually arrows go from Dependency TO Dependent.
                        // But for "Supports", usually Low Level -> High Level.
                        // Let's stick to the Flowchart logic: Project -> Goal (Supports)
                    });
                    // Adjusting to match Flowchart v1
                    newLinks.push({
                        source_type: 'project',
                        source_id: p.id!,
                        target_type: 'goal',
                        target_id: p.goal_id,
                        relationship: 'supports',
                        created_at: new Date()
                    });
                }

                // Migrate Related Projects
                if (p.related_projects && p.related_projects.length > 0) {
                    for (const relId of p.related_projects) {
                        // Prevent duplicates (only link if ID < relId)
                        if (p.id! < relId) {
                            newLinks.push({
                                source_type: 'project',
                                source_id: p.id!,
                                target_type: 'project',
                                target_id: relId,
                                relationship: 'relates_to',
                                created_at: new Date()
                            });
                        }
                    }
                }
            }

            if (newLinks.length > 0) {
                await tx.table('links').bulkAdd(newLinks);
                console.log(`[Migration v45] Migrated ${newLinks.length} legacy connections to 'links' table.`);
            }
        });

        // v46: Manuscript & Production
        this.version(46).stores({
            project_documents: '++id, project_id, order, type',
            project_production_items: '++id, project_id, order, type',
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y, image_url, github_repo, *print_parts, goal_id'
        });

        // v47: Activity Log & Templates Update
        this.version(47).stores({
            activity_log: '++id, entity_type, entity_id, action_type, timestamp, actor',
            project_templates: '++id, slug, name, category, is_custom'
        });

        // v48: Songs & Albums System
        this.version(48).stores({
            songs: '++id, title, status, album_id, *tags',
            albums: '++id, title, status',
            recordings: '++id, song_id, type'
        });

        // v49: Enhanced Songs System (Manuscript & Files)
        this.version(49).stores({
            song_documents: '++id, song_id, order, type',
            song_files: '++id, song_id, type, category'
        });

        // v50: Album Files
        this.version(50).stores({
            album_files: '++id, album_id, type, category'
        });

        // v51: Granular Goal Data
        this.version(51).stores({
            goals: '++id, title, parent_id, level, status, priority, target_date, *tags' // Schema unchanged (fields not indexed), but bumping version for safety/migration trigger if needed
        });

        // v52: Dynamic Item Templates
        this.version(52).stores({
            item_templates: '++id, name, collection_name'
        });

        // v53: Library & Knowledge Base
        this.version(53).stores({
            library_items: '++id, type, title, tags, created_at'
        });

        // v54: Debug Logs (persistent crash-resistant logs for Universal Test Page)
        this.version(54).stores({
            debug_logs: '++id, timestamp, type'
        });
        // v55: Indexing created_at for sorting
        this.version(55).stores({
            projects: '++id, title, status, version, *tags, current_branch_id, intrusiveness, target_completion_date, parent_id, category, kingdom, phylum, design_philosophy, golden_voltages, is_archived, updated_at, priority, taxonomy_path, label_color, deleted_at, project_code, design_status, build_status, exp_cv_usage, *domains, *hazards, *upstream_dependencies, sort_order, *related_projects, flow_x, flow_y, image_url, github_repo, *print_parts, goal_id, created_at'
        });
    }

    // v52
    get item_templates() { return this.table('item_templates'); }
    // v53
    get library_items() { return this.table('library_items'); }
    // v54
    get debug_logs() { return this.table('debug_logs'); }
}

console.log("[db] Instantiating DB");
export const db = new ProjectManagerDB();
console.log("[db] DB Instantiated");

// ... (Interface update below)

export interface ProjectTemplate {
    id?: number;
    slug?: string; // Stable ID for default templates (e.g. 'pedal-analog')
    name: string;
    description: string;
    category: string;

    // === Defaults for Project Creation ===

    // Basic Config
    tags: string[];
    priority: number;
    status: Project['status'];
    github_repo?: string;

    // Classification / Taxonomy
    kingdom?: string;
    phylum?: string;
    taxonomy_path?: string;
    domains?: string[];
    label_color?: string;

    // Estimates & Budget
    time_estimate_active?: number;
    time_estimate_passive?: number;
    financial_budget?: number;
    total_theorized_hours?: number;

    // Design & Build Status
    design_status?: string;
    build_status?: string;
    risk_level?: 'low' | 'medium' | 'high';

    // Safety
    hazards?: string[];

    // Default External Resources
    external_links?: Array<{ label: string; url: string }>;

    // Default I/O and Specs
    io_spec?: string[];
    design_philosophy?: string;

    // Default Specs (JSON templates)
    specs_technical?: Record<string, unknown>;
    specs_performance?: Record<string, unknown>;
    specs_environment?: Record<string, unknown>;

    // === UI Settings ===
    settings?: {
        hidden_tabs?: string[];
    };

    // === Template Tasks ===
    tasks: Array<{
        title: string;
        phase: string;
        priority: 1 | 2 | 3 | 4 | 5;
        estimated_time?: string;
    }>;

    // Meta
    is_custom: boolean;
    created_at: Date;
}

export interface SystemConfig {
    key: string;
    value: any;
}

export interface InboxItem {
    id?: number;
    content: string;
    type: 'idea' | 'link' | 'photo' | 'task' | 'general';
    created_at: Date;
    // AI suggestions
    suggested_action?: 'create_project' | 'add_task' | 'reference' | 'someday';
    suggested_project_id?: number;
    suggested_project_title?: string;
    extracted_title?: string;
    confidence?: number;
    // Triage outcome
    triaged_at?: Date;
    triaged_to?: 'project' | 'task' | 'reference' | 'someday' | 'deleted';
    resolved_id?: number;
}

export interface GlobalNote {
    id?: number;
    title: string;
    content: string;
    category?: string;
    created_at: Date;
    updated_at: Date;
    pinned?: boolean;
}

export interface PurchaseItem {
    id?: number;
    name: string;
    quantity_needed: number;
    project_ids?: number[];          // Linked projects
    inventory_item_id?: number;      // For restock
    vendor_id?: number;              // Preferred vendor
    url?: string;

    // Costs
    estimated_unit_cost?: number;    // From BOM
    actual_unit_cost?: number;       // From Purchase
    currency?: string;               // 'USD' | 'EUR' etc.

    // Status
    status: 'planned' | 'ordered' | 'shipped' | 'arrived' | 'installed';
    priority: 1 | 2 | 3 | 4 | 5;     // 5 = urgent

    // Tracking
    order_date?: Date;
    expected_arrival?: Date;
    tracking_number?: string;
    invoice_path?: string;           // Path to saved invoice in vault

    created_at: Date;
    updated_at: Date;
}

export interface Vendor {
    id?: number;
    name: string;
    website?: string;
    api_integration?: 'octopart' | 'digikey' | 'none';
    api_key_ref?: string;            // Key name in system_config
}

export interface Reminder {
    id?: number;
    content: string;
    is_completed: boolean;
    priority: number;
    created_at: Date;
}

export interface PartCacheEntry {
    provider: string; // 'digikey', 'trustedparts'
    proxied_id: string; // The ID from the provider
    data: any; // The full JSON response
    expires_at: Date;
}

// === LLM Instructions Management ===
export interface LLMInstructionVersion {
    version: string;           // e.g., "1.0.0", "2.0.0-draft"
    content: string;           // The actual instruction text
    changelog: string;         // What changed in this version
    created_at: Date;
}

export interface LLMInstruction {
    id?: number;
    name: string;              // e.g., "Creative Writing Assistant"
    description: string;       // Purpose and use case
    category: string;          // e.g., "Creative", "Technical", "Research", "System"
    tags: string[];            // For filtering/searching

    // Current Active Version
    current_version: string;   // e.g., "1.2.0"
    content: string;           // Active instruction text

    // Version History
    versions: LLMInstructionVersion[];

    // File Management
    source_file?: string;      // Original filename if imported
    file_path?: string;        // Path if linked to filesystem

    // Git Integration
    github_repo?: string;      // e.g., "username/repo"
    github_path?: string;      // Path within repo
    github_branch?: string;    // Branch name
    last_sync?: Date;          // Last git sync time

    // Metadata
    author?: string;
    license?: string;          // e.g., "MIT", "CC-BY", "Proprietary"
    target_model?: string;     // e.g., "GPT-4", "Claude", "Gemini", "Universal"
    token_estimate?: number;   // Approximate token count

    // Status
    is_active: boolean;        // Whether this is deployable
    is_draft: boolean;         // Work in progress

    // Timestamps
    created_at: Date;
    updated_at: Date;
}

// === Life Goals System ===
export type GoalLevel = 'vision' | 'year' | 'quarter' | 'objective';
export type GoalStatus = 'active' | 'achieved' | 'paused' | 'abandoned';

export interface Goal {
    id?: number;
    title: string;
    description?: string;

    // Hierarchy
    parent_id?: number;          // For nesting (null = top-level)
    level: GoalLevel;            // vision > year > quarter > objective
    children_count?: number;     // Computed field for UI

    // Status & Progress
    status: GoalStatus;
    progress?: number;           // 0-100 percentage

    // Timing
    target_date?: Date;
    started_at?: Date;
    achieved_at?: Date;

    // Visual & Organization
    label_color?: string;        // e.g. "#ff6b6b"
    icon?: string;               // e.g. "target", "heart", "briefcase"
    priority?: number;           // 1-5
    tags?: string[];

    // Flowchart Positioning (for visualization)
    flow_x?: number;
    flow_y?: number;

    // Linked Items (computed via queries, not stored)
    // linked_projects and linked_tasks are fetched separately

    // Meta
    notes?: string;              // Markdown notes

    // v51 New Fields
    motivation?: string; // "Why" / Driving Force
    success_criteria?: string[]; // KPIs / Definition of Done
    review_cadence?: 'weekly' | 'monthly' | 'quarterly' | 'yearly';

    created_at: Date;
    updated_at: Date;
}

// === Routine Maintenance System ===
export interface Routine {
    id?: number;
    title: string;
    description?: string;
    frequency: 'daily' | 'weekly' | 'monthly' | 'quarterly' | 'yearly' | 'seasonal';
    season?: 'spring' | 'summer' | 'fall' | 'winter';
    last_completed?: Date;
    next_due: Date;
    category?: string; // e.g. "Home", "Digital", "Car"
    google_event_id?: string; // For future Google Calendar Sync
    created_at: Date;

    // v44: Universal Card System Integration
    flow_x?: number;
    flow_y?: number;
    linked_project_ids?: number[];
    linked_goal_ids?: number[];
}
