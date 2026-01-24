import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import {
    useNodesState,
    useEdgesState,
    type Node,
    type Edge,
    type Connection,
    addEdge,
    useReactFlow,
    type NodeProps,
    ReactFlowProvider
} from 'reactflow';
import 'reactflow/dist/style.css';
import { db, type Song, type SongDocument } from '../../../lib/db';
import { Plus, Music, ChevronDown, ChevronRight, FileText, X } from 'lucide-react';
import { Button } from '../../ui/Button';
import { BaseFlowchart } from '../../flow/BaseFlowchart';
import { useFlowchartLayout } from '../../../hooks/useFlowchartLayout';
import { toast } from 'sonner';
import clsx from 'clsx';

interface FlowProps {
    songId: number;
}

const SECTION_TYPES = [
    { value: 'VERSE', color: 'from-pink-900/40 to-pink-700/40', border: 'border-pink-500/50', text: 'text-pink-400', bg: 'bg-pink-500' },
    { value: 'CHORUS', color: 'from-indigo-900/40 to-indigo-700/40', border: 'border-indigo-500/50', text: 'text-indigo-400', bg: 'bg-indigo-500' },
    { value: 'BRIDGE', color: 'from-orange-900/40 to-orange-700/40', border: 'border-orange-500/50', text: 'text-orange-400', bg: 'bg-orange-500' },
    { value: 'INTRO', color: 'from-gray-800/40 to-gray-700/40', border: 'border-gray-500/50', text: 'text-gray-400', bg: 'bg-gray-500' },
    { value: 'OUTRO', color: 'from-gray-800/40 to-gray-700/40', border: 'border-gray-500/50', text: 'text-gray-400', bg: 'bg-gray-500' },
    { value: 'INSTRUMENTAL', color: 'from-cyan-900/40 to-cyan-700/40', border: 'border-cyan-500/50', text: 'text-cyan-400', bg: 'bg-cyan-500' },
    { value: 'PRE-CHORUS', color: 'from-purple-900/40 to-purple-700/40', border: 'border-purple-500/50', text: 'text-purple-400', bg: 'bg-purple-500' },
    { value: 'HOOK', color: 'from-yellow-900/40 to-yellow-700/40', border: 'border-yellow-500/50', text: 'text-yellow-400', bg: 'bg-yellow-500' },
];

// Editable Section Node Component
function SectionNode({ data, id }: NodeProps) {
    const { setNodes } = useReactFlow();

    const currentType = SECTION_TYPES.find(t => t.value === data.type) || SECTION_TYPES[0];

    const updateLabel = (newLabel: string) => {
        setNodes(nds => nds.map(n => {
            if (n.id === id) {
                const newData = { ...n.data, label: newLabel };
                if (n.data.onSave) n.data.onSave(n.id, newData);
                return { ...n, data: newData };
            }
            return n;
        }));
    };

    const updateType = (newType: string) => {
        setNodes(nds => nds.map(n => {
            if (n.id === id) {
                const newData = { ...n.data, type: newType };
                if (n.data.onSave) n.data.onSave(n.id, newData);
                return { ...n, data: newData };
            }
            return n;
        }));
    };

    return (
        <div className={clsx(
            "bg-gradient-to-br border-2 rounded-lg p-3 min-w-[240px] shadow-lg transition-all group",
            currentType.color,
            currentType.border
        )}>
            <div className="flex items-center justify-between mb-2">
                <div className="flex items-center gap-2">
                    <Music size={14} className={currentType.text} />
                    <select
                        className="bg-black/20 text-xs font-bold text-white border border-white/10 rounded px-1 py-0.5 outline-none hover:bg-black/40"
                        value={data.type || 'VERSE'}
                        onChange={(e) => updateType(e.target.value)}
                        onPointerDown={(e) => e.stopPropagation()}
                    >
                        {SECTION_TYPES.map(t => (
                            <option key={t.value} value={t.value}>{t.value}</option>
                        ))}
                    </select>
                </div>
            </div>

            <textarea
                className="w-full bg-black/20 text-white text-sm p-2 rounded border border-white/5 outline-none resize-y min-h-[60px] font-medium leading-relaxed"
                value={data.label}
                onChange={(e) => updateLabel(e.target.value)}
                placeholder="Enter lyrics or notes..."
                onPointerDown={(e) => e.stopPropagation()}
            />
        </div>
    );
}

