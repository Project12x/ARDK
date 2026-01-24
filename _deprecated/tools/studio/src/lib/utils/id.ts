/**
 * ID Utilities
 * 
 * @module lib/utils/id
 * @description
 * Standard interface for generating unique identifiers.
 * Uses `nanoid` for collision-resistant, URL-safe strings.
 */

import { nanoid } from 'nanoid';

/**
 * Generate a unique ID for an entity
 * @returns {string} URL-safe unique ID (21 chars)
 */
export const createId = (): string => nanoid();
