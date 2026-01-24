/**
 * XState Machines Index
 * 
 * @module lib/machines
 * @description
 * Central export for all XState machine definitions.
 * Also provides `useMachineWithEventBus` hook for integration with app event system.
 */

// Machine Exports
export { projectStatusMachine, type ProjectContext, type ProjectEvent } from './projectMachine';
export { taskStatusMachine, type TaskContext, type TaskEvent } from './taskMachine';
export { goalStatusMachine, type GoalContext, type GoalEvent } from './goalMachine';
export { purchaseStatusMachine, type PurchaseContext, type PurchaseEvent } from './purchaseMachine';
export { syncStatusMachine, type SyncContext, type SyncEvent } from './syncMachine';

// Wrapper Hook
export { useMachineWithEventBus } from './useMachineWrapper';

// Inspector (dev mode only)
export { setupXStateInspector } from './inspector';