function SongFlowchartInner({ songId }: FlowProps) {
    const [nodes, setNodes, onNodesChange] = useNodesState([]);
    const [edges, setEdges, onEdgesChange] = useEdgesState([]);
    const [showToybox, setShowToybox] = useState(true);
    const [loading, setLoading] = useState(true);
    const [documents, setDocuments] = useState<SongDocument[]>([]);
    const [activeDocId, setActiveDocId] = useState<number | null>(null);

    // Dropdown state for Add Section button
    const [showAddDropdown, setShowAddDropdown] = useState(false);

    // Selection state - only show menu when there's an active selection
    const [hasSelection, setHasSelection] = useState(false);
    const [selectionPos, setSelectionPos] = useState({ x: 0, y: 0 });

    // Collapsible manuscript panel
    const [manuscriptExpanded, setManuscriptExpanded] = useState(true);

    const { getLayoutedElements } = useFlowchartLayout();

    // Track text selection in manuscript
    useEffect(() => {
        const handleSelectionChange = () => {
            const selection = window.getSelection();
            if (selection && selection.toString().trim().length > 0) {
                const range = selection.getRangeAt(0);
                const rect = range.getBoundingClientRect();
                setHasSelection(true);
                setSelectionPos({ x: rect.left + rect.width / 2, y: rect.top - 10 });
            } else {
                setHasSelection(false);
            }
        };

        document.addEventListener('selectionchange', handleSelectionChange);
        return () => document.removeEventListener('selectionchange', handleSelectionChange);
    }, []);

    // Load initial data
    useEffect(() => {
        const load = async () => {
            const song = await db.songs.get(songId);
            if (song && song.lyrics_structure) {
                const { nodes: savedNodes, edges: savedEdges } = song.lyrics_structure;
                const hydratedNodes = (savedNodes || []).map((n: Node) => ({
                    ...n,
                    data: { ...n.data, onSave: handleNodeDataChange }
                }));
                setNodes(hydratedNodes);
                if (savedEdges) setEdges(savedEdges);
            }

            const docs = await db.song_documents.where('song_id').equals(songId).toArray();
            setDocuments(docs);
            if (docs.length > 0) setActiveDocId(docs[0].id!);

            setLoading(false);
        };
        load();
    }, [songId, setNodes, setEdges]);

    const save = useCallback(async (currentNodes: Node[], currentEdges: Edge[]) => {
        const serializableNodes = currentNodes.map(n => {
            const { onSave, ...restData } = n.data;
            return { ...n, data: restData };
        });

        await db.songs.update(songId, {
            lyrics_structure: {
                nodes: serializableNodes,
                edges: currentEdges
            }
        });
    }, [songId]);

    const handleNodeDataChange = (nodeId: string, newData: any) => {
        setNodes(currentNodes => {
            const updatedNodes = currentNodes.map(n => n.id === nodeId ? { ...n, data: { ...newData, onSave: handleNodeDataChange } } : n);
            save(updatedNodes, edges);
            return updatedNodes;
        });
    };

    const onConnect = useCallback((params: Connection) => {
        setEdges((eds) => {
            const newEdges = addEdge(params, eds);
            save(nodes, newEdges);
            return newEdges;
        });
    }, [nodes, setEdges, save]);

    const onNodeDragStop = useCallback((_event: React.MouseEvent, node: Node) => {
        setNodes(nds => {
            const updated = nds.map(n => {
                if (n.id === node.id) {
                    return { ...n, position: node.position };
                }
                return n;
            });
            save(updated, edges);
            return updated;
        });
    }, [edges, save, setNodes]);

    const addNode = useCallback((initialLabel: string = 'New Section', initialType: string = 'VERSE') => {
        const id = `section-${Date.now()}`;
        const position = { x: 250 + Math.random() * 50, y: 100 + Math.random() * 50 };

        const newNode: Node = {
            id,
            type: 'section',
            position,
            data: {
                label: initialLabel,
                type: initialType,
                onSave: handleNodeDataChange
            }
        };

        setNodes(nds => {
            const updated = [...nds, newNode];
            save(updated, edges);
            return updated;
        });
        toast.success(`${initialType} added`);
        setShowAddDropdown(false);
    }, [edges, save, setNodes]);

    const handleTextSelection = (type: string) => {
        const selection = window.getSelection();
        if (!selection || selection.rangeCount === 0) return;

        const text = selection.toString().trim();
        if (!text) {
            toast.error("Select some text first!");
            return;
        }

        addNode(text, type);
        selection.removeAllRanges(); // Clear selection after creating node
        setHasSelection(false);
    };

    const onLayout = useCallback((direction: 'TB' | 'LR' = 'LR') => {
        const { nodes: layoutedNodes } = getLayoutedElements(nodes, edges, {
            direction,
            nodeWidth: 240,
            nodeHeight: 100
        });
        setNodes(layoutedNodes);
        save(layoutedNodes, edges);
    }, [nodes, edges, setNodes, save, getLayoutedElements]);

    const nodeTypesMemo = useMemo(() => ({
        section: SectionNode
    }), []);

    const activeDoc = documents.find(d => d.id === activeDocId);

    if (loading) return null;

    return (
        <BaseFlowchart
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeDragStop={onNodeDragStop}
            onNodesDelete={(deleted) => {
                setNodes(nds => {
                    const rem = nds.filter(n => !deleted.find(d => d.id === n.id));
                    save(rem, edges);
                    return rem;
                });
            }}
            nodeTypes={nodeTypesMemo}
            onLayout={onLayout}

            showToybox={showToybox}
            setShowToybox={setShowToybox}
            toyboxTitle="MANUSCRIPT"
            toyboxCount={documents.length}
            miniMapColor={() => '#ec4899'}

            toolbarActions={
                <div className="relative">
                    <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowAddDropdown(!showAddDropdown)}
                        className="backdrop-blur-md bg-black/50 hover:bg-pink-500/20 border-pink-500/50 text-pink-400"
                    >
                        <Plus size={14} className="mr-2" /> ADD SECTION <ChevronDown size={12} className="ml-1" />
                    </Button>

                    {showAddDropdown && (
                        <div className="absolute top-full right-0 mt-1 bg-neutral-900 border border-white/10 rounded-lg shadow-2xl z-50 min-w-[160px] py-1 animate-in fade-in slide-in-from-top-2">
                            {SECTION_TYPES.map(t => (
                                <button
                                    key={t.value}
                                    onClick={() => addNode('New Section', t.value)}
                                    className="w-full text-left px-3 py-2 hover:bg-white/5 text-sm text-gray-300 flex items-center gap-2"
                                >
                                    <div className={`w-2 h-2 rounded-full ${t.bg}`} />
                                    {t.value}
                                </button>
                            ))}
                        </div>
                    )}
                </div>
            }

            toyboxContent={
                <div className="h-full flex flex-col">
                    {/* Document Selector Header */}
                    <div className="mb-2">
                        <button
                            onClick={() => setManuscriptExpanded(!manuscriptExpanded)}
                            className="w-full flex items-center justify-between p-2 rounded hover:bg-white/5 transition-colors"
                        >
                            <div className="flex items-center gap-2 text-sm text-gray-300">
                                <FileText size={14} className="text-pink-400" />
                                <span>Manuscript</span>
                            </div>
                            {manuscriptExpanded ? <ChevronDown size={14} className="text-gray-500" /> : <ChevronRight size={14} className="text-gray-500" />}
                        </button>
                    </div>

                    {manuscriptExpanded && (
                        <>
                            <div className="mb-3">
                                <select
                                    className="w-full bg-black/40 border border-white/10 rounded p-2 text-sm text-white outline-none"
                                    value={activeDocId || ''}
                                    onChange={(e) => setActiveDocId(Number(e.target.value))}
                                >
                                    {documents.length === 0 && <option value="">No Documents Found</option>}
                                    {documents.map(d => (
                                        <option key={d.id} value={d.id}>{d.title} ({d.type})</option>
                                    ))}
                                </select>
                            </div>

                            {activeDoc ? (
                                <div className="flex-1 overflow-y-auto bg-black/20 p-4 rounded border border-white/5 relative">
                                    {/* Selection Popup - Only shows when text is selected */}
                                    {hasSelection && (
                                        <div
                                            className="fixed bg-neutral-900 border border-white/10 rounded-lg shadow-2xl z-50 py-1 animate-in fade-in zoom-in-95"
                                            style={{ left: selectionPos.x, top: selectionPos.y, transform: 'translate(-50%, -100%)' }}
                                        >
                                            <div className="text-[10px] text-gray-500 px-3 py-1 uppercase tracking-wider border-b border-white/10">Create Section</div>
                                            <div className="max-h-[200px] overflow-y-auto">
                                                {SECTION_TYPES.map(t => (
                                                    <button
                                                        key={t.value}
                                                        onMouseDown={(e) => { e.preventDefault(); handleTextSelection(t.value); }}
                                                        className="w-full text-left px-3 py-1.5 hover:bg-white/10 text-xs text-gray-300 flex items-center gap-2"
                                                    >
                                                        <div className={`w-2 h-2 rounded-full ${t.bg}`} />
                                                        {t.value}
                                                    </button>
                                                ))}
                                            </div>
                                        </div>
                                    )}

                                    <div className="prose prose-invert prose-sm max-w-none whitespace-pre-wrap font-mono text-gray-300 selection:bg-purple-500/40 selection:text-white">
                                        {activeDoc.content || "(Empty Document)"}
                                    </div>
                                </div>
                            ) : (
                                <div className="text-gray-500 text-sm text-center italic mt-10">
                                    No lyrics documents found. <br />
                                    Create one in the "Lyrics" tab first.
                                </div>
                            )}
                        </>
                    )}

                    {!manuscriptExpanded && (
                        <div className="text-gray-500 text-xs text-center italic py-4">
                            Click to expand manuscript
                        </div>
                    )}
                </div>
            }
        />
    );
}

export function SongFlowchart(props: FlowProps) {
    return (
        <ReactFlowProvider>
            <SongFlowchartInner {...props} />
        </ReactFlowProvider>
    );
}
