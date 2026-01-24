/**
 * Feature Flags for Parity Migration
 * 
 * @module lib/featureFlags
 * @description
 * Runtime feature flags for safely rolling out new implementations.
 * Flags can be toggled via localStorage for testing.
 * 
 * @example
 * ```typescript
 * import { isFeatureEnabled, FEATURE_FLAGS } from './featureFlags';
 * 
 * if (isFeatureEnabled(FEATURE_FLAGS.USE_NEW_AI_SERVICE)) {
 *   // Use new AI SDK
 * } else {
 *   // Use legacy AIService
 * }
 * ```
 */

// ============================================================================
// Flag Definitions
// ============================================================================

export const FEATURE_FLAGS = {
    /** Use new Vercel AI SDK instead of legacy AIService */
    USE_NEW_AI_SERVICE: 'ff_use_new_ai_service',
    /** Use new Universal Card system */
    USE_UNIVERSAL_CARDS: 'ff_use_universal_cards',
    /** Enable offline/PWA mode */
    ENABLE_OFFLINE_MODE: 'ff_enable_offline_mode',
    /** Show debug panels and extra logging */
    DEBUG_MODE: 'ff_debug_mode',
} as const;

export type FeatureFlag = typeof FEATURE_FLAGS[keyof typeof FEATURE_FLAGS];

// ============================================================================
// Default Values
// ============================================================================

const FLAG_DEFAULTS: Record<FeatureFlag, boolean> = {
    [FEATURE_FLAGS.USE_NEW_AI_SERVICE]: false,
    [FEATURE_FLAGS.USE_UNIVERSAL_CARDS]: false,
    [FEATURE_FLAGS.ENABLE_OFFLINE_MODE]: false,
    [FEATURE_FLAGS.DEBUG_MODE]: import.meta.env.DEV,
};

// ============================================================================
// API
// ============================================================================

/**
 * Check if a feature flag is enabled
 */
export function isFeatureEnabled(flag: FeatureFlag): boolean {
    // Check localStorage override first
    const override = localStorage.getItem(flag);
    if (override !== null) {
        return override === 'true';
    }

    // Fall back to default
    return FLAG_DEFAULTS[flag] ?? false;
}

/**
 * Enable a feature flag (persisted to localStorage)
 */
export function enableFeature(flag: FeatureFlag): void {
    localStorage.setItem(flag, 'true');
    console.log(`[FeatureFlag] Enabled: ${flag}`);
}

/**
 * Disable a feature flag (persisted to localStorage)
 */
export function disableFeature(flag: FeatureFlag): void {
    localStorage.setItem(flag, 'false');
    console.log(`[FeatureFlag] Disabled: ${flag}`);
}

/**
 * Reset a feature flag to its default value
 */
export function resetFeature(flag: FeatureFlag): void {
    localStorage.removeItem(flag);
    console.log(`[FeatureFlag] Reset to default: ${flag}`);
}

/**
 * Get all feature flag states
 */
export function getAllFeatureFlags(): Record<FeatureFlag, boolean> {
    return Object.values(FEATURE_FLAGS).reduce((acc, flag) => {
        acc[flag] = isFeatureEnabled(flag);
        return acc;
    }, {} as Record<FeatureFlag, boolean>);
}

/**
 * Toggle a feature flag
 */
export function toggleFeature(flag: FeatureFlag): boolean {
    const current = isFeatureEnabled(flag);
    if (current) {
        disableFeature(flag);
    } else {
        enableFeature(flag);
    }
    return !current;
}
