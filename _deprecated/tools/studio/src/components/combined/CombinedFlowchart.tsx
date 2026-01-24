import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
    ConnectionMode,
    type XYPosition,
    ReactFlowProvider,
    useReactFlow,
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { db, type Project, type Goal, type Routine, type EntityLink, type Asset } from '../../lib/db';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { Box, LayoutTemplate, Target, Network, Repeat, Database } from 'lucide-react';
import { LinkService } from '../../services/LinkService';
import { Button } from '../ui/Button';
import { ProjectNode } from '../projects/flow/ProjectNode';
import { FullscreenToggleButton } from '../ui/FullscreenToggleButton';
import { useFlowchartLayout } from '../../hooks/useFlowchartLayout';
import { BaseFlowchart } from '../flow/BaseFlowchart';
import { useExportFlow } from '../../hooks/useExportFlow';
import { ExportDialog } from '../ui/ExportComponents/ExportDialog';
import { FlowchartImageStrategy, FlowchartMermaidStrategy } from '../../lib/strategies/flowchartStrategies';
import { Download } from 'lucide-react';

// Goal Node Component
function GoalNode({ data }: { data: { goal: Goal } }) {
    const navigate = useNavigate();

    return (
        <div
            className="bg-gradient-to-br from-purple-900/40 to-purple-700/40 border-2 border-purple-500/50 rounded-lg p-4 min-w-[250px] shadow-lg hover:shadow-purple-500/20 transition-all cursor-pointer"
            onClick={() => navigate('/goals')}
        >
            <div className="flex items-center gap-2 mb-2">
                <Target size={16} className="text-purple-400" />
                <div className="font-bold text-white text-sm">{data.goal.title}</div>
            </div>
            {data.goal.description && (
                <div className="text-xs text-gray-400 line-clamp-2">{data.goal.description}</div>
            )}
            <div className="mt-2 flex gap-2">
                <span className="text-[10px] px-2 py-0.5 rounded bg-purple-500/20 text-purple-300 border border-purple-500/30">
                    {data.goal.level}
                </span>
                {data.goal.progress !== undefined && (
                    <span className="text-[10px] px-2 py-0.5 rounded bg-white/5 text-gray-400">
                        {data.goal.progress}%
                    </span>
                )}
            </div>
        </div>
    );
}

// Routine Node Component
function RoutineNode({ data }: { data: { routine: Routine } }) {
    const navigate = useNavigate();

    return (
        <div
            className="bg-gradient-to-br from-indigo-900/40 to-indigo-700/40 border-2 border-indigo-500/50 rounded-lg p-3 min-w-[200px] shadow-lg hover:shadow-indigo-500/20 transition-all cursor-pointer group"
            onClick={() => navigate('/routines')}
        >
            <div className="flex items-center gap-2 mb-2">
                <Repeat size={14} className="text-indigo-400 group-hover:text-white transition-colors" />
                <div className="font-bold text-white text-sm group-hover:text-white">{data.routine.title}</div>
            </div>
            <div className="text-[10px] text-gray-400 font-mono flex items-center gap-2">
                <span className="bg-indigo-500/20 px-1.5 py-0.5 rounded text-indigo-300 border border-indigo-500/30">
                    {data.routine.frequency.toUpperCase()}
                </span>
                {data.routine.season && (
                    <span className="bg-white/5 px-1.5 py-0.5 rounded text-gray-400 border border-white/5">
                        {data.routine.season}
                    </span>
                )}
            </div>
        </div>
    );
}

// Universal Node Component (Handles Assets and future generic types)
function UniversalNode({ data }: { data: { item: any, type: string, icon?: any, color?: string } }) {
    const navigate = useNavigate();
    const ItemIcon = data.icon || Database;
    const colorClass = data.color || 'text-emerald-400';
    const borderClass = data.color ? `border-${data.color.split('-')[1]}-500/50` : 'border-emerald-500/50';
    const bgGradient = data.color ? `from-${data.color.split('-')[1]}-900/40` : 'from-emerald-900/40';

    return (
        <div
            className={clsx(
                "bg-gradient-to-br border-2 rounded-lg p-3 min-w-[200px] shadow-lg transition-all cursor-pointer group hover:brightness-110",
                bgGradient,
                borderClass
            )}
            onClick={() => data.type === 'asset' ? navigate(`/assets`) : navigate(`/collection/${data.type}s`)}
        >
            <div className="flex items-center gap-2 mb-2">
                <ItemIcon size={14} className={clsx(colorClass, "group-hover:text-white transition-colors")} />
                <div className="font-bold text-white text-sm group-hover:text-white truncate">{data.item.title || data.item.name}</div>
            </div>
            <div className="text-[10px] text-gray-400 font-mono flex items-center gap-2">
                <span className={clsx("px-1.5 py-0.5 rounded border opacity-70", colorClass, "border-current bg-white/5")}>
                    {data.type.toUpperCase()}
                </span>
                {data.item.status && (
                    <span className="bg-white/5 px-1.5 py-0.5 rounded text-gray-400 border border-white/5">
                        {data.item.status}
                    </span>
                )}
            </div>
        </div>
    );
}

