/**
 * useRegistryCard - Connect Registry to UniversalCard
 * 
 * @module lib/registry/useRegistryCard
 * @description
 * A composable hook that generates UniversalCard props from registry definitions.
 * This provides a clean bridge between the registry architecture and the UI layer.
 * 
 * ## Usage
 * ```tsx
 * const cardProps = useRegistryCard(entity);
 * return <UniversalCard {...cardProps} />;
 * ```
 * 
 * ## What This Hook Provides:
 * - Status configuration from STATE_MACHINES
 * - Action handlers from ACTION_REGISTRY
 * - Icon and color from ENTITY_REGISTRY
 * - Computed fields evaluation
 * 
 * @see UniversalCard for the card component
 * @see ENTITY_REGISTRY for entity definitions
 */

import { useMemo, useCallback } from 'react';
import type { UniversalEntity, UniversalAction } from '../universal/types';
import {
    getEntityDefinition,
    getEntityActions,
    getStateMeta,
    executeAction,
    getValidEvents,
    ACTION_REGISTRY,
    eventBus,
} from './index';

// ============================================================================
// Type Definitions
// ============================================================================

export interface RegistryCardProps {
    /** Status stripe color derived from state machine */
    statusStripeColor?: string;
    /** Status glow effect */
    statusGlow?: boolean;
    /** Status label for display */
    statusLabel?: string;
    /** Status icon name (Lucide) */
    statusIcon?: string;

    /** Collapsible configuration */
    collapsible?: boolean;
    defaultCollapsed?: boolean;

    /** Computed data */
    tags: string[];
    metaGrid: Array<{ label: string; value: string; icon?: string }>;
    computedValues: {
        progress: number;
        impact: number;
        priority: string;
    };

    /** Actions derived from entity definition */
    actions: UniversalAction[];
    /** Valid state transitions as actions */
    transitionActions: Array<{
        event: string;
        label: string;
        onClick: () => void;
    }>;
    /** Quick actions for hover display */
    quickActions: Array<{
        id: string;
        icon: React.ReactNode;
        label: string;
        onClick: () => void;
        variant?: 'default' | 'success' | 'danger' | 'warning';
    }>;
    /** Handler for registry actions */
    onAction: (actionId: string) => void;
    /** Edit handler that emits to event bus */
    onEdit: () => void;
    /** Delete handler that emits to event bus */
    onDelete: () => void;
}

// ============================================================================
// Hook Implementation
// ============================================================================

/**
 * Generates UniversalCard-compatible props from registry definitions.
 * 
 * @param entity - The UniversalEntity to generate props for
 * @param options - Optional configuration
 * @returns Props that can be spread onto UniversalCard
 */
