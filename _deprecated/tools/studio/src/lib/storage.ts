import { db } from './db';

const VAULT_HANDLE_KEY = 'vault_root_handle';

export class StorageService {

    /**
     * Checks if a Vault is currently configured (handle exists in DB).
     */
    static async hasVault(): Promise<boolean> {
        const entry = await db.system_config.get(VAULT_HANDLE_KEY);
        return !!entry;
    }

    /**
     * Retrieves the persisted Directory Handle.
     * Note: Does NOT guarantee permissions.
     */
    static async getVaultHandle(): Promise<FileSystemDirectoryHandle | null> {
        const entry = await db.system_config.get(VAULT_HANDLE_KEY);
        return entry ? entry.value : null;
    }

    /**
     * Verifies if we have R/W permissions for the handle.
     * If not, it requests them (requires user gesture).
     */
    static async verifyPermission(handle: FileSystemDirectoryHandle, readWrite = true): Promise<boolean> {
        const options: FileSystemHandlePermissionDescriptor = {
            mode: readWrite ? 'readwrite' : 'read'
        };

        // Check if we already have permission
        if ((await handle.queryPermission(options)) === 'granted') {
            return true;
        }

        // Request permission
        if ((await handle.requestPermission(options)) === 'granted') {
            return true;
        }

        return false;
    }

    /**
     * Sets the new Vault Root (User picks a folder).
     * Saves handle to DB.
     */
    static async setVaultRoot(handle: FileSystemDirectoryHandle) {
        await db.system_config.put({
            key: VAULT_HANDLE_KEY,
            value: handle
        });
    }

    /**
     * Clears the Vault setting.
     */
    static async disconnectVault() {
        await db.system_config.delete(VAULT_HANDLE_KEY);
    }

    /**
     * Ensures a directory path exists.
     * @param path Array of folder names e.g. ['Projects', '123-MyProject']
     */
    static async ensureDirectory(root: FileSystemDirectoryHandle, path: string[]): Promise<FileSystemDirectoryHandle> {
        let current = root;
        for (const part of path) {
            current = await current.getDirectoryHandle(part, { create: true });
        }
        return current;
    }

    /**
     * Writes a file to a specific path in the Vault.
     */
    static async writeFile(root: FileSystemDirectoryHandle, path: string[], filename: string, content: string | Blob | BufferSource) {
        const dir = await this.ensureDirectory(root, path);
        const fileHandle = await dir.getFileHandle(filename, { create: true });
        const writable = await fileHandle.createWritable();
        await writable.write(content);
        await writable.close();
    }

    /**
     * Reads a file as text.
     */
    static async readFileText(root: FileSystemDirectoryHandle, path: string[], filename: string): Promise<string> {
        const dir = await this.ensureDirectory(root, path);
        const fileHandle = await dir.getFileHandle(filename);
        const file = await fileHandle.getFile();
        return await file.text();
    }
}
