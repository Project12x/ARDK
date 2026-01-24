import { db } from './db';
import { ALL_TABLES } from './sync-registry';
import { toast } from 'sonner';

export function validateSchemaRegistry() {
    // Wait for DB to be ready/open (though Dexie tables are usually available synchronously on instance)
    const dbTables = db.tables.map(t => t.name);
    const registryTables = new Set(ALL_TABLES);

    const missing = dbTables.filter(t => !registryTables.has(t));

    if (missing.length > 0) {
        console.error("CRITICAL: The following tables are in DB but NOT in Sync Registry:", missing);
        // Delay toast slightly to ensure UI is ready
        setTimeout(() => {
            toast.error(`CRITICAL: Tables excluded from backup: ${missing.join(', ')}`, {
                duration: 20000,
                description: "Update src/lib/sync-registry.ts immediately!"
            });
        }, 2000);
    } else {
        console.log("[SchemaValidator] Registry is consistent with DB. All tables accounted for.");
    }
}
