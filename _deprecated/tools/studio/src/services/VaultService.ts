import { db } from '../lib/db';
import { StorageService } from '../lib/storage';
import git from 'isomorphic-git';
import http from 'isomorphic-git/http/web';
import { GitFSA } from '../lib/git-fsa';
import { LOCALSTORAGE_KEYS, GLOBAL_TABLES, PROJECT_SCOPED_TABLES, type GlobalTable } from '../lib/sync-registry';

export class VaultService {

    /**
     * Entry point to sync a project to the vault.
     * Call this after a project save.
     */
    static async syncProject(projectId: number, activeHandle?: FileSystemDirectoryHandle | null) {
        if (!projectId) return;

        // 1. Check if Vault is active
        let handle = activeHandle;
        if (!handle) {
            handle = await StorageService.getVaultHandle();
        }

        if (!handle) return; // Vault not configured

        // 2. Check permissions (fail silently if not granted to avoid nagging)
        // Ideally, we check this once on app boot/interaction.
        const hasPerm = await StorageService.verifyPermission(handle, true);
        if (!hasPerm) {
            console.warn("Vault Sync Skipped: No permission");
            return;
        }

        // 3. Fetch Data
        const project = await db.projects.get(projectId);
        if (!project) return;

        // 3. Fetch Data & Write dynamically
        // We iterate ALL project scoped tables to ensure nothing is missed.
        try {
            const projectFolder = `Projects/${project.id} - ${this.sanitizeName(project.title)}`;

            // Ensure main project file exists
            await StorageService.writeFile(handle, projectFolder.split('/'), 'project.json', JSON.stringify(project, null, 2));

            for (const tableName of PROJECT_SCOPED_TABLES) {
                // Skip the project itself implies (it's the parent), and special handlers we do manually later/or inside loop
                if (tableName === 'projects') continue;

                const rows = await db.table(tableName).where('project_id').equals(projectId).toArray();

                // Skip empty tables to reduce clutter? Or Keep for completeness?
                // User wants "full file structure". Empty files are noise. Skip empty.
                if (rows.length === 0) continue;

                // SPECIAL HANDLERS
                if (tableName === 'project_files') {
                    // Handled by syncProjectFiles below (binary extraction)
                    continue;
                }
                if (tableName === 'project_scripts') {
                    for (const s of rows) {
                        const ext = s.language === 'python' ? 'py' : s.language === 'javascript' ? 'js' : s.language === 'json' ? 'json' : 'txt';
                        await StorageService.writeFile(handle, [...projectFolder.split('/'), 'scripts'], `${s.name}.${ext}`, s.content);
                    }
                    continue;
                }
                if (tableName === 'notebook') {
                    // Match Global Notebook sync style
                    for (const entry of rows) {
                        const safeEntry = { ...entry, images: undefined }; // strip blobs
                        const dateStr = entry.date instanceof Date ? entry.date.toISOString().split('T')[0] : 'nodate';
                        await StorageService.writeFile(handle, [...projectFolder.split('/'), 'notebook'], `${dateStr}_${entry.id}.json`, JSON.stringify(safeEntry, null, 2));

                        if (entry.images && entry.images.length > 0) {
                            for (let i = 0; i < entry.images.length; i++) {
                                await StorageService.writeFile(handle, [...projectFolder.split('/'), 'notebook'], `${dateStr}_${entry.id}_img${i}.png`, entry.images[i]);
                            }
                        }
                    }
                    continue;
                }

                // DEFAULT HANDLER (JSON Dump + Blob Extraction)
                const simpleName = tableName.replace(/^project_/, ''); // bom, tasks, tools

                // We use the Universal Extractor here too.
                // Assets go to filtered subfolder: Projects/ID/assets/tablename/
                const assetPath = projectFolder.split('/').concat(['assets', simpleName]);

                const { safeRows } = await this.extractBlobsAndSerialize(rows, handle, assetPath);

                await StorageService.writeFile(handle, projectFolder.split('/'), `${simpleName}.json`, JSON.stringify(safeRows, null, 2));
            }

            // Sync Associated Files (Blobs)
            await this.syncProjectFiles(projectId, handle);


        } catch (err) {
            console.error("[Vault] Sync Failed:", err);
        }
    }

