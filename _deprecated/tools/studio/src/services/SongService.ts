import { db } from '../lib/db';
import type { Song, Album, Recording, SongDocument, SongFile, AlbumFile } from '../lib/db';

export const SongService = {
    /**
     * Get all songs, optionally filtered by albumId
     */
    async getSongs(albumId?: number): Promise<Song[]> {
        if (albumId) {
            return await db.songs.where('album_id').equals(albumId).toArray();
        }
        return await db.songs.toArray();
    },

    /**
     * Get a single song by ID
     */
    async getSong(id: number): Promise<Song | undefined> {
        return await db.songs.get(id);
    },

    /**
     * Create a new song
     */
    async createSong(data: Partial<Song>): Promise<number> {
        const song: Omit<Song, 'id'> = {
            title: data.title || 'Untitled Song',
            album_id: data.album_id,
            track_number: data.track_number,
            duration: data.duration || '',
            lyrics: data.lyrics || '',
            lyrics_structure: data.lyrics_structure || {},
            status: data.status || 'idea',
            bpm: data.bpm,
            key: data.key,
            tags: data.tags || [],
            created_at: new Date(),
            updated_at: new Date(),
            is_archived: false
        };
        return await db.songs.add(song as Song);
    },

    /**
     * Update a song
     */
    async updateSong(id: number, updates: Partial<Song>): Promise<number> {
        return await db.songs.update(id, {
            ...updates,
            updated_at: new Date()
        });
    },

    /**
     * Delete a song
     */
    async deleteSong(id: number): Promise<void> {
        await db.songs.delete(id);
    },

    // --- ALBUMS ---

    async getAlbums(): Promise<Album[]> {
        return await db.albums.toArray();
    },

    async getAlbum(id: number): Promise<Album | undefined> {
        return await db.albums.get(id);
    },

    async createAlbum(data: Partial<Album>): Promise<number> {
        const album: Omit<Album, 'id'> = {
            title: data.title || 'Untitled Album',
            artist: data.artist || 'Unknown Artist',
            release_date: data.release_date,
            cover_art_url: data.cover_art_url,
            status: data.status || 'planned',
            created_at: new Date(),
            updated_at: new Date()
        };
        return await db.albums.add(album as Album);
    },

    async updateAlbum(id: number, updates: Partial<Album>): Promise<number> {
        return await db.albums.update(id, {
            ...updates,
            updated_at: new Date()
        });
    },

    async deleteAlbum(id: number): Promise<void> {
        // Optional: Unlink songs first? Or cascade delete?
        // For now, let's just keep songs but remove their album_id
        await db.songs.where('album_id').equals(id).modify({ album_id: undefined });
        await db.albums.delete(id);
    },

    // --- RECORDINGS ---

    async getRecordings(songId: number): Promise<Recording[]> {
        return await db.recordings.where('song_id').equals(songId).toArray();
    },

    async addRecording(data: Partial<Recording> & { content?: Blob }): Promise<number> {
        const recording: Omit<Recording, 'id'> = {
            song_id: data.song_id, // Now optional
            title: data.title || data.filename || 'Untitled Recording',
            type: data.type || 'demo',
            file_path: data.file_path || '',
            filename: data.filename || 'recording.mp3',
            created_at: new Date(),
            notes: data.notes,
            content: data.content, // Support blob storage if passed
            file_type: data.file_type
        };
        return await db.recordings.add(recording as Recording);
    },

    async deleteRecording(id: number): Promise<void> {
        await db.recordings.delete(id);
    },

    // --- MANUSCRIPT (DOCUMENTS) ---

    async createDocument(songId: number, title: string, type: SongDocument['type'] = 'lyrics'): Promise<number> {
        const count = await db.song_documents.where('song_id').equals(songId).count();
        return await db.song_documents.add({
            song_id: songId,
            title,
            content: '',
            order: count,
            type,
            status: 'draft',
            updated_at: new Date()
        } as SongDocument);
    },

    async updateDocument(id: number, updates: Partial<SongDocument>): Promise<number> {
        return await db.song_documents.update(id, {
            ...updates,
            updated_at: new Date()
        });
    },

    async deleteDocument(id: number): Promise<void> {
        await db.song_documents.delete(id);
    },

    // --- FILES (ATTACHMENTS/ARTWORK) ---

    async addFile(songId: number, file: Blob, category: SongFile['category'] = 'attachment'): Promise<number> {
        return await db.song_files.add({
            song_id: songId,
            name: (file as File).name || 'Unknown File',
            type: file.type,
            content: file,
            category,
            created_at: new Date()
        } as SongFile);
    },

    async deleteFile(id: number): Promise<void> {
        await db.song_files.delete(id);
    },

    async getFiles(songId: number): Promise<SongFile[]> {
        return await db.song_files.where('song_id').equals(songId).toArray();
    },

    // --- ALBUM FILES ---

    async addAlbumFile(albumId: number, file: Blob, category: AlbumFile['category'] = 'attachment'): Promise<number> {
        return await db.album_files.add({
            album_id: albumId,
            name: (file as File).name || 'Unknown File',
            type: file.type,
            content: file,
            category,
            created_at: new Date()
        } as AlbumFile);
    },

    async deleteAlbumFile(id: number): Promise<void> {
        await db.album_files.delete(id);
    },

    async getAlbumFiles(albumId: number): Promise<AlbumFile[]> {
        return await db.album_files.where('album_id').equals(albumId).toArray();
    }
};
