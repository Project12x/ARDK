/**
 * Universal View Renderer
 * 
 * Dynamically renders view modules based on ViewConfig from the registry.
 * This enables any entity to have rich, interactive views like Kanban, Tables, Charts, etc.
 */

import React, { Suspense } from 'react';
import { Loader2 } from 'lucide-react';
import type { ViewConfig } from '../../lib/registry/entityRegistry';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';

// Lazy load heavy components
const ThreeViewer = React.lazy(() => import('../ui/ThreeViewer').then(m => ({ default: m.ThreeViewer })));

interface ViewRendererProps {
    view: ViewConfig;
    entityId: string | number;
    entityType: string;
    entityData: Record<string, any>;
}

export function UniversalViewRenderer({ view, entityId, entityType, entityData }: ViewRendererProps) {
    // Fetch related data if dataSource is specified
    const relatedData = useLiveQuery(async () => {
        if (!view.dataSource || !view.filterKey) return null;
        const table = db.table(view.dataSource);
        return table.where(view.filterKey).equals(Number(entityId)).toArray();
    }, [view.dataSource, view.filterKey, entityId]);

    const loading = (
        <div className="flex items-center justify-center h-40 text-gray-500">
            <Loader2 className="animate-spin" size={24} />
        </div>
    );

    switch (view.type) {
        case 'overview':
            return <OverviewView entityData={entityData} />;

        case 'table':
            return <TableView data={relatedData || []} columns={view.columns} />;

        case 'kanban':
            return <KanbanView data={relatedData || []} groupBy={view.groupBy || 'status'} />;

        case 'timeline':
            return <TimelineView data={relatedData || []} />;

        case 'three_viewer':
            return (
                <Suspense fallback={loading}>
                    <ThreeViewer file={entityData.model_url || entityData.file_url} />
                </Suspense>
            );

        case 'notebook':
            return <NotebookView entityId={entityId} entityType={entityType} />;

        case 'chart':
            return <ChartPlaceholder />;

        case 'custom':
            return <CustomViewPlaceholder componentName={view.component} />;

        default:
            return (
                <div className="p-6 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-500 text-sm">
                    ⚠ Unknown view type: {view.type}
                </div>
            );
    }
}

// ----------------------------------------------------------------------------
// View Components
// ----------------------------------------------------------------------------

function OverviewView({ entityData }: { entityData: Record<string, any> }) {
    const fields = Object.entries(entityData).filter(([k]) => !['id', 'created_at', 'updated_at'].includes(k));

    return (
        <div className="grid grid-cols-2 gap-4">
            {fields.slice(0, 12).map(([key, value]) => (
                <div key={key} className="flex flex-col">
                    <span className="text-xs text-gray-500 uppercase">{key.replace(/_/g, ' ')}</span>
                    <span className="font-mono text-sm text-white truncate">
                        {typeof value === 'object' ? JSON.stringify(value) : String(value ?? '-')}
                    </span>
                </div>
            ))}
        </div>
    );
}

function TableView({ data, columns }: { data: any[], columns?: string[] }) {
    if (!data.length) {
        return <div className="text-gray-500 text-sm p-4">No items found.</div>;
    }

    const cols = columns || Object.keys(data[0]).filter(k => !['id', 'created_at'].includes(k)).slice(0, 6);

    return (
        <div className="overflow-x-auto">
            <table className="w-full text-sm">
                <thead>
                    <tr className="border-b border-white/10">
                        {cols.map(col => (
                            <th key={col} className="text-left py-2 px-3 text-xs text-gray-500 uppercase">{col.replace(/_/g, ' ')}</th>
                        ))}
                    </tr>
                </thead>
                <tbody>
                    {data.map((row, i) => (
                        <tr key={i} className="border-b border-white/5 hover:bg-white/5">
                            {cols.map(col => (
                                <td key={col} className="py-2 px-3 font-mono text-gray-300 truncate max-w-xs">
                                    {String(row[col] ?? '-')}
                                </td>
                            ))}
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
    );
}

function KanbanView({ data, groupBy }: { data: any[], groupBy: string }) {
    const groups = data.reduce((acc, item) => {
        const group = item[groupBy] || 'unknown';
        if (!acc[group]) acc[group] = [];
        acc[group].push(item);
        return acc;
    }, {} as Record<string, any[]>);

    const groupNames = Object.keys(groups);

    if (!groupNames.length) {
        return <div className="text-gray-500 text-sm p-4">No items to display.</div>;
    }

    return (
        <div className="flex gap-4 overflow-x-auto pb-4">
            {groupNames.map(group => (
                <div key={group} className="min-w-[200px] bg-white/5 border border-white/10 rounded-lg p-3">
                    <h4 className="text-xs font-bold text-gray-400 uppercase mb-3">{group}</h4>
                    <div className="space-y-2">
                        {groups[group].map((item, i) => (
                            <div key={i} className="p-2 bg-black/30 border border-white/10 rounded text-xs text-gray-300">
                                {item.title || item.name || `Item ${i + 1}`}
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
}

function TimelineView({ data }: { data: any[] }) {
    const sorted = [...data].sort((a, b) =>
        new Date(b.created_at || 0).getTime() - new Date(a.created_at || 0).getTime()
    );

    if (!sorted.length) {
        return <div className="text-gray-500 text-sm p-4">No history available.</div>;
    }

    return (
        <div className="space-y-3">
            {sorted.slice(0, 20).map((item, i) => (
                <div key={i} className="flex gap-3 items-start">
                    <div className="w-2 h-2 rounded-full bg-accent mt-1.5 flex-shrink-0" />
                    <div>
                        <p className="text-sm text-white">{item.title || item.summary || item.message || 'Event'}</p>
                        <p className="text-xs text-gray-500">{item.created_at ? new Date(item.created_at).toLocaleDateString() : ''}</p>
                    </div>
                </div>
            ))}
        </div>
    );
}

function NotebookView({ entityId, entityType }: { entityId: string | number, entityType: string }) {
    const notes = useLiveQuery(async () => {
        // Try to find notes linked to this entity
        return db.table('notebook').where('entity_id').equals(Number(entityId)).toArray();
    }, [entityId]) || [];

    if (!notes.length) {
        return (
            <div className="text-center py-8 text-gray-500">
                <p className="text-sm">No notebook entries yet.</p>
                <button className="mt-2 px-4 py-2 bg-accent/20 text-accent rounded text-xs font-bold hover:bg-accent/30">
                    + Add Entry
                </button>
            </div>
        );
    }

    return (
        <div className="space-y-4">
            {notes.map((note, i) => (
                <div key={i} className="p-4 bg-black/20 border border-white/10 rounded-lg">
                    <h4 className="font-bold text-white mb-2">{note.title}</h4>
                    <p className="text-sm text-gray-400">{note.content}</p>
                </div>
            ))}
        </div>
    );
}

function ChartPlaceholder() {
    return (
        <div className="flex items-center justify-center h-40 bg-white/5 border border-white/10 rounded-lg text-gray-500 text-sm">
            📊 Chart View (Coming Soon)
        </div>
    );
}

function CustomViewPlaceholder({ componentName }: { componentName?: string }) {
    return (
        <div className="flex items-center justify-center h-40 bg-purple-500/10 border border-purple-500/20 rounded-lg text-purple-400 text-sm">
            🔌 Custom Component: {componentName || 'Not specified'}
        </div>
    );
}
