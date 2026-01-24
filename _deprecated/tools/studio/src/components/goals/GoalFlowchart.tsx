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
import 'reactflow/dist/style.css';
import dagre from 'dagre';
import { toast } from 'sonner';
import { db, type Goal } from '../../lib/db';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { Box, Plus, Link as LinkIcon, LayoutTemplate, Target } from 'lucide-react';
import { Button } from '../ui/Button';
import { useFlowchartLayout } from '../../hooks/useFlowchartLayout';
import { BaseFlowchart } from '../flow/BaseFlowchart';

interface FlowProps {
    goals: Goal[];
}

// Simple Goal Node Component
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

export function GoalFlowchart({ goals }: FlowProps) {
    return (
        <ReactFlowProvider>
            <FlowInner goals={goals} />
        </ReactFlowProvider>
    );
}

function FlowInner({ goals }: FlowProps) {
    const navigate = useNavigate();
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const { screenToFlowPosition } = useReactFlow();
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [showToybox, setShowToybox] = useState(false);

    useEffect(() => {
        const newNodes: Node[] = [];
        const newEdges: Edge[] = [];

        goals.forEach(g => {
            let position: XYPosition = { x: 0, y: 0 };

            if (g.flow_x !== undefined && g.flow_y !== undefined) {
                position = { x: g.flow_x, y: g.flow_y };
            } else {
                return; // Skip goals without position
            }

            newNodes.push({
                id: String(g.id),
                type: 'goal',
                position,
                data: { goal: g }
            });

            // Draw parent-child relationships
            if (g.parent_id) {
                const parentExists = goals.some(goal => goal.id === g.parent_id);
                if (parentExists) {
                    newEdges.push({
                        id: `e${g.parent_id}-${g.id}`,
                        source: String(g.parent_id),
                        target: String(g.id),
                        animated: true,
                        style: { stroke: '#a855f7', strokeWidth: 2 },
                        label: 'SUB-GOAL',
                        labelStyle: { fill: '#a855f7', fontWeight: 700, fontSize: 10 },
                        labelBgStyle: { fill: '#1a051a', fillOpacity: 0.8 },
                        type: 'smoothstep'
                    });
                }
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);

        if (newNodes.length === 0 && goals.length > 0) {
            setShowToybox(true);
        }
    }, [goals, setNodes, setEdges]);

    const onNodeDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
        const id = Number(node.id);
        db.goals.update(id, {
            flow_x: Math.round(node.position.x),
            flow_y: Math.round(node.position.y)
        });
    }, []);

    const onConnect = useCallback((params: Connection) => {
        // For goals, we link parent-child relationships
        const sourceId = Number(params.source);
        const targetId = Number(params.target);

        db.goals.update(targetId, { parent_id: sourceId })
            .then(() => toast.success('Goals linked'))
            .catch(() => toast.error('Failed to link goals'));

        setEdges((eds) => addEdge(params, eds));
    }, [setEdges]);

    const toyboxGoals = useMemo(() => {
        const activeIds = new Set(nodes.map((n: Node) => Number(n.id)));
        return goals.filter(g => !activeIds.has(g.id!));
    }, [goals, nodes]);

    const addToCanvas = async (id: number) => {
        await db.goals.update(id, { flow_x: 250, flow_y: 250 });
        setShowToybox(false);
    };

    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();

            const goalId = event.dataTransfer.getData('application/goal-id');
            if (!goalId) return;

            const reactFlowBounds = reactFlowWrapper.current?.getBoundingClientRect();
            if (!reactFlowBounds) return;

            const position = screenToFlowPosition({
                x: event.clientX,
                y: event.clientY,
            });

            const id = Number(goalId);
            db.goals.update(id, { flow_x: position.x, flow_y: position.y });
        },
        [screenToFlowPosition]
    );

    // Layout Logic
    const { getLayoutedElements } = useFlowchartLayout();

    const onLayout = useCallback((direction: 'TB' | 'LR' = 'TB') => {
        const { nodes: layoutedNodes } = getLayoutedElements(nodes, edges, {
            direction,
            nodeWidth: 280,
            nodeHeight: 120
        });

        setNodes(layoutedNodes);

        layoutedNodes.forEach(node => {
            db.goals.update(Number(node.id), {
                flow_x: Math.round(node.position.x),
                flow_y: Math.round(node.position.y)
            });
        });
    }, [nodes, edges, setNodes, getLayoutedElements]);

    const onNodesDelete = useCallback((deleted: Node[]) => {
        deleted.forEach(node => {
            const id = Number(node.id);
            db.goals.update(id, { flow_x: undefined, flow_y: undefined });
        });
    }, []);

    const nodeTypesMemo = useMemo(() => ({
        goal: GoalNode
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
            onNodeDoubleClick={(_e, node) => navigate('/goals')}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypesMemo}
            onLayout={onLayout}

            showToybox={showToybox}
            setShowToybox={setShowToybox}
            toyboxTitle="GOAL TOYBOX"
            toyboxCount={toyboxGoals.length}
            miniMapColor={() => '#a855f7'}

            toyboxContent={
                <>
                    {toyboxGoals.map(g => (
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
                            <Plus size={14} className="text-purple-400 opacity-0 group-hover:opacity-100 transition-opacity" onClick={() => addToCanvas(g.id!)} />
                        </div>
                    ))}
                </>
            }
        />
    );
}
