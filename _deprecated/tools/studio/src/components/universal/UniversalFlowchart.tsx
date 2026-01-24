import { useCallback } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    useNodesState,
    useEdgesState,
    addEdge,
    ConnectionMode
} from 'reactflow';
import type { Node, Edge, Connection } from 'reactflow';
import 'reactflow/dist/style.css';

interface UniversalFlowchartProps {
    initialNodes?: Node[];
    initialEdges?: Edge[];
    height?: number | string;
    readOnly?: boolean;
}

const defaultNodes: Node[] = [
    { id: '1', position: { x: 0, y: 0 }, data: { label: 'Start' }, type: 'input' },
    { id: '2', position: { x: 0, y: 100 }, data: { label: 'Process' } },
];

const defaultEdges: Edge[] = [
    { id: 'e1-2', source: '1', target: '2', animated: true },
];

export function UniversalFlowchart({
    initialNodes = defaultNodes,
    initialEdges = defaultEdges,
    height = 400,
    readOnly = false
}: UniversalFlowchartProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
    const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

    const onConnect = useCallback((params: Connection) => setEdges((eds) => addEdge(params, eds)), [setEdges]);

    return (
        <div style={{ height }} className="w-full border border-white/10 rounded-xl overflow-hidden bg-black/40">
            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onConnect={readOnly ? undefined : onConnect}
                connectionMode={ConnectionMode.Loose}
                fitView
                className="bg-neutral-900/50"
            >
                <Background color="#333" gap={16} />
                {!readOnly && <Controls className="bg-black/50 border-white/10 fill-white text-white" />}
                <MiniMap
                    nodeColor={() => '#555'}
                    maskColor="rgba(0, 0, 0, 0.7)"
                    className="bg-black/50 border border-white/10 rounded-lg"
                />
            </ReactFlow>
        </div>
    );
}
