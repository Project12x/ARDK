/**
 * Project Entity Fixture Generator
 * 
 * Uses zod-fixture to generate realistic Project data for tests.
 */
import { z } from 'zod';
import { createFixture } from 'zod-fixture';

// Define a simplified Project schema for fixture generation
const ProjectSchema = z.object({
    id: z.number().optional(),
    title: z.string().min(1),
    project_code: z.string().optional(),
    status: z.enum(['active', 'on-hold', 'completed', 'archived', 'legacy', 'rnd_long', 'dropped', 'someday']),
    design_status: z.string().optional(),
    build_status: z.string().optional(),
    priority: z.number().min(1).max(5).optional(),
    version: z.string().default('1.0.0'),
    intrusiveness: z.number().min(1).max(5).optional(),
    time_estimate_active: z.number().optional(),
    total_theorized_hours: z.number().optional(),
    financial_budget: z.number().optional(),
    financial_spend: z.number().optional(),
    category: z.string().optional(),
    tags: z.array(z.string()).default([]),
    target_completion_date: z.date().optional(),
    created_at: z.date(),
    updated_at: z.date(),
});

export type MockProject = z.infer<typeof ProjectSchema>;

/**
 * Generator instance for creating Project fixtures
 */
export const ProjectGenerator = {
    schema: ProjectSchema,

    /**
     * Generate a single mock Project with optional overrides
     */
    create(overrides: Partial<MockProject> = {}): MockProject {
        const fixture = createFixture(ProjectSchema);
        return {
            ...fixture,
            ...overrides,
            // Ensure dates are valid
            created_at: overrides.created_at ?? new Date(),
            updated_at: overrides.updated_at ?? new Date(),
        };
    },

    /**
     * Generate multiple mock Projects
     */
    createMany(count: number, overrides: Partial<MockProject> = {}): MockProject[] {
        return Array.from({ length: count }, (_, i) =>
            this.create({
                ...overrides,
                id: overrides.id ?? i + 1,
                title: `${overrides.title ?? 'Project'} ${i + 1}`,
            })
        );
    },
};

// Convenience function
export const createMockProject = ProjectGenerator.create.bind(ProjectGenerator);
