import { db } from './db';
import { VaultService } from '../services/VaultService';
import { StorageService } from './storage';
import { PROJECT_SCOPED_TABLES, GLOBAL_TABLES, type GlobalTable } from './sync-registry';

// Use central registry as source of truth
const PROJECT_TABLES = [...PROJECT_SCOPED_TABLES];

// Debounce Map
const debounceTimers = new Map<number, ReturnType<typeof setTimeout>>();

function triggerProjectSync(projectId: number) {
    if (!projectId) return;

    // Clear existing timer
    if (debounceTimers.has(projectId)) {
        clearTimeout(debounceTimers.get(projectId)!);
    }

    // Set new timer
    const timer = setTimeout(() => {
        console.log(`[Vault Middleware] Auto-syncing Project #${projectId}`);
        // VaultService.syncProject handles getting the vault handle internally
        VaultService.syncProject(projectId).catch(err => {
            console.warn(`[Vault Middleware] Sync Failed for Project #${projectId} (Vault may not be connected)`, err);
        });
        debounceTimers.delete(projectId);
    }, 2000); // 2 second delay to batch rapid changes

    debounceTimers.set(projectId, timer);
}

// Global Sync Debounce
const globalDebounceTimers = new Map<string, ReturnType<typeof setTimeout>>();

function triggerGlobalSync(table: GlobalTable) {
    if (globalDebounceTimers.has(table)) {
        clearTimeout(globalDebounceTimers.get(table)!);
    }

    const timer = setTimeout(async () => {
        console.log(`[Vault Middleware] Auto-syncing Global Table: ${table}`);

        // Dynamic import to avoid circular dependency
        const handle = await StorageService.getVaultHandle();

        if (handle) {
            VaultService.syncTable(table, handle).catch(e => console.warn(`[Vault Middleware] Global Sync Failed for ${table}`, e));
        }
        globalDebounceTimers.delete(table);
    }, 3000); // 3 seconds - slightly longer for global stuff

    globalDebounceTimers.set(table, timer);
}

export function initVaultMiddleware() {
    console.log("[Vault] Initializing Real-time Sync Middleware...");

    // Hook Projects Table (Title/Status changes)
    db.projects.hook('updating', (_mod, prim, _obj, _trans) => {
        if (prim) triggerProjectSync(prim as number);
    });

    // Hook Related Tables (Tasks, BOM, Files, etc)
    PROJECT_TABLES.forEach(tableName => {
        const table = db.table(tableName);

        table.hook('creating', (_prim, obj, _trans) => {
            if (obj && obj.project_id) triggerProjectSync(obj.project_id);
        });

        table.hook('updating', (_mod, _prim, obj, _trans) => {
            // obj is the object *before* modification.
            if (obj && obj.project_id) triggerProjectSync(obj.project_id);
        });

        table.hook('deleting', (_prim, obj, _trans) => {
            if (obj && obj.project_id) triggerProjectSync(obj.project_id);
        });
        table.hook('deleting', (_prim, obj, _trans) => {
            if (obj && obj.project_id) triggerProjectSync(obj.project_id);
        });
    });

    // Hook Global Tables
    GLOBAL_TABLES.forEach(tableName => {
        const table = db.table(tableName);
        // We just need any change -> trigger sync

        table.hook('creating', () => triggerGlobalSync(tableName));
        table.hook('updating', () => triggerGlobalSync(tableName));
        table.hook('deleting', () => triggerGlobalSync(tableName));
    });
}