export function useRegistryCard(
    entity: UniversalEntity,
    options: {
        /** Override which actions to include */
        actionIds?: string[];
        /** Callback after any action completes */
        onActionComplete?: (actionId: string) => void;
        /** Enable transition actions */
        showTransitions?: boolean;
    } = {}
): RegistryCardProps {
    const { actionIds, onActionComplete, showTransitions = false } = options;

    // Get entity definition from registry
    const entityDef = useMemo(() => {
        return getEntityDefinition(entity.type);
    }, [entity.type]);

    // Get table/card config
    const tableConfig = useMemo(() => {
        return {
            collapsible: entityDef?.collapsible,
            defaultCollapsed: entityDef?.defaultCollapsed?.(entity),
            statusStripe: entityDef?.statusStripe?.(entity),
            statusGlow: entityDef?.statusGlow?.(entity),
        };
    }, [entity, entityDef]);

    // Get Computed Fields
    const computedValues = useMemo(() => {
        // In a real implementation, we'd use a computed field registry
        // For now, we'll derive common ones
        return {
            progress: (entity.data?.progress as number) ?? 0,
            impact: (entity.data?.impact as number) ?? 0,
            priority: (entity.data?.priority as string) ?? 'medium',
        };
    }, [entity]);

    // Get Tags
    const tags = useMemo(() => {
        if (entityDef?.tags && Array.isArray((entity.data as any)[entityDef.tags])) {
            return (entity.data as any)[entityDef.tags] as string[];
        }
        return entity.data?.tags as string[] ?? [];
    }, [entity, entityDef]);

    // Get Meta Grid
    const metaGrid = useMemo(() => {
        if (!entityDef?.metaGrid) return [];
        return entityDef.metaGrid.map(item => ({
            label: item.label,
            value: String((entity.data as any)[item.field] ?? ''), // Basic string conversion
            icon: item.icon,
        }));
    }, [entity, entityDef]);

    // Get state metadata
    const stateMeta = useMemo(() => {
        if (!entity.status) return undefined;

        // Map entity type to state machine ID
        const machineMap: Record<string, string> = {
            project: 'projectStatus',
            task: 'taskStatus',
            goal: 'goalStatus',
            purchase: 'purchaseStatus',
            routine: 'routineStatus',
            song: 'songStatus',
            recording: 'songStatus',
            inbox: 'inboxStatus',
        };

        const machineId = machineMap[entity.type];
        if (!machineId) return undefined;

        return getStateMeta(machineId, entity.status);
    }, [entity.type, entity.status]);

    // Generate action handlers
    const handleAction = useCallback((actionId: string) => {
        const result = executeAction(actionId, entity);

        // Handle async actions
        if (result && typeof result === 'object' && 'then' in result) {
            result.then(() => {
                onActionComplete?.(actionId);
            });
        } else {
            onActionComplete?.(actionId);
        }
    }, [entity, onActionComplete]);

    // Get actions from registry
    const actions = useMemo((): UniversalAction[] => {
        const ids = actionIds ?? entityDef?.actions ?? ['edit', 'delete'];
        const registryActions = getEntityActions(entity.type, ids);

        return registryActions
            .filter(action => {
                // Check visibility predicate
                if (action.visible && !action.visible(entity)) {
                    return false;
                }
                return true;
            })
            .map(action => ({
                id: action.id,
                label: action.label,
                icon: undefined, // Icons are strings in registry, need conversion
                action: () => handleAction(action.id),
                variant: action.destructive ? 'danger' as const : undefined,
                disabled: action.enabled ? !action.enabled(entity) : false,
                hidden: false,
            }));
    }, [entity, entityDef, actionIds, handleAction]);

    // Get valid transitions as actions
    const transitionActions = useMemo(() => {
        if (!showTransitions || !entity.status) return [];

        const machineMap: Record<string, string> = {
            project: 'projectStatus',
            task: 'taskStatus',
            goal: 'goalStatus',
            purchase: 'purchaseStatus',
            routine: 'routineStatus',
            song: 'songStatus',
            recording: 'songStatus',
            inbox: 'inboxStatus',
        };

        const machineId = machineMap[entity.type];
        if (!machineId) return [];

        const validEvents = getValidEvents(machineId, entity.status);

        return validEvents.map(event => ({
            event,
            label: event.replace(/_/g, ' ').toLowerCase(),
            onClick: () => {
                // Execute transition via Command Layer
                executeTransition(entity.type, entity, machineId, event);
            },
        }));
    }, [entity, showTransitions]);

    // Build quick actions (commonly used actions)
    const quickActions = useMemo(() => {
        const quickIds = ['complete', 'edit', 'archive'];
        const result: RegistryCardProps['quickActions'] = [];

        for (const id of quickIds) {
            const action = ACTION_REGISTRY[id];
            if (!action) continue;
            if (action.visible && !action.visible(entity)) continue;

            result.push({
                id: action.id,
                icon: null as any, // Would need icon component mapping
                label: action.label,
                onClick: () => handleAction(action.id),
                variant: action.destructive ? 'danger' : 'default',
            });
        }

        return result;
    }, [entity, handleAction]);

    // Edit handler
    const onEdit = useCallback(() => {
        handleAction('edit');
    }, [handleAction]);

    // Delete handler
    const onDelete = useCallback(() => {
        handleAction('delete');
    }, [handleAction]);

    return {
        // Style & Config
        statusStripeColor: tableConfig.statusStripe || stateMeta?.color,
        statusGlow: tableConfig.statusGlow || !!stateMeta?.color,
        statusLabel: stateMeta?.label,
        statusIcon: stateMeta?.icon,
        collapsible: tableConfig.collapsible,
        defaultCollapsed: tableConfig.defaultCollapsed,

        // Data
        tags,
        metaGrid,
        computedValues,

        // Actions
        actions,
        transitionActions,
        quickActions,
        onAction: handleAction,
        onEdit,
        onDelete,
    };
}

// ============================================================================
// Status Configuration Helpers
// ============================================================================

/**
 * Get status display configuration for any entity.
 * Falls back to generic colors if no state machine exists.
 */
export function getStatusDisplay(entity: UniversalEntity): {
    color: string;
    label: string;
    icon: string;
} {
    const machineMap: Record<string, string> = {
        project: 'projectStatus',
        task: 'taskStatus',
        goal: 'goalStatus',
        purchase: 'purchaseStatus',
        routine: 'routineStatus',
        song: 'songStatus',
        recording: 'songStatus',
        inbox: 'inboxStatus',
    };

    const machineId = machineMap[entity.type];

    if (machineId && entity.status) {
        const meta = getStateMeta(machineId, entity.status);
        if (meta) {
            return {
                color: meta.color,
                label: meta.label,
                icon: meta.icon || 'Circle',
            };
        }
    }

    // Fallback generic status colors
    const fallbackColors: Record<string, string> = {
        active: '#10b981',
        completed: '#10b981',
        done: '#10b981',
        in_progress: '#3b82f6',
        pending: '#f59e0b',
        blocked: '#ef4444',
        archived: '#6b7280',
    };

    return {
        color: fallbackColors[entity.status || ''] || '#6b7280',
        label: entity.status || '',
        icon: 'Circle',
    };
}

// ============================================================================
// Export for index
// ============================================================================

export default useRegistryCard;
