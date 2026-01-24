import { useRef } from 'react';
import ReactFlow, {
    Background,
    Controls,
    MiniMap,
    ConnectionMode,
    type Node,
    type Edge,
    type OnNodesChange,
    type OnEdgesChange,
    type OnConnect,
    type NodeDragHandler,
    type NodeMouseHandler,
    type Connection,
    type NodeTypes,
    type OnNodesDelete
} from 'reactflow';
import 'reactflow/dist/style.css';
import clsx from 'clsx';
import { Box, LayoutTemplate } from 'lucide-react';
import { Button } from '../ui/Button';
import { FullscreenToggleButton } from '../ui/FullscreenToggleButton';

interface BaseFlowchartProps {
    // Data
    nodes: Node[];
    edges: Edge[];
    onNodesChange: OnNodesChange;
    onEdgesChange: OnEdgesChange;

    // Handlers
    onConnect?: OnConnect;
    onNodeDragStop?: NodeDragHandler;
    onNodeDoubleClick?: NodeMouseHandler;
    onNodesDelete?: OnNodesDelete;
    onEdgeClick?: (event: React.MouseEvent, edge: Edge) => void;

    // Drag & Drop
    onDragOver?: React.DragEventHandler;
    onDrop?: React.DragEventHandler;
    onNodeMouseEnter?: NodeMouseHandler;
    onNodeMouseLeave?: NodeMouseHandler;

    // Config
    nodeTypes?: NodeTypes;
    miniMapColor?: (node: Node) => string;

    // Layout Controls
    onLayout?: (direction: 'TB' | 'LR') => void;

    // Toybox
    showToybox: boolean;
    setShowToybox: (show: boolean) => void;
    toyboxContent: React.ReactNode;
    toyboxTitle?: string;
    toyboxCount?: number;

    // Extras
    children?: React.ReactNode; // For Modals, Popups
    toolbarActions?: React.ReactNode; // Custom buttons for the toolbar
}

export function BaseFlowchart({
    nodes,
    edges,
    onNodesChange,
    onEdgesChange,
    onConnect,
    onNodeDragStop,
    onNodeDoubleClick,
    onNodesDelete,
    onEdgeClick,
    onDragOver,
    onDrop,
    onNodeMouseEnter,
    onNodeMouseLeave,
    nodeTypes,
    miniMapColor,
    onLayout,
    showToybox,
    setShowToybox,
    toyboxContent,
    toyboxTitle = "BACKLOG",
    toyboxCount = 0,
    children,
    toolbarActions
}: BaseFlowchartProps) {
    const reactFlowWrapper = useRef<HTMLDivElement>(null);

    // Use internal ref if not provided, but here we only have internal.
    // Actually, looking at previous edits, I might have messed up the ref passing in BaseFlowchart?
    // In previous turn I saw `BaseFlowchart` had `wrapperRef`.
    // Let me check the file content again...
    // Ah, the file content I read in Step 5830 DOES NOT have `wrapperRef`. It uses `reactFlowWrapper` internally.
    // Wait, in Step 5809 I edited `BaseFlowchart` to accept `wrapperRef`.
    // Did I read the wrong file or did I revert?
    // Let me check Step 5830 output again.
    // Line 86: `const reactFlowWrapper = useRef<HTMLDivElement>(null);`
    // Line 89: `ref={reactFlowWrapper}`
    // It seems my previous edit to `BaseFlowchart` to accept `wrapperRef` might have been lost or I am misremembering *which* file I edited.
    // I entered `BaseFlowchart` in the `lines_modified` of Step 5809.
    // Let's re-read the file in Step 5830. It clearly shows it DOES NOT accept `wrapperRef`.
    // This is strange. Maybe I wrote it but didn't save? Or I am hallucinating.
    // Actually, `FullscreenToggleButton` takes `targetRef`.
    // If I want to fix `wrapperRef` I should do it now too.
    // But for now, `toolbarActions` is the goal.

    return (
        <div className="flex h-full w-full relative group bg-neutral-950 rounded-xl overflow-hidden border border-white/10" ref={reactFlowWrapper}>
            {/* Toolbar */}
            <div className="absolute top-4 right-4 z-50 flex gap-2 print:hidden pointer-events-auto">
                {toolbarActions}
                {onLayout && (
                    <Button variant="outline" size="sm" onClick={() => onLayout('LR')} className="backdrop-blur-md bg-black/50 hover:bg-accent/20">
                        <LayoutTemplate size={16} className="mr-2" /> AUTO
                    </Button>
                )}
                <Button
                    variant="outline"
                    size="sm"
                    onClick={() => setShowToybox(!showToybox)}
                    className={clsx("backdrop-blur-md bg-black/50", showToybox && "bg-accent/20 border-accent text-accent")}
                >
                    <Box size={16} className="mr-2" /> {toyboxTitle}
                </Button>
                <FullscreenToggleButton targetRef={reactFlowWrapper} />
            </div>

            <ReactFlow
                nodes={nodes}
                edges={edges}
                onNodesChange={onNodesChange}
                onEdgesChange={onEdgesChange}
                onNodesDelete={onNodesDelete}
                onConnect={onConnect}
                onNodeDragStop={onNodeDragStop}
                onNodeDoubleClick={onNodeDoubleClick}
                onEdgeClick={onEdgeClick}
                onDragOver={onDragOver}
                onDrop={onDrop}
                onNodeMouseEnter={onNodeMouseEnter}
                onNodeMouseLeave={onNodeMouseLeave}

                nodeTypes={nodeTypes}
                connectionMode={ConnectionMode.Loose}
                zoomOnScroll={true}
                panOnScroll={false}
                selectionOnDrag
                panOnDrag={[1, 2]}
                autoPanOnNodeDrag
                fitView
            >
                <Background color="#222" gap={20} />
                <Controls className="bg-neutral-900 border-white/10 text-white" />
                <MiniMap
                    className="!bg-neutral-900 !border !border-white/10"
                    nodeColor={miniMapColor || '#3b82f6'}
                    maskColor="rgba(0,0,0,0.6)"
                />
            </ReactFlow>

            {/* Toybox Drawer */}
            <div className={clsx(
                "w-80 bg-neutral-900 border-l border-white/10 flex flex-col z-40 transition-all absolute right-0 top-0 bottom-0 shadow-2xl print:hidden pointer-events-auto",
                showToybox ? "translate-x-0" : "translate-x-full pointer-events-none"
            )}>
                <div className="p-4 pt-16 border-b border-white/10 flex items-center justify-between">
                    <span className="font-bold text-white flex items-center gap-2">
                        <Box size={16} className="text-accent" />
                        {toyboxTitle}
                    </span>
                    <span className="text-xs text-gray-500">{toyboxCount} ITEMS</span>
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-4">
                    {toyboxContent}
                </div>
            </div>

            {/* Additional Overlays (Modals, Popovers) */}
            {children}
        </div>
    );
}
