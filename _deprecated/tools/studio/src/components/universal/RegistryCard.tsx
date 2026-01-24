/**
 * RegistryCard - Registry-Powered UniversalCard Wrapper
 * 
 * @module components/universal/RegistryCard
 * @description
 * A thin wrapper around UniversalCard that automatically connects to the
 * registry infrastructure. Use this for consistent entity rendering.
 * 
 * ## Usage
 * ```tsx
 * // Simple usage - just pass entity
 * <RegistryCard entity={projectEntity} />
 * 
 * // With callbacks
 * <RegistryCard 
 *   entity={taskEntity}
 *   onActionComplete={(actionId) => console.log('Completed:', actionId)}
 * />
 * ```
 * 
 * ## Features
 * - Automatic status colors from STATE_MACHINES
 * - Action handlers from ACTION_REGISTRY  
 * - Entity icon and color from ENTITY_REGISTRY
 * - Computed fields integration
 * 
 * @see UniversalCard for base component
 * @see useRegistryCard for the underlying hook
 */

import React from 'react';
import { UniversalCard } from './UniversalCard';
import type { UniversalEntity } from '../../lib/universal/types';
import { useRegistryCard } from '../../lib/registry';
import * as LucideIcons from 'lucide-react';

// ============================================================================
// Props
// ============================================================================

interface RegistryCardProps {
    /** The entity to render */
    entity: UniversalEntity;
    /** Called after any action completes */
    onActionComplete?: (actionId: string) => void;
    /** Show state transition actions */
    showTransitions?: boolean;
    /** Override which action IDs to include */
    actionIds?: string[];
    /** Click handler for card */
    onClick?: () => void;
    /** Additional className */
    className?: string;
    /** Card variant */
    variant?: 'default' | 'compact' | 'minimal' | 'media' | 'list';
    /** Layout mode */
    layoutMode?: 'grid' | 'list' | 'kanban';
    /** Enable drag and drop */
    isDraggable?: boolean;
    /** Show action buttons on hover */
    showActions?: boolean;
    /** Show status indicator */
    showStatus?: boolean;
    /** Enable collapsible behavior */
    collapsible?: boolean;
    /** Custom children for body slot */
    children?: React.ReactNode;
}

// ============================================================================
// Icon Mapping Helper
// ============================================================================

/**
 * Get a Lucide icon component by name
 */
function getIconComponent(iconName: string): React.ReactNode {

    const Icon = (LucideIcons as any)[iconName];
    if (Icon) {
        return <Icon size={12} />;
    }
    return <LucideIcons.Circle size={12} />;
}

// ============================================================================
// Component
// ============================================================================

export function RegistryCard({
    entity,
    onActionComplete,
    showTransitions = false,
    actionIds,
    onClick,
    className,
    variant = 'default',
    layoutMode = 'grid',
    isDraggable = true,
    showActions = true,
    showStatus = true,
    collapsible,
    children,
}: RegistryCardProps) {
    // Use the registry hook to get card props
    const registryProps = useRegistryCard(entity, {
        actionIds,
        onActionComplete,
        showTransitions,
    });

    // Convert quick actions with proper icons
    const quickActionsWithIcons = registryProps.quickActions.map(action => ({
        ...action,
        icon: getIconComponent(action.label === 'Complete' ? 'CheckCircle' :
            action.label === 'Edit' ? 'Pencil' :
                action.label === 'Archive' ? 'Archive' : 'Circle'),
    }));

    return (
        <UniversalCard
            entity={entity}
            onClick={onClick}
            className={className}
            variant={variant}
            layoutMode={layoutMode}
            isDraggable={isDraggable}
            showActions={showActions}
            showStatus={showStatus}

            // Configuration derived from registry
            collapsible={collapsible ?? registryProps.collapsible ?? false}
            defaultCollapsed={registryProps.defaultCollapsed}
            statusStripeColor={registryProps.statusStripeColor}
            statusGlow={registryProps.statusGlow}

            // Data derived from registry
            metaGrid={registryProps.metaGrid}
            progress={registryProps.computedValues.progress}

            // Actions
            actions={registryProps.actions}
            quickActions={quickActionsWithIcons}
            onEdit={async () => {
                registryProps.onEdit();
            }}
            onDelete={async () => {
                registryProps.onDelete();
            }}

            // Custom footer with tags and LED bar
            footerSlot={
                <div className="flex flex-col gap-2 pt-2">
                    {/* Tags Row */}
                    {registryProps.tags.length > 0 && (
                        <div className="flex flex-wrap gap-1">
                            {registryProps.tags.slice(0, 4).map((tag, i) => (
                                <span key={i} className="text-[10px] px-2 py-0.5 rounded-full bg-white/5 text-gray-400 border border-white/5">
                                    #{tag}
                                </span>
                            ))}
                        </div>
                    )}

                    {/* Impact Bar (if existing) */}
                    {registryProps.computedValues.impact > 0 && (
                        <div className="flex items-center gap-2 text-[10px] text-gray-500">
                            <span>Impact</span>
                            <div className="flex-1 h-1.5 bg-white/5 rounded-full overflow-hidden">
                                <div
                                    className="h-full bg-gradient-to-r from-blue-500 to-purple-500"
                                    style={{ width: `${registryProps.computedValues.impact}%` }}
                                />
                            </div>
                        </div>
                    )}
                </div>
            }
        >
            {children}
        </UniversalCard>
    );
}

// ============================================================================
// Export
// ============================================================================

export default RegistryCard;
