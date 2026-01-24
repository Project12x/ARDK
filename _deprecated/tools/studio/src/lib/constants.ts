// Global Application Constants
// Central source of truth for Logic-to-Visual mappings

export const DOMAIN_COLORS: Record<string, string> = {
    // === Technical / Maker ===
    'Electronics': '#3b82f6',     // blue-500
    'Software': '#10b981',        // emerald-500
    'Woodworking': '#d97706',     // amber-600
    'Metalworking': '#ef4444',    // red-500
    '3D Printing': '#8b5cf6',     // violet-500
    'Fabrication': '#a855f7',     // purple-500
    'Mechanical': '#6366f1',      // indigo-500
    'CNC': '#7c3aed',             // violet-600

    // === Creative / Art ===
    'Art': '#f43f5e',             // rose-500
    'Music': '#f59e0b',           // amber-500
    'Writing': '#f472b6',         // pink-400
    'Photography': '#fbbf24',     // amber-400
    'Video': '#fb923c',           // orange-400
    'Design': '#ec4899',          // pink-500
    'Textile': '#ec4899',         // pink-500
    'Crafts': '#c084fc',          // purple-400

    // === Knowledge / Research ===
    'Research': '#818cf8',        // indigo-400
    'Education': '#2dd4bf',       // teal-400
    'Science': '#06b6d4',         // cyan-500
    'Engineering': '#0ea5e9',     // sky-500

    // === Life / Personal ===
    'Home': '#14b8a6',            // teal-500
    'Personal': '#a78bfa',        // violet-400
    'Health': '#f87171',          // red-400
    'Fitness': '#22c55e',         // green-500
    'Travel': '#38bdf8',          // sky-400
    'Cooking': '#fb7185',         // rose-400

    // === Business / Professional ===
    'Business': '#0284c7',        // sky-600
    'Finance': '#84cc16',         // lime-500
    'Marketing': '#e879f9',       // fuchsia-400
    'Event Planning': '#4ade80',  // green-400
    'Consulting': '#60a5fa',      // blue-400

    // === Automotive / Vehicle ===
    'Automotive': '#64748b',      // slate-500
    'Motorcycle': '#78716c',      // stone-500
    'Bicycle': '#65a30d',         // lime-600

    // === Maintenance ===
    'Maintenance': '#94a3b8',     // slate-400
    'Repair': '#9ca3af',          // gray-400

    // === Default ===
    'Other': '#6b7280',           // gray-500
    'General': '#71717a',         // zinc-500
};

export const STATUS_COLORS: Record<string, string> = {
    'active': '#3b82f6', // blue-500
    'completed': '#10b981', // emerald-500
    'on-hold': '#f59e0b', // amber-500
    'archived': '#6b7280', // gray-500
    'planning': '#a855f7', // purple-500
    'legacy': '#9ca3af', // gray-400
    'dropped': '#ef4444', // red-500
    'rnd_long': '#06b6d4', // cyan-500
};

export const MATERIAL_COLORS: Record<string, string> = {
    'PLA': '#00ffd2',   // Cyan
    'PETG': '#ff4d00',  // Orange
    'ABS': '#ff0055',   // Pinkish Red
    'TPU': '#0099ff',   // Blue
    'ASA': '#ffee00',   // Yellow
    'Resin': '#cc00ff', // Purple
    'Other': '#888888'  // Gray
};

// === Universal Phase System ===
// These phases apply across ALL project types
export const UNIVERSAL_PHASES = [
    'Ideation',      // Concept, brainstorm, spark
    'Research',      // Discovery, learning, exploration
    'Planning',      // Design, architecture, roadmap
    'Preparation',   // Procurement, setup, staging
    'Execution',     // Build, create, implement
    'Review',        // Test, QA, feedback, edit
    'Delivery',      // Deploy, publish, ship, present
    'Maintenance',   // Support, iterate, archive
] as const;

export type UniversalPhase = typeof UNIVERSAL_PHASES[number];

// Domain-specific phase aliases (maps to universal phases)
export const PHASE_ALIASES: Record<string, Record<string, UniversalPhase>> = {
    'Electronics': {
        'Schematic': 'Planning',
        'PCB Layout': 'Planning',
        'Procurement': 'Preparation',
        'Assembly': 'Execution',
        'Fabrication': 'Execution',
        'Testing': 'Review',
        'Calibration': 'Review',
        'Release': 'Delivery',
    },
    'Software': {
        'Requirements': 'Research',
        'Architecture': 'Planning',
        'Setup': 'Preparation',
        'Development': 'Execution',
        'Coding': 'Execution',
        'QA': 'Review',
        'Testing': 'Review',
        'Deployment': 'Delivery',
        'DevOps': 'Maintenance',
    },
    'Woodworking': {
        'Design': 'Planning',
        'Cut List': 'Planning',
        'Lumber': 'Preparation',
        'Rough Cuts': 'Execution',
        'Joinery': 'Execution',
        'Glue-Up': 'Execution',
        'Finishing': 'Delivery',
    },
    'Writing': {
        'Outline': 'Planning',
        'Draft': 'Execution',
        'Editing': 'Review',
        'Proofreading': 'Review',
        'Publishing': 'Delivery',
    },
    'Photography': {
        'Concept': 'Ideation',
        'Scouting': 'Research',
        'Prep': 'Preparation',
        'Shoot': 'Execution',
        'Culling': 'Review',
        'Editing': 'Review',
        'Delivery': 'Delivery',
    },
    'Event Planning': {
        'Concept': 'Ideation',
        'Logistics': 'Planning',
        'Vendors': 'Preparation',
        'Promotion': 'Preparation',
        'Event Day': 'Execution',
        'Debrief': 'Review',
    },
    'Research': {
        'Literature Review': 'Research',
        'Hypothesis': 'Planning',
        'Experiment': 'Execution',
        'Analysis': 'Review',
        'Writing': 'Delivery',
        'Submission': 'Delivery',
    },
};

// Get all valid phases for a domain (universal + aliases)
export function getPhasesForDomain(domain?: string): string[] {
    const universal = [...UNIVERSAL_PHASES];
    if (domain && PHASE_ALIASES[domain]) {
        return [...new Set([...universal, ...Object.keys(PHASE_ALIASES[domain])])];
    }
    return universal;
}

// Normalize a phase to its universal equivalent
export function normalizePhase(phase: string, domain?: string): UniversalPhase {
    if (UNIVERSAL_PHASES.includes(phase as UniversalPhase)) {
        return phase as UniversalPhase;
    }
    if (domain && PHASE_ALIASES[domain]?.[phase]) {
        return PHASE_ALIASES[domain][phase];
    }
    // Fuzzy match
    const lower = phase.toLowerCase();
    if (lower.includes('plan') || lower.includes('design')) return 'Planning';
    if (lower.includes('research') || lower.includes('learn')) return 'Research';
    if (lower.includes('buy') || lower.includes('procure') || lower.includes('setup')) return 'Preparation';
    if (lower.includes('build') || lower.includes('create') || lower.includes('make') || lower.includes('code')) return 'Execution';
    if (lower.includes('test') || lower.includes('review') || lower.includes('edit') || lower.includes('qa')) return 'Review';
    if (lower.includes('deploy') || lower.includes('ship') || lower.includes('publish') || lower.includes('release')) return 'Delivery';
    return 'Execution'; // Default
}