    static async syncProjectFiles(projectId: number, handle: FileSystemDirectoryHandle) {
        const files = await db.project_files.where('project_id').equals(projectId).toArray();
        const project = await db.projects.get(projectId);
        if (!project || files.length === 0) return;

        const projectFolder = `Projects/${project.id} - ${this.sanitizeName(project.title)}/assets`;

        for (const file of files) {
            try {
                // Ensure unique name or use stored name
                const filename = file.name;
                // We use StorageService to write the Blob directly
                await StorageService.writeFile(handle, projectFolder.split('/'), filename, file.content);
            } catch (e) {
                console.warn(`[Vault] Failed to write asset ${file.name}`, e);
            }
        }
    }

    /**
     * Syncs ALL projects to the vault.
     * Use this on initial setup or "Force Sync".
     */
    static async syncAll(activeHandle?: FileSystemDirectoryHandle | null): Promise<number> {
        let handle = activeHandle;
        if (!handle) {
            handle = await StorageService.getVaultHandle();
        }

        if (!handle) {
            console.error("[Vault] SyncAll failed: No handle found.");
            return 0;
        }

        const hasPerm = await StorageService.verifyPermission(handle, true);
        if (!hasPerm) {
            console.error("[Vault] SyncAll failed: Permission denied.");
            return 0;
        }

        const projects = await db.projects.toArray();
        let count = 0;


        for (const p of projects) {
            if (p.id) {
                // Pass the handle to avoid re-fetching/re-checking for each project if possible, 
                // but syncProject currently fetches it internally. 
                // We should ideally refactor syncProject too, but for now let's rely on the fact permissions are cached on the handle object if it's the same reference? 
                // Actually syncProject calls StorageService.getVaultHandle(). 
                // Let's refactor syncProject to accept handle too.
                await this.syncProject(p.id, handle);
                count++;
            }
        }



        // Universal Global Sync
        for (const table of GLOBAL_TABLES) {
            await this.syncTable(table, handle);
        }

        // Auto-commit

        // Auto-commit
        if (count > 0) {
            await this.commit(`Auto-Sync: ${count} projects updated`);
        }

        return count;
    }

    /**
     * Dispatcher for syncing any GlobalTable.
     * Used by syncAll and Real-time Middleware.
     */
    static async syncTable(table: GlobalTable, handle: FileSystemDirectoryHandle) {
        switch (table) {
            case 'inventory': return this.syncInventory(handle);
            case 'inbox_items': return this.syncInbox(handle);
            case 'global_notes': return this.syncNotes(handle);
            case 'purchase_items': return this.syncPurchasing(handle);
            case 'vendors': return this.syncPurchasing(handle); // Valid: purchasing syncs both
            case 'system_config': return this.syncSystemConfig(handle);
            case 'logs': return this.syncLogs(handle);
            case 'assets': return this.syncAssets(handle);
            case 'reminders': return this.syncReminders(handle);
            case 'part_cache': return this.syncPartCache(handle);
            case 'project_templates': return this.syncTemplates(handle);
            case 'goals': return this.syncGoals(handle);
            case 'llm_instructions': return this.syncLLMInstructions(handle);
            case 'projects': return; // Projects are synced individually

            // Music System (Consolidated Sync)
            case 'songs': return this.syncSongs(handle);
            case 'albums': return this.syncAlbums(handle);
            case 'recordings': return; // Handled by syncSongs
            case 'song_documents': return; // Handled by syncSongs
            case 'song_files': return; // Handled by syncSongs
            case 'album_files': return; // Handled by syncAlbums

            default:
                // FALLBACK: Dump Unknown Tables to 'Global' folder
                return this.syncGenericGlobal(table, handle);
        }
    }

    static async syncSongs(handle: FileSystemDirectoryHandle) {
        try {
            const songs = await db.songs.toArray();
            const musicDir = ['Music', 'Songs'];

            for (const song of songs) {
                const folderName = `${song.id} - ${this.sanitizeName(song.title)}`;
                const path = [...musicDir, folderName];

                // 1. Sync Metadata
                await StorageService.writeFile(handle, path, 'song.json', JSON.stringify(song, null, 2));

                // 2. Sync Documents
                const docs = await db.song_documents.where({ song_id: song.id }).toArray();
                if (docs.length > 0) {
                    await StorageService.writeFile(handle, path, 'documents.json', JSON.stringify(docs, null, 2));
                }

                // 3. Sync Recordings
                const recordings = await db.recordings.where({ song_id: song.id }).toArray();
                for (const rec of recordings) {
                    if (rec.content) {
                        try {
                            const ext = rec.file_type?.split('/')[1] || 'webm'; // default to webm if unknown
                            const filename = `recordings/${rec.title}.${ext}`;
                            // Write blob
                            await StorageService.writeFile(handle, path, filename, rec.content);
                        } catch (e) {
                            console.warn(`[Vault] Failed to write recording ${rec.title}`, e);
                        }
                    }
                }

                // 4. Sync Files (Artwork/Other)
                const files = await db.song_files.where({ song_id: song.id }).toArray();
                for (const file of files) {
                    if (file.content) {
                        const ext = file.type?.split('/')[1] || 'bin';
                        const filename = `files/${file.category}/${file.name}`; // e.g. files/artwork/cover.jpg
                        await StorageService.writeFile(handle, path, filename, file.content);
                    }
                }
            }
        } catch (e) {
            console.error("[Vault] Songs Sync Failed", e);
        }
    }

