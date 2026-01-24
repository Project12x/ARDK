import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { ProjectFlowchart } from '../components/projects/ProjectFlowchart';
import { GoalFlowchart } from '../components/goals/GoalFlowchart';
import { CombinedFlowchart } from '../components/combined/CombinedFlowchart';
import { Loader2, Network, Target, GitMerge } from 'lucide-react';
import clsx from 'clsx';

export function ProjectFlowPage() {
    const [viewMode, setViewMode] = useState<'projects' | 'goals' | 'combined'>('projects');

    const projects = useLiveQuery(() => db.projects.filter(p => !p.deleted_at).toArray());
    const goals = useLiveQuery(() => db.goals.toArray());
    const routines = useLiveQuery(() => db.routines.toArray()) || [];
    const assets = useLiveQuery(() => db.assets.toArray()) || [];
    const links = useLiveQuery(() => db.links.toArray()) || [];

    if (!projects || !goals) {
        return (
            <div className="flex items-center justify-center h-full bg-black">
                <Loader2 size={32} className="text-accent animate-spin" />
            </div>
        );
    }

    const activeProjects = projects.filter(p => !p.deleted_at);

    const getNodeCount = () => {
        if (viewMode === 'projects') return activeProjects.length;
        if (viewMode === 'goals') return goals.length;
        return activeProjects.length + goals.length + routines.length;
    };

    return (
        <div className="h-full bg-black p-6 flex flex-col">
            {/* Header with Toggle */}
            <div className="flex items-center justify-between mb-6">
                <h1 className="text-3xl font-black uppercase tracking-tighter text-white flex items-center gap-4">
                    <span className="text-accent text-4xl">☍</span>
                    {viewMode === 'projects' ? 'Project Flow' : viewMode === 'goals' ? 'Goal Flow' : 'Combined Flow'}
                    <span className="text-sm font-mono text-gray-500 mt-2 opacity-50">
                        {getNodeCount()} NODES
                    </span>
                </h1>

                {/* View Toggle */}
                <div className="flex gap-2 bg-neutral-900 border border-white/10 rounded-lg p-1">
                    <button
                        onClick={() => setViewMode('projects')}
                        className={clsx(
                            "px-4 py-2 rounded-md text-sm font-bold uppercase tracking-wider transition-all flex items-center gap-2",
                            viewMode === 'projects'
                                ? "bg-accent text-black"
                                : "text-gray-500 hover:text-white hover:bg-white/5"
                        )}
                    >
                        <Network size={16} />
                        Projects
                    </button>
                    <button
                        onClick={() => setViewMode('goals')}
                        className={clsx(
                            "px-4 py-2 rounded-md text-sm font-bold uppercase tracking-wider transition-all flex items-center gap-2",
                            viewMode === 'goals'
                                ? "bg-purple-600 text-white"
                                : "text-gray-500 hover:text-white hover:bg-white/5"
                        )}
                    >
                        <Target size={16} />
                        Goals
                    </button>
                    <button
                        onClick={() => setViewMode('combined')}
                        className={clsx(
                            "px-4 py-2 rounded-md text-sm font-bold uppercase tracking-wider transition-all flex items-center gap-2",
                            viewMode === 'combined'
                                ? "bg-green-600 text-white"
                                : "text-gray-500 hover:text-white hover:bg-white/5"
                        )}
                    >
                        <GitMerge size={16} />
                        Combined
                    </button>
                </div>
            </div>

            {/* Flowchart Area */}
            <div className="flex-1 overflow-hidden border border-white/10 rounded-xl bg-neutral-900/50 relative">
                {viewMode === 'projects' ? (
                    <ProjectFlowchart projects={activeProjects} />
                ) : viewMode === 'goals' ? (
                    <GoalFlowchart goals={goals} />
                ) : (
                    <CombinedFlowchart projects={activeProjects} goals={goals} routines={routines} assets={assets} links={links} />
                )}
            </div>
        </div>
    );
}
