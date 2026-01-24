/**
 * UniversalCard - Enhanced Generic Card Component
 * 
 * A fully-featured card that works with ANY UniversalEntity type.
 * Includes: DND, edit mode, status indicators, action buttons, and slots.
 */

import React, { useState, useEffect, ReactNode } from 'react';
import { useDraggable } from '@dnd-kit/core';
import { CSS } from '@dnd-kit/utilities';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import clsx from 'clsx';
import { toast } from 'sonner';
import {
    GripVertical, Settings, Save, X, Trash2, ExternalLink,
    Circle, CheckCircle, AlertCircle, Clock, Archive, Folder, Box
} from 'lucide-react';

import type { UniversalEntity, UniversalDragPayload, UniversalAction } from '../../lib/universal/types';
import { cardVariants, statusStripeVariants, badgeVariants } from '../../lib/universal/cardVariants';
import { AutoEditForm } from '../../lib/universal/AutoEditForm';
import { useUniversalDnd } from '../../lib/universal/useUniversalDnd';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// GENERIC EDIT SCHEMA (Title + basic fields)
// ============================================================================

const genericEditSchema = z.object({
    title: z.string().min(1, 'Title required'),
    subtitle: z.string().optional(),
    status: z.string().optional(),
});

type GenericEditFormData = z.infer<typeof genericEditSchema>;

// ============================================================================
// STATUS CONFIG
// ============================================================================

const STATUS_CONFIG: Record<string, { icon: typeof Circle; color: string; label: string }> = {
    'active': { icon: CheckCircle, color: 'text-green-500', label: 'Active' },
    'completed': { icon: CheckCircle, color: 'text-green-500', label: 'Completed' },
    'in-progress': { icon: Clock, color: 'text-blue-500', label: 'In Progress' },
    'pending': { icon: Circle, color: 'text-gray-500', label: 'Pending' },
    'blocked': { icon: AlertCircle, color: 'text-red-500', label: 'Blocked' },
    'paused': { icon: Clock, color: 'text-amber-500', label: 'Paused' },
    'archived': { icon: Archive, color: 'text-gray-600', label: 'Archived' },
    'default': { icon: Circle, color: 'text-gray-500', label: '' },
};

// ============================================================================
// PROPS - Expanded for Universal Functionality
// ============================================================================

interface UniversalCardProps {
    entity: UniversalEntity;

    /** Visual Variant */
    variant?: 'default' | 'dense' | 'compact' | 'moderate' | 'expanded' | 'text';

    // === CONTENT SLOTS ===
    /** Custom header content (replaces default) */
    header?: ReactNode;
    /** Media/thumbnail slot (image, video, icon placeholder) */
    media?: ReactNode;
    /** Main body content */
    children?: ReactNode;
    /** Footer content (metadata, tags, timestamps) */
    footer?: ReactNode;

    // === THUMBNAIL & VISUAL ===
    /** Thumbnail URL - auto-renders image if provided */
    thumbnail?: string;
    /** Fallback icon if no thumbnail */
    thumbnailIcon?: ReactNode;
    /** Show progress bar (0-100) */
    progress?: number;
    /** Progress bar color class */
    progressColor?: string;
    /** Badge content (top-left overlay) */
    badge?: ReactNode;
    /** Status badge configuration */
    statusBadge?: { label: string; icon?: ReactNode; color?: string; bg?: string };

    // === CORE BEHAVIOR ===
    isDraggable?: boolean;
    dragOnType?: 'card' | 'handle';
    dragOrigin?: UniversalDragPayload['origin'];
    onClick?: () => void;
    onEdit?: (data: GenericEditFormData) => Promise<void>;
    onDelete?: () => Promise<void>;

    // === ACTION CALLBACKS ===
    /** Called when play button clicked (for media entities) */
    onPlay?: () => void;
    /** Called when download action triggered */
    onDownload?: () => void;
    /** Called when preview action triggered */
    onPreview?: () => void;
    /** Called when triage action triggered (for inbox/queue items) */
    onTriage?: () => void;
    /** Called when complete/check action triggered (for tasks/routines) */
    onComplete?: () => void;
    /** Called when archive action triggered */
    onArchive?: () => void;
    /** Called when duplicate action triggered */
    onDuplicate?: () => void;
    /** Called when link/relationship action triggered */
    onLink?: () => void;
    /** Called when pin/unpin action triggered (for notes, favorites) */
    onPin?: () => void;

    // === ENTITY-SPECIFIC DATA (Future-Proofing) ===
    /** External URL to display/link (websites, stores, repos) */
    externalUrl?: string;
    /** Tracking/reference number (orders, shipments) */
    trackingNumber?: string;
    /** Priority level (1-5) */
    priority?: number;
    /** Is this item pinned/favorited */
    isPinned?: boolean;
    /** API integration status (for vendors, services) */
    apiStatus?: 'connected' | 'disconnected' | 'none';
    /** Quantity display (for inventory, orders) */
    quantity?: number;
    /** Unit cost/price display */
    unitCost?: number;
    /** Currency for cost display */
    currency?: string;
    /** Version/revision string (for logs, documents) */
    version?: string;
    /** Category string */
    category?: string;