    static async syncAlbums(handle: FileSystemDirectoryHandle) {
        try {
            const albums = await db.albums.toArray();
            const musicDir = ['Music', 'Albums'];

            for (const album of albums) {
                const folderName = `${album.id} - ${this.sanitizeName(album.title)}`;
                const path = [...musicDir, folderName];

                // 1. Metadata
                await StorageService.writeFile(handle, path, 'album.json', JSON.stringify(album, null, 2));

                // 2. Files (Artwork)
                const files = await db.album_files.where({ album_id: album.id }).toArray();
                for (const file of files) {
                    if (file.content) {
                        const filename = `files/${file.category}/${file.name}`;
                        await StorageService.writeFile(handle, path, filename, file.content);
                    }
                }
            }
        } catch (e) {
            console.error("[Vault] Albums Sync Failed", e);
        }
    }

    static async syncInventory(handle: FileSystemDirectoryHandle) {
        const items = await db.inventory.toArray();
        const json = JSON.stringify(items, null, 2);
        try {
            await StorageService.writeFile(handle, ['Inventory'], 'items.json', json);
        } catch (e) {
            console.error("[Vault] Inventory Sync Failed", e);
        }
    }

    static async syncInbox(handle: FileSystemDirectoryHandle) {
        const items = await db.inbox_items.toArray();
        const json = JSON.stringify(items, null, 2);
        try {
            await StorageService.writeFile(handle, ['Inbox'], 'inbox.json', json);
        } catch (e) {
            console.error("[Vault] Inbox Sync Failed", e);
        }
    }

    static async syncNotes(handle: FileSystemDirectoryHandle) {
        const notes = await db.global_notes.toArray();
        const json = JSON.stringify(notes, null, 2);
        try {
            await StorageService.writeFile(handle, ['Notes'], 'global_notes.json', json);
        } catch (e) {
            console.error("[Vault] Notes Sync Failed", e);
        }
    }

    // Note: Notebooks are now project-scoped primarily, but we kept syncNotebooks for generic "Notebook" table dump if needed?
    // The "notebook" table in db.ts is `notebook`. sync-registry says it's PROJECT_SCOPED.
    // So it shouldn't be in GLOBAL_TABLES.
    // Checking sync-registry... yes, 'notebook' is PROJECT_SCOPED.
    // So syncAll shouldn't call syncNotebooks() as a global dump unless there are "global" notebooks?
    // Current db schema shows project_id is a field, could be optional? "++id, project_id, ..."
    // If project_id is optional, they are global. But typical use is project scoped.
    // For universal sync, let's leave legacy syncNotebooks out of GLOBAL loop if it's not in GLOBAL_TABLES.

