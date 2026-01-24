
import type { ExportStrategy } from '../../types/export';
import { toPng } from 'html-to-image';
import { textToBlob } from '../../utils/exportTransformers';
import type { Node, Edge } from 'reactflow';

// We need the ReactFlow instance or nodes/edges to export.
// Context will effectively be { nodes: Node[], edges: Edge[], flowWrapper: HTMLElement }

interface FlowchartContext {
    nodes: Node[];
    edges: Edge[];
    flowWrapperRef: React.RefObject<HTMLElement>;
}

export const FlowchartImageStrategy: ExportStrategy<any> = {
    id: 'flowchart-image',
    name: 'Flowchart Image',
    description: 'Export the current view as a high-quality image.',
    supportedFormats: [
        { id: 'png', label: 'PNG Image', extension: 'png' },
        { id: 'svg', label: 'SVG Vector', extension: 'svg' } // Future
    ],
    getData: (context: FlowchartContext) => Promise.resolve([context]), // Single item array for the strategy pattern

    transform: async (data, format) => {
        const { flowWrapperRef } = data[0];
        if (!flowWrapperRef.current) throw new Error("Flowchart wrapper not found");

        if (format === 'png') {
            const dataUrl = await toPng(flowWrapperRef.current, { backgroundColor: '#111' }); // Dark mode bg
            // Convert DataURL to Blob
            const res = await fetch(dataUrl);
            return await res.blob();
        }

        // Fallback or SVG logic could go here
        throw new Error("Unsupported format for this strategy");
    }
};

export const FlowchartMermaidStrategy: ExportStrategy<any> = {
    id: 'flowchart-mermaid',
    name: 'Mermaid Diagram',
    description: 'Export as Mermaid.js markdown syntax.',
    supportedFormats: [
        { id: 'markdown', label: 'Mermaid Text', extension: 'md' }
    ],
    getData: (context: FlowchartContext) => Promise.resolve([context]),

    transform: async (data, format) => {
        const { nodes, edges } = data[0];

        let mermaid = 'graph TD\n';

        // Map Nodes
        nodes.forEach((node: Node) => {
            // Clean label
            const label = node.data.label || node.id;
            const cleanLabel = label.replace(/["\n]/g, '');
            // Mermaid syntax: A["Label"]
            mermaid += `    ${node.id}["${cleanLabel}"]\n`;
        });

        // Map Edges
        edges.forEach((edge: Edge) => {
            mermaid += `    ${edge.source} --> ${edge.target}\n`;
        });

        return textToBlob(mermaid, 'text/markdown');
    }
};