    // === CONTROLLED EDIT MODE ===
    isEditing?: boolean;
    onEditChange?: (isEditing: boolean) => void;

    // === PHASE 11b: CONSOLIDATION PROPS ===

    /** Enable collapsed/expanded toggle */
    collapsible?: boolean;
    /** Is card currently collapsed */
    isCollapsed?: boolean;
    /** Callback when collapse state changes */
    onToggleCollapse?: () => void;
    /** Layout mode for responsive variants */
    layoutMode?: 'grid' | 'list' | 'kanban';

    /** Background image URL (full-bleed with gradient overlay) */
    backgroundImage?: string;
    /** Status stripe color (left edge) */
    statusStripeColor?: string;
    /** Enable status glow effect */
    statusGlow?: boolean;

    /** Configurable rating bars */
    ratings?: Array<{
        label: string;
        value: number;
        max: number;
        color: string;
        onChange?: (value: number) => void;
    }>;

    /** Raw metrics content (e.g. charts, time tracking) displayed alongside ratings */
    metrics?: ReactNode;

    /** Metadata grid display */
    metaGrid?: Array<{
        label: string;
        value: string | number;
        icon?: ReactNode;
    }>;

    /** Next action/step display */
    nextAction?: {
        label: string;
        subtitle?: string;
        icon?: ReactNode;
        onClick?: () => void;
    };

    /** External links (GitHub, website, etc) */
    externalLinks?: Array<{
        label: string;
        url: string;
        icon?: ReactNode;
    }>;

    /** Zod schema for auto-generated edit form */
    editSchema?: z.ZodObject<any>;
    /** Field configuration for auto edit form */
    editFieldConfig?: Record<string, any>;
    /** Custom edit form slot (bespoke mode) */
    editSlot?: ReactNode;
    /** Detail page URL for navigation */
    detailUrl?: string;
    /** Callback for navigation to detail */
    onNavigate?: () => void;

    /** Due date for overdue detection */
    dueDate?: Date;
    /** Is item overdue */
    isOverdue?: boolean;
    /** Is item due today */
    isDueToday?: boolean;

    // === COMPOSITION SLOTS ===
    /** Header slot for custom header content */
    headerSlot?: ReactNode;
    /** Body slot for custom body content */
    bodySlot?: ReactNode;
    /** Footer slot for custom footer content */
    footerSlot?: ReactNode;
    /** Actions slot for custom action buttons */
    actionsSlot?: ReactNode;

    // === ACTION CONFIGURATION ===
    /** Custom actions array for action menu */
    actions?: UniversalAction[];
    /** Quick actions shown on hover (max 3 recommended) */
    quickActions?: Array<{
        id: string;
        icon: ReactNode;
        label: string;
        onClick: () => void;
        variant?: 'default' | 'success' | 'danger' | 'warning';
    }>;

    // === DISPLAY OPTIONS ===
    /** Disable all default styles for custom content control */
    noDefaultStyles?: boolean;
    className?: string;
    variant?: 'default' | 'compact' | 'minimal' | 'media' | 'list';
    loading?: boolean;
    showStatus?: boolean;
    showActions?: boolean;
    /** Show play button overlay on thumbnail */
    showPlayButton?: boolean;
    /** Show progress bar */
    showProgress?: boolean;
    /** Show drag handle */
    showDragHandle?: boolean;
    /** Show timestamp */
    showTimestamp?: boolean;
    /** Show tags */
    showTags?: boolean;
    /** Show external URL */
    showExternalUrl?: boolean;
    /** Show tracking number */
    showTracking?: boolean;
    /** Show priority indicator */
    showPriority?: boolean;
    /** Show quantity */
    showQuantity?: boolean;
    /** Show cost */
    showCost?: boolean;
    /** Show pin button */
    showPinButton?: boolean;
    /** Disable hover effects */
    disableHover?: boolean;
    /** Make card selectable (checkbox mode) */
    selectable?: boolean;
    /** Is card selected */
    selected?: boolean;
    /** Selection change callback */
    onSelectChange?: (selected: boolean) => void;

    // === LIFECYCLE STATES ===
    /** Is item in trash */
    isTrash?: boolean;
    /** Is item archived */
    isArchived?: boolean;
    /** Callback to restore from trash */
    onRestoreTrash?: () => void;
    /** Callback to purge from trash */
    onPurge?: () => void;

