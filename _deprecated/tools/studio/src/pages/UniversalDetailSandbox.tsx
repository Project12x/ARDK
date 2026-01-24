/**
 * Universal Detail Sandbox
 * 
 * Safe testing environment for the Universal View System.
 * This page allows testing all view types (Kanban, Table, Timeline, etc.)
 * without modifying production code.
 */

import React, { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { ENTITY_REGISTRY } from '../lib/registry/entityRegistry';
import type { ViewConfig, EntityDefinition } from '../lib/registry/entityRegistry';
import { UniversalViewRenderer } from '../components/universal/UniversalViewRenderer';
import { Loader2, CheckCircle, Target, Package, Music, ShoppingCart, LayoutGrid, Table2, KanbanSquare, Clock } from 'lucide-react';
import clsx from 'clsx';

// Test view configurations
const TEST_VIEWS: ViewConfig[] = [
    { id: 'overview', title: 'Overview', icon: 'LayoutGrid', type: 'overview' },
    { id: 'table', title: 'Table', icon: 'Table2', type: 'table', dataSource: 'project_tasks', filterKey: 'project_id' },
    { id: 'kanban', title: 'Kanban', icon: 'KanbanSquare', type: 'kanban', dataSource: 'project_tasks', filterKey: 'project_id', groupBy: 'status' },
    { id: 'timeline', title: 'Timeline', icon: 'Clock', type: 'timeline' },
    { id: 'chart', title: 'Chart', icon: 'BarChart', type: 'chart' },
];

// Test entities to load
const TEST_ENTITIES = [
    { type: 'project', label: 'Project', icon: Target },
    { type: 'task', label: 'Task', icon: CheckCircle },
    { type: 'inventory', label: 'Inventory', icon: Package },
    { type: 'goal', label: 'Goal', icon: Target },
];

export function UniversalDetailSandbox() {
    const [selectedType, setSelectedType] = useState<string>('project');
    const [selectedId, setSelectedId] = useState<number | null>(null);
    const [activeView, setActiveView] = useState<ViewConfig>(TEST_VIEWS[0]);

    // Fetch available entities of selected type
    const definition = ENTITY_REGISTRY[selectedType];
    const entities = useLiveQuery(async () => {
        if (!definition) return [];
        return db.table(definition.table).limit(10).toArray();
    }, [selectedType, definition]);

    // Load selected entity
    const entity = useLiveQuery(async () => {
        if (!selectedId || !definition) return null;
        return db.table(definition.table).get(selectedId);
    }, [selectedId, definition]);

    return (
        <div className="h-full flex flex-col bg-black text-white overflow-hidden">
            {/* Header */}
            <div className="flex-none p-4 border-b border-white/10 bg-purple-500/10">
                <h1 className="text-xl font-black uppercase tracking-wider text-purple-400">
                    🧪 Universal Detail Sandbox
                </h1>
                <p className="text-xs text-gray-500 mt-1">
                    Test View Types without modifying production code
                </p>
            </div>

            {/* Controls */}
            <div className="flex-none p-4 border-b border-white/10 bg-white/5 space-y-4">
                {/* Entity Type Selector */}
                <div>
                    <label className="text-xs text-gray-500 uppercase font-bold mb-2 block">1. Select Entity Type</label>
                    <div className="flex gap-2 flex-wrap">
                        {TEST_ENTITIES.map(e => (
                            <button
                                key={e.type}
                                onClick={() => { setSelectedType(e.type); setSelectedId(null); }}
                                className={clsx(
                                    "flex items-center gap-2 px-3 py-2 rounded text-xs font-bold uppercase border transition-all",
                                    selectedType === e.type
                                        ? "bg-accent text-black border-accent"
                                        : "bg-white/5 text-gray-400 border-white/10 hover:bg-white/10"
                                )}
                            >
                                <e.icon size={14} />
                                {e.label}
                            </button>
                        ))}
                    </div>
                </div>

                {/* Entity Instance Selector */}
                <div>
                    <label className="text-xs text-gray-500 uppercase font-bold mb-2 block">2. Select Entity Instance</label>
                    <div className="flex gap-2 flex-wrap">
                        {entities?.map((e: any) => (
                            <button
                                key={e.id}
                                onClick={() => setSelectedId(e.id)}
                                className={clsx(
                                    "px-3 py-1.5 rounded text-xs border transition-all",
                                    selectedId === e.id
                                        ? "bg-accent text-black border-accent font-bold"
                                        : "bg-white/5 text-gray-400 border-white/10 hover:bg-white/10"
                                )}
                            >
                                {e[definition?.primaryField || 'id'] || `ID: ${e.id}`}
                            </button>
                        )) || <span className="text-gray-500 text-xs">Loading...</span>}
                    </div>
                </div>

                {/* View Type Selector */}
                <div>
                    <label className="text-xs text-gray-500 uppercase font-bold mb-2 block">3. Select View Type</label>
                    <div className="flex gap-2 flex-wrap">
                        {TEST_VIEWS.map(v => (
                            <button
                                key={v.id}
                                onClick={() => setActiveView(v)}
                                className={clsx(
                                    "flex items-center gap-2 px-3 py-2 rounded text-xs font-bold uppercase border transition-all",
                                    activeView.id === v.id
                                        ? "bg-purple-500 text-white border-purple-500"
                                        : "bg-white/5 text-gray-400 border-white/10 hover:bg-white/10"
                                )}
                            >
                                {v.title}
                            </button>
                        ))}
                    </div>
                </div>
            </div>

            {/* View Renderer */}
            <div className="flex-1 overflow-y-auto p-6">
                {!entity ? (
                    <div className="flex flex-col items-center justify-center h-full text-gray-500">
                        <LayoutGrid size={48} className="mb-4 opacity-30" />
                        <p>Select an entity above to preview views</p>
                    </div>
                ) : (
                    <div className="bg-zinc-900 border border-white/10 rounded-xl p-6 min-h-[400px]">
                        <div className="flex items-center justify-between mb-4 pb-4 border-b border-white/10">
                            <div>
                                <h2 className="font-bold text-lg">{entity[definition?.primaryField || 'id']}</h2>
                                <span className="text-xs text-gray-500 font-mono">{selectedType}:{selectedId}</span>
                            </div>
                            <span className="px-3 py-1 bg-purple-500/20 text-purple-400 text-xs font-bold uppercase rounded">
                                {activeView.type}
                            </span>
                        </div>

                        <UniversalViewRenderer
                            view={activeView}
                            entityId={selectedId!}
                            entityType={selectedType}
                            entityData={entity}
                        />
                    </div>
                )}
            </div>

            {/* Status Bar */}
            <div className="flex-none p-2 border-t border-white/10 bg-black/50 text-xs text-gray-500 font-mono flex justify-between">
                <span>Registry: {Object.keys(ENTITY_REGISTRY).length} entities</span>
                <span>View: {activeView.type}</span>
            </div>
        </div>
    );
}
