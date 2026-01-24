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
    ReactFlowProvider,
    useReactFlow,
    Handle,
    Position
} from 'reactflow';
import 'reactflow/dist/style.css';
import dagre from 'dagre';

import { db, type ProjectTask } from '../../lib/db';
import clsx from 'clsx';
import { Box, LayoutTemplate, Clock, AlertCircle } from 'lucide-react';
import { Button } from '../ui/Button';
import { useFlowchartLayout } from '../../hooks/useFlowchartLayout';
import { BaseFlowchart } from '../flow/BaseFlowchart';

// --- Task Node Component ---
function TaskNode({ data }: { data: { task: ProjectTask, is_blocked: boolean } }) {
    const task = data.task as ProjectTask;
    const isCompleted = task.status === 'completed';
    const isBlocked = data.is_blocked;

    return (
        <div className={clsx(
            "w-[200px] h-auto bg-black border rounded-lg shadow-xl transition-all group flex flex-col",
            isCompleted ? "border-green-500/50 opacity-60" : isBlocked ? "border-red-500" : "border-white/20 hover:border-accent"
        )}>
            {/* Input Handle */}
            <Handle
                type="target"
                position={Position.Left}
                className="!w-3 !h-6 !bg-neutral-800 !border-2 !border-white/20 !rounded-sm !-left-2 hover:!bg-accent hover:!border-accent transition-colors"
            />

            {/* Header Stripe */}
            <div className={clsx("h-1 w-full rounded-t-lg",
                task.is_high_priority ? "bg-red-600 animate-pulse" : "bg-gray-700"
            )} />

            <div className="p-3">
                <div className="flex justify-between items-start gap-2">
                    <span className="text-[10px] uppercase font-mono text-gray-400">{task.id}</span>
                    {/* Hazards / Caution Flags */}
                    <div className="flex gap-1">
                        {task.caution_flags?.map((flag, idx) => (
                            <div key={idx} className="text-[10px] bg-yellow-500/20 text-yellow-500 px-1 rounded border border-yellow-500/50 flex items-center" title={flag}>
                                <AlertCircle size={8} className="mr-1" />
                            </div>
                        ))}
                    </div>
                </div>

                <div className="mt-1">
                    {task.is_high_priority && (
                        <span className="text-[9px] font-bold bg-red-500/20 text-red-400 px-1.5 py-0.5 rounded border border-red-500/30 inline-block mb-1">
                            HIGH PRIORITY
                        </span>
                    )}
                    <div className="font-bold text-white text-sm">{task.title}</div>
                </div>

                <div className="flex items-center gap-2 mt-2">
                    {task.estimated_time && <span className="text-[9px] bg-white/10 px-1 rounded flex items-center gap-1 text-gray-300"><Clock size={8} /> {task.estimated_time}</span>}
                    {task.phase && <span className="text-[9px] border border-white/10 px-1 rounded text-gray-500 uppercase">{task.phase}</span>}
                </div>
            </div>

            {/* Output Handle */}
            <Handle
                type="source"
                position={Position.Right}
                className="!w-4 !h-4 !bg-neutral-800 !border-2 !border-white/20 !rounded-full !-right-2 hover:!bg-accent hover:!border-accent hover:!scale-110 transition-all flex items-center justify-center"
            />
        </div>
    );
}

const nodeTypes = {
    task: TaskNode
};

interface FlowProps {
    tasks: ProjectTask[];
}

export function TaskFlowchart({ tasks }: FlowProps) {
    return (
        <ReactFlowProvider>
            <TaskFlowInner tasks={tasks} />
        </ReactFlowProvider>
    );
}