    /** Extended Badges (Sync/Async) */
    badges?: Array<ReactNode | {
        label?: string;
        icon?: ReactNode;
        color?: string;
        onClick?: () => void;
        tooltip?: string;
    }>;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function UniversalCard({
    entity,
    // === Content Slots ===
    header,
    media,
    children,
    noDefaultStyles,
    footer,
    // === Thumbnail & Visual ===
    thumbnail,
    thumbnailIcon,
    progress,
    progressColor = 'bg-accent',
    badge,
    statusBadge,
    // === Core Behavior ===
    isDraggable = true,
    dragOnType = 'handle',
    dragOrigin = 'grid',
    onClick,
    onEdit,
    onDelete,
    // === Action Callbacks ===
    onPlay,
    onDownload,
    onPreview,
    onTriage,
    onComplete,
    onArchive,
    onDuplicate,
    onLink,
    onPin,
    // === Phase 11b: Consolidation Props ===
    collapsible = false,
    isCollapsed: controlledCollapsed,
    onToggleCollapse,
    layoutMode = 'grid',
    backgroundImage,
    statusStripeColor,
    statusGlow = false,
    ratings = [],
    metrics,
    metaGrid = [],
    nextAction,
    externalLinks = [],
    editSchema,
    editFieldConfig,
    editSlot,
    detailUrl,
    onNavigate,
    dueDate,
    isOverdue = false,
    isDueToday = false,
    // === Composition Slots ===
    headerSlot,
    bodySlot,
    footerSlot,
    actionsSlot,
    // === Action Configuration ===
    actions = [],
    quickActions = [],
    // === Display Options ===
    className,
    variant = 'default',
    loading = false,
    showStatus = true,
    showActions = true,
    showPlayButton = false,
    showProgress = false,
    showDragHandle = true,
    showTimestamp = false,
    showTags = false,
    disableHover = false,
    selectable = false,
    selected = false,
    onSelectChange,
    isEditing: controlledIsEditing,
    onEditChange,

    // Lifecycle
    isTrash = false,
    isArchived = false,
    onRestoreTrash,
    onPurge,
    badges = [],
}: UniversalCardProps) {
    const [internalIsEditing, setInternalIsEditing] = useState(false);
    const isEditing = controlledIsEditing !== undefined ? controlledIsEditing : internalIsEditing;

    const handleSetIsEditing = (value: boolean) => {
        if (onEditChange) {
            onEditChange(value);
        } else {
            setInternalIsEditing(value);
        }
    };

    // === DERIVE EFFECTIVE CONFIG FROM ENTITY ===
    // If specific props are not provided, fall back to entity.cardConfig
    const activeBackgroundImage = backgroundImage ?? entity.cardConfig?.backgroundImage;
    const activeStatusStripeColor = statusStripeColor ?? entity.cardConfig?.statusStripe;
    const activeStatusGlow = statusGlow || entity.cardConfig?.statusGlow || false;
    const activeCollapsible = collapsible || entity.cardConfig?.collapsible || false;
    const activeDefaultCollapsed = entity.cardConfig?.defaultCollapsed || false;

    const activeRatings = ratings.length > 0 ? ratings : (entity.cardConfig?.ratings || []);
    const activeMetaGrid = metaGrid.length > 0 ? metaGrid : (entity.cardConfig?.metaGrid || []);
    const activeNextAction = nextAction || entity.cardConfig?.nextAction;
    const activeExternalLinks = externalLinks.length > 0 ? externalLinks : (entity.cardConfig?.externalLinks || []);

    const [internalCollapsed, setInternalCollapsed] = useState(activeDefaultCollapsed);

    // Controlled or uncontrolled collapsed state
    const isCollapsed = controlledCollapsed !== undefined ? controlledCollapsed : internalCollapsed;
    const handleToggleCollapse = () => {
        if (onToggleCollapse) {
            onToggleCollapse();
        } else {
            setInternalCollapsed(!internalCollapsed);
        }
    };

    // -- Form Setup --
    const { register, handleSubmit, reset, formState: { errors, isSubmitting } } = useForm<GenericEditFormData>({
        resolver: zodResolver(genericEditSchema),
        defaultValues: {
            title: '',
            subtitle: '',
            status: '',
        },
    });

    // Reset form when entity changes or edit mode opens
    useEffect(() => {
        reset({
            title: entity.title || '',
            subtitle: entity.subtitle || '',
            status: entity.status || '',
        });
    }, [entity, isEditing, reset]);

    // === DND HOOK ===
    // Use the standardized hook for consistent payload structure
    const { attributes, listeners, setNodeRef, isDragging } = useUniversalDnd(
        entity,
        dragOrigin || 'grid',
        !isDraggable || isEditing // disable dnd if not draggable OR if editing
    );

    // We do NOT apply transform to the card itself, because we use a global DragOverlay
    // This prevents the card from moving out of its slot during drag (it just dims)

    // -- Form Submit --
    const handleFormSubmit = async (data: GenericEditFormData) => {
        if (onEdit) {
            try {
                await onEdit(data);
                toast.success('Updated successfully');
                handleSetIsEditing(false);
            } catch (error) {
                console.error('Failed to save:', error);
                toast.error('Failed to save');
            }
        } else {
            // No custom handler, just close
            handleSetIsEditing(false);
        }
    };

    // -- Delete Handler --
    const handleDelete = async () => {
        if (onDelete && confirm(`Delete "${entity.title}"?`)) {
            try {
                await onDelete();
                toast.success('Deleted');
            } catch (error) {
                console.error('Failed to delete:', error);
                toast.error('Failed to delete');
            }
        }
    };

    // -- Status Badge --
    const statusConfig = STATUS_CONFIG[entity.status || 'default'] || STATUS_CONFIG['default'];
    const StatusIcon = statusConfig.icon;

    // -- Loading State --
    if (loading) {
        return (
            <div className={clsx("rounded-xl bg-white/5 border border-white/5 animate-pulse h-48", className)} />
        );
    }

    // ========================================================================
    // TRASH STATE
    // ========================================================================
    if (isTrash) {
        return (
            <div
                className={clsx(
                    "border border-red-900/30 bg-red-950/10 p-4 flex justify-between items-center rounded-xl overflow-hidden min-h-[4rem]",
                    className
                )}
            >
                <div className="opacity-50 flex items-center gap-4">
                    <Trash2 className="text-red-700" size={20} />
                    <div>
                        <h3 className="text-lg font-black text-red-700 line-through truncate max-w-[200px]">{entity.title}</h3>
                        <p className="text-xs font-mono text-red-900">DELETED</p>
                    </div>
                </div>
                <div className="flex gap-2">
                    {onRestoreTrash && (
                        <Button size="sm" variant="outline" onClick={(e) => { e.stopPropagation(); onRestoreTrash(); }}>
                            RESTORE
                        </Button>
                    )}
                    {onPurge && (
                        <Button size="sm" className="bg-red-900 hover:bg-red-800 text-white border-none" onClick={(e) => { e.stopPropagation(); onPurge(); }}>
                            PURGE
                        </Button>
                    )}
                </div>
            </div>
        )
    }

    // ========================================================================
    // EDIT MODE
    // ========================================================================

    if (isEditing) {
        return (
            <div className="bg-black border border-accent/50 rounded-xl p-4 shadow-xl z-20 animate-in fade-in zoom-in-95 relative">
                {/* Mode 1: Bespoke Edit Slot (Fully Custom Form) */}
                {editSlot ? (
                    <div className="relative">
                        <button
                            type="button"
                            onClick={() => handleSetIsEditing(false)}
                            className="absolute -top-1 -right-1 text-gray-500 hover:text-white z-10"
                        >
                            <X size={16} />
                        </button>
                        {editSlot}
                    </div>
                ) :
                    /* Mode 2: Auto Edit Form (Schema Driven) */
                    editSchema ? (
                        <AutoEditForm
                            schema={editSchema}
                            defaultValues={entity as any} // Entity usually matches schema
                            onSubmit={async (data) => {
                                if (onEdit) {
                                    await onEdit(data);
                                    handleSetIsEditing(false);
                                }
                            }}
                            onCancel={() => handleSetIsEditing(false)}
                            fieldConfig={editFieldConfig}
                            title={`Edit ${entity.type}`}
                            compact={true}
                        />
                    ) : (
                        /* Mode 3: Generic Fallback Form */
                        <form onSubmit={handleSubmit(handleFormSubmit)} className="space-y-4">
                            <div className="flex items-center justify-between mb-2">
                                <h3 className="text-sm font-bold text-accent">
                                    Edit {entity.type}
                                </h3>
                                <button type="button" onClick={() => handleSetIsEditing(false)} className="text-gray-500 hover:text-white">
                                    <X size={16} />
                                </button>
                            </div>

                            <Input
                                label="Title"
                                {...register('title')}
                                error={errors.title?.message}
                                autoFocus
                            />

                            <Input
                                label="Subtitle"
                                {...register('subtitle')}
                                placeholder="Optional description"
                            />

                            <div>
                                <label className="block text-xs font-bold text-gray-500 mb-1 uppercase">Status</label>
                                <select
                                    {...register('status')}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                                >
                                    <option value="">None</option>
                                    <option value="active">Active</option>
                                    <option value="in-progress">In Progress</option>
                                    <option value="pending">Pending</option>
                                    <option value="completed">Completed</option>
                                    <option value="blocked">Blocked</option>
                                    <option value="paused">Paused</option>
                                    <option value="archived">Archived</option>
                                </select>
                            </div>

                            <div className="flex justify-between items-center pt-3 border-t border-white/10">
                                {onDelete && (
                                    <Button
                                        type="button"
                                        variant="ghost"
                                        size="sm"
                                        onClick={handleDelete}
                                        className="text-red-500 hover:bg-red-500/10"
                                    >
                                        <Trash2 size={14} />
                                    </Button>
                                )}
                                <div className="flex gap-2 ml-auto">
                                    <Button type="button" variant="ghost" size="sm" onClick={() => setIsEditing(false)}>
                                        Cancel
                                    </Button>
                                    <Button type="submit" size="sm" disabled={isSubmitting}>
                                        <Save size={14} className="mr-1" /> Save
                                    </Button>
                                </div>
                            </div>
                        </form>
                    )}
            </div>
        );
    }

    // ========================================================================
    // VIEW MODE
    // ========================================================================

    // Map entity status to cva status variant
    const cvaStatus = (['active', 'pending', 'completed', 'archived', 'error'].includes(entity.status || ''))
        ? entity.status as 'active' | 'pending' | 'completed' | 'archived' | 'error'
        : 'default';

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            {...(dragOnType === 'card' && isDraggable ? { ...attributes, ...listeners } : {})}
            className={cardVariants({
                variant: variant as any,
                status: cvaStatus,
                interactive: !disableHover && !!onClick,
                dragging: isDragging,
                selected: selected,
                collapsed: isCollapsed,
                hasBackground: !!backgroundImage,
                className: clsx(className, isArchived && "opacity-60 saturate-50 hover:opacity-100 hover:saturate-100 transition-all"),
            })}
        >
            {/* Status Stripe (Left Edge) */}
            {activeStatusStripeColor && (
                <div
                    onClick={activeCollapsible ? handleToggleCollapse : undefined}
                    title={activeCollapsible ? (isCollapsed ? 'Expand' : 'Collapse') : undefined}
                    className={statusStripeVariants({
                        size: 'md',
                        interactive: activeCollapsible
                    })}
                    style={{
                        backgroundColor: activeStatusStripeColor,
                        boxShadow: activeStatusGlow ? `0 0 10px ${activeStatusStripeColor}` : undefined,
                    }}
                />
            )}

            {/* Background Image with Gradient Overlay */}
            {/* Universal Background System (Advanced) */}
            {!isCollapsed && (activeBackgroundImage || activeStatusGlow) && (
                <div className="absolute inset-0 z-0 pointer-events-none">
                    {activeBackgroundImage ? (
                        <div className="absolute inset-0 bg-cover bg-center opacity-10 mix-blend-overlay transition-transform duration-700 group-hover:scale-105" style={{ backgroundImage: `url(${activeBackgroundImage})` }} />
                    ) : (
                        /* Generated Gradient for No-Image State */
                        <div
                            className="absolute inset-0 opacity-20 transition-transform duration-700 group-hover:scale-105"
                            style={{
                                background: activeStatusStripeColor
                                    ? `radial-gradient(circle at top right, ${activeStatusStripeColor}, transparent 80%)`
                                    : 'linear-gradient(to bottom right, rgba(255,255,255,0.05), transparent)'
                            }}
                        />
                    )}
                    <div className="absolute inset-0 bg-gradient-to-t from-black via-black/90 to-black/40" />
                    {activeStatusGlow && activeStatusStripeColor && (
                        <div
                            className="absolute top-0 right-0 w-64 h-64 bg-current opacity-10 blur-[80px] -translate-y-1/2 translate-x-1/2 rounded-full mix-blend-screen pointer-events-none"
                            style={{ backgroundColor: activeStatusStripeColor, color: activeStatusStripeColor }}
                        />
                    )}
                </div>
            )}

            {/* Drag Handle (Visible on Hover) */}
            {isDraggable && showDragHandle && (
                <div
                    {...attributes}
                    {...listeners}
                    className="absolute top-2 right-2 p-1.5 rounded cursor-grab active:cursor-grabbing text-gray-500 hover:text-white hover:bg-white/10 opacity-0 group-hover:opacity-100 transition-opacity z-20"
                >
                    <GripVertical size={16} />
                </div>
            )}

            {/* Media Slot (Top) - Hidden when collapsed */}
            {media && !isCollapsed && (
                <div className="w-full aspect-video bg-black/50 relative overflow-hidden border-b border-white/5">
                    {media}
                    {/* Media Overlay Action (e.g. Play) */}
                    {entity.cardConfig?.media?.playAction && (
                        <div className="absolute inset-0 flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity bg-black/20 backdrop-blur-[1px]">
                            <button
                                onClick={(e) => {
                                    e.stopPropagation();
                                    entity.cardConfig?.media?.playAction?.();
                                }}
                                className="w-12 h-12 rounded-full bg-accent text-black flex items-center justify-center hover:scale-110 transition-transform shadow-xl"
                            >
                                <div className="ml-1 border-l-8 border-t-6 border-b-6 border-transparent border-l-black" />
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Content Container */}
            <div className={clsx("flex flex-col h-full", variant === 'default' ? "p-4" : (variant === 'dense' || variant === 'moderate' || variant === 'text') ? "" : "gap-2")}>

                {/* Header Slot (Title/Meta) */}
                {!noDefaultStyles && ((variant === 'dense' || variant === 'moderate' || variant === 'text') ? (
                    // DENSE HEADER VARIANT (High Fidelity)
                    <div className="flex items-center gap-3 px-4 py-4 border-b border-white/5 bg-white/[0.02]">
                        {/* Icon Box */}
                        <div className="w-10 h-10 rounded-lg bg-white/5 flex items-center justify-center border border-white/10 shrink-0 text-gray-400 shadow-inner">
                            {/* Use entity.icon if string/element, else generic */}
                            {typeof entity.icon === 'string' && entity.icon === 'Folder' ? <Folder size={20} /> : (entity.icon || <Box size={20} />)}
                        </div>

                        <div className="flex-1 min-w-0">
                            <div className="flex items-center gap-2 mb-1">
                                {/* Status Indicator (Dot) */}
                                {showStatus && entity.status && (
                                    <div className={clsx(
                                        "flex items-center gap-1.5 px-1.5 py-0.5 rounded-full text-[9px] font-bold uppercase tracking-wider",
                                        statusConfig.color.replace('text-', 'text-').replace('500', '400'),
                                        "bg-white/5 border border-white/5"
                                    )}>
                                        <div className={clsx("w-1.5 h-1.5 rounded-full shadow-[0_0_5px_currentColor]", statusConfig.color.replace('text-', 'bg-'))} />
                                        {entity.status.slice(0, 4)}
                                    </div>
                                )}
                                <h3 className="text-sm font-bold text-white uppercase tracking-wide truncate group-hover:text-accent transition-colors">
                                    {entity.title}
                                </h3>
                            </div>
                            <div className="text-[11px] text-gray-500 font-mono truncate pl-1">
                                {entity.subtitle || entity.type}
                            </div>
                        </div>
                    </div>
                ) : (
                    // STANDARD HEADER VARIANT
                    <div className="flex items-start justify-between gap-4 mb-2">
                        <div className="flex-1 min-w-0">
                            {header || (
                                <div>
                                    <div className="flex items-center gap-2">
                                        {/* Status Indicator */}
                                        {showStatus && entity.status && (
                                            <StatusIcon size={14} className={statusConfig.color} />
                                        )}
                                        <h3 className="font-bold text-white truncate text-base leading-tight group-hover:text-accent transition-colors">
                                            {entity.title}
                                        </h3>
                                    </div>
                                    {entity.subtitle && (
                                        <p className="text-xs text-gray-500 font-mono mt-1 truncate">
                                            {entity.subtitle}
                                        </p>
                                    )}
                                </div>
                            )}
                        </div>

                        {/* Type Badge */}
                        <span className="text-[9px] uppercase font-bold text-gray-600 bg-white/5 px-1.5 py-0.5 rounded">
                            {entity.type}
                        </span>
                    </div>
                ))}

                {/* Body Content Wrapper */}
                <div className={clsx("flex-1 min-h-0 flex flex-col relative", noDefaultStyles ? "" : (variant === 'dense' ? "p-3 gap-3" : "gap-1"))}>

                    {/* Next Action - Hero Slot (Top for Dense) */}
                    {!noDefaultStyles && activeNextAction && (
                        <div className={clsx(variant !== 'dense' && "mb-3")}>
                            {variant === 'dense' ? (
                                // High Fidelity Next Action (Glow)
                                <button
                                    onClick={(e) => { e.stopPropagation(); activeNextAction.onClick?.(); }}
                                    className="w-full text-left bg-white/[0.03] border border-white/10 hover:border-accent/40 rounded-lg overflow-hidden group/nextstep transition-all relative"
                                >
                                    <div className="absolute inset-0 bg-gradient-to-br from-accent/5 via-transparent to-transparent opacity-50 group-hover/nextstep:opacity-100 transition-opacity" />
                                    <div className="relative p-3 flex items-start gap-3">
                                        <div className="w-8 h-8 rounded-md bg-white/5 flex items-center justify-center shrink-0 border border-white/5 shadow-inner group-hover/nextstep:scale-105 transition-transform text-accent">
                                            {activeNextAction.icon || <Circle size={14} />}
                                        </div>
                                        <div className="min-w-0 flex-1 py-0.5">
                                            <div className="text-[9px] uppercase font-bold text-gray-500 mb-0.5 tracking-wider">Next Action</div>
                                            <div className="text-xs font-medium text-gray-200 leading-snug line-clamp-2 group-hover/nextstep:text-accent transition-colors">
                                                {activeNextAction.label}
                                            </div>
                                        </div>
                                    </div>
                                </button>
                            ) : (
                                // Standard Next Action
                                <button
                                    onClick={(e) => { e.stopPropagation(); activeNextAction.onClick?.(); }}
                                    className="w-full relative group/nextstep overflow-hidden rounded-md border border-white/5 bg-white/5 hover:border-accent/40 hover:bg-white/10 transition-all duration-300 text-left"
                                >
                                    <div className="absolute inset-0 bg-gradient-to-r from-accent/0 via-accent/5 to-transparent opacity-0 group-hover/nextstep:opacity-100 transition-opacity" />
                                    <div className="relative p-2 flex items-center gap-3">
                                        <div className="p-1.5 rounded-full bg-accent/20 text-accent group-hover/nextstep:scale-110 transition-transform shadow-[0_0_10px_rgba(var(--accent-rgb),0.2)]">
                                            {activeNextAction.icon || <Circle size={14} />}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <div className="text-xs font-bold text-accent truncate group-hover/nextstep:text-white transition-colors">
                                                {activeNextAction.label}
                                            </div>
                                            {activeNextAction.subtitle && (
                                                <div className="text-[10px] text-gray-500 truncate group-hover/nextstep:text-gray-400">
                                                    {activeNextAction.subtitle}
                                                </div>
                                            )}
                                        </div>
                                    </div>
                                </button>
                            )}
                        </div>
                    )}

                    {/* Dense: Custom Children (The Grid) */}
                    {(variant === 'dense' || noDefaultStyles) && children}


                    {/* Tags (Standard Only) */}
                    {!noDefaultStyles && variant !== 'dense' && entity.tags && entity.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1 mb-2">
                            {entity.tags.slice(0, 3).map((tag, i) => (
                                <span key={i} className="text-[9px] bg-accent/10 text-accent px-1.5 py-0.5 rounded-full">
                                    {tag}
                                </span>
                            ))}
                            {entity.tags.length > 3 && (
                                <span className="text-[9px] text-gray-600">+{entity.tags.length - 3}</span>
                            )}
                        </div>
                    )}

                    {/* Progress Bar (Standard Only) */}
                    {!noDefaultStyles && variant !== 'dense' && typeof entity.progress === 'number' && (
                        <div className="mb-2">
                            <div className="h-1 bg-white/10 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-accent transition-all duration-500"
                                    style={{ width: `${entity.progress}%` }}
                                />
                            </div>
                            <span className="text-[10px] text-gray-500 mt-0.5 block">{entity.progress}%</span>
                        </div>
                    )}

                    {/* Metrics Dashboard (Standard Only) */}
                    {!noDefaultStyles && variant !== 'dense' && (activeRatings?.length > 0 || metrics) && (
                        <div className="flex flex-wrap items-center justify-between gap-3 mb-3 bg-black/20 p-2 rounded border border-white/5">
                            {/* Ratings Bars */}
                            {activeRatings && activeRatings.length > 0 && (
                                <div className="space-y-1.5 flex-1 min-w-[140px]">
                                    {activeRatings.map((rate, i) => (
                                        <div key={i} className="flex items-center gap-2 text-[10px] group/rating">
                                            <span className="text-gray-500 w-12 truncate text-right group-hover/rating:text-gray-300 transition-colors uppercase font-bold">{rate.label}</span>
                                            <div className="flex-1 flex gap-0.5 h-1.5 cursor-pointer" title={`${rate.label}: ${rate.value}/${rate.max}`}>
                                                {Array.from({ length: rate.max }).map((_, idx) => {
                                                    const val = idx + 1;
                                                    const isActive = rate.value >= val;
                                                    return (
                                                        <div
                                                            key={idx}
                                                            onClick={(e) => {
                                                                e.stopPropagation();
                                                                rate.onChange?.(val);
                                                            }}
                                                            className={clsx(
                                                                "flex-1 rounded-[1px] transition-all duration-200 border border-transparent",
                                                                rate.onChange && "hover:border-white/50 hover:scale-110",
                                                                isActive ? "" : "bg-white/5",
                                                            )}
                                                            style={{
                                                                backgroundColor: isActive ? rate.color : undefined
                                                            }}
                                                        />
                                                    );
                                                })}
                                            </div>
                                            <span className="text-gray-500 w-3 font-mono text-center">{rate.value}</span>
                                        </div>
                                    ))}
                                </div>
                            )}

                            {/* Custom Metrics Slot */}
                            {metrics && (
                                <div className={clsx("flex flex-col items-end gap-0.5", activeRatings?.length > 0 && "pl-3 border-l border-white/10")}>
                                    {metrics}
                                </div>
                            )}
                        </div>
                    )}

                    {/* Meta Grid (Standard Only) */}
                    {!noDefaultStyles && variant !== 'dense' && activeMetaGrid && activeMetaGrid.length > 0 && (
                        <div className={clsx(
                            "grid gap-2 mb-3 text-xs bg-white/5 p-2 rounded border border-white/5",
                            activeMetaGrid.length > 2 ? "grid-cols-3" : activeMetaGrid.length > 1 ? "grid-cols-2" : "grid-cols-1"
                        )}>
                            {activeMetaGrid.map((meta, i) => {
                                const val = meta.value;
                                const isComplex = typeof val === 'object' && val !== null && 'text' in val;
                                const displayVal = isComplex ? (val as { text: string }).text : val;
                                const color = isComplex ? (val as { color?: string }).color : undefined;

                                return (
                                    <div key={i} className={clsx("overflow-hidden flex flex-col", i > 0 && "border-l border-white/5 pl-2")}>
                                        <span className="block text-[9px] uppercase text-gray-500 font-bold mb-0.5">{meta.label}</span>
                                        <div className="flex items-center gap-1.5 text-gray-300 truncate font-mono">
                                            {meta.icon && <span className="text-accent">{meta.icon}</span>}
                                            <span style={{ color }} className="truncate">{displayVal}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Badges (Standard Only) */}
                    {!noDefaultStyles && variant !== 'dense' && (badges.length > 0 || (entity.cardConfig?.badges && entity.cardConfig.badges.length > 0)) && (
                        <div className="flex flex-wrap gap-1 mb-3">
                            {/* Prop Badges */}
                            {badges.map((b, i) => (
                                <div key={`prop-badge-${i}`}>
                                    {React.isValidElement(b) ? b : (
                                        <div
                                            onClick={(e) => {
                                                if ((b as any).onClick) {
                                                    e.stopPropagation();
                                                    (b as any).onClick();
                                                }
                                            }}
                                            className={clsx(
                                                "text-[9px] px-1.5 py-0.5 rounded border flex items-center gap-1",
                                                (b as any).onClick ? "cursor-pointer hover:bg-white/10" : "cursor-default"
                                            )}
                                            style={{
                                                borderColor: (b as any).color ? `${(b as any).color}40` : 'rgba(255,255,255,0.1)',
                                                backgroundColor: (b as any).color ? `${(b as any).color}10` : 'rgba(255,255,255,0.05)',
                                                color: (b as any).color || '#9ca3af'
                                            }}
                                            title={(b as any).tooltip}
                                        >
                                            {(b as any).icon && <span>{(b as any).icon}</span>}
                                            {(b as any).label}
                                        </div>
                                    )}
                                </div>
                            ))}

                            {/* Config Badges */}
                            {entity.cardConfig?.badges?.map((badge, i) => {
                                const isClickable = !!badge.onClick;
                                return (
                                    <div
                                        key={`config-badge-${i}`}
                                        onClick={(e) => {
                                            if (isClickable) {
                                                e.stopPropagation();
                                                badge.onClick?.();
                                            }
                                        }}
                                        role={isClickable ? "button" : undefined}
                                        className={clsx(
                                            "text-[9px] px-1.5 py-0.5 rounded border flex items-center gap-1",
                                            isClickable ? "cursor-pointer hover:bg-white/10" : "cursor-default"
                                        )}
                                        style={{
                                            borderColor: badge.color ? `${badge.color}40` : 'rgba(255,255,255,0.1)',
                                            backgroundColor: badge.color ? `${badge.color}10` : 'rgba(255,255,255,0.05)',
                                            color: badge.color || '#9ca3af'
                                        }}
                                    >
                                        {badge.label}
                                    </div>
                                );
                            })}
                        </div>
                    )}

                    {/* Children Slot (Standard Only) */}
                    {!noDefaultStyles && variant !== 'dense' && children && (
                        <div className="flex-1 text-sm text-gray-400">
                            {children}
                        </div>
                    )}

                    {/* Footer Slot */}
                    {footer && (
                        <div className="mt-auto pt-3 border-t border-white/10 text-xs text-gray-500 font-mono flex items-center justify-between">
                            {footer}
                        </div>
                    )}

                </div>
            </div>

            {/* Action Buttons (hover) */}
            {showActions && (
                <div className="absolute bottom-2 right-2 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    {/* Edit Button */}
                    {onEdit && (
                        <button
                            onClick={(e) => { e.stopPropagation(); handleSetIsEditing(true); }}
                            className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                            title="Edit"
                        >
                            <Settings size={12} />
                        </button>
                    )}

                    {/* Custom Actions */}
                    {actions.filter(a => !a.hidden).map(action => (
                        <button
                            key={action.id}
                            onClick={(e) => { e.stopPropagation(); action.action(); }}
                            className={clsx(
                                "p-1.5 rounded transition-colors",
                                action.variant === 'danger'
                                    ? "bg-red-500/10 text-red-400 hover:text-red-300 hover:bg-red-500/20"
                                    : "bg-white/10 text-gray-400 hover:text-white hover:bg-white/20"
                            )}
                            title={action.tooltip || action.label}
                            disabled={action.disabled}
                        >
                            {action.icon ? <action.icon size={12} /> : action.label}
                        </button>
                    ))}

                    {/* External Links */}
                    {activeExternalLinks.map((link, i) => (
                        <a
                            key={`ext-${i}`}
                            href={link.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                            title={link.label}
                        >
                            {link.icon || <ExternalLink size={12} />}
                        </a>
                    ))}

                    {/* Default External Link (Legacy) */}
                    {entity.metadata?.url && !activeExternalLinks.some(l => l.url === entity.metadata?.url) && (
                        <a
                            href={entity.metadata.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            onClick={(e) => e.stopPropagation()}
                            className="p-1.5 rounded bg-white/10 text-gray-400 hover:text-white hover:bg-white/20 transition-colors"
                            title="Open Link"
                        >
                            <ExternalLink size={12} />
                        </a>
                    )}
                </div>
            )}
        </div>
    );
}
