/**
 * Validation - Zod Schema Integration & Sanitization
 * 
 * @module lib/registry/validation
 * @description
 * Validates entity data against Zod schemas defined in ENTITY_REGISTRY.
 * Also provides sanitization ("self-healing") for common data issues.
 * 
 * ## Why Use This?
 * - **Type Safety**: Validate data before saving
 * - **Self-Healing**: Auto-fix common issues (trim strings, ensure arrays)
 * - **Error Handling**: Typed ValidationError with Zod details
 * - **Composable**: `withValidation()` wraps any operation
 * 
 * ## Usage Examples
 * ```typescript
 * // Validate data
 * const result = validateEntity('project', formData);
 * if (!result.success) console.log(result.error);
 * 
 * // Sanitize + validate
 * const clean = validateAndSanitize('project', formData);
 * 
 * // Wrap an operation
 * const saveProject = withValidation('project', async (data) => {
 *   await db.projects.add(data);
 * });
 * ```
 * 
 * @see ENTITY_REGISTRY.schema for entity schemas
 */

import { z } from 'zod';
import { ENTITY_REGISTRY, getEntityDefinition } from './entityRegistry';

// ============================================================================
// Type Definitions
// ============================================================================

export interface ValidationResult {
    success: boolean;
    data?: Record<string, unknown>;
    error?: z.ZodError;
}

// ============================================================================
// Validation Functions
// ============================================================================

/**
 * Validate entity data against its schema
 */
export function validateEntity(type: string, data: Record<string, unknown>): ValidationResult {
    const def = getEntityDefinition(type);

    if (!def?.schema) {
        // No schema defined, pass through
        return { success: true, data };
    }

    const result = def.schema.safeParse(data);

    if (result.success) {
        return { success: true, data: result.data as Record<string, unknown> };
    }

    return { success: false, error: result.error };
}

/**
 * Sanitize entity data to fix common issues
 */
export function sanitizeEntity(type: string, data: Record<string, unknown>): Record<string, unknown> {
    const sanitized = { ...data };

    // Trim string fields
    for (const [key, value] of Object.entries(sanitized)) {
        if (typeof value === 'string') {
            sanitized[key] = value.trim();
        }
    }

    // Ensure arrays are arrays
    const def = getEntityDefinition(type);
    if (def?.tags && !Array.isArray(sanitized[def.tags])) {
        sanitized[def.tags] = [];
    }

    // Convert date strings to Date objects if needed
    const dateFields = ['created_at', 'updated_at', 'due_date', 'target_completion_date', 'deadline'];
    for (const field of dateFields) {
        if (sanitized[field] && typeof sanitized[field] === 'string') {
            const date = new Date(sanitized[field] as string);
            if (!isNaN(date.getTime())) {
                sanitized[field] = date;
            }
        }
    }

    return sanitized;
}

/**
 * Validate and sanitize entity data
 */
export function validateAndSanitize(type: string, data: Record<string, unknown>): ValidationResult {
    const sanitized = sanitizeEntity(type, data);
    return validateEntity(type, sanitized);
}

// ============================================================================
// Higher-Order Function
// ============================================================================

/**
 * Wrap an operation with validation
 */
export function withValidation<T extends Record<string, unknown>>(
    type: string,
    operation: (data: T) => Promise<unknown>
) {
    return async (data: T): Promise<unknown> => {
        const result = validateEntity(type, data);

        if (!result.success) {
            throw new ValidationError(type, result.error!);
        }

        return operation(result.data as T);
    };
}

// ============================================================================
// Custom Error
// ============================================================================

export class ValidationError extends Error {
    public entityType: string;
    public zodError: z.ZodError;

    constructor(entityType: string, zodError: z.ZodError) {
        super(`Validation failed for ${entityType}: ${zodError.message}`);
        this.name = 'ValidationError';
        this.entityType = entityType;
        this.zodError = zodError;
    }
}
