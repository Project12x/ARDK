import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getEntityById } from '../lib/commands';
import { ENTITY_REGISTRY } from '../lib/registry/entityRegistry';
import { executeAction, getEntityActions } from '../lib/registry/actionRegistry';
import { Loader2, AlertTriangle, ArrowLeft, Calendar, Tag, MoreHorizontal } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import clsx from 'clsx';
import { format } from 'date-fns';
import * as LucideIcons from 'lucide-react';
import { UniversalHistoryPanel } from '../components/universal/panels/UniversalHistoryPanel';
import { UniversalRelationshipsPanel } from '../components/universal/panels/UniversalRelationshipsPanel';

export function UniversalDetailPage() {
    const { type, id } = useParams<{ type: string; id: string }>();
    const navigate = useNavigate();
    const [entity, setEntity] = useState<any>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const definition = type ? ENTITY_REGISTRY[type] : undefined;

    // Load Data
    useEffect(() => {
        async function load() {
            if (!type || !id) return;
            console.log(`[UniversalDetail] Loading ${type}:${id}`);
            setIsLoading(true);
            try {
                const data = await getEntityById(type, id);
                console.log(`[UniversalDetail] Result:`, data);
                if (data) {
                    setEntity(data);
                } else {
                    setError('Entity not found');
                }
            } catch (err) {
                console.error(err);
                setError('Failed to load entity');
            } finally {
                setIsLoading(false);
            }
        }
        load();
    }, [type, id]);

    if (isLoading) {
        return (
            <div className="flex items-center justify-center h-full w-full">
                <Loader2 className="animate-spin text-accent" size={32} />
            </div>
        );
    }

    if (!definition || error || !entity) {
        return (
            <div className="flex flex-col items-center justify-center h-full w-full text-gray-500">
                <AlertTriangle size={48} className="mb-4 opacity-50" />
                <h1 className="text-xl font-bold">Entity Not Found</h1>
                <p>Type: {type}, ID: {id}</p>
                <button onClick={() => navigate(-1)} className="mt-4 px-4 py-2 bg-white/5 rounded hover:bg-white/10">
                    Go Back
                </button>
            </div>
        );
    }

    // Dynamic Icon
    const IconComponent = (LucideIcons as any)[definition.icon] || LucideIcons.Box;
    const actions = getEntityActions(type!, definition.actions);

    return (
        <div className="flex flex-col h-full w-full bg-background overflow-hidden relative">
            {/* Background Pattern */}
            <div className="absolute inset-0 z-0 pointer-events-none opacity-[0.03]"
                style={{ backgroundImage: 'radial-gradient(circle at 1px 1px, white 1px, transparent 0)', backgroundSize: '24px 24px' }}
            />

            {/* Header */}
            <div className="flex-none h-16 border-b border-white/5 flex items-center justify-between px-6 bg-black/20 z-10 backdrop-blur-sm">
                <div className="flex items-center gap-4">
                    <button onClick={() => navigate(-1)} className="p-2 hover:bg-white/5 rounded-full transition-colors text-gray-400 hover:text-white">
                        <ArrowLeft size={18} />
                    </button>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg" style={{ backgroundColor: `${definition.color}20`, color: definition.color }}>
                            <IconComponent size={20} />
                        </div>
                        <div>
                            <div className="flex items-center gap-2">
                                <span className="text-xs font-mono uppercase tracking-wider text-gray-500 bg-white/5 px-1.5 py-0.5 rounded">
                                    {definition.table}
                                </span>
                                <span className="text-xs text-gray-600">ID: {entity.id}</span>
                            </div>
                            <h1 className="text-lg font-bold leading-none mt-1">{entity[definition.primaryField]}</h1>
                        </div>
                    </div>
                </div>

                {/* Actions Toolbar */}
                <div className="flex items-center gap-1">
                    {actions.map(action => (
                        <button
                            key={action.id}
                            onClick={() => executeAction(action.id, { type: type!, id: entity.id, ...entity })}
                            className={clsx(
                                "p-2 rounded hover:bg-white/10 transition-colors text-gray-400 hover:text-white relative group",
                                action.destructive && "hover:bg-red-500/10 hover:text-red-500"
                            )}
                            title={action.label}
                        >
                            <span className="sr-only">{action.label}</span>
                            {/* Render Icon dynamically if needed, or use text */}
                            {(LucideIcons as any)[action.icon] ?
                                React.createElement((LucideIcons as any)[action.icon], { size: 18 }) :
                                <span>{action.label[0]}</span>}
                        </button>
                    ))}
                </div>
            </div>

            {/* Content Scrollable */}
            <div className="flex-1 overflow-y-auto p-8 z-10">
                <div className="max-w-5xl mx-auto">

                    {/* VIEW TABS (if views configured) */}
                    {definition.views && definition.views.length > 0 ? (
                        <ViewTabsLayout
                            views={definition.views}
                            entityId={entity.id}
                            entityType={type!}
                            entityData={entity}
                            definition={definition}
                        />
                    ) : (
                        /* FALLBACK: Default Grid Layout */
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">

                            {/* Main Content Column */}
                            <div className="lg:col-span-2 space-y-8">

                                {/* Summary Card */}
                                <section className="bg-black/20 border border-white/10 rounded-xl p-6">
                                    <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4 flex items-center gap-2">
                                        <Tag size={14} /> Properties
                                    </h2>
                                    <div className="grid grid-cols-2 gap-y-6 gap-x-4">
                                        {/* Auto-Render Search Fields as Key Properties for now */}
                                        {definition.searchFields.map(field => {
                                            const value = entity[field];
                                            if (['title', 'name'].includes(field)) return null; // Skip title as it's in header
                                            return (
                                                <div key={field} className="flex flex-col">
                                                    <span className="text-xs text-gray-500 uppercase">{field.replace(/_/g, ' ')}</span>
                                                    <span className="font-mono text-sm break-words">{String(value || '-')}</span>
                                                </div>
                                            );
                                        })}
                                        {/* Render Meta Grid items if avail */}
                                        {definition.metaGrid?.map(item => (
                                            <div key={item.field} className="flex flex-col">
                                                <span className="text-xs text-gray-500 uppercase">{item.label}</span>
                                                <span className="font-mono text-sm break-words">{String(entity[item.field] || '-')}</span>
                                            </div>
                                        ))}
                                    </div>
                                </section>

                                {/* Description / Content (Generic guess) */}
                                {(entity.description || entity.content || entity.notes) && (
                                    <section className="bg-black/20 border border-white/10 rounded-xl p-6">
                                        <h2 className="text-sm font-bold text-gray-400 uppercase tracking-widest mb-4">Content</h2>
                                        <div className="prose prose-invert max-w-none text-sm text-gray-300">
                                            {entity.description || entity.content || entity.notes}
                                        </div>
                                    </section>
                                )}

                                {/* History Panel */}
                                <UniversalHistoryPanel entityType={type!} entityId={entity.id} />

                                {/* Relations / Links */}
                                <UniversalRelationshipsPanel entityType={type as any} entityId={entity.id} />

                            </div>

                            {/* Sidebar Column */}
                            <div className="space-y-6">
                                {/* Stats / Metadata */}
                                <div className="bg-zinc-900/50 border border-white/10 rounded-lg p-4">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase mb-3">System Data</h3>
                                    <div className="space-y-2 text-xs font-mono text-gray-400">
                                        <div className="flex justify-between">
                                            <span>Created</span>
                                            <span>{entity.created_at ? format(new Date(entity.created_at), 'yyyy-MM-dd') : '-'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Updated</span>
                                            <span>{entity.updated_at ? format(new Date(entity.updated_at), 'yyyy-MM-dd') : '-'}</span>
                                        </div>
                                        <div className="flex justify-between">
                                            <span>Type</span>
                                            <span style={{ color: definition.color }}>{type}</span>
                                        </div>
                                    </div>
                                </div>

                                {/* Raw JSON (Debug for now) */}
                                <div className="bg-black border border-white/10 rounded-lg p-0 overflow-hidden">
                                    <div className="bg-white/5 px-3 py-2 border-b border-white/5 text-xs font-bold text-gray-500">
                                        RAW DATA
                                    </div>
                                    <pre className="p-3 text-[10px] text-green-500/80 overflow-auto max-h-60 font-mono">
                                        {JSON.stringify(entity, null, 2)}
                                    </pre>
                                </div>
                            </div>

                        </div>
                    )}

                </div>
            </div>
        </div>
    );
}

// ----------------------------------------------------------------------------
// View Tabs Layout Component
// ----------------------------------------------------------------------------

import { UniversalViewRenderer } from '../components/universal/UniversalViewRenderer';
import type { ViewConfig, EntityDefinition } from '../lib/registry/entityRegistry';

function ViewTabsLayout({
    views,
    entityId,
    entityType,
    entityData,
    definition
}: {
    views: ViewConfig[],
    entityId: string | number,
    entityType: string,
    entityData: Record<string, any>,
    definition: EntityDefinition
}) {
    const [activeTab, setActiveTab] = useState<string>(views[0]?.id || 'overview');
    const activeView = views.find(v => v.id === activeTab) || views[0];

    return (
        <div className="space-y-6">
            {/* Tab Bar */}
            <div className="flex gap-1 border-b border-white/10 overflow-x-auto">
                {views.map(view => {
                    const Icon = view.icon ? (LucideIcons as any)[view.icon] : null;
                    const isActive = activeTab === view.id;
                    return (
                        <button
                            key={view.id}
                            onClick={() => setActiveTab(view.id)}
                            className={clsx(
                                "flex items-center gap-2 px-4 py-3 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors whitespace-nowrap",
                                isActive
                                    ? "border-accent text-accent"
                                    : "border-transparent text-gray-500 hover:text-gray-300"
                            )}
                        >
                            {Icon && <Icon size={14} />}
                            {view.title}
                        </button>
                    );
                })}
            </div>

            {/* Active View Content */}
            <div className="bg-black/20 border border-white/10 rounded-xl p-6 min-h-[300px] animate-in fade-in duration-300" key={activeTab}>
                <UniversalViewRenderer
                    view={activeView}
                    entityId={entityId}
                    entityType={entityType}
                    entityData={entityData}
                />
            </div>

            {/* Sidebar panels below on views layout */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <UniversalHistoryPanel entityType={entityType} entityId={entityId} />
                <UniversalRelationshipsPanel entityType={entityType as any} entityId={entityId} />
            </div>
        </div>
    );
}