interface FlowProps {
    projects: Project[];
    goals: Goal[];
    routines: Routine[];
    assets: Asset[]; // Added Assets
    links: EntityLink[];
}

export function CombinedFlowchart({ projects, goals, routines, assets, links }: FlowProps) {
    return (
        <ReactFlowProvider>
            <FlowInner projects={projects} goals={goals} routines={routines} assets={assets} links={links} />
        </ReactFlowProvider>
    );
}

function FlowInner({ projects, goals, routines, assets = [], links }: FlowProps) {
    const navigate = useNavigate();
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const { screenToFlowPosition } = useReactFlow();
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [showToybox, setShowToybox] = useState(false);

    // Export Hook
    const { isExportOpen, openExport, closeExport, exportContext } = useExportFlow();

    useEffect(() => {
        const newNodes: Node[] = [];
        const newEdges: Edge[] = [];

        // --- NODES ---

        // Add Project Nodes
        projects.forEach(p => {
            if (p.flow_x === undefined || p.flow_y === undefined) return;
            newNodes.push({
                id: `project-${p.id}`,
                type: 'project',
                position: { x: p.flow_x, y: p.flow_y },
                data: {
                    project: p,
                    label_color: p.label_color,
                    is_blocked: (p.upstream_dependencies?.length || 0) > 0
                }
            });
        });

        // Add Routine Nodes
        routines.forEach(r => {
            if (r.flow_x === undefined || r.flow_y === undefined) return;
            newNodes.push({
                id: `routine-${r.id}`,
                type: 'routine',
                position: { x: r.flow_x, y: r.flow_y },
                data: { routine: r }
            });
        });

        // Add Goal Nodes
        goals.forEach(g => {
            if (g.flow_x === undefined || g.flow_y === undefined) return;
            newNodes.push({
                id: `goal-${g.id}`,
                type: 'goal',
                position: { x: g.flow_x, y: g.flow_y },
                data: { goal: g }
            });
        });

        // Add Asset Nodes (Universal)
        assets.forEach(a => {
            // @ts-ignore - Assuming we add flow props to assets or check for them
            if (a.flow_x === undefined || a.flow_y === undefined) return;
            newNodes.push({
                id: `asset-${a.id}`,
                type: 'universal', // Use Universal Node
                // @ts-ignore
                position: { x: a.flow_x, y: a.flow_y },
                data: {
                    item: a,
                    type: 'asset',
                    icon: Box,
                    color: 'text-emerald-400'
                }
            });
        });

        // UNIVERSAL LINKS (The New System)
        // This is now the ONLY source of truth for edges
        links.forEach(link => {
            const sourceId = `${link.source_type}-${link.source_id}`;
            const targetId = `${link.target_type}-${link.target_id}`;

            // Check if both nodes exist in the current graph
            const sourceExists = newNodes.some(n => n.id === sourceId);
            const targetExists = newNodes.some(n => n.id === targetId);

            if (sourceExists && targetExists) {
                let style = { stroke: '#71717a', strokeWidth: 1, strokeDasharray: '4 4' };
                const label = link.relationship.toUpperCase();
                let color = '#71717a';

                if (link.relationship === 'blocks') {
                    style = { stroke: '#ef4444', strokeWidth: 2, strokeDasharray: '0' };
                    color = '#ef4444';
                } else if (link.relationship === 'supports') {
                    color = '#22c55e';
                    style = { stroke: color, strokeWidth: 1.5, strokeDasharray: '4 4' };
                } else if (link.relationship === 'maintains') {
                    color = '#6366f1';
                    style = { stroke: color, strokeWidth: 1.5, strokeDasharray: '4 4' };
                }

                newEdges.push({
                    id: `link-${link.id}`, // specific link ID
                    source: sourceId,
                    target: targetId,
                    style,
                    label,
                    labelStyle: { fill: color, fontSize: 9, fontWeight: 700 },
                    labelBgStyle: { fill: '#000', fillOpacity: 0.7 },
                    type: 'default',
                    data: {
                        linkId: link.id,
                        relationship: link.relationship
                    } // Store ID or deletion and Type for layout
                });
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);

        if (newNodes.length === 0 && (projects.length > 0 || goals.length > 0 || routines.length > 0 || assets.length > 0)) {
            setShowToybox(true);
        }
    }, [projects, goals, routines, assets, links, setNodes, setEdges]); // Removed specific legacy checks

    // --- INTERACTION HANDLERS ---

    const onConnect = useCallback(async (params: any) => {
        if (!params.source || !params.target) return;

        const [sourceType, sourceIdStr] = params.source.split('-');
        const [targetType, targetIdStr] = params.target.split('-');
        const sourceId = Number(sourceIdStr);
        const targetId = Number(targetIdStr);

        // Determine Default Relationship
        let relationship: 'blocks' | 'supports' | 'maintains' | 'relates_to' = 'relates_to';

        if (sourceType === 'project' && targetType === 'project') relationship = 'blocks';
        else if (sourceType === 'project' && targetType === 'goal') relationship = 'supports'; // Proj supports Goal
        else if (sourceType === 'routine' && targetType === 'project') relationship = 'maintains';
        else if (sourceType === 'routine' && targetType === 'goal') relationship = 'supports';
        else if (sourceType === 'goal' && targetType === 'goal') relationship = 'blocks'; // Parent/Child logic typically

        // Placeholder for LinkService. You'll need to implement this or replace with direct db calls.
        // For example: await db.links.add({ source_type: sourceType, source_id: sourceId, target_type: targetType, target_id: targetId, relationship });
        console.log(`Linking ${sourceType}-${sourceId} to ${targetType}-${targetId} with relationship: ${relationship}`);
        // Assuming LinkService.link exists and handles the database operation
        // await LinkService.link(sourceType as any, sourceId, targetType as any, targetId, relationship);
    }, []);

    const onEdgeClick = useCallback(async (_: React.MouseEvent, edge: Edge) => {
        // Simple delete mechanism for now
        // In real app, could open a popup to change type
        if (edge.id.startsWith('link-') && edge.data?.linkId) {
            if (confirm("Remove this link?")) {
                await db.links.delete(edge.data.linkId);
            }
        }
    }, []);

    const onNodeDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
        const [type, id] = node.id.split('-');
        const numId = Number(id);

        if (type === 'project') {
            db.projects.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
        } else if (type === 'goal') {
            db.goals.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
        } else if (type === 'routine') {
            db.routines.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
        } else if (type === 'asset') {
            // @ts-ignore
            db.assets.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
        }
    }, []);

    const toyboxItems = useMemo(() => {
        const activeIds = new Set(nodes.map((n: Node) => n.id));
        const projectsNotPlaced = projects.filter(p => !activeIds.has(`project-${p.id}`));
        const goalsNotPlaced = goals.filter(g => !activeIds.has(`goal-${g.id}`));
        const routinesNotPlaced = routines.filter(r => !activeIds.has(`routine-${r.id}`));
        const assetsNotPlaced = assets.filter(a => !activeIds.has(`asset-${a.id}`));

        return {
            projects: projectsNotPlaced,
            goals: goalsNotPlaced,
            routines: routinesNotPlaced,
            assets: assetsNotPlaced
        };
    }, [projects, goals, routines, assets, nodes]);

    // Helpers to add to canvas
    const addToCanvas = async (type: 'project' | 'goal' | 'routine' | 'asset', id: number) => {
        const update = { flow_x: 250, flow_y: 250 };
        if (type === 'project') await db.projects.update(id, update);
        else if (type === 'goal') await db.goals.update(id, update);
        else if (type === 'routine') await db.routines.update(id, update);
        // @ts-ignore
        else if (type === 'asset') await db.assets.update(id, update);
        setShowToybox(false);
    };

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();

            const projectId = event.dataTransfer.getData('application/project-id');
            const goalId = event.dataTransfer.getData('application/goal-id');
            const routineId = event.dataTransfer.getData('application/routine-id');

            if (!projectId && !goalId && !routineId) return;

            const position = screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            if (projectId) {
                db.projects.update(Number(projectId), { flow_x: position.x, flow_y: position.y });
            } else if (goalId) {
                db.goals.update(Number(goalId), { flow_x: position.x, flow_y: position.y });
            } else if (routineId) {
                db.routines.update(Number(routineId), { flow_x: position.x, flow_y: position.y });
            }

            // Handle Assets Drop
            const assetId = event.dataTransfer.getData('application/asset-id');
            if (assetId) {
                // @ts-ignore
                db.assets.update(Number(assetId), { flow_x: position.x, flow_y: position.y });
            }
        },
        [screenToFlowPosition]
    );

    const { getLayoutedElements } = useFlowchartLayout();

    const onLayout = useCallback((direction: 'TB' | 'LR' = 'LR') => {
        const { nodes: layoutedNodes } = getLayoutedElements(nodes, edges, {
            direction,
            nodeWidth: 280,
            nodeHeight: 120
        });

        setNodes(layoutedNodes);

        // Persist layout
        layoutedNodes.forEach(node => {
            const [type, id] = node.id.split('-');
            const numId = Number(id);
            if (type === 'project') db.projects.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
            else if (type === 'goal') db.goals.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
            else if (type === 'routine') db.routines.update(numId, { flow_x: Math.round(node.position.x), flow_y: Math.round(node.position.y) });
        });
    }, [nodes, edges, setNodes, getLayoutedElements]);

    const onNodesDelete = useCallback((deleted: Node[]) => {
        deleted.forEach(node => {
            const [type, id] = node.id.split('-');
            const numId = Number(id);
            if (type === 'project') db.projects.update(numId, { flow_x: undefined, flow_y: undefined });
            else if (type === 'goal') db.goals.update(numId, { flow_x: undefined, flow_y: undefined });
            else if (type === 'routine') db.routines.update(numId, { flow_x: undefined, flow_y: undefined });
            // @ts-ignore
            else if (type === 'asset') db.assets.update(numId, { flow_x: undefined, flow_y: undefined });
        });
    }, []);

    const nodeTypesMemo = useMemo(() => ({
        project: ProjectNode,
        goal: GoalNode,
        routine: RoutineNode,
        universal: UniversalNode, // Register Universal
    }), []);

    return (
        <BaseFlowchart
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodesDelete={onNodesDelete}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onNodeDoubleClick={(_e: React.MouseEvent, node: Node) => {
                const [type] = node.id.split('-');
                if (type === 'project') navigate(`/projects/${node.id.split('-')[1]}`);
                else if (type === 'goal') navigate('/goals');
                else if (type === 'routine') navigate('/routines');
            }}
            onEdgeClick={onEdgeClick}
            onDragOver={onDragOver}
            onDrop={onDrop}

            nodeTypes={nodeTypesMemo}
            onLayout={onLayout}

            showToybox={showToybox}        // Toybox Props
            setShowToybox={setShowToybox}
            toyboxTitle="COMBINED TOYBOX"
            toyboxCount={toyboxItems.projects.length + toyboxItems.goals.length + toyboxItems.routines.length + toyboxItems.assets.length}
            miniMapColor={(node: Node) => {
                if (node.type === 'goal') return '#a855f7';
                if (node.type === 'routine') return '#6366f1';
                if (node.type === 'universal') return '#10b981'; // Emerald for assets
                return '#3b82f6';
            }}

            toyboxContent={
                <>
                    {/* Assets Section (Universal) */}
                    {toyboxItems.assets.length > 0 && (
                        <div>
                            <div className="text-xs font-bold text-emerald-400 mb-2 flex items-center gap-2">
                                <Box size={12} />
                                ASSETS ({toyboxItems.assets.length})
                            </div>
                            <div className="space-y-2">
                                {toyboxItems.assets.map(a => (
                                    <div
                                        key={a.id}
                                        draggable
                                        onDragStart={(e) => {
                                            e.dataTransfer.setData('application/asset-id', String(a.id));
                                            e.dataTransfer.effectAllowed = 'move';
                                        }}
                                        className="bg-black/40 border border-white/5 p-3 rounded hover:border-emerald-500/30 flex items-center justify-between group cursor-move active:cursor-grabbing"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Box size={14} className="text-emerald-400" />
                                            <div>
                                                <div className="font-bold text-gray-300 text-xs truncate max-w-[150px]">{a.name}</div>
                                                <div className="text-[10px] text-gray-600">{a.category}</div>
                                            </div>
                                        </div>
                                        <button onClick={() => addToCanvas('asset', a.id!)} className="opacity-0 group-hover:opacity-100">
                                            <Network size={14} className="text-emerald-400" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Goals Section */}
                    {toyboxItems.goals.length > 0 && (
                        <div>
                            <div className="text-xs font-bold text-purple-400 mb-2 flex items-center gap-2">
                                <Target size={12} />
                                GOALS ({toyboxItems.goals.length})
                            </div>
                            <div className="space-y-2">
                                {toyboxItems.goals.map(g => (
                                    <div
                                        key={g.id}
                                        draggable
                                        onDragStart={(e) => {
                                            e.dataTransfer.setData('application/goal-id', String(g.id));
                                            e.dataTransfer.effectAllowed = 'move';
                                        }}
                                        className="bg-black/40 border border-white/5 p-3 rounded hover:border-purple-500/30 flex items-center justify-between group cursor-move active:cursor-grabbing"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Target size={14} className="text-purple-400" />
                                            <div>
                                                <div className="font-bold text-gray-300 text-xs">{g.title}</div>
                                                <div className="text-[10px] text-gray-600">{g.level}</div>
                                            </div>
                                        </div>
                                        <button onClick={() => addToCanvas('goal', g.id!)} className="opacity-0 group-hover:opacity-100">
                                            <Network size={14} className="text-purple-400" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Projects Section */}
                    {toyboxItems.projects.length > 0 && (
                        <div>
                            <div className="text-xs font-bold text-accent mb-2 flex items-center gap-2">
                                <Network size={12} />
                                PROJECTS ({toyboxItems.projects.length})
                            </div>
                            <div className="space-y-2">
                                {toyboxItems.projects.map(p => (
                                    <div
                                        key={p.id}
                                        draggable
                                        onDragStart={(e) => {
                                            e.dataTransfer.setData('application/project-id', String(p.id));
                                            e.dataTransfer.effectAllowed = 'move';
                                        }}
                                        className="bg-black/40 border border-white/5 p-3 rounded hover:border-accent/30 flex items-center justify-between group cursor-move active:cursor-grabbing"
                                    >
                                        <div className="flex items-center gap-2">
                                            <div className="w-2 h-8 rounded-sm" style={{ backgroundColor: p.label_color || '#333' }} />
                                            <div>
                                                <div className="font-bold text-gray-300 text-xs">{p.title}</div>
                                                <div className="text-[10px] text-gray-600">{p.project_code}</div>
                                            </div>
                                        </div>
                                        <button onClick={() => addToCanvas('project', p.id!)} className="opacity-0 group-hover:opacity-100">
                                            <Network size={14} className="text-accent" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Routines Section */}
                    {toyboxItems.routines.length > 0 && (
                        <div>
                            <div className="text-xs font-bold text-indigo-400 mb-2 flex items-center gap-2">
                                <Repeat size={12} />
                                ROUTINES ({toyboxItems.routines.length})
                            </div>
                            <div className="space-y-2">
                                {toyboxItems.routines.map(r => (
                                    <div
                                        key={r.id}
                                        draggable
                                        onDragStart={(e) => {
                                            e.dataTransfer.setData('application/routine-id', String(r.id));
                                            e.dataTransfer.effectAllowed = 'move';
                                        }}
                                        className="bg-black/40 border border-white/5 p-3 rounded hover:border-indigo-500/30 flex items-center justify-between group cursor-move active:cursor-grabbing"
                                    >
                                        <div className="flex items-center gap-2">
                                            <Repeat size={14} className="text-indigo-400" />
                                            <div>
                                                <div className="font-bold text-gray-300 text-xs">{r.title}</div>
                                                <div className="text-[10px] text-gray-600">{r.frequency}</div>
                                            </div>
                                        </div>
                                        <button onClick={() => addToCanvas('routine', r.id!)} className="opacity-0 group-hover:opacity-100">
                                            <Network size={14} className="text-indigo-400" />
                                        </button>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </>
            }
        >
            <div className="absolute top-4 right-4 z-50 flex gap-2">
                <Button
                    onClick={() => openExport({ nodes, edges, flowWrapperRef: reactFlowWrapper })}
                    className="bg-black/50 border border-white/10 text-white hover:bg-black/70 backdrop-blur-sm"
                    size="sm"
                >
                    <Download size={16} className="mr-2" />
                    Export Map
                </Button>
            </div>

            <ExportDialog
                isOpen={isExportOpen}
                onClose={closeExport}
                strategies={[FlowchartImageStrategy, FlowchartMermaidStrategy]}
                context={exportContext}
            />
        </BaseFlowchart>
    );
}
