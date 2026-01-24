/**
 * RecordingEntityAdapter
 * Transforms raw Recording objects into UniversalEntity<Recording>
 */

import type { Recording } from '../../db';
import type { UniversalEntity } from '../types';

/**
 * Convert Recording to UniversalEntity with full fidelity
 */
export function toUniversalRecording(
    recording: Recording
): UniversalEntity<Recording> {
    return {
        // Core Identity
        urn: `recording:${recording.id}`,
        id: recording.id!,
        type: 'recording',

        // Presentation
        title: recording.title,
        subtitle: `${recording.type}${recording.duration ? ` • ${recording.duration}` : ''}`,
        icon: getRecordingIcon(recording.type),
        color: getRecordingColor(recording.type),

        // Context
        status: recording.type,
        tags: [],
        createdAt: recording.created_at,
        updatedAt: undefined,

        // Full Payload
        data: recording,

        // Extended
        metadata: {
            type: recording.type,
            duration: recording.duration,
            file_path: recording.file_path,
            filename: recording.filename,
            file_type: recording.file_type,
            notes: recording.notes,
            song_id: recording.song_id,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Recording',
            statusStripe: getRecordingColor(recording.type),
            statusGlow: recording.type === 'master',
            collapsible: true,

            metaGrid: [
                { label: 'Type', value: recording.type },
                { label: 'Dur', value: recording.duration || '0:00' },
                { label: 'File', value: recording.file_type || '' }
            ].filter(i => !!i.value),

            externalLinks: recording.file_path ? [
                { label: 'Open File', url: recording.file_path }
            ] : undefined
        }
    };
}

function getRecordingIcon(type: string): string {
    switch (type) {
        case 'demo': return 'Mic';
        case 'voice_memo': return 'VoiceMail';
        case 'stem': return 'AudioWaveform';
        case 'master': return 'Crown';
        default: return 'Music';
    }
}

function getRecordingColor(type: string): string {
    switch (type) {
        case 'demo': return '#f59e0b';
        case 'voice_memo': return '#8b5cf6';
        case 'stem': return '#06b6d4';
        case 'master': return '#22c55e';
        default: return '#6b7280';
    }
}

export function toUniversalRecordingBatch(recordings: Recording[]): UniversalEntity<Recording>[] {
    return recordings.map(recording => toUniversalRecording(recording));
}
