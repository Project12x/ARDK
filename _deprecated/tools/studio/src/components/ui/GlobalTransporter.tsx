import { useState } from 'react';
import { useUIStore } from '../../store/useStore';
import type { StashItem } from '../../store/useStore';
import { Package, X, Box, FileText, Folder, ChevronDown, ChevronUp, Target, Repeat, ExternalLink, Minimize2, Music } from 'lucide-react';
import { useDraggable, useDroppable } from '@dnd-kit/core';
import clsx from 'clsx';

const STASH_ICONS: Record<string, any> = {
    inventory: Package,
    project: Folder,
    note: FileText,
    asset: Box,
    goal: Target,
    routine: Repeat,
    library: FileText,
    song: Music,
    album: Music,
    // Universal fallback handled by default
};

// Sidebar-integrated Stash component
export function SidebarStash({ isCollapsed, isDraggingGlobal }: { isCollapsed?: boolean, isDraggingGlobal?: boolean }) {
    const { stashItems, removeFromStash, clearStash, setTransporterPopped, isTransporterPopped } = useUIStore();
    const [isExpanded, setIsExpanded] = useState(false);

    const { setNodeRef, isOver } = useDroppable({
        id: 'transporter-sidebar',
        data: { type: 'stash' }
    });

    // If popped out, show minimal indicator in sidebar BUT KEEP DROP ZONE ACTIVE
    if (isTransporterPopped && !isCollapsed) {
        return (
            <div
                ref={setNodeRef}
                className={clsx(
                    "border-t border-white/10 mt-auto p-3 transition-all",
                    isOver && "bg-neon/10 border-neon"
                )}
            >
                <button
                    onClick={() => setTransporterPopped(false)}
                    className="w-full px-3 py-2 flex items-center justify-center gap-2 bg-neon/10 border border-neon/30 rounded-lg hover:bg-neon/20 transition-colors text-neon text-[10px] font-mono uppercase"
                >
                    <Minimize2 size={12} />
                    {isOver ? "Drop Here!" : "Dock Transporter"}
                </button>
            </div>
        );
    }

    if (isCollapsed) {
        // Minimal icon when sidebar is collapsed
        return (
            <div
                ref={setNodeRef}
                onClick={() => setTransporterPopped(true)}
                title="Click to Open Transporter"
                className={clsx(
                    "relative p-1.5 mx-1 my-1 rounded-lg border-2 border-solid transition-all duration-300 cursor-pointer hover:bg-white/10 z-50 min-h-[40px]",
                    isOver ? "border-neon bg-neon/20 shadow-[0_0_15px_rgba(34,197,94,0.5)]" : (isDraggingGlobal ? "border-neon/50 bg-neon/5 shadow-[0_0_10px_rgba(34,197,94,0.2)] animate-pulse" : "border-white/10 hover:border-white/30"),
                    stashItems.length > 0 && !isOver && !isDraggingGlobal && "border-neon/50"
                )}
            >
                <Box size={20} className={clsx(
                    "mx-auto transition-colors",
                    (stashItems.length > 0 || isOver || isDraggingGlobal) ? "text-neon" : "text-gray-500"
                )} />
                {stashItems.length > 0 && (
                    <span className="absolute -top-1 -right-1 flex h-4 w-4 items-center justify-center rounded-full bg-red-500 text-[10px] text-white font-bold">
                        {stashItems.length}
                    </span>
                )}
            </div>
        );
    }

    return (
        <div ref={setNodeRef} className={clsx(
            "border-t border-white/10 mt-auto transition-all duration-300 min-h-[52px] relative z-[100]",
            isOver
                ? "bg-neon/20 border-neon border-2 border-solid shadow-[0_0_20px_rgba(34,197,94,0.3)]"
                : (isDraggingGlobal
                    ? "bg-neon/5 border-neon/40 border-2 border-solid shadow-[0_0_10px_rgba(34,197,94,0.1)]"
                    : "border-solid border-white/10")
        )}>
            {/* Header */}
            <div className="w-full px-3 py-2 flex items-center justify-between">
                <button
                    onClick={() => setIsExpanded(!isExpanded)}
                    className="flex-1 flex items-center gap-2 hover:bg-white/5 rounded px-2 py-1.5 transition-colors"
                >
                    <span className={clsx(
                        "text-[11px] font-bold uppercase tracking-wider flex items-center gap-2 transition-colors",
                        (stashItems.length > 0 || isDraggingGlobal) ? "text-neon" : "text-gray-500"
                    )}>
                        <Box size={14} className={clsx(stashItems.length > 0 || isDraggingGlobal ? "text-neon" : "")} />
                        Transporter
                        {stashItems.length > 0 && (
                            <span className="px-1.5 py-0.5 rounded-full bg-neon/20 text-neon text-[10px]">
                                {stashItems.length}
                            </span>
                        )}
                        {isDraggingGlobal && !isOver && (
                            <span className="px-1.5 py-0.5 rounded-full bg-neon/20 text-neon text-[10px] animate-pulse">
                                DROP HERE
                            </span>
                        )}
                    </span>
                    {isExpanded ? <ChevronDown size={14} className="text-gray-500" /> : <ChevronUp size={14} className="text-gray-500" />}
                </button>
                {/* Pop-out button */}
                <button
                    onClick={() => setTransporterPopped(true)}
                    className="p-1.5 text-gray-500 hover:text-neon transition-colors rounded hover:bg-white/5"
                    title="Pop out Transporter"
                >
                    <ExternalLink size={14} />
                </button>
            </div >

            {isExpanded && (
                <div className="px-2 pb-3">
                    {/* Drop Zone Visual Indicator - parent div handles dnd-kit drops */}
                    <div
                        className={clsx(
                            "rounded-lg border-2 border-solid p-4 transition-all min-h-[160px]",
                            isOver
                                ? "border-neon bg-neon/10 shadow-[0_0_20px_rgba(34,197,94,0.3)]"
                                : (isDraggingGlobal
                                    ? "border-neon/40 bg-neon/5 animate-pulse"
                                    : stashItems.length > 0
                                        ? "border-neon/30 bg-black/30"
                                        : "border-white/10 bg-black/20")
                        )}
                    >
                        {stashItems.length === 0 ? (
                            <div className={clsx(
                                "text-center py-6 transition-colors",
                                isOver || isDraggingGlobal ? "text-neon" : "text-gray-600"
                            )}>
                                <Box size={32} className="mx-auto mb-3 opacity-50" />
                                <div className="text-xs font-mono uppercase">
                                    {isOver ? "Drop to stash" : (isDraggingGlobal ? "Release to Stash" : "Drag items here")}
                                </div>
                            </div>
                        ) : (
                            <div className="space-y-1">
                                {stashItems.map(item => (
                                    <StashCard key={item.id} item={item} onRemove={() => removeFromStash(item.id)} />
                                ))}
                                {stashItems.length > 0 && (
                                    <button
                                        onClick={() => clearStash()}
                                        className="w-full mt-2 py-1.5 text-xs text-red-500/50 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                                    >
                                        Clear All
                                    </button>
                                )}
                            </div>
                        )}
                    </div>


                </div>
            )
            }
        </div >
    );
}

