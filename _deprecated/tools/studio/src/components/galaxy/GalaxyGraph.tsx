import { useState, useMemo, useRef, useEffect } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { RefreshCw } from 'lucide-react';
import clsx from 'clsx';

export function GalaxyGraph() {
    const fgRef = useRef<any>();
    const containerRef = useRef<HTMLDivElement>(null);
    const [dimensions, setDimensions] = useState({ width: 800, height: 600 });

    useEffect(() => {
        if (!containerRef.current) return;

        const resizeObserver = new ResizeObserver((entries) => {
            for (const entry of entries) {
                const { width, height } = entry.contentRect;
                setDimensions({ width, height });
            }
        });

        resizeObserver.observe(containerRef.current);
        return () => resizeObserver.disconnect();
    }, []);

    // Fetch All Data
    const projects = useLiveQuery(() => db.projects.toArray()) || [];
    const goals = useLiveQuery(() => db.goals.toArray()) || [];
    const tasks = useLiveQuery(() => db.project_tasks.where('status').notEqual('completed').toArray()) || []; // Only open tasks to reduce noise
    const assets = useLiveQuery(() => db.assets.toArray()) || [];
    const routines = useLiveQuery(() => db.routines.toArray()) || [];

    // Transform Data
    const graphData = useMemo(() => {
        const nodes: any[] = [];
        const links: any[] = [];

        // Add Nodes
        projects.forEach(p => nodes.push({ id: `project-${p.id}`, name: p.title, group: 'project', val: 20 }));
        goals.forEach(g => nodes.push({ id: `goal-${g.id}`, name: g.title, group: 'goal', val: 30 }));
        tasks.forEach(t => nodes.push({ id: `task-${t.id}`, name: t.title, group: 'task', val: 5 }));
        assets.forEach(a => nodes.push({ id: `asset-${a.id}`, name: a.name, group: 'asset', val: 10 }));
        routines.forEach(r => nodes.push({ id: `routine-${r.id}`, name: r.title, group: 'routine', val: 15 }));

        // Add Links
        // 1. Task -> Project Ownership
        tasks.forEach(t => {
            if (t.project_id) {
                links.push({
                    source: `task-${t.id}`,
                    target: `project-${t.project_id}`,
                    type: 'ownership',
                    color: 'rgba(255,255,255,0.1)'
                });
            }
        });

        // 2. Asset -> Project Ownership
        assets.forEach(a => {
            if (a.related_project_ids) {
                a.related_project_ids.forEach(pid => {
                    links.push({
                        source: `asset-${a.id}`,
                        target: `project-${pid}`,
                        type: 'related',
                        color: 'rgba(16, 185, 129, 0.2)'
                    });
                });
            }
        });

        // 3. Task Dependencies (BLOCKERS)
        const blockedTaskIds = new Set<number>();
        tasks.forEach(t => {
            if (t.upstream_task_ids && t.upstream_task_ids.length > 0) {
                t.upstream_task_ids.forEach(upstreamId => {
                    // Start of Arrow = Blocker (Upstream)
                    // End of Arrow = Blocked (Downstream/Current)
                    // "Blocker BLOCKS Blocked"
                    links.push({
                        source: `task-${upstreamId}`,
                        target: `task-${t.id}`,
                        type: 'blocker',
                        color: '#ef4444', // Red
                        width: 2
                    });
                    blockedTaskIds.add(t.id!);
                });
            }
        });

        return { nodes, links, blockedTaskIds };
    }, [projects, goals, tasks, assets, routines]);


    const getNodeColor = (node: any) => {
        // Highlight Blocked Tasks
        if (node.group === 'task' && graphData.blockedTaskIds.has(Number(node.id.replace('task-', '')))) {
            return '#f97316'; // Orange for blocked tasks
        }

        switch (node.group) {
            case 'project': return '#3b82f6'; // Blue
            case 'goal': return '#eab308'; // Yellow
            case 'task': return '#4b5563'; // Gray
            case 'asset': return '#10b981'; // Green
            case 'routine': return '#a855f7'; // Purple
            default: return '#fff';
        }
    };

    return (
        <div className="h-full w-full relative bg-black" ref={containerRef}>
            <div className="absolute top-4 right-4 z-10 flex gap-2">
                <Button size="sm" variant="ghost" className="bg-black/50 hover:bg-black" onClick={() => {
                    fgRef.current?.zoomToFit(400);
                }}>
                    <RefreshCw size={16} />
                </Button>
            </div>

            <ForceGraph3D
                ref={fgRef}
                width={dimensions.width}
                height={dimensions.height}
                graphData={graphData}
                nodeLabel="name"
                nodeColor={getNodeColor}
                nodeVal="val"
                // Link Styling
                linkColor={(link: any) => link.color}
                linkWidth={(link: any) => link.width || 1}
                linkDirectionalParticles={(link: any) => link.type === 'blocker' ? 4 : 0}
                linkDirectionalParticleSpeed={(link: any) => link.type === 'blocker' ? 0.005 : 0}
                linkDirectionalParticleWidth={2}
                backgroundColor="#000000"
                onNodeClick={(node) => {
                    // Fly to node
                    const distance = 40;
                    const distRatio = 1 + distance / Math.hypot(node.x, node.y, node.z);

                    fgRef.current.cameraPosition(
                        { x: node.x * distRatio, y: node.y * distRatio, z: node.z * distRatio }, // new position
                        node, // lookAt ({ x, y, z })
                        3000  // ms transition duration
                    );

                    // Navigate logic could go here
                }}
            />

            {/* Legend */}
            <div className="absolute bottom-4 left-4 bg-black/50 p-2 rounded border border-white/10 text-[10px] font-mono space-y-1 pointer-events-none select-none">
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-blue-500" /> PROJECT</div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-yellow-500" /> GOAL</div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-green-500" /> ASSET</div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-purple-500" /> ROUTINE</div>
                <div className="flex items-center gap-2"><div className="w-2 h-2 rounded-full bg-gray-600" /> TASK</div>
            </div>
        </div>
    );
}
