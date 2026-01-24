import React from 'react';
import { useDraggable, useDroppable } from '@dnd-kit/core';
import clsx from 'clsx';
import type { EntityType, UniversalDragPayload } from '../../lib/universal';

export interface UniversalCardProps {
    /** Core identity */
    entityType: EntityType;
    entityId: number;
    title: string;

    /** Optional: Additional data to pass in the drag payload */
    metadata?: Record<string, any>;

    /** Render prop for card content */
    children: React.ReactNode;

    /** If true, this card can also receive drops */
    isDroppable?: boolean;
    dropZoneId?: string;
    onDrop?: (dragData: any) => void;

    /** Optional handlers */
    onClick?: () => void;
    onDelete?: () => void;

    /** Visual Variant */
    variant?: 'card' | 'compact' | 'token';

    /** Optional: Full override for drag data or additional properties */
    data?: Record<string, any>;

    /** Styling */
    className?: string;
    accentColor?: string; // Border/highlight color
    noDefaultStyles?: boolean; // If true, disables default border/padding/bg
}

/**
 * UniversalCard: A standardized wrapper for any draggable entity.
 * Provides consistent drag-and-drop behavior and Transporter compatibility.
 */
export function UniversalCard({
    entityType,
    entityId,
    title,
    metadata,
    data: extraData,
    children,
    variant = 'card',
    isDroppable: isDroppableEnabled = false,
    dropZoneId,
    onDrop,
    onClick,
    onDelete,
    className,
    accentColor = 'white/10',
    noDefaultStyles = false
}: UniversalCardProps) {
    // Draggable Setup
    const dragId = `${entityType}-${entityId}`;
    const dragPayload: UniversalDragPayload = {
        type: 'universal-card',
        entityType,
        id: entityId,
        title,
        ...extraData // Allow overriding or extending payload
    };

    const { attributes, listeners, setNodeRef: setDragRef, isDragging, transform } = useDraggable({
        id: dragId,
        data: { ...dragPayload, metadata, variant }
    });

    // Transform style for proper drag positioning
    // Transform: We do NOT move the original card. We use DragOverlay in Layout.
    // However, we want to hide the original or make it 'ghost' like.
    const dragStyle = undefined;

    // Droppable Setup (optional)
    const { setNodeRef: setDropRef, isOver } = useDroppable({
        id: dropZoneId || `drop-${dragId}`,
        data: { type: entityType, id: entityId },
        disabled: !isDroppableEnabled
    });

    // Combine refs if both draggable and droppable
    const combinedRef = (node: HTMLDivElement | null) => {
        setDragRef(node);
        if (isDroppableEnabled) setDropRef(node);
    };

    // Base classes always applied
    const baseClasses = "group relative transition-all cursor-grab active:cursor-grabbing";

    // Variant Styles
    const variantClasses = {
        card: "rounded-lg border hover:shadow-lg hover:-translate-y-0.5",
        compact: "rounded border flex items-center gap-2 px-2 py-1",
        token: "rounded-full border px-3 py-1 text-xs inline-flex items-center"
    };

    // Default style classes (conditional)
    const defaultClasses = variantClasses[variant] || variantClasses.card;

    // Dynamic interaction classes
    const interactionClasses = clsx(
        isDragging && "opacity-30 scale-95",
        isOver && isDroppableEnabled && "ring-2 ring-neon shadow-neon/20"
    );

    return (
        <div
            ref={combinedRef}
            style={dragStyle}
            {...listeners}
            {...attributes}
            onClick={onClick}
            className={clsx(
                baseClasses,
                !noDefaultStyles && defaultClasses,
                !noDefaultStyles && `border-${accentColor}`,
                interactionClasses,
                className,
                isDragging ? "opacity-20 grayscale border-dashed border-white/20" : "opacity-100" // Explicit ghost styling
            )}
        >
            {children}

            {/* Optional Delete Button (appears on hover) */}
            {onDelete && (
                <button
                    onClick={(e) => { e.stopPropagation(); onDelete(); }}
                    className="absolute top-1 right-1 p-1 rounded bg-black/50 text-gray-400 hover:text-red-400 opacity-0 group-hover:opacity-100 transition-opacity"
                    title="Delete"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 6h18" /><path d="M19 6v14c0 1-1 2-2 2H7c-1 0-2-1-2-2V6" /><path d="M8 6V4c0-1 1-2 2-2h4c1 0 2 1 2 2v2" /></svg>
                </button>
            )}
        </div>
    );
}

export default UniversalCard;
