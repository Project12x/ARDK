import React from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../../lib/db';
import { formatDistanceToNow } from 'date-fns';
import { Activity, Clock } from 'lucide-react';

interface UniversalHistoryPanelProps {
    entityType: string;
    entityId: string;
}

export function UniversalHistoryPanel({ entityType, entityId }: UniversalHistoryPanelProps) {
    const logs = useLiveQuery(async () => {
        // Query logs where related_entity_type = type AND related_entity_id = id
        // Note: Our logs schema might vary. Let's assume standard 'logs' table with payload/metadata or explicit fields.
        // Checking entityRegistry "log" def: primaryField 'summary', subtitle 'version'.
        // We really want specific entity logs. 
        // Assuming we look for logs where `data.entityId` == id or similar.
        // For now, let's query broadly if indexed, or filter.

        return db.logs
            .orderBy('date')
            .reverse()
            .filter(log => {
                // Heuristic match on metadata
                const meta = log.metadata as any;
                return (meta?.entityId === entityId && meta?.entityType === entityType) ||
                    (log.summary.includes(entityId)); // Fallback
            })
            .limit(20)
            .toArray();
    }, [entityType, entityId]);

    if (!logs?.length) {
        return (
            <div className="p-4 text-center text-gray-500 text-xs border border-dashed border-white/10 rounded-lg">
                No history recorded.
            </div>
        );
    }

    return (
        <div className="space-y-4">
            <h3 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                <Clock size={14} /> History
            </h3>
            <div className="space-y-3 relative before:absolute before:left-2 before:top-2 before:bottom-2 before:w-px before:bg-white/10">
                {logs.map(log => (
                    <div key={log.id} className="relative pl-6">
                        <div className="absolute left-0 top-1 w-4 h-4 rounded-full bg-zinc-900 border border-white/20 flex items-center justify-center">
                            <div className="w-1.5 h-1.5 rounded-full bg-gray-500" />
                        </div>
                        <div className="bg-white/5 border border-white/5 rounded p-3 text-sm">
                            <div className="font-semibold text-gray-200">{log.summary}</div>
                            <div className="text-xs text-gray-500 mt-1 flex justify-between">
                                <span>{log.actor || 'System'}</span>
                                <span>{formatDistanceToNow(new Date(log.date), { addSuffix: true })}</span>
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
