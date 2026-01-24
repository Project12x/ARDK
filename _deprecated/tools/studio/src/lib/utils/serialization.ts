/**
 * Serialization Utilities
 * 
 * @module lib/utils/serialization
 * @description
 * Tools for ensuring deterministic data output, essential for
 * Vault hashing, syncing, and version control integrity.
 */

import superjson from 'superjson';

/**
 * Deterministically stringify an object (stable key order).
 * Used for generating content hashes or Vault signatures.
 * 
 * @param obj - The object to stringify
 * @returns Sorted JSON string
 */
export function deterministicStringify(obj: any): string {
    // 1. Handle primitives
    if (obj === null || typeof obj !== 'object') {
        return JSON.stringify(obj);
    }

    // 2. Handle Arrays
    if (Array.isArray(obj)) {
        return '[' + obj.map(deterministicStringify).join(',') + ']';
    }

    // 3. Handle Dates (ISO string)
    if (obj instanceof Date) {
        return JSON.stringify(obj.toISOString());
    }

    // 4. Handle Objects (Sort keys)
    const keys = Object.keys(obj).sort();
    const parts = keys.map(
        (key) => JSON.stringify(key) + ':' + deterministicStringify(obj[key])
    );
    return '{' + parts.join(',') + '}';
}

/**
 * Serialize entity for transfer/storage using SuperJSON
 * (Preserves Dates, Maps, Sets, etc.)
 */
export function serializeEntity<T>(entity: T): string {
    return superjson.stringify(entity);
}

/**
 * Deserialize entity from storage
 */
export function deserializeEntity<T>(json: string): T {
    return superjson.parse(json);
}
