/**
 * AlbumEntityAdapter
 * Transforms raw Album objects into UniversalEntity<Album>
 */

import type { Album } from '../../db';
import type { UniversalEntity } from '../types';

/**
 * Convert Album to UniversalEntity with full fidelity
 */
export function toUniversalAlbum(
    album: Album
): UniversalEntity<Album> {
    return {
        // Core Identity
        urn: `album:${album.id}`,
        id: album.id!,
        type: 'album',

        // Presentation
        title: album.title,
        subtitle: album.artist || getAlbumStatusLabel(album.status),
        icon: 'Disc',
        color: getAlbumColor(album.status),

        // Context
        status: album.status,
        tags: [],
        createdAt: album.created_at,
        updatedAt: album.updated_at,

        // Full Payload
        data: album,

        // Extended
        thumbnail: album.cover_art_url,
        metadata: {
            artist: album.artist,
            release_date: album.release_date,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Album',
            backgroundImage: album.cover_art_url,
            statusStripe: getAlbumColor(album.status),
            statusGlow: album.status === 'released',
            collapsible: true,

            metaGrid: [
                { label: 'Artist', value: album.artist || 'Unknown' },
                { label: 'Rel', value: album.release_date ? new Date(album.release_date).toLocaleDateString() : 'TBD' }
            ].filter(i => i.value !== 'Unknown' && i.value !== 'TBD'),

            ratings: [
                { label: 'Status', value: album.status === 'released' ? 100 : (album.status === 'in-progress' ? 50 : 10), max: 100, color: getAlbumColor(album.status) }
            ]
        }
    };
}

function getAlbumStatusLabel(status: string): string {
    switch (status) {
        case 'planned': return '📋 Planned';
        case 'in-progress': return '🎵 In Progress';
        case 'released': return '🚀 Released';
        default: return status;
    }
}

function getAlbumColor(status: string): string {
    switch (status) {
        case 'planned': return '#6b7280';
        case 'in-progress': return '#3b82f6';
        case 'released': return '#22c55e';
        default: return '#6b7280';
    }
}

export function toUniversalAlbumBatch(albums: Album[]): UniversalEntity<Album>[] {
    return albums.map(album => toUniversalAlbum(album));
}