// Floating Transporter (pop-out mode)
export function FloatingTransporter() {
    const { stashItems, removeFromStash, clearStash, isTransporterPopped, setTransporterPopped } = useUIStore();

    const { setNodeRef, isOver } = useDroppable({
        id: 'transporter-floating',
        data: { type: 'stash' }
    });

    if (!isTransporterPopped) return null;

    return (
        <div
            ref={setNodeRef}
            className={clsx(
                "fixed bottom-4 right-4 w-96 bg-black/95 backdrop-blur-xl border rounded-xl shadow-2xl z-50 overflow-hidden flex flex-col",
                isOver ? "border-neon shadow-neon/20 bg-neon/5" : "border-white/10"
            )}
            style={{ height: '400px' }} // Fixed generous height
        >
            {/* Header */}
            <div className="px-3 py-2 bg-white/5 border-b border-white/10 flex items-center justify-between shrink-0">
                <span className="text-xs font-bold uppercase tracking-wider text-gray-400 flex items-center gap-2">
                    <Box size={14} className={stashItems.length > 0 ? "text-neon" : ""} />
                    Transporter
                    {stashItems.length > 0 && (
                        <span className="px-1.5 py-0.5 rounded-full bg-neon/20 text-neon text-[10px]">
                            {stashItems.length}
                        </span>
                    )}
                </span>
                <button
                    onClick={() => setTransporterPopped(false)}
                    className="p-1 text-gray-500 hover:text-white transition-colors rounded hover:bg-white/5"
                    title="Dock Transporter"
                >
                    <Minimize2 size={14} />
                </button>
            </div>

            {/* Content / Drop Zone - 1:1 Coverage */}
            <div className="flex-1 overflow-y-auto custom-scrollbar p-3 flex flex-col">
                <div
                    className={clsx(
                        "rounded-lg border-2 border-dashed flex-1 transition-all flex flex-col relative",
                        isOver
                            ? "border-neon bg-neon/10"
                            : stashItems.length > 0
                                ? "border-neon/30 bg-black/30"
                                : "border-white/20 bg-black/20"
                    )}
                >
                    {stashItems.length === 0 ? (
                        <div className={clsx(
                            "absolute inset-0 flex flex-col items-center justify-center transition-colors pointer-events-none",
                            isOver ? "text-neon" : "text-gray-600"
                        )}>
                            <Box size={32} className="mb-2 opacity-50" />
                            <div className="text-xs font-mono uppercase">
                                {isOver ? "Drop to stash" : "Drag items here"}
                            </div>
                        </div>
                    ) : (
                        <div className="space-y-1 p-3">
                            {stashItems.map(item => (
                                <StashCard key={item.id} item={item} onRemove={() => removeFromStash(item.id)} />
                            ))}
                            {stashItems.length > 0 && (
                                <button
                                    onClick={() => clearStash()}
                                    className="w-full mt-2 py-1 text-xs text-red-500/50 hover:text-red-500 hover:bg-red-500/10 rounded transition-colors"
                                >
                                    Clear All
                                </button>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}

// Keep for backward compatibility
export function GlobalTransporter() {
    return null;
}


function StashCard({ item, onRemove }: { item: StashItem, onRemove: () => void }) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `transport-${item.id}`,
        data: {
            type: 'stash-item',
            payload: item
        }
    });

    // No self-transform, use Layout DragOverlay
    const style = undefined;

    const Icon = STASH_ICONS[item.type] || Box;

    return (
        <div
            ref={setNodeRef}
            style={style}
            {...listeners}
            {...attributes}
            className={clsx(
                "group relative bg-white/5 border border-white/10 rounded p-2 hover:border-neon/50 transition-colors cursor-grab active:cursor-grabbing flex items-center gap-2",
                isDragging && "opacity-20 grayscale border-dashed border-white/20"
            )}
        >
            <div className="text-gray-400 flex-shrink-0">
                <Icon size={12} />
            </div>

            <div className="flex-1 min-w-0">
                <div className="text-[11px] font-bold text-white truncate">{item.title}</div>
                {item.subtitle && <div className="text-[9px] text-gray-500 truncate">{item.subtitle}</div>}
            </div>

            <button
                onClick={(e) => { e.stopPropagation(); onRemove(); }}
                className="opacity-0 group-hover:opacity-100 p-0.5 text-gray-500 hover:text-red-500 transition-opacity flex-shrink-0"
            >
                <X size={10} />
            </button>
        </div>
    );
}
