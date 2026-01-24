import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
    type Connection,
    ConnectionMode,
    type XYPosition,
    ReactFlowProvider,
    useReactFlow,
    addEdge
} from 'reactflow';
import 'reactflow/dist/style.css'; // Essential Styles
import dagre from 'dagre';
import { toast } from 'sonner';

import type { Project } from '../../lib/db';
import { db } from '../../lib/db';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { Box, Plus, Link as LinkIcon, AlertCircle, LayoutTemplate } from 'lucide-react';
import { Button } from '../ui/Button';
import { ProjectNode, type ProjectNodeData } from './flow/ProjectNode';
import { ProjectCard } from './ProjectCard';
import { useFlowchartLayout } from '../../hooks/useFlowchartLayout';
import { BaseFlowchart } from '../flow/BaseFlowchart';

interface FlowProps {
    projects: Project[];
}

// Node types moved to memo inside FlowInner

export function ProjectFlowchart({ projects }: FlowProps) {
    // If defining inside, do this:
    // const nodeTypes = useMemo(() => ({ project: ProjectNode }), []);

    return (
        <ReactFlowProvider>
            <FlowInner projects={projects} />
        </ReactFlowProvider>
    );
}

function FlowInner({ projects }: FlowProps) {
    const navigate = useNavigate();
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const { screenToFlowPosition } = useReactFlow();
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [showToybox, setShowToybox] = useState(false);

    const [hoveredNodeData, setHoveredNodeData] = useState<{ id: string, x: number, y: number, project: Project } | null>(null);

    // Link Modal State
    const [pendingConnection, setPendingConnection] = useState<Connection | null>(null);

    // 1. Sync Data to Nodes/Edges
    useEffect(() => {
        const newNodes: Node<ProjectNodeData>[] = [];
        const newEdges: Edge[] = [];

        projects.forEach(p => {
            // Determine Position
            let position: XYPosition = { x: 0, y: 0 };

            if (p.flow_x !== undefined && p.flow_y !== undefined) {
                position = { x: p.flow_x, y: p.flow_y };
            } else {
                // For React Flow, to be safe, we usually only render "placed" nodes
                // OR we render everything. Let's filter out "unplaced" ones to the Toybox
                // UNLESS the user wants everything on board by default.
                // Current logic: If NO coords, it goes to toybox (not in newNodes)
                return;
            }

            // Create Node
            newNodes.push({
                id: String(p.id),
                type: 'project',
                position,
                data: {
                    project: p,
                    label_color: p.label_color,
                    is_blocked: (p.upstream_dependencies?.length || 0) > 0
                }
            });

            // Create Edges
            // 1. Upstream (Blockers) -> This Project
            if (p.upstream_dependencies) {
                p.upstream_dependencies.forEach(sourceId => {
                    // Check if source exists in loaded projects
                    // Note: We only draw edge if source is also on board? Or at least in project list
                    const sourceExists = projects.some(proj => proj.id === sourceId);
                    if (sourceExists) {
                        newEdges.push({
                            id: `e${sourceId}-${p.id}`,
                            source: String(sourceId),
                            target: String(p.id),
                            animated: true,
                            style: { stroke: '#ef4444', strokeWidth: 2 },
                            label: 'BLOCKS',
                            labelStyle: { fill: '#ef4444', fontWeight: 700, fontSize: 10 },
                            labelBgStyle: { fill: '#1a0505', fillOpacity: 0.8 },
                            type: 'smoothstep'
                        });
                    }
                });
            }

            // 2. Related -> This Project (Deduped by ID comparison)
            if (p.related_projects) {
                p.related_projects.forEach(relId => {
                    if (p.id! < relId) { // Draw once
                        const relExists = projects.some(proj => proj.id === relId);
                        if (relExists) {
                            newEdges.push({
                                id: `rel${p.id}-${relId}`,
                                source: String(p.id),
                                target: String(relId),
                                style: { stroke: '#a855f7', strokeWidth: 1, strokeDasharray: '5 5' },
                                type: 'straight'
                            });
                        }
                    }
                });
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);

        // Auto open toybox if empty
        if (newNodes.length === 0 && projects.length > 0) {
            setShowToybox(true);
        }

    }, [projects, setNodes, setEdges, navigate]); // Caution: this rewrites everything on every project update. Efficient enough for < 100 projects.

    // 2. Interactions
    const onNodeDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
        // Update DB
        const id = Number(node.id);
        db.projects.update(id, {
            flow_x: Math.round(node.position.x),
            flow_y: Math.round(node.position.y)
        });
    }, []);

    const onConnect = useCallback((params: Connection) => {
        // Don't modify edges locally yet, wait for user confirmation
        setPendingConnection(params);
        setEdges((eds) => addEdge(params, eds)); // Visually connect immediately (optional, or wait for confirm)
    }, [setEdges]);

    const confirmLink = async (type: 'block' | 'reverse-block' | 'related') => {
        // alert(`DEBUG: Linking type=${type}`); // Removed
        if (!pendingConnection) return;
        const sourceId = Number(pendingConnection.source);
        const targetId = Number(pendingConnection.target);

        // alert(`DEBUG: Source=${sourceId}, Target=${targetId}`); // Removed

        try {
            const source = projects.find(p => p.id === sourceId);
            const target = projects.find(p => p.id === targetId);
            if (!target || !source) {
                toast.error(`Project not found. Source: ${source ? 'Found' : 'Missing'}, Target: ${target ? 'Found' : 'Missing'}`);
                return;
            }

            if (type === 'block') {
                // Source BLOCKS Target (Target depends on Source)
                // Add SourceID to Target's upstream
                const current = target.upstream_dependencies || [];
                if (!current.includes(sourceId)) {
                    await db.projects.update(target.id!, {
                        upstream_dependencies: [...current, sourceId]
                    });
                }
            } else if (type === 'reverse-block') {
                // Source is BLOCKED BY Target (Source depends on Target)
                // Add TargetID to Source's upstream
                const current = source.upstream_dependencies || [];
                if (!current.includes(targetId)) {
                    await db.projects.update(source.id!, {
                        upstream_dependencies: [...current, targetId],
                        // If we are blocking, we might want to clear any reverse loop? Cyclic check?
                        // For MVP, allow cycles or let user fail.
                    });
                }
            } else {
                // Related - Bidirectional
                const targetRelated = target.related_projects || [];
                const sourceRelated = source.related_projects || [];

                if (!targetRelated.includes(sourceId)) {
                    await db.projects.update(target.id!, {
                        related_projects: [...targetRelated, sourceId]
                    });
                }
                if (!sourceRelated.includes(targetId)) {
                    await db.projects.update(source.id!, {
                        related_projects: [...sourceRelated, targetId]
                    });
                }
            }

            // Optimistic Update: Add exact edge that useEffect would create
            // This prevents the edge from disappearing while DB syncs
            const edgeId = type === 'related' ? `rel${source.id}-${target.id}` : `e${source.id}-${target.id}`;
            const newEdge: Edge = {
                id: edgeId,
                source: String(source.id),
                target: String(target.id),
                animated: type !== 'related',
                style: type !== 'related' ? { stroke: '#ef4444', strokeWidth: 2 } : { stroke: '#a855f7', strokeWidth: 1, strokeDasharray: '5 5' },
                label: type === 'block' || type === 'reverse-block' ? 'BLOCKS' : undefined,
                labelStyle: (type === 'block' || type === 'reverse-block') ? { fill: '#ef4444', fontWeight: 700, fontSize: 10 } : undefined,
                labelBgStyle: (type === 'block' || type === 'reverse-block') ? { fill: '#1a0505', fillOpacity: 0.8 } : undefined,
                type: type !== 'related' ? 'smoothstep' : 'straight'
            };
            setEdges((eds) => eds.concat(newEdge));

        } catch (e) {
            console.error(e);
            toast.error("Failed to link");
        } finally {
            setPendingConnection(null);
        }
    };

    // Toybox / Drop Logic
    const toyboxProjects = useMemo(() => {
        // Projects NOT in nodes
        const activeIds = new Set(nodes.map((n: Node) => Number(n.id)));
        return projects.filter(p => !activeIds.has(p.id!));
    }, [projects, nodes]);

    const addToCanvas = async (id: number) => {
        // Place in center (approximated)
        // Ideally we project screen center to flow coords, but fixed offset is fine for MVP
        await db.projects.update(id, { flow_x: 250, flow_y: 250 });
        setShowToybox(false);
    };

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();

            // Check if we dropped a project from toybox (we'll implement drag start there)
            const projectId = event.dataTransfer.getData('application/project-id');
            if (!projectId) return;

            const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
            if (!reactFlowBounds) return;

            const position = screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            const id = Number(projectId);
            db.projects.update(id, { flow_x: position.x, flow_y: position.y });
        },
        [screenToFlowPosition]
    );

    const { getLayoutedElements } = useFlowchartLayout();

    const onLayout = useCallback((direction: 'TB' | 'LR' = 'LR') => {
        const { nodes: layoutedNodes } = getLayoutedElements(nodes, edges, {
            direction,
            nodeWidth: 280,
            nodeHeight: 100
        });

        setNodes(layoutedNodes);

        // Persist to DB
        layoutedNodes.forEach(node => {
            db.projects.update(Number(node.id), {
                flow_x: Math.round(node.position.x),
                flow_y: Math.round(node.position.y)
            });
        });

        window.requestAnimationFrame(() => {
            // fitView handled by Prop usually, or rely on internal
        });
    }, [nodes, edges, setNodes, getLayoutedElements]);

    // 3. Delete Logic (Send to Toybox)
    const onNodesDelete = useCallback((deleted: Node[]) => {
        deleted.forEach(node => {
            const id = Number(node.id);
            // Reset flow coordinates to remove from board
            db.projects.update(id, { flow_x: undefined, flow_y: undefined });
        });
    }, []);

    // 4. Hover Logic with Delay
    const hoverTimer = useRef<NodeJS.Timeout | null>(null);

    const onNodeMouseEnter = useCallback((_event: React.MouseEvent, node: Node) => {
        // Clear any pending hide/show timers
        if (hoverTimer.current) clearTimeout(hoverTimer.current);

        // Start new timer for show
        hoverTimer.current = setTimeout(() => {
            setHoveredNodeData({
                id: node.id,
                x: _event.clientX,
                y: _event.clientY,
                project: node.data.project
            });
        }, 1500);
    }, []);

    const onNodeMouseLeave = useCallback(() => {
        if (hoverTimer.current) clearTimeout(hoverTimer.current);
        setHoveredNodeData(null);
    }, []);

    const nodeTypesMemo = useMemo(() => ({
        project: ProjectNode
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
            onNodeDoubleClick={(_e, node) => navigate(`/projects/${node.id}`)}
            onDragOver={onDragOver}
            onDrop={onDrop}
            onNodeMouseEnter={onNodeMouseEnter}
            onNodeMouseLeave={onNodeMouseLeave}
            nodeTypes={nodeTypesMemo}
            onLayout={onLayout}

            showToybox={showToybox}
            setShowToybox={setShowToybox}
            toyboxTitle="TOYBOX"
            toyboxCount={toyboxProjects.length}
            miniMapColor={() => '#3b82f6'}

            toyboxContent={
                <>
                    {toyboxProjects.map(p => (
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
                            <Plus size={14} className="text-accent opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => addToCanvas(p.id!)} />
                        </div>
                    ))}
                </>
            }
        >
            {/* Link Confirmation Modal */}
            {pendingConnection && (
                <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                    <div className="bg-neutral-900 border border-white/20 p-6 rounded-xl shadow-2xl max-w-md w-full animate-in fade-in zoom-in-95 duration-200">
                        <div className="flex items-center gap-3 mb-4 text-white">
                            <LinkIcon className="text-accent" />
                            <h3 className="font-bold text-lg">Connect Projects</h3>
                        </div>
                        <p className="text-sm text-gray-400 mb-6">
                            Define the relationship between <span className="text-white font-bold">{projects.find(p => p.id === Number(pendingConnection.source))?.title}</span> and <span className="text-white font-bold">{projects.find(p => p.id === Number(pendingConnection.target))?.title}</span>.
                        </p>
                        <div className="grid grid-cols-3 gap-3">
                            <Button variant="outline" onClick={() => confirmLink('block')} className="flex flex-col h-28 items-center justify-center gap-2 hover:border-red-500 hover:text-red-500 hover:bg-red-500/10 transition-all text-center pointer-events-auto z-[2000] relative">
                                <AlertCircle size={20} />
                                <span className="font-bold text-xs">BLOCKS</span>
                                <span className="text-[9px] opacity-70 leading-tight">Source blocks Target<br />(Target comes AFTER)</span>
                            </Button>

                            <Button variant="outline" onClick={() => confirmLink('reverse-block')} className="flex flex-col h-28 items-center justify-center gap-2 hover:border-orange-500 hover:text-orange-500 hover:bg-orange-500/10 transition-all text-center pointer-events-auto z-[2000] relative">
                                <AlertCircle size={20} />
                                <span className="font-bold text-xs">BLOCKED BY</span>
                                <span className="text-[9px] opacity-70 leading-tight">Source blocked by Target<br />(Target comes BEFORE)</span>
                            </Button>

                            <Button variant="outline" onClick={() => confirmLink('related')} className="flex flex-col h-28 items-center justify-center gap-2 hover:border-purple-500 hover:text-purple-500 hover:bg-purple-500/10 transition-all text-center pointer-events-auto z-[2000] relative">
                                <LinkIcon size={20} />
                                <span className="font-bold text-xs">RELATED</span>
                                <span className="text-[9px] opacity-70 leading-tight">Bi-directional<br />Association</span>
                            </Button>
                        </div>
                        <div className="mt-4 flex justify-center">
                            <button
                                onClick={() => setPendingConnection(null)}
                                className="text-xs text-gray-500 hover:text-white underline"
                            >
                                Cancel Connection
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* Project Hover Preview */}
            {hoveredNodeData && (
                <div
                    className="fixed z-[9999] pointer-events-none w-[350px] animate-in fade-in zoom-in-95 duration-100"
                    style={{
                        top: hoveredNodeData.y > (window.innerHeight - 300) ? hoveredNodeData.y - 20 : hoveredNodeData.y + 20,
                        left: hoveredNodeData.x + 20,
                        transform: hoveredNodeData.y > (window.innerHeight - 300) ? 'translateY(-100%)' : 'none'
                    }}
                >
                    {/* Render standard Project Card in read-only / preview mode */}
                    <div className="bg-neutral-950 shadow-2xl rounded-lg overflow-hidden border border-white/20">
                        {/* We import ProjectCard at top (need to add import) */}
                        {/* Passing no-ops for handlers as this is a preview */}
                        <ProjectCard
                            project={hoveredNodeData.project}
                            onClick={() => { }}
                            isTrash={false}
                            onPurge={() => { }}
                            onRestoreTrash={() => { }}
                            collapsed={false}
                            layoutMode="grid"
                            hideActions={true}
                        />
                    </div>
                </div>
            )}
        </BaseFlowchart>
    );
}
