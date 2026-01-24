/**
 * Task Entity Fixture Generator
 * 
 * Uses zod-fixture to generate realistic ProjectTask data for tests.
 */
import { z } from 'zod';
import { createFixture } from 'zod-fixture';

// Define a simplified Task schema for fixture generation
const TaskSchema = z.object({
    id: z.number().optional(),
    project_id: z.number(),
    title: z.string().min(1),
    status: z.enum(['pending', 'in-progress', 'completed', 'blocked']),
    phase: z.string().optional(),
    priority: z.union([z.literal(1), z.literal(2), z.literal(3), z.literal(4), z.literal(5)]),
    estimated_time: z.string().optional(),
    calendar_duration: z.string().optional(),
    blockers: z.array(z.string()).optional(),
    materials_needed: z.array(z.string()).optional(),
    is_high_priority: z.boolean().optional(),
    energy_level: z.enum(['low', 'medium', 'high']).optional(),
    scheduled_date: z.date().optional(),
    goal_id: z.number().optional(),
});

export type MockTask = z.infer<typeof TaskSchema>;

/**
 * Generator instance for creating Task fixtures
 */
export const TaskGenerator = {
    schema: TaskSchema,

    /**
     * Generate a single mock Task with optional overrides
     */
    create(overrides: Partial<MockTask> = {}): MockTask {
        const fixture = createFixture(TaskSchema);
        return {
            ...fixture,
            ...overrides,
            // Ensure project_id is valid
            project_id: overrides.project_id ?? 1,
        };
    },

    /**
     * Generate multiple mock Tasks for a project
     */
    createMany(count: number, projectId: number, overrides: Partial<MockTask> = {}): MockTask[] {
        return Array.from({ length: count }, (_, i) =>
            this.create({
                ...overrides,
                id: overrides.id ?? i + 1,
                project_id: projectId,
                title: `${overrides.title ?? 'Task'} ${i + 1}`,
            })
        );
    },

    /**
     * Create a complete task with common defaults
     */
    createComplete(projectId: number, title: string): MockTask {
        return this.create({
            project_id: projectId,
            title,
            status: 'completed',
            priority: 3,
        });
    },

    /**
     * Create a blocked task
     */
    createBlocked(projectId: number, title: string, blockers: string[]): MockTask {
        return this.create({
            project_id: projectId,
            title,
            status: 'blocked',
            blockers,
            priority: 4,
        });
    },
};

// Convenience function
export const createMockTask = TaskGenerator.create.bind(TaskGenerator);
