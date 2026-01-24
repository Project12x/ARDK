import JSZip from 'jszip';
import { saveAs } from 'file-saver';
import { db } from './db';
import { ALL_TABLES, LOCALSTORAGE_KEYS } from './sync-registry';

// Use dynamic db.tables instead of static registry for backups to ensure complete coverage.


export const BackupService = {
    /**
     * Exports all database content to a ZIP file.
     * Blobs are extracted and saved as separate files to work around JSON limitations.
     */
    async exportToZip() {
        const zip = new JSZip();
        const exportData: Record<string, any[]> = {};

        // 1. Iterate over all tables dynamically (Single Source of Truth)
        // This ensures we never miss a table even if sync-registry is outdated.
        const allTables = db.tables.map(t => t.name);

        for (const tableName of allTables) {
            const table = db.table(tableName);
            const records = await table.toArray();
            const processedRecords = [];

            for (const record of records) {
                const processed = { ...record };

                // Scan for Blobs to extract
                for (const [key, value] of Object.entries(record)) {
                    if (value instanceof Blob) {
                        const fileExt = value.type.split('/')[1] || 'bin';
                        const fileName = `${tableName}/${record.id}_${key}.${fileExt}`;

                        // Add file to ZIP
                        zip.file(fileName, value);

                        // Replace Blob with reference
                        // @ts-ignore
                        processed[key] = {
                            __type: 'blob_reference',
                            path: fileName,
                            mimeType: value.type
                        };
                    }
                }
                processedRecords.push(processed);
            }
            exportData[tableName] = processedRecords;
        }

        // 2. Add JSON data
        zip.file('database_dump.json', JSON.stringify(exportData, null, 2));

        // 2.5 Add localStorage settings (from central registry)
        const settingsBackup: Record<string, string | null> = {};
        LOCALSTORAGE_KEYS.forEach(key => {
            settingsBackup[key] = localStorage.getItem(key);
        });
        zip.file('local_settings.json', JSON.stringify(settingsBackup, null, 2));

        // 3. Generate and Save
        const content = await zip.generateAsync({ type: 'blob' });
        const date = new Date().toISOString().split('T')[0];
        saveAs(content, `antigravity_backup_${date}.zip`);
    },

    /**
     * Imports a ZIP backup, wiping the current database.
     */
    async importFromZip(file: File) {
        const zip = await JSZip.loadAsync(file);

        // 1. Read JSON
        const jsonFile = zip.file('database_dump.json');
        if (!jsonFile) throw new Error("Invalid Backup: Missing database_dump.json");

        const jsonContent = await jsonFile.async('string');
        const importData = JSON.parse(jsonContent);

        // 2. Reconstruct Blobs
        for (const tableName of Object.keys(importData)) {
            const records = importData[tableName];

            for (const record of records) {
                for (const [key, value] of Object.entries(record)) {
                    if (value && typeof value === 'object' && (value as any).__type === 'blob_reference') {
                        const ref = value as any;
                        const fileInZip = zip.file(ref.path);
                        if (fileInZip) {
                            const blob = await fileInZip.async('blob');
                            // Restore original mimetype if possible, though async('blob') might guess
                            const correctBlob = new Blob([blob], { type: ref.mimeType });
                            // @ts-ignore
                            record[key] = correctBlob;
                        }
                    }
                    // Fix Dates (JSON stringify converts dates to strings)
                    // We detect keys commonly associated with dates or rely on known schema?
                    // Dexie handles string dates okay, but Date objects are better.
                    // Let's do a heuristic for keys ending in _at or 'date'
                    if (typeof value === 'string' &&
                        (key.endsWith('_at') || key === 'date' || key === 'target_completion_date' || key === 'deleted_at')
                    ) {
                        const date = new Date(value);
                        if (!isNaN(date.getTime())) {
                            // @ts-ignore
                            record[key] = date;
                        }
                    }
                }
            }
        }

        // 3. Wipe and Restore in Transaction
        await db.transaction('rw', db.tables, async () => {
            // Nuke everything
            // @ts-ignore
            await Promise.all(db.tables.map(table => table.clear()));

            // Restore
            const currentTables = db.tables.map(t => t.name);
            for (const tableName of Object.keys(importData)) {
                if (currentTables.includes(tableName)) {
                    // @ts-ignore
                    await db.table(tableName).bulkAdd(importData[tableName]);
                }
            }
        });

        // 4. Restore localStorage settings
        const settingsFile = zip.file('local_settings.json');
        if (settingsFile) {
            try {
                const settingsContent = await settingsFile.async('string');
                const settings = JSON.parse(settingsContent);
                for (const [key, value] of Object.entries(settings)) {
                    if (value !== null) {
                        localStorage.setItem(key, value as string);
                    }
                }
                console.log("[Backup] localStorage settings restored.");
            } catch (e) {
                console.warn("[Backup] Failed to restore localStorage settings:", e);
            }
        }
    },

    /**
     * Wipes the entire database.
     */
    async factoryReset() {
        await db.transaction('rw', db.tables, async () => {
            // @ts-ignore
            await Promise.all(db.tables.map(table => table.clear()));
        });
    }
};