function TaskFlowInner({ tasks }: FlowProps) {
    const reactFlowWrapper = useRef<HTMLDivElement>(null);
    const { screenToFlowPosition } = useReactFlow();
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [showToybox, setShowToybox] = useState(false);
    // Link Modal State
    const [pendingConnection, setPendingConnection] = useState<Connection | null>(null);

    // Sync Data
    useEffect(() => {
        const newNodes: Node[] = [];
        const newEdges: Edge[] = [];

        tasks.forEach(t => {
            // Filter unplaced nodes to Toybox
            if (t.flow_x === undefined || t.flow_y === undefined) return;

            newNodes.push({
                id: String(t.id),
                type: 'task',
                position: { x: t.flow_x, y: t.flow_y },
                data: {
                    task: t,
                    is_blocked: (t.upstream_task_ids?.length || 0) > 0
                }
            });

            // Edges (Blockers)
            if (t.upstream_task_ids) {
                t.upstream_task_ids.forEach(sourceId => {
                    // Check if source exists in loaded tasks
                    if (tasks.some(task => task.id === sourceId)) {
                        newEdges.push({
                            id: `e${sourceId}-${t.id}`,
                            source: String(sourceId),
                            target: String(t.id),
                            animated: true,
                            style: { stroke: '#ef4444', strokeWidth: 2 },
                            label: 'BLOCKS',
                            labelStyle: { fill: '#ef4444', fontWeight: 700, fontSize: 8 },
                            labelBgStyle: { fill: '#1a0505', fillOpacity: 0.8 },
                        });
                    }
                });
            }
        });

        setNodes(newNodes);
        setEdges(newEdges);

        if (newNodes.length === 0 && tasks.length > 0) {
            setTimeout(() => setShowToybox(true), 0);
        }
    }, [tasks, setNodes, setEdges]);

    // Interactions
    const onNodeDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
        const id = Number(node.id);
        db.project_tasks.update(id, {
            flow_x: Math.round(node.position.x),
            flow_y: Math.round(node.position.y)
        });
    }, []);

    const onConnect = useCallback((params: Connection) => {
        setPendingConnection(params);
    }, []);

    const confirmLink = async (type: 'block' | 'reverse-block') => {
        if (!pendingConnection) return;
        const sourceId = Number(pendingConnection.source);
        const targetId = Number(pendingConnection.target);

        if (type === 'block') {
            // Source BLOCKS Target
            const target = tasks.find(t => t.id === targetId);
            if (target) {
                const current = target.upstream_task_ids || [];
                if (!current.includes(sourceId)) {
                    await db.project_tasks.update(targetId, {
                        upstream_task_ids: [...current, sourceId]
                    });
                }
            }
        } else if (type === 'reverse-block') {
            // Source IS BLOCKED BY Target
            const source = tasks.find(t => t.id === sourceId);
            if (source) {
                const current = source.upstream_task_ids || [];
                if (!current.includes(targetId)) {
                    await db.project_tasks.update(sourceId, {
                        upstream_task_ids: [...current, targetId]
                    });
                }
            }
        }
        setPendingConnection(null);
    };

    // Toybox
    const toyboxTasks = useMemo(() => {
        const activeIds = new Set(nodes.map(n => Number(n.id)));
        return tasks.filter(t => !activeIds.has(t.id!));
    }, [tasks, nodes]);

    // Drag Drop from Toybox
    const onDragOver = useCallback((event: React.DragEvent) => {
        event.preventDefault();
        event.dataTransfer.dropEffect = 'move';
    }, []);

    const onDrop = useCallback(
        (event: React.DragEvent) => {
            event.preventDefault();
            const taskId = event.dataTransfer.getData('application/task-id');
            if (!taskId) return;

            const position = screenToFlowPosition({ x: event.clientX, y: event.clientY });
            db.project_tasks.update(Number(taskId), { flow_x: position.x, flow_y: position.y });
        },
        [screenToFlowPosition]
    );

    // Auto Layout
    const { getLayoutedElements } = useFlowchartLayout();

    const onLayout = useCallback((direction: 'TB' | 'LR' = 'LR') => {
        const { nodes: layoutedNodes } = getLayoutedElements(nodes, edges, {
            direction,
            nodeWidth: 220,
            nodeHeight: 150
        });

        setNodes(layoutedNodes);

        // Persist
        layoutedNodes.forEach(n => {
            db.project_tasks.update(Number(n.id), { flow_x: Math.round(n.position.x), flow_y: Math.round(n.position.y) });
        });
    }, [nodes, edges, setNodes, getLayoutedElements]);

    // Delete Logic (Send to Toybox)
    const onNodesDelete = useCallback((deleted: Node[]) => {
        deleted.forEach(node => {
            const id = Number(node.id);
            // Reset flow coordinates to remove from board
            db.project_tasks.update(id, { flow_x: undefined, flow_y: undefined });
        });
    }, []);


    return (
        <BaseFlowchart
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodesDelete={onNodesDelete}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onDragOver={onDragOver}
            onDrop={onDrop}
            nodeTypes={nodeTypes}
            onLayout={onLayout}

            showToybox={showToybox}
            setShowToybox={setShowToybox}
            toyboxTitle="TASKS"
            toyboxCount={toyboxTasks.length}
            miniMapColor={() => '#3b82f6'}

            toyboxContent={
                <>
                    {toyboxTasks.map(t => (
                        <div
                            key={t.id}
                            draggable
                            onDragStart={(e) => {
                                e.dataTransfer.setData('application/task-id', String(t.id));
                                e.dataTransfer.effectAllowed = 'move';
                            }}
                            className="bg-black/40 border border-white/5 p-3 rounded hover:border-accent/30 flex items-center justify-between group cursor-move active:cursor-grabbing"
                        >
                            <div>
                                <div className="font-bold text-gray-300 text-xs">{t.title}</div>
                                <div className="text-[10px] text-gray-600">P:{t.priority}</div>
                            </div>
                        </div>
                    ))}
                </>
            }
        >
            {/* Link Confirmation Modal */}
            {pendingConnection && (
                <div className="absolute inset-0 z-[1000] flex items-center justify-center bg-black/80 backdrop-blur-sm">
                    <div className="bg-neutral-900 border border-white/20 p-6 rounded-xl shadow-2xl max-w-sm w-full animate-in fade-in zoom-in-95 duration-200">
                        <h3 className="font-bold text-lg text-white mb-2">Connect Tasks</h3>
                        <p className="text-sm text-gray-400 mb-6">
                            Define dependency between <span className="text-white font-bold">{tasks.find(t => t.id === Number(pendingConnection.source))?.title}</span> and <span className="text-white font-bold">{tasks.find(t => t.id === Number(pendingConnection.target))?.title}</span>.
                        </p>
                        <div className="grid grid-cols-2 gap-3">
                            <Button variant="outline" onClick={() => confirmLink('block')} className="flex flex-col h-24 items-center justify-center gap-2 hover:border-red-500 hover:text-red-500 hover:bg-red-500/10 transition-all text-center">
                                <AlertCircle size={20} />
                                <span className="font-bold text-xs">BLOCKS</span>
                                <span className="text-[9px] opacity-70 leading-tight">Source blocks Target</span>
                            </Button>

                            <Button variant="outline" onClick={() => confirmLink('reverse-block')} className="flex flex-col h-24 items-center justify-center gap-2 hover:border-orange-500 hover:text-orange-500 hover:bg-orange-500/10 transition-all text-center">
                                <AlertCircle size={20} />
                                <span className="font-bold text-xs">BLOCKED BY</span>
                                <span className="text-[9px] opacity-70 leading-tight">Source blocked by Target</span>
                            </Button>
                        </div>
                        <div className="mt-4 flex justify-center">
                            <button onClick={() => setPendingConnection(null)} className="text-xs text-gray-500 hover:text-white underline">
                                Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </BaseFlowchart>
    );
}

