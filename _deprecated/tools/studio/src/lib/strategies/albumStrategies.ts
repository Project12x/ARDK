
import type { ExportStrategy } from '../../types/export';
import { db, type Album, type Song, type Recording } from '../db';
import JSZip from 'jszip';
// @ts-ignore
import * as ID3WriterPkg from 'browser-id3-writer';
// @ts-ignore
const ID3Writer = ID3WriterPkg.default || ID3WriterPkg;
import { saveAs } from 'file-saver';

interface AlbumExportContext {
    albumId: number;
}

export const AlbumZipStrategy: ExportStrategy<AlbumExportContext> = {
    id: 'album-zip',
    name: 'Album Archive (Zip)',
    description: 'Export album as a Zip file containing tagged MP3s and cover art.',
    supportedFormats: [
        { id: 'json', label: 'Zip Archive', extension: 'zip' } // Using 'json' ID as placeholder for "binary package", label clarifies. Fix types if needed.
    ],
    getData: async (context) => {
        return [context];
    },

    transform: async (data, format) => {
        const { albumId } = data[0];
        const album = await db.albums.get(albumId);
        if (!album) throw new Error("Album not found");

        const songs = await db.songs.where('album_id').equals(albumId).toArray();
        const zip = new JSZip();
        const folder = zip.folder(album.title.replace(/[^a-z0-9]/gi, '_'));

        // Process Songs
        for (const song of songs) {
            // Find "Master" recording or "Demo"
            let recording = await db.recordings
                .where('song_id').equals(song.id!)
                .filter(r => r.type === 'master')
                .first();

            if (!recording) {
                recording = await db.recordings
                    .where('song_id').equals(song.id!)
                    .first();
            }

            if (recording && recording.content) {
                let fileBuffer = await recording.content.arrayBuffer();

                // Add ID3 Tags
                try {
                    const writer = new ID3Writer(fileBuffer);
                    writer.setFrame('TIT2', song.title)
                        .setFrame('TPE1', [album.artist || 'Unknown Artist'])
                        .setFrame('TALB', album.title)
                        .setFrame('TRCK', String(song.track_number || 0));

                    if (album.cover_art_url) {
                        // Fetch cover art if URL is valid blob or fetchable
                        // For now, assume we might skip cover art in ID3 if complicate to fetch
                        // But we can try fetching if it's external
                    }

                    writer.addTag();
                    fileBuffer = writer.arrayBuffer();
                } catch (e) {
                    console.warn("Failed to add ID3 tags", e);
                }

                const filename = `${String(song.track_number || 0).padStart(2, '0')} - ${song.title}.mp3`;
                folder?.file(filename, fileBuffer);
            }
        }

        // Add Cover Art to Folder if available
        // (Skipping for this MVP to ensure stability, or reading from album_files)
        const artFile = await db.album_files.where({ album_id: albumId, category: 'artwork' }).first();
        if (artFile && artFile.content) {
            folder?.file('cover.jpg', artFile.content);
        }

        const content = await zip.generateAsync({ type: 'blob' });
        return content;
    }
};
