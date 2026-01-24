/**
 * LogEntityAdapter
 * Transforms raw Log objects (changelog entries) into UniversalEntity<Log>
 */

import type { Log } from '../../db';
import type { UniversalEntity } from '../types';

export function toUniversalLog(log: Log): UniversalEntity<Log> {
    return {
        urn: `log:${log.id}`,
        id: log.id!,
        type: 'log',

        title: log.summary,
        subtitle: `${log.version} • ${log.type}`,
        icon: 'History',
        color: log.type === 'auto' ? '#6b7280' : '#3b82f6',

        status: log.type,
        tags: [],
        createdAt: log.date,
        updatedAt: undefined,

        data: log,

        metadata: {
            project_id: log.project_id,
            branch_id: log.branch_id,
            version: log.version,
            type: log.type,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Log Entry',
            statusStripe: log.type === 'auto' ? '#6b7280' : '#3b82f6',
            statusGlow: false,
            collapsible: true,

            metaGrid: [
                { label: 'Version', value: log.version || 'v1.0' },
                { label: 'Type', value: log.type },
                { label: 'Date', value: new Date(log.date).toLocaleDateString() }
            ]
        }
    };
}

export function toUniversalLogBatch(logs: Log[]): UniversalEntity<Log>[] {
    return logs.map(log => toUniversalLog(log));
}
