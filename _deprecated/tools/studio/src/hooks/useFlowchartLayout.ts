import { useCallback } from 'react';
import type { Node, Edge } from 'reactflow';
import dagre from 'dagre';

interface LayoutOptions {
    direction?: 'TB' | 'LR';
    nodeWidth?: number;
    nodeHeight?: number;
    rankSep?: number;
    nodeSep?: number;
}

export function useFlowchartLayout() {
    const getLayoutedElements = useCallback((nodes: Node[], edges: Edge[], options: LayoutOptions = {}) => {
        const {
            direction = 'LR',
            nodeWidth = 280,
            nodeHeight = 100,
            rankSep = 100,
            nodeSep = 80
        } = options;

        const dagreGraph = new dagre.graphlib.Graph();
        dagreGraph.setDefaultEdgeLabel(() => ({}));

        dagreGraph.setGraph({ rankdir: direction, ranksep: rankSep, nodesep: nodeSep });

        nodes.forEach((node) => {
            dagreGraph.setNode(node.id, { width: nodeWidth, height: nodeHeight });
        });

        edges.forEach((edge) => {
            dagreGraph.setEdge(edge.source, edge.target);
        });

        dagre.layout(dagreGraph);

        const layoutedNodes = nodes.map((node) => {
            const nodeWithPosition = dagreGraph.node(node.id);
            // Dagre returns center coords, ReactFlow needs top-left
            return {
                ...node,
                position: {
                    x: nodeWithPosition.x - nodeWidth / 2,
                    y: nodeWithPosition.y - nodeHeight / 2,
                },
            };
        });

        return { nodes: layoutedNodes, edges };
    }, []);

    return { getLayoutedElements };
}
