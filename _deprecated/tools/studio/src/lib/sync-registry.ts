import { db } from './db';

/**
 * DYNAMIC SYNC REGISTRY
 * ======================
 * 
 * Automatically detects table categories based on schema introspection.
 * - Tables with 'project_id' index -> Project Scoped
 * - All other tables -> Global
 * 
 * This ensures new features are automatically supported in Backup, Sync, and LLM Context.
 */

// Helper to check schema
const isProjectScoped = (tableName: string) => {
    // Special exceptions if any (e.g. logs is debatable, but project_id implies project context)
    // currently logs was Global, but logic suggests Project Scoped is better.
    // We will stick to strict schema introspection.
    const table = db.table(tableName);
    return table.schema.indexes.some(idx => idx.name === 'project_id') ||
        table.schema.primKey.name === 'project_id' || // unlikely
        tableName === 'projects'; // 'projects' table itself is GLOBAL (root), despite maybe having IDs.
    // Wait, projects table DOES NOT have project_id. It has 'id'.
    // So 'projects' will naturally be Global. OK.
};

// Compute lists at runtime
// We filter out 'projects' explicitly from ProjectScoped just in case, though it lacks project_id index generally.
const allTableNames = db.tables.map(t => t.name);

export const PROJECT_SCOPED_TABLES = allTableNames.filter(name => {
    const table = db.table(name);
    // Explicitly exclude 'projects' from children tables
    if (name === 'projects') return false;

    // Check for project_id index
    return table.schema.indexes.some(idx => idx.name === 'project_id');
});

export const GLOBAL_TABLES = allTableNames.filter(name => !PROJECT_SCOPED_TABLES.includes(name));

// Re-export for compatibility
export const ALL_TABLES = allTableNames;

// ============================================
// LOCALSTORAGE KEYS
// These are backed up to local_settings.json
// ============================================
export const LOCALSTORAGE_KEYS = [
    // API Keys
    'OPENAI_API_KEY',
    'GEMINI_API_KEY',
    'ANTHROPIC_API_KEY',
    'TAVILY_API_KEY',
    'OCTOPART_API_KEY',
    'DIGIKEY_CLIENT_ID',
    'DIGIKEY_CLIENT_SECRET',
    'GROQ_API_KEY',

    // GitHub/Git
    'GITHUB_TOKEN',
    'GITHUB_REPO',
    'GIT_BRANCH',
    'GIT_PROXY',

    // Services
    'OLLAMA_URL',
    'PRINTER_IP',
    'PRINTER_API_KEY',
    'NWS_ZONE',

    // App State
    'ACTIVE_LLM_VENDOR',
    'GEMINI_VALID_MODELS',  // Cached model list

    // User Preferences
    'musicplayer_volume',
    'musicplayer_muted',
    'quick_capture_draft',

    // AI Configuration
    'AI_PROVIDER',
    'AI_MODEL',
    'AI_TEMPERATURE',
    'OLLAMA_MODEL',

    // GitHub Extended
    'GITHUB_OWNER',

    // System Handles (Flags)
    'VAULT_ROOT_HANDLE' // Existence check only
] as const;

// ============================================
// Type Exports
// ============================================
// Since arrays are dynamic strings now, we can't strict type specific table names easily without 'as const',
// but for consumers this is usually string[] anyway.
export type ProjectScopedTable = string;
export type GlobalTable = string;
export type SyncableTable = string;
export type LocalStorageKey = typeof LOCALSTORAGE_KEYS[number];

