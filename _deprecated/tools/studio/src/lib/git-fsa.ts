import { StorageService } from './storage';

// Basic FS adapter for isomorphic-git using File System Access API
// Note: This is an incomplete implementation focused on support for basic git operations (add, commit)
// Sync operations are NOT supported.

export class GitFSA {
    root: FileSystemDirectoryHandle;

    constructor(rootHandle: FileSystemDirectoryHandle) {
        this.root = rootHandle;
    }

    // Helper to resolve path
    async cleanPath(path: string): Promise<string[]> {
        return path.split('/').filter(p => p && p !== '.');
    }

    async getHandle(path: string, options: { create?: boolean, directory?: boolean } = {}) {
        const parts = await this.cleanPath(path);
        let current: FileSystemDirectoryHandle = this.root;

        // Traverse to parent
        for (let i = 0; i < parts.length - 1; i++) {
            current = await current.getDirectoryHandle(parts[i], { create: options.create });
        }

        const name = parts[parts.length - 1];
        if (!name) return this.root;

        if (options.directory) {
            return await current.getDirectoryHandle(name, { create: options.create });
        } else {
            return await current.getFileHandle(name, { create: options.create });
        }
    }

    promises = {
        readFile: async (path: string, options?: any) => {
            try {
                const parts = path.split('/').filter(p => p && p !== '.');
                const filename = parts.pop();
                if (!filename) throw new Error("Invalid path");

                // Use StorageService logic for traversal
                const content = await StorageService.readFileText(this.root, parts, filename);

                // encoding? Isomorphic-git usually expects Buffer or Uint8Array or String depending on opts.
                // If encoding is utf8 return string.
                if (options === 'utf8' || options?.encoding === 'utf8') {
                    return content;
                }
                // Else return Uint8Array (Buffer-like)
                return new TextEncoder().encode(content);
            } catch (e: any) {
                if (e.name === 'NotFoundError') {
                    const err: any = new Error('ENOENT');
                    err.code = 'ENOENT';
                    throw err;
                }
                throw e;
            }
        },

        writeFile: async (path: string, data: any, _options?: any) => {
            const parts = path.split('/').filter(p => p && p !== '.');
            const filename = parts.pop();
            if (!filename) throw new Error("Invalid path");

            // Write
            await StorageService.writeFile(this.root, parts, filename, data);
        },

        unlink: async (path: string) => {
            const parts = path.split('/').filter(p => p && p !== '.');
            const filename = parts.pop();
            if (!filename) return;

            const dir = await StorageService.ensureDirectory(this.root, parts);
            await dir.removeEntry(filename);
        },

        readdir: async (path: string) => {
            const parts = path.split('/').filter(p => p && p !== '.');
            let dir = this.root;

            if (parts.length > 0) {
                dir = await StorageService.ensureDirectory(this.root, parts);
            }

            const entries = [];
            // Cast to any to bypass TS lib limitation for AsyncIterable
            for await (const [name, _handle] of (dir as any).entries()) {
                entries.push(name);
            }
            return entries;
        },

        mkdir: async (path: string) => {
            await StorageService.ensureDirectory(this.root, path.split('/').filter(p => p && p !== '.'));
        },

        rmdir: async (path: string) => {
            const parts = path.split('/').filter(p => p && p !== '.');
            const dirname = parts.pop();
            if (!dirname) return;
            // Parent
            const parent = await StorageService.ensureDirectory(this.root, parts);
            await parent.removeEntry(dirname, { recursive: true });
        },

        stat: async (path: string) => {
            try {
                const parts = path.split('/').filter(p => p && p !== '.');
                const dir = this.root;
                let handle: FileSystemHandle | undefined;

                // Locate handle
                if (parts.length === 0) {
                    handle = this.root;
                } else {
                    const filename = parts.pop()!;
                    const parent = await StorageService.ensureDirectory(this.root, parts);
                    try {
                        handle = await parent.getFileHandle(filename);
                    } catch {
                        handle = await parent.getDirectoryHandle(filename);
                    }
                }

                if (!handle) throw new Error("ENOENT");

                const kind = handle.kind;
                // FSA doesn't give size/mtime for directories easily, and file mtime is async
                let size = 0;
                let mtimeMs = Date.now();
                const type = kind === 'directory' ? 2 : 1; // 2=dir, 1=file? No, standard stat has verify methods.

                if (kind === 'file') {
                    const file = await (handle as FileSystemFileHandle).getFile();
                    size = file.size;
                    mtimeMs = file.lastModified;
                }

                return {
                    dev: 0,
                    ino: 0,
                    mode: kind === 'directory' ? 16877 : 33188, // 040755 : 0100644
                    nlink: 1,
                    uid: 0,
                    gid: 0,
                    rdev: 0,
                    size: size,
                    blksize: 4096,
                    blocks: 0,
                    atimeMs: mtimeMs,
                    mtimeMs: mtimeMs,
                    ctimeMs: mtimeMs,
                    birthtimeMs: mtimeMs,
                    isDirectory: () => kind === 'directory',
                    isFile: () => kind === 'file',
                    isSymbolicLink: () => false
                };

            } catch (_e) {
                const err: any = new Error('ENOENT');
                err.code = 'ENOENT';
                throw err;
            }
        },

        lstat: async (path: string) => {
            // FSA doesn't support symlinks, so lstat == stat
            return this.promises.stat(path);
        }
    };
}
