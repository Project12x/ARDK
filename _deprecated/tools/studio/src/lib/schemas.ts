import { z } from 'zod';

export const FilamentSchema = z.object({
    name: z.string().min(1, "Name is required").max(50, "Name too long"),
    brand: z.string().optional(),
    material: z.enum(['PLA', 'PETG', 'ABS', 'TPU', 'ASA', 'Resin']),
    color: z.string().regex(/^#[0-9A-F]{6}$/i, "Invalid color code"),
    weight: z.number().min(1, "Weight must be positive").max(10000, "Spool too heavy"),
    cost: z.number().min(0).optional(),
    temp_nozzle: z.number().min(150).max(350).optional(),
    temp_bed: z.number().min(0).max(120).optional(),
});

export type FilamentFormData = z.infer<typeof FilamentSchema>;

// Helper for "comma-separated strings to array"
const commaStringToArray = (val: unknown) => {
    if (typeof val === 'string') {
        return val.split(',').map(s => s.trim()).filter(Boolean);
    }
    return [];
};

// Project Schema matching db.ts interface
export const ProjectSchema = z.object({
    title: z.string().min(1, "Title is required"),
    status: z.enum(['active', 'on-hold', 'completed', 'archived', 'legacy', 'rnd_long', 'dropped', 'someday']),
    version: z.string().default('0.1.0'),
    priority: z.preprocess((val) => Number(val), z.number().min(1).max(5).default(3)),

    // Descriptive
    status_description: z.string().optional(),
    role: z.string().optional(),
    category: z.string().optional(),
    tags: z.union([z.string(), z.array(z.string())]).transform(val => {
        if (Array.isArray(val)) return val;
        return commaStringToArray(val);
    }),
    label_color: z.string().optional(),
    intrusiveness: z.preprocess((val) => Number(val), z.number().min(1).max(5).default(1)),

    // Estimates
    total_theorized_hours: z.preprocess((val) => Number(val), z.number().min(0).optional()),
    target_completion_date: z.string().optional().transform(str => str ? new Date(str) : undefined),

    // Hierarchy
    taxonomy_path: z.string().optional(),

    // v16 Fields
    project_code: z.string().optional(),
    design_status: z.enum(['idea', 'draft', 'full', 'frozen']).default('idea'),
    build_status: z.enum(['unbuilt', 'wip', 'boxed', 'finished']).default('unbuilt'),
    exp_cv_usage: z.string().optional(),
    image_url: z.string().optional(),
    github_repo: z.string().optional(),

    // v17 Fields
    time_estimate_active: z.preprocess((val) => Number(val), z.number().min(0).optional()),
    financial_budget: z.preprocess((val) => Number(val), z.number().min(0).optional()),
    rationale: z.string().optional(),
    risk_level: z.enum(['low', 'medium', 'high']).default('low'),
});

export type ProjectFormData = z.infer<typeof ProjectSchema>;
