/**
 * SongEntityAdapter
 * Transforms raw Song objects into UniversalEntity<Song>
 * Zero data loss - original object preserved in data payload
 */

import type { Song } from '../../db';
import type { UniversalEntity, UniversalFile } from '../types';

export interface SongRelatedData {
    album?: { id: number; title: string };
    recordings?: { id: number; title: string; type: string }[];
    documents?: { id: number; title: string }[];
    files?: { id: number; name: string; type: string }[];
}

/**
 * Convert Song to UniversalEntity with full fidelity
 */
export function toUniversalSong(
    song: Song,
    related?: SongRelatedData
): UniversalEntity<Song> {
    return {
        // Core Identity
        urn: `song:${song.id}`,
        id: song.id!,
        type: 'song',

        // Presentation
        title: song.title,
        subtitle: related?.album?.title || getSongStatusLabel(song.status),
        icon: 'Music',
        color: getSongColor(song.status),

        // Context
        status: song.status,
        tags: song.tags || [],
        createdAt: song.created_at,
        updatedAt: song.updated_at,

        // Full Payload (Zero Data Loss)
        data: song,

        // Extended Fields
        progress: getSongProgress(song.status),
        thumbnail: song.cover_art_url || song.thumbnail_url,
        metadata: {
            duration: song.duration,
            bpm: song.bpm,
            key: song.key,
            album_id: song.album_id,
            track_number: song.track_number,
            lyrics_structure: song.lyrics_structure,
            is_archived: song.is_archived,
        },
        relatedData: {
            album: related?.album ? [related.album] : [],
            recordings: related?.recordings || [],
            documents: related?.documents || [],
            files: related?.files || [],
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Song',
            backgroundImage: song.cover_art_url || song.thumbnail_url, // Use cover art
            statusStripe: getSongColor(song.status),
            statusGlow: song.status === 'released',
            collapsible: true,

            metaGrid: [
                { label: 'BPM', value: song.bpm || '' },
                { label: 'Key', value: song.key || '' },
                { label: 'Dur', value: song.duration ? `${Math.floor(song.duration / 60)}:${(song.duration % 60).toString().padStart(2, '0')}` : '' }
            ].filter(i => !!i.value),

            ratings: [
                { label: 'Stage', value: getSongProgress(song.status), max: 100, color: getSongColor(song.status) }
            ]
        }
    };
}

/**
 * Get song status display label
 */
function getSongStatusLabel(status: string): string {
    switch (status) {
        case 'draft': return '📝 Draft';
        case 'idea': return '💡 Idea';
        case 'demo': return '🎤 Demo';
        case 'recording': return '🎙️ Recording';
        case 'mixing': return '🎛️ Mixing';
        case 'mastering': return '🔊 Mastering';
        case 'released': return '🚀 Released';
        default: return status;
    }
}

/**
 * Get color based on song status
 */
function getSongColor(status: string): string {
    switch (status) {
        case 'idea': return '#8b5cf6'; // purple
        case 'draft': return '#6b7280'; // gray
        case 'demo': return '#f59e0b'; // amber
        case 'recording': return '#3b82f6'; // blue
        case 'mixing': return '#06b6d4'; // cyan
        case 'mastering': return '#ec4899'; // pink
        case 'released': return '#22c55e'; // green
        default: return '#6b7280';
    }
}

/**
 * Get progress based on song status
 */
function getSongProgress(status: string): number {
    switch (status) {
        case 'idea': return 10;
        case 'draft': return 20;
        case 'demo': return 40;
        case 'recording': return 60;
        case 'mixing': return 75;
        case 'mastering': return 90;
        case 'released': return 100;
        default: return 0;
    }
}

/**
 * Batch convert multiple songs
 */
export function toUniversalSongBatch(
    songs: Song[]
): UniversalEntity<Song>[] {
    return songs.map(song => toUniversalSong(song));
}
