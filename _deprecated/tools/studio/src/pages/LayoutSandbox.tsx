import React, { useState } from 'react';
import { UniversalPage } from '../components/universal/layout/UniversalPage';
import { UniversalTabs } from '../components/universal/layout/UniversalTabs';
import { UniversalCard } from '../components/universal/UniversalCard';
import { UniversalProjectCard as UniversalProjectCardGeneric } from '../components/universal/cards/UniversalProjectCard';

import { ProjectCard } from '../components/projects/ProjectCard';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { Button } from '../components/ui/Button';

export function LayoutSandbox() {
    const [variant, setVariant] = useState<'default' | 'dense' | 'compact' | 'moderate' | 'expanded' | 'text'>('moderate');
    const projects = useLiveQuery(() => db.projects.toArray()) || [];
    const activeProjects = projects.filter(p => p.status === 'active').slice(0, 3);

    return (
        <UniversalPage
            title="Layout Sandbox"
            subtitle="Testing Universal Project Card V2"
            breadcrumbs={
                <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="hover:text-white cursor-pointer">Home</span>
                    <span>/</span>
                    <span className="text-white">Sandbox</span>
                </div>
            }
        >
            <div className="p-6 space-y-8">

                {/* Section 1: Comparison */}
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h2 className="text-xl font-bold text-accent">Feature Parity Check</h2>
                        <div className="flex items-center gap-2">
                            <label className="text-xs text-gray-400">Density:</label>
                            <select
                                value={variant}
                                onChange={(e) => setVariant(e.target.value as any)}
                                className="bg-black border border-white/20 rounded px-2 py-1 text-xs text-white outline-none focus:border-accent"
                            >
                                <option value="moderate">Moderate (Standard)</option>
                                <option value="text">Text (List)</option>
                                <option value="dense">Dense</option>
                                <option value="compact">Compact</option>
                                <option value="expanded">Expanded</option>
                                <option value="default">Legacy Default</option>
                            </select>
                        </div>
                    </div>
                    <p className="text-gray-400">Comparing original ProjectCard vs UniversalProjectCard (V2)</p>

                    {activeProjects.map(project => (
                        <div key={project.id} className="grid grid-cols-1 md:grid-cols-2 gap-6 p-6 border border-white/10 rounded-xl bg-white/5">

                            {/* ORIGINAL */}
                            <div className="space-y-2">
                                <div className="text-xs uppercase font-bold text-gray-500">1. Original (Legacy)</div>
                                <ProjectCard
                                    project={project}
                                    onClick={() => { }}
                                    isTrash={false}
                                    onPurge={() => { }}
                                    onRestoreTrash={() => { }}
                                    collapsed={false}
                                    density={variant as any}
                                />
                            </div>

                            {/* GENERIC WRAPPER */}
                            <div className="space-y-2">
                                <div className="text-xs uppercase font-bold text-accent">2. Universal ({variant})</div>
                                <UniversalProjectCardGeneric
                                    project={project}
                                    variant={variant}
                                    onClick={() => console.log("Clicked Generic")}
                                />
                            </div>

                        </div>
                    ))}
                </div>

                {/* Section 2: UniversalCard Trash & Archive States */}
                <div className="space-y-4">
                    <h2 className="text-xl font-bold text-accent">State Visualization</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                        {/* Trash State */}
                        {/* Trash State */}
                        {activeProjects[0] && (
                            <UniversalProjectCardGeneric
                                project={{ ...activeProjects[0], id: 999999, title: 'Deleted Project Demo' }}
                                isTrash={true}
                                onRestoreTrash={() => alert('Restore')}
                                onPurge={() => alert('Purge')}
                            />
                        )}

                        {/* Archived State */}
                        {activeProjects[0] && (
                            <UniversalProjectCardGeneric
                                project={{ ...activeProjects[0], id: 999998, title: 'Archived Project Demo', status: 'archived' }}
                                isArchived={true}
                            />
                        )}

                        {!activeProjects[0] && <div className="text-gray-500">No active projects found to create demos from.</div>}
                    </div>
                </div>

            </div>
        </UniversalPage>
    );
}
