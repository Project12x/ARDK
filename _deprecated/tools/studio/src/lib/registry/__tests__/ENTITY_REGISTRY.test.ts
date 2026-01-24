/**
 * ENTITY_REGISTRY Unit Tests
 * 
 * Validates the structure and completeness of the entity registry.
 * These tests ensure all entity types are properly configured.
 */
import { describe, it, expect } from 'vitest';
import {
    ENTITY_REGISTRY,
    getEntityDefinition,
    getEntityIcon,
    getEntityColor,
    getAllEntityTypes,
    STATUS_COLORS,
    type EntityDefinition,
} from '../entityRegistry';

describe('ENTITY_REGISTRY', () => {
    describe('Structure Validation', () => {
        it('exports a non-empty registry object', () => {
            expect(ENTITY_REGISTRY).toBeDefined();
            expect(typeof ENTITY_REGISTRY).toBe('object');
            expect(Object.keys(ENTITY_REGISTRY).length).toBeGreaterThan(0);
        });

        it('contains all expected core entity types', () => {
            const coreTypes = ['project', 'task', 'goal', 'routine', 'inventory', 'song', 'purchase'];
            coreTypes.forEach(type => {
                expect(ENTITY_REGISTRY[type]).toBeDefined();
            });
        });

        it('has at least 20 entity types registered', () => {
            const typeCount = Object.keys(ENTITY_REGISTRY).length;
            expect(typeCount).toBeGreaterThanOrEqual(20);
        });
    });

    describe('Entity Definition Validation', () => {
        const allTypes = Object.entries(ENTITY_REGISTRY);

        it.each(allTypes)('%s has required fields', (type, definition: EntityDefinition) => {
            // Required fields
            expect(definition.table).toBeDefined();
            expect(typeof definition.table).toBe('string');
            expect(definition.table.length).toBeGreaterThan(0);

            expect(definition.primaryField).toBeDefined();
            expect(typeof definition.primaryField).toBe('string');

            expect(definition.icon).toBeDefined();
            expect(typeof definition.icon).toBe('string');

            expect(definition.color).toBeDefined();
            expect(definition.color).toMatch(/^#[a-fA-F0-9]{6}$/);

            expect(definition.actions).toBeDefined();
            expect(Array.isArray(definition.actions)).toBe(true);

            expect(definition.searchFields).toBeDefined();
            expect(Array.isArray(definition.searchFields)).toBe(true);
        });

        it.each(allTypes)('%s has valid searchFields', (type, definition: EntityDefinition) => {
            expect(definition.searchFields.length).toBeGreaterThan(0);
            definition.searchFields.forEach(field => {
                expect(typeof field).toBe('string');
            });
        });
    });

    describe('Helper Functions', () => {
        it('getEntityDefinition returns correct definition for valid type', () => {
            const projectDef = getEntityDefinition('project');
            expect(projectDef).toBeDefined();
            expect(projectDef?.table).toBe('projects');
            expect(projectDef?.icon).toBe('FolderKanban');
        });

        it('getEntityDefinition returns undefined for invalid type', () => {
            const invalid = getEntityDefinition('not_a_real_type');
            expect(invalid).toBeUndefined();
        });

        it('getEntityIcon returns correct icon for valid type', () => {
            expect(getEntityIcon('project')).toBe('FolderKanban');
            expect(getEntityIcon('task')).toBe('CheckSquare');
            expect(getEntityIcon('goal')).toBe('Target');
        });

        it('getEntityIcon returns fallback for invalid type', () => {
            expect(getEntityIcon('invalid_type')).toBe('Box');
        });

        it('getEntityColor returns correct color for valid type', () => {
            expect(getEntityColor('project')).toBe('#3b82f6');
            expect(getEntityColor('task')).toBe('#10b981');
        });

        it('getEntityColor returns fallback for invalid type', () => {
            expect(getEntityColor('invalid_type')).toBe('#6b7280');
        });

        it('getAllEntityTypes returns all registered types', () => {
            const types = getAllEntityTypes();
            expect(types.length).toBe(Object.keys(ENTITY_REGISTRY).length);
            expect(types).toContain('project');
            expect(types).toContain('task');
            expect(types).toContain('goal');
        });
    });

    describe('STATUS_COLORS', () => {
        it('exports status colors', () => {
            expect(STATUS_COLORS).toBeDefined();
            expect(Object.keys(STATUS_COLORS).length).toBeGreaterThan(0);
        });

        it('has valid hex color values', () => {
            Object.values(STATUS_COLORS).forEach(color => {
                expect(color).toMatch(/^#[a-fA-F0-9]{6}$/);
            });
        });

        it('includes common status colors', () => {
            expect(STATUS_COLORS.active).toBeDefined();
            expect(STATUS_COLORS.completed).toBeDefined();
            expect(STATUS_COLORS.blocked).toBeDefined();
        });
    });

    describe('Project Entity Specifics', () => {
        it('project has comprehensive configuration', () => {
            const project = ENTITY_REGISTRY.project;

            // Ratings
            expect(project.ratings).toBeDefined();
            expect(project.ratings?.length).toBeGreaterThanOrEqual(2);

            // Meta grid
            expect(project.metaGrid).toBeDefined();
            expect(project.metaGrid?.length).toBeGreaterThanOrEqual(1);

            // Computed fields
            expect(project.computedFields).toBeDefined();
            expect(project.computedFields).toContain('progress');

            // State machine
            expect(project.stateMachine).toBe('projectStatus');

            // Schema
            expect(project.schema).toBeDefined();
        });
    });

    describe('Task Entity Specifics', () => {
        it('task has form configuration', () => {
            const task = ENTITY_REGISTRY.task;

            expect(task.form).toBeDefined();
            expect(task.form?.sections).toBeDefined();
            expect(task.form?.sections?.length).toBeGreaterThanOrEqual(1);
        });
    });
});
