/**
 * XState Inspector Configuration
 * 
 * @module lib/machines/inspector
 * @description
 * Configures @xstate/inspect for development-time state machine debugging.
 * Opens a separate window/panel showing all active state machines.
 * 
 * Only active in development mode.
 */

// ============================================================================
// Inspector Setup
// ============================================================================

let inspectorInitialized = false;

/**
 * Initialize XState Inspector for development.
 * Should be called once at app startup (e.g., in main.tsx).
 * 
 * @example
 * ```typescript
 * // In main.tsx
 * import { setupXStateInspector } from './lib/machines';
 * 
 * if (import.meta.env.DEV) {
 *   setupXStateInspector();
 * }
 * ```
 */
export async function setupXStateInspector(): Promise<void> {
    // Only run in development
    if (!import.meta.env.DEV) {
        return;
    }

    // Prevent double initialization
    if (inspectorInitialized) {
        console.debug('[XState Inspector] Already initialized');
        return;
    }

    try {
        // Dynamic import to avoid bundling in production
        const { createBrowserInspector } = await import('@xstate/inspect');

        createBrowserInspector({
            // Opens in a new window
            // Set to false to use embedded iframe instead
        });

        inspectorInitialized = true;
        console.log('[XState Inspector] ✅ Initialized - Open DevTools to view machines');
    } catch (error) {
        console.warn('[XState Inspector] Failed to initialize:', error);
        console.info('[XState Inspector] Install @xstate/inspect if not present:');
        console.info('  npm install @xstate/inspect');
    }
}

/**
 * Check if inspector is currently active
 */
export function isInspectorActive(): boolean {
    return inspectorInitialized;
}
