/**
 * Registry Module - Central exports
 * 
 * This module provides the single source of truth for:
 * - Entity definitions
 * - Action handlers
 * - State machines
 * - Computed fields
 * - Event bus
 * - Validation
 */

// Event Bus
export {
    eventBus,
    emitEntityCreated,
    emitEntityUpdated,
    emitEntityDeleted,
    showToast,
    openEditModal,
    closeModal,
    type EventMap,
    type EntityEventPayload,
    type ModalEventPayload,
    type SearchEventPayload,
    type SyncEventPayload,
    type ActionEventPayload,
} from './eventBus';

// Entity Registry
export {
    ENTITY_REGISTRY,
    STATUS_COLORS,
    getEntityDefinition,
    getEntityIcon,
    getEntityColor,
    getStatusColor,
    getAllEntityTypes,
    type EntityDefinition,
    type RatingConfig,
    type MetaGridItem,
} from './entityRegistry';

// Adapter Factory
export {
    createUniversalEntity,
    createAdapter,
} from './createAdapter';

// Action Registry
export {
    ACTION_REGISTRY,
    getAction,
    getEntityActions,
    executeAction,
    type ActionDefinition,
} from './actionRegistry';

// State Machines
export {
    STATE_MACHINES,
    getStateMachine,
    getStateMeta,
    canTransition,
    getValidEvents,
    getNextState,
    type StateMachine,
    type StateDefinition,
    type StateMetadata,
} from './stateMachines';

// Computed Fields
export {
    COMPUTED_FIELDS,
    computeField,
    computeAllFields,
    type ComputedFieldDefinition,
} from './computedFields';

export {
    validateEntity,
    sanitizeEntity,
    validateAndSanitize,
    withValidation,
    ValidationError,
    type ValidationResult,
} from './validation';

// Registry Card Hook (Phase 11D)
export {
    useRegistryCard,
    getStatusDisplay,
    type RegistryCardProps,
} from './useRegistryCard';

// ============================================================================
// Future: Plugin System (Phase 23)
// ============================================================================

// export function registerPlugin(plugin: PluginDefinition) {
//   // Register entity types
//   // Register actions
//   // Register state machines
//   // Register computed fields
// }