    static async syncPurchasing(handle: FileSystemDirectoryHandle) {
        try {
            const items = await db.purchase_items.toArray();
            const vendors = await db.vendors.toArray();
            const data = { items, vendors };
            await StorageService.writeFile(handle, ['Global'], 'purchasing.json', JSON.stringify(data, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncSystemConfig(handle: FileSystemDirectoryHandle) {
        try {
            const configs = await db.system_config.toArray();
            const safeConfigs = configs.filter(c => c.key !== 'vault_handle');
            await StorageService.writeFile(handle, ['System'], 'config.json', JSON.stringify(safeConfigs, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncLogs(handle: FileSystemDirectoryHandle) {
        try {
            const logs = await db.logs.toArray();
            await StorageService.writeFile(handle, ['System'], 'logs.json', JSON.stringify(logs, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncAssets(handle: FileSystemDirectoryHandle) {
        try {
            const assets = await db.assets.toArray();
            await StorageService.writeFile(handle, ['Assets'], 'assets.json', JSON.stringify(assets, null, 2));
        } catch (e) {
            console.error("[Vault] Asset Registry Sync Failed", e);
        }
    }

    static async syncReminders(handle: FileSystemDirectoryHandle) {
        try {
            const reminders = await db.reminders.toArray();
            await StorageService.writeFile(handle, ['Global'], 'reminders.json', JSON.stringify(reminders, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncPartCache(handle: FileSystemDirectoryHandle) {
        try {
            const cache = await db.part_cache.toArray();
            await StorageService.writeFile(handle, ['System'], 'part_cache.json', JSON.stringify(cache, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncTemplates(handle: FileSystemDirectoryHandle) {
        try {
            const temps = await db.project_templates.toArray();
            await StorageService.writeFile(handle, ['Global'], 'templates.json', JSON.stringify(temps, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncGoals(handle: FileSystemDirectoryHandle) {
        try {
            const goals = await db.goals.toArray();
            await StorageService.writeFile(handle, ['Global'], 'goals.json', JSON.stringify(goals, null, 2));
        } catch (e) { console.error(e); }
    }

    static async syncSettings(handle: FileSystemDirectoryHandle) {
        // Backup localStorage keys (from central registry)
        const keysToBackup = [...LOCALSTORAGE_KEYS];

        const settings: Record<string, string | null> = {};
        keysToBackup.forEach(k => {
            const val = localStorage.getItem(k);
            if (val) settings[k] = val;
        });

        try {
            // Save to a specialized file
            await StorageService.writeFile(handle, ['System'], 'local_settings.json', JSON.stringify(settings, null, 2));
        } catch (e) {
            console.error("[Vault] Settings Sync Failed", e);
        }
    }

    static async syncLLMInstructions(handle: FileSystemDirectoryHandle) {
        try {
            // Write to local_settings.json for backup parity
            await this.syncSettings(handle);

            const instructions = await db.llm_instructions.toArray();
            for (const inst of instructions) {
                const folder = ['LLM Instructions', inst.category || 'Other'];
                const filename = `${this.sanitizeName(inst.name)}.md`;
                const frontmatter = [
                    '---',
                    `name: ${inst.name}`,
                    `description: ${inst.description.replace(/\n/g, ' ')}`,
                    `category: ${inst.category}`,
                    `tags: [${inst.tags.join(', ')}]`,
                    `version: ${inst.current_version}`,
                    `last_updated: ${inst.updated_at.toISOString()}`,
                    '---',
                    '',
                    inst.content
                ].join('\n');

                await StorageService.writeFile(handle, folder, filename, frontmatter);
            }
        } catch (e) {
            console.error("[Vault] LLM Instructions Sync Failed", e);
        }
    }

    /**
     * Syncs a file asset to the project's asset folder in the vault.
     */
    static async syncAsset(projectId: number, file: File | Blob, filename: string) {
        const handle = await StorageService.getVaultHandle();
        if (!handle || !(await StorageService.verifyPermission(handle, true))) return;

        const project = await db.projects.get(projectId);
        if (!project) return;

        const projectFolder = `Projects/${project.id} - ${this.sanitizeName(project.title)}/assets`;

        try {
            await StorageService.writeFile(handle, projectFolder.split('/'), filename, file);
        } catch (err) {
            console.error("[Vault] Asset Save Failed:", err);
        }
    }

    private static sanitizeName(name: string) {
        return name.replace(/[^a-z0-9]/gi, '_').replace(/_+/g, '_');
    }

    /**
     * Commits all changes to the local git repo in Vault.
     */
    static async commit(message: string, activeHandle?: FileSystemDirectoryHandle | null) {
        let handle = activeHandle;
        if (!handle) {
            handle = await StorageService.getVaultHandle();
        }
        if (!handle) return;

        const fs = new GitFSA(handle);
        const dir = '/'; // Root of FSA

        try {
            // 1. Init if needed (non-destructive)
            await git.init({ fs, dir });

            // 2. Add All
            await git.add({ fs, dir, filepath: '.' });

            // 3. Commit
            const sha = await git.commit({
                fs,
                dir,
                message,
                author: {
                    name: 'Workshop Oracle',
                    email: 'oracle@antigravity.local'
                }
            });

            return sha;
        } catch (e) {
            console.error("[Vault] Git Commit Failed:", e);
        }
    }

    static async push(activeHandle?: FileSystemDirectoryHandle) {
        const handle = activeHandle || await StorageService.getVaultHandle();
        if (!handle) return;
        const config = this.getGitConfig();
        if (!config.token || !config.repo) {
            console.warn("[Vault] Push skipped: Missing GIT credentials (GITHUB_TOKEN, GITHUB_REPO)");
            return;
        }

        const fs = new GitFSA(handle);
        const dir = '/';

        try {
            await git.addRemote({ fs, dir, remote: 'origin', url: config.repo, force: true });


            const pushResult = await git.push({
                fs,
                http,
                dir,
                remote: 'origin',
                ref: config.branch,
                onAuth: () => ({ username: config.token || undefined }),
                corsProxy: config.proxy
            });

            return pushResult;
        } catch (e) {
            console.error("[Vault] Git Push Failed", e);
            throw e;
        }
    }

    static async pull(activeHandle?: FileSystemDirectoryHandle) {
        const handle = activeHandle || await StorageService.getVaultHandle();
        if (!handle) return;
        const config = this.getGitConfig();
        if (!config.token || !config.repo) return;

        const fs = new GitFSA(handle);
        const dir = '/';

        try {
            await git.addRemote({ fs, dir, remote: 'origin', url: config.repo, force: true });



            const result = await git.pull({
                fs,
                http,
                dir,
                remote: 'origin',
                ref: config.branch,
                singleBranch: true,
                onAuth: () => ({ username: config.token || undefined }),
                corsProxy: config.proxy,
                author: {
                    name: 'Workshop Oracle',
                    email: 'oracle@antigravity.local'
                }
            });

            return result;
        } catch (e) {
            console.error("[Vault] Git Pull Failed", e);
            throw e;
        }
    }

    private static getGitConfig() {
        const token = localStorage.getItem('GITHUB_TOKEN');
        let repo = localStorage.getItem('GITHUB_REPO');
        const branch = localStorage.getItem('GIT_BRANCH') || 'main';
        const proxy = localStorage.getItem('GIT_PROXY') || 'https://cors.isomorphic-git.org';

        if (repo && !repo.startsWith('http')) {
            repo = `https://github.com/${repo}.git`;
        }

        return { token, repo, branch, proxy };
    }
    /**
     * Fallback for unknown global tables.
     * Dumps content to Global/{tableName}.json
     */
    /**
     * Fallback for unknown global tables.
     * Dumps content to Global/{tableName}.json AND extracts any blobs found.
     */
    static async syncGenericGlobal(tableName: string, handle: FileSystemDirectoryHandle) {
        try {
            // @ts-ignore - dynamic table access
            const table = db.table(tableName);
            const rows = await table.toArray();
            if (rows.length === 0) return;

            // Use Universal Blob Extractor
            const { safeRows } = await this.extractBlobsAndSerialize(rows, handle, ['Global', '_assets', tableName]);

            await StorageService.writeFile(handle, ['Global'], `${tableName}.json`, JSON.stringify(safeRows, null, 2));
        } catch (e) {
            console.error(`[Vault] Generic Sync Failed for ${tableName}`, e);
        }
    }

    /**
     * UNIVERSAL BLOB EXTRACTOR
     * Scans records for Blobs, saves them to file system, and replaces them with string paths in JSON.
     * Hardens functionality for ANY future table structure.
     */
    static async extractBlobsAndSerialize(rows: any[], handle: FileSystemDirectoryHandle, assetBasePath: string[]) {
        const safeRows = [];

        for (const row of rows) {
            const safeRow = { ...row };
            const id = row.id || 'noid';

            for (const key of Object.keys(safeRow)) {
                const value = safeRow[key];

                // 1. Direct Blob
                if (value instanceof Blob) {
                    const ext = value.type.split('/')[1] || 'bin';
                    const filename = `${id}_${key}.${ext}`;
                    await StorageService.writeFile(handle, assetBasePath, filename, value);
                    safeRow[key] = `file://${assetBasePath.join('/')}/${filename}`;
                }
                // 2. Array of Blobs (e.g. simple gallery)
                else if (Array.isArray(value) && value.length > 0 && value[0] instanceof Blob) {
                    const newArray = [];
                    for (let i = 0; i < value.length; i++) {
                        const blob = value[i];
                        const ext = blob.type.split('/')[1] || 'bin';
                        const filename = `${id}_${key}_${i}.${ext}`;
                        await StorageService.writeFile(handle, assetBasePath, filename, blob);
                        newArray.push(`file://${assetBasePath.join('/')}/${filename}`);
                    }
                    safeRow[key] = newArray;
                }
                // 3. Nested Objects? (Might be overkill for now, keeping flat primarily + arrays)
            }
            safeRows.push(safeRow);
        }

        return { safeRows };
    }
}
