import { useState } from 'react';
import { UniversalPage } from '../components/universal/layout/UniversalPage';
import { UniversalCard } from '../components/universal/UniversalCard';
import { UniversalWidget } from '../components/universal/UniversalWidget';
import { UniversalActionBar } from '../components/universal/UniversalActionBar';
import { UniversalPanel } from '../components/universal/UniversalPanel';
import { UniversalTable } from '../components/universal/UniversalTable';
import {
    LayoutGrid, List, Plus, Palette, Star, Settings, CheckSquare, Activity,
    Link as LinkIcon, RefreshCw, Trash2, Box, X
} from 'lucide-react';
import { UniversalTabs } from '../components/universal/layout/UniversalTabs';
import { getAllEntityTypes, createUniversalEntity, getEntityDefinition } from '../lib/registry';

// ============================================================================
// COMPONENT SANDBOX (MODERNIZED v8.1)
// ============================================================================
// Focuses on:
// 1. Registry Integration (Proof that all 30+ types work)
// 2. Feature Depth (Density, Collapsible, Metadata)
// 3. Component Primitive Library
// ============================================================================

export function ComponentSandbox() {
    const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
    const [activeTab, setActiveTab] = useState('registry'); // Default to Registry Showcase
    const [searchTerm, setSearchTerm] = useState('');

    // Generate one test entity for every registered type
    const entityTypes = getAllEntityTypes();
    const allTestEntities = entityTypes.map(type => {
        const def = getEntityDefinition(type);
        // Create a mock entity with all bells and whistles
        return createUniversalEntity(type, {
            id: 9000 + type.length, // Fake ID
            title: `Test ${def?.title || type}`,
            status: 'active',
            [def?.primaryField || 'title']: `Test ${def?.title || type}`,
            // Add some dummy data for tags/meta to show up
            tags: ['test', 'sandbox', 'v8.1'],
            priority: 3,
            description: `Auto-generated test entity for type: ${type}`
        });
    });

    // Filter entities
    const filteredEntities = allTestEntities.filter(e =>
        e.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
        e.type.toLowerCase().includes(searchTerm.toLowerCase())
    );

    return (
        <UniversalPage
            title="Component Sandbox"
            subtitle={`Consolidated Registry System (${entityTypes.length} Types)`}
            tabs={
                <UniversalTabs
                    tabs={[
                        { id: 'registry', label: 'Registry Showcase', icon: Box },
                        { id: 'features', label: 'Feature Lab', icon: Star },
                        { id: 'library', label: 'UI Library', icon: Palette },
                        { id: 'debug', label: 'Debug', icon: Settings },
                    ]}
                    activeTab={activeTab}
                    onChange={setActiveTab}
                    variant="square-pill"
                />
            }
            actions={
                <div className="flex items-center gap-2">
                    {/* Search Input */}
                    <div className="relative">
                        <input
                            type="text"
                            placeholder="Filter components..."
                            className="bg-black/20 border border-white/10 rounded-lg pl-3 pr-8 py-1.5 text-sm text-white focus:outline-none focus:border-accent/50 w-48 transition-all focus:w-64"
                            value={searchTerm}
                            onChange={(e) => setSearchTerm(e.target.value)}
                        />
                        {searchTerm && (
                            <button
                                onClick={() => setSearchTerm('')}
                                className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>

                    <UniversalActionBar
                        actions={[
                            {
                                id: 'view',
                                label: viewMode === 'grid' ? 'List' : 'Grid',
                                icon: viewMode === 'grid' ? List : LayoutGrid,
                                action: () => setViewMode(viewMode === 'list' ? 'grid' : 'list'),
                                variant: 'secondary'
                            }
                        ]}
                    />
                </div>
            }
        >
            {/* TAB 1: REGISTRY SHOWCASE (Breadth) */}
            {activeTab === 'registry' && (
                <div className="space-y-6">
                    <div className="p-4 bg-blue-500/10 border border-blue-500/20 rounded-xl text-sm text-blue-200 flex justify-between items-center">
                        <div>
                            <strong>Registry Verification:</strong> Displaying {filteredEntities.length} of {entityTypes.length} registered entity types.
                            This proves that the generic adapter works for the entire system ecosystem.
                        </div>
                        {searchTerm && (
                            <div className="text-xs bg-blue-500/20 px-2 py-1 rounded">
                                Filtering by "{searchTerm}"
                            </div>
                        )}
                    </div>

                    <div className={viewMode === 'grid' ? "grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6" : "flex flex-col gap-4"}>
                        {filteredEntities.map(entity => (
                            <UniversalCard
                                key={entity.urn}
                                entity={entity}
                                layoutMode={viewMode}
                                showStatus={true}
                                showTags={true}
                                showActions={true}
                                // We use the standard RegistryCard wrapper logic implicit in UniversalCard if configured,
                                // but for raw UniversalCard testing we pass props directly.
                                // In the real app, we use <RegistryCard> wrapper.
                                // Let's simulate some registry-like features here:
                                collapsible={true}
                                onClick={() => console.log('Clicked', entity.urn)}
                            />
                        ))}

                        {filteredEntities.length === 0 && (
                            <div className="col-span-full py-12 text-center text-gray-500">
                                No components match your filter.
                            </div>
                        )}
                    </div>
                </div>
            )}

            {/* TAB 2: FEATURE LAB (Depth) */}
            {activeTab === 'features' && (
                <div className="space-y-12 pb-20">
                    {/* 1. Density Variants */}
                    <section className="space-y-4">
                        <div className="flex items-center justify-between border-b border-white/10 pb-2">
                            <h3 className="text-xl font-bold text-accent">1. Density Variants</h3>
                            <span className="text-xs text-gray-500 font-mono">Phase 11D</span>
                        </div>

                        <div className="space-y-8">
                            {/* Default */}
                            <div className="grid grid-cols-1 gap-4">
                                <h4 className="text-sm font-bold text-gray-400 uppercase">Default (Grid)</h4>
                                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                                    <UniversalCard
                                        entity={allTestEntities[0]}
                                        variant="default"
                                        layoutMode="grid"
                                    />
                                </div>
                            </div>

                            {/* Compact */}
                            <div className="grid grid-cols-1 gap-4">
                                <h4 className="text-sm font-bold text-gray-400 uppercase">Compact (Row)</h4>
                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                    <UniversalCard
                                        entity={allTestEntities[1] || allTestEntities[0]}
                                        variant="compact"
                                        layoutMode="list"
                                    />
                                    <UniversalCard
                                        entity={allTestEntities[2] || allTestEntities[0]}
                                        variant="compact"
                                        layoutMode="list"
                                    />
                                </div>
                            </div>

                            {/* Minimal */}
                            <div className="grid grid-cols-1 gap-4">
                                <h4 className="text-sm font-bold text-gray-400 uppercase">Minimal (Dense)</h4>
                                <div className="grid grid-cols-4 gap-2 w-full max-w-2xl bg-white/5 p-4 rounded-xl">
                                    {allTestEntities.slice(0, 4).map(t => (
                                        <UniversalCard
                                            key={t.urn}
                                            entity={t}
                                            variant="minimal"
                                            layoutMode="grid"
                                            showStatus={false}
                                            showActions={false}
                                            className="bg-black/40 hover:bg-white/10"
                                        />
                                    ))}
                                </div>
                            </div>
                        </div>
                    </section>
                </div>
            )}

            {/* TAB 3: UI LIBRARY (Primitives) */}
            {activeTab === 'library' && (
                <div className="space-y-8 pb-20">
                    <section className="space-y-4">
                        <h3 className="text-xl font-bold border-b border-white/10 pb-2">1. Widgets</h3>
                        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                            <UniversalWidget
                                definition={{ id: 'w-stat', type: 'stat', title: 'Revenue', data: { value: '$12k', trend: 15 } }}
                            />
                        </div>
                    </section>

                    <section className="space-y-4">
                        <h3 className="text-xl font-bold border-b border-white/10 pb-2">2. Action Bar</h3>
                        <UniversalActionBar
                            actions={[
                                { id: '1', label: 'Primary', variant: 'primary' },
                                { id: '2', label: 'Destructive', variant: 'danger', icon: Trash2 }
                            ]}
                        />
                    </section>

                    <section className="space-y-4">
                        <h3 className="text-xl font-bold border-b border-white/10 pb-2">3. Panels</h3>
                        <UniversalPanel title="Collapsible Panel" defaultExpanded={true} variant="card">
                            <div className="p-4 text-gray-400">Content goes here...</div>
                        </UniversalPanel>
                    </section>
                </div>
            )}
        </UniversalPage>
    );
}
