import { db } from './db';

export interface BlueprintTask {
    title: string;
    phase: string;
    priority: 1 | 2 | 3 | 4 | 5;
    estimated_time?: string;
}

export interface Blueprint {
    id: string | number;
    name: string;
    description: string;
    category: string;

    // === Project Defaults ===

    // Basic Config
    tags: string[];
    priority: number;
    status: 'active' | 'on-hold' | 'completed' | 'archived' | 'legacy' | 'rnd_long' | 'dropped' | 'someday';
    github_repo?: string;

    // Classification / Taxonomy
    kingdom?: string;
    phylum?: string;
    taxonomy_path?: string;
    domains?: string[];
    label_color?: string;

    // Estimates & Budget
    time_estimate_active?: number;
    time_estimate_passive?: number;
    financial_budget?: number;
    total_theorized_hours?: number;

    // Design & Build Status
    design_status?: string;
    build_status?: string;
    risk_level?: 'low' | 'medium' | 'high';

    // Safety
    hazards?: string[];

    // Default External Resources
    external_links?: Array<{ label: string; url: string }>;

    // Default I/O and Specs
    io_spec?: string[];
    design_philosophy?: string;

    // === UI Settings ===
    settings?: {
        hidden_tabs?: string[];
    };

    // === Template Tasks ===
    defaultTasks: BlueprintTask[];

    // Meta
    isCustom?: boolean;
}

export const DEFAULT_BLUEPRINTS: Blueprint[] = [
    // 1. Blank
    {
        id: 'empty',
        name: 'Blank Slate',
        description: 'Start with a clean project with no tasks.',
        category: 'Uncategorized',
        tags: [],
        priority: 3,
        status: 'active',
        defaultTasks: [],
        settings: {
            hidden_tabs: ['manuscript', 'production', 'bom', 'tools', 'safety_qa', 'printing', 'code', 'assets', 'notebook', 'specs', 'blueprint']
        }
    },

    // === Guitar Pedals & Amps (Core) ===
    {
        id: 'pedal-analog',
        name: 'Guitar Pedal: Analog',
        description: 'Classic MDBD workflow for Drive, Fuzz, Modulation. Breadboard -> PCB -> Build.',
        category: 'Musical Electronics',
        tags: ['pedal', 'analog', 'mdbd', 'electronics'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing']
        },
        defaultTasks: [
            // Planning
            { title: 'Define Concept & Golden Voltages', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Breadboard Prototype & Validation', phase: 'Planning', priority: 5, estimated_time: '6h' },
            { title: 'Schematic Capture (KiCad)', phase: 'Planning', priority: 4, estimated_time: '3h' },
            { title: 'BOM Consolidation', phase: 'Planning', priority: 4, estimated_time: '1h' },
            // Design
            { title: 'PCB Layout & Routing', phase: 'Design', priority: 4, estimated_time: '4h' },
            { title: 'Enclosure Drill Template', phase: 'Design', priority: 3, estimated_time: '1h' },
            { title: 'Order PCBs & Parts', phase: 'Design', priority: 5, estimated_time: '0.5h' },
            // Fabrication
            { title: 'Enclosure Drilling & Finishing', phase: 'Fabrication', priority: 3, estimated_time: '2h' },
            { title: 'PCB Assembly (Populate)', phase: 'Fabrication', priority: 4, estimated_time: '3h' },
            { title: 'Off-Board Wiring', phase: 'Fabrication', priority: 3, estimated_time: '1.5h' },
            // Validation
            { title: 'Safe Power-Up & Current Check', phase: 'Testing', priority: 5, estimated_time: '0.5h' },
            { title: 'Audio Probe & Bias Trimming', phase: 'Testing', priority: 4, estimated_time: '1h' },
            // Release
            { title: 'Box-Up & Final Assembly', phase: 'Release', priority: 4, estimated_time: '1h' },
            { title: 'Final Play Test & Demo', phase: 'Release', priority: 3, estimated_time: '1h' }
        ]
    },
    {
        id: 'pedal-digital',
        name: 'Guitar Pedal: Digital / DSP',
        description: 'Workflow for DSP-based effects (FV-1, Daisy, Teensy). Includes Firmware phases.',
        category: 'Musical Electronics',
        tags: ['pedal', 'digital', 'dsp', 'code', 'firmware'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'printing']
        },
        defaultTasks: [
            // Planning
            { title: 'Algorithm Concept & Flow', phase: 'Planning', priority: 5, estimated_time: '3h' },
            { title: 'Dev Board Prototyping (PoC)', phase: 'Planning', priority: 5, estimated_time: '5h' },
            { title: 'Hardware Schematic Selection', phase: 'Planning', priority: 4, estimated_time: '2h' },
            // Design
            { title: 'PCB Layout (Mixed Signal)', phase: 'Design', priority: 4, estimated_time: '5h' },
            { title: 'Firmware Architecture Setup', phase: 'Design', priority: 4, estimated_time: '2h' },
            // Fabrication
            { title: 'PCB Assembly (SMD Focus)', phase: 'Fabrication', priority: 4, estimated_time: '4h' },
            // Firmware Dev (The "Build" of Digital)
            { title: 'Implement DSP Algorithms', phase: 'Fabrication', priority: 5, estimated_time: '10h' },
            { title: 'UI/Control Logic Implementation', phase: 'Fabrication', priority: 4, estimated_time: '4h' },
            // Validation
            { title: 'Flash & Hardware Debug', phase: 'Testing', priority: 5, estimated_time: '2h' },
            { title: 'Audio Performance Test', phase: 'Testing', priority: 4, estimated_time: '1h' },
            // Release
            { title: 'Final Code Commit & Tag', phase: 'Release', priority: 2, estimated_time: '0.5h' },
            { title: 'Demo Recording', phase: 'Release', priority: 3, estimated_time: '1h' }
        ]
    },
    {
        id: 'pedal-utility',
        name: 'Guitar Pedal: Utility',
        description: 'Buffers, Loopers, Switchers. Mechanical and wiring focused.',
        category: 'Musical Electronics',
        tags: ['pedal', 'utility', 'wiring', 'passive'],
        priority: 4,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'specs', 'safety_qa']
        },
        defaultTasks: [
            { title: 'Define I/O Logic', phase: 'Planning', priority: 5, estimated_time: '1h' },
            { title: 'Enclosure Layout (CAD/Paper)', phase: 'Design', priority: 4, estimated_time: '1h' },
            { title: 'Drill Enclosure', phase: 'Fabrication', priority: 4, estimated_time: '2h' },
            { title: 'Install Jacks & Switches', phase: 'Fabrication', priority: 3, estimated_time: '1h' },
            { title: 'Point-to-Point Wiring', phase: 'Fabrication', priority: 4, estimated_time: '2h' },
            { title: 'Continuity Check', phase: 'Testing', priority: 5, estimated_time: '0.5h' },
            { title: 'Functional Test', phase: 'Testing', priority: 4, estimated_time: '0.5h' }
        ]
    },
    {
        id: 'guitar-amp',
        name: 'Guitar Amplifier Project',
        description: 'Tube or Solid State amp build. Emphasis on High Voltage Safety.',
        category: 'Musical Electronics',
        tags: ['amp', 'high-voltage', 'tube', 'enclosure'],
        priority: 3,
        status: 'active',
        risk_level: 'high',
        hazards: ['High Voltage', 'Heat', 'AC Mains'],
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing']
        },
        defaultTasks: [
            { title: 'Topology Selection & Schematic', phase: 'Planning', priority: 5, estimated_time: '5h' },
            { title: 'BOM Sourcing (Transformers/Chassis)', phase: 'Planning', priority: 5, estimated_time: '3h' },
            { title: 'Layout Design (Heater/Grounding)', phase: 'Design', priority: 5, estimated_time: '6h' },
            { title: 'Chassis Punching & Drilling', phase: 'Fabrication', priority: 3, estimated_time: '4h' },
            { title: 'Power Supply Board/Wiring', phase: 'Fabrication', priority: 5, estimated_time: '4h' },
            { title: 'Heater Wiring (Twisted Pair)', phase: 'Fabrication', priority: 4, estimated_time: '2h' },
            { title: 'Signal Circuit Build', phase: 'Fabrication', priority: 4, estimated_time: '6h' },
            { title: 'Safety Check (Earth/Fuse)', phase: 'Testing', priority: 5, estimated_time: '1h' },
            { title: 'Variac Power Up', phase: 'Testing', priority: 5, estimated_time: '2h' },
            { title: 'Cabinet Install', phase: 'Release', priority: 2, estimated_time: '2h' }
        ]
    },

    // === Synthesizers ===
    {
        id: 'synth-eurorack',
        name: 'Eurorack Module',
        description: 'Modular synth hardware. Panel ergonomics and power constraints.',
        category: 'Musical Electronics',
        tags: ['synth', 'eurorack', 'modular'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code']
        },
        defaultTasks: [
            { title: 'Concept & HP Width Target', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Circuit Simulation', phase: 'Planning', priority: 4, estimated_time: '4h' },
            { title: 'Panel Design (Faceplate)', phase: 'Design', priority: 5, estimated_time: '3h' },
            { title: 'PCB Stackup Design', phase: 'Design', priority: 5, estimated_time: '5h' },
            { title: 'Control Board Assembly', phase: 'Fabrication', priority: 4, estimated_time: '3h' },
            { title: 'Main Board Assembly', phase: 'Fabrication', priority: 4, estimated_time: '3h' },
            { title: 'Calibration', phase: 'Testing', priority: 5, estimated_time: '2h' }
        ]
    },
    {
        id: 'synth-desktop',
        name: 'Synthesizer (Desktop/Standalone)',
        description: 'Complex standalone instrument design.',
        category: 'Musical Electronics',
        tags: ['synth', 'instrument', 'midi'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production']
        },
        defaultTasks: [
            { title: 'Voice Architecture Design', phase: 'Planning', priority: 5, estimated_time: '5h' },
            { title: 'UI/UX Design (Knobs/Screens)', phase: 'Design', priority: 5, estimated_time: '4h' },
            { title: 'Mechanical Enclosure Design', phase: 'Design', priority: 4, estimated_time: '6h' },
            { title: 'Electronics Design', phase: 'Design', priority: 5, estimated_time: '10h' },
            { title: 'Fabrication & Assembly', phase: 'Fabrication', priority: 4, estimated_time: '20h' },
            { title: 'Firmware & Tuning', phase: 'Testing', priority: 5, estimated_time: '15h' }
        ]
    },

    // === Maintenance & DIY ===
    {
        id: 'repair-gear',
        name: 'Repair / Restoration (Gear)',
        description: 'Diagnostics and repair for instruments and audio equipment.',
        category: 'Maintenance',
        tags: ['repair', 'maintenance', 'fix'],
        priority: 4,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'blueprint', 'specs', 'bom', 'safety_qa']
        },
        defaultTasks: [
            { title: 'Initial Triage & Symptom Log', phase: 'Planning', priority: 5, estimated_time: '0.5h' },
            { title: 'Disassembly & Visual Check', phase: 'Planning', priority: 4, estimated_time: '1h' },
            { title: 'Fault Isolation', phase: 'Testing', priority: 5, estimated_time: '2h' },
            { title: 'Order Parts', phase: 'Design', priority: 5, estimated_time: '0.5h' },
            { title: 'Component Replacement', phase: 'Fabrication', priority: 4, estimated_time: '2h' },
            { title: 'Reassembly & Cleaning', phase: 'Release', priority: 3, estimated_time: '1h' },
            { title: 'Soak Test', phase: 'Release', priority: 4, estimated_time: '4h' }
        ]
    },
    {
        id: 'guitar-maint',
        name: 'Guitar Maintenance / Setup',
        description: 'Setup, restringing, and light repair (e.g. pickup swap).',
        category: 'Maintenance',
        tags: ['guitar', 'luthierie', 'setup'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'blueprint', 'specs', 'bom', 'safety_qa']
        },
        defaultTasks: [
            { title: 'Inspect & Diagnose Issues', phase: 'Planning', priority: 4, estimated_time: '0.5h' },
            { title: 'Remove Old Strings & Clean', phase: 'Preparation', priority: 3, estimated_time: '0.5h' },
            { title: 'Electronics Work / Soldering', phase: 'Execution', priority: 4, estimated_time: '1h' },
            { title: 'Restring', phase: 'Execution', priority: 3, estimated_time: '0.5h' },
            { title: 'Truss Rod & Action Setup', phase: 'Testing', priority: 5, estimated_time: '0.5h' },
            { title: 'Intonation Adjustment', phase: 'Testing', priority: 5, estimated_time: '0.5h' },
            { title: 'Final Polish & Play Test', phase: 'Release', priority: 3, estimated_time: '0.5h' }
        ]
    },
    {
        id: 'diy-home',
        name: 'Home Improvement / Reno',
        description: 'Renovations and fixes (e.g. refinishing furniture, fixing fixtures).',
        category: 'Home',
        tags: ['diy', 'house', 'renovation', 'construct'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'bom', 'safety_qa', 'specs', 'blueprint']
        },
        defaultTasks: [
            { title: 'Scope & Measurements', phase: 'Planning', priority: 5, estimated_time: '1h' },
            { title: 'Material Purchase', phase: 'Design', priority: 5, estimated_time: '2h' },
            { title: 'Prep / Demolition', phase: 'Fabrication', priority: 3, estimated_time: '2h' },
            { title: 'Installation / Build', phase: 'Fabrication', priority: 5, estimated_time: '4h' },
            { title: 'Sanding / Finishing', phase: 'Fabrication', priority: 4, estimated_time: '6h' },
            { title: 'Cleanup & Disposal', phase: 'Release', priority: 2, estimated_time: '1h' }
        ]
    },
    {
        id: 'deep-clean',
        name: 'Deep Clean / Organization',
        description: 'Large scale decluttering or deep cleaning projects.',
        category: 'Home',
        tags: ['cleaning', 'organization', 'declutter'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'bom', 'blueprint', 'specs', 'safety_qa']
        },
        defaultTasks: [
            { title: 'Empty Area Completely', phase: 'Planning', priority: 5, estimated_time: '1h' },
            { title: 'Sort: Keep / Donate / Trash', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Deep Clean Surfaces', phase: 'Fabrication', priority: 4, estimated_time: '2h' },
            { title: 'Repair / Touch-up Paint', phase: 'Fabrication', priority: 2, estimated_time: '1h' },
            { title: 'Re-organize & Return Items', phase: 'Release', priority: 4, estimated_time: '2h' },
            { title: 'Dispose of Trash/Donations', phase: 'Release', priority: 3, estimated_time: '1h' }
        ]
    },
    {
        id: 'woodworking',
        name: 'Woodworking / Furniture',
        description: 'Building physical objects from wood.',
        category: 'Fab',
        tags: ['wood', 'furniture', 'build'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'bom', 'safety_qa']
        },
        defaultTasks: [
            { title: 'Sketches & Dimensions', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Cut List & Material Buy', phase: 'Design', priority: 5, estimated_time: '2h' },
            { title: 'Rough Cuts', phase: 'Fabrication', priority: 3, estimated_time: '3h' },
            { title: 'Joinery', phase: 'Fabrication', priority: 4, estimated_time: '5h' },
            { title: 'Glue Up', phase: 'Fabrication', priority: 4, estimated_time: '24h' },
            { title: 'Sanding & Finishing', phase: 'Release', priority: 3, estimated_time: '6h' }
        ]
    },
    {
        id: '3d-print',
        name: '3D Print Design',
        description: 'CAD -> Slicer -> Print workflow.',
        category: 'Fab',
        tags: ['3d-printing', 'cad', 'plastic'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'bom', 'tools', 'safety_qa']
        },
        defaultTasks: [
            { title: 'Measure & Constraints', phase: 'Planning', priority: 5, estimated_time: '0.5h' },
            { title: 'CAD Modeling (Fusion360)', phase: 'Design', priority: 5, estimated_time: '2h' },
            { title: 'Draft Print', phase: 'Testing', priority: 4, estimated_time: '1h' },
            { title: 'Iterate & Refine', phase: 'Design', priority: 3, estimated_time: '1h' },
            { title: 'Final Print', phase: 'Fabrication', priority: 5, estimated_time: '4h' }
        ]
    },
    {
        id: 'gardening',
        name: 'Gardening / Agriculture',
        description: 'Seasonal planting, maintenance, and harvest.',
        category: 'Lifestyle',
        tags: ['garden', 'plants', 'nature', 'seasonal'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'code', 'printing', 'bom', 'safety_qa', 'specs', 'blueprint']
        },
        defaultTasks: [
            { title: 'Seasonal Planning & Selection', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Soil Prep / Amendment', phase: 'Preparation', priority: 4, estimated_time: '2h' },
            { title: 'Sowing / Planting', phase: 'Execution', priority: 5, estimated_time: '3h' },
            { title: 'Watering & Weeding Routine', phase: 'Execution', priority: 4, estimated_time: '20h' },
            { title: 'Pest Control', phase: 'Maintenance', priority: 3, estimated_time: '5h' },
            { title: 'Harvesting', phase: 'Release', priority: 5, estimated_time: '4h' },
            { title: 'Winterizing / Cleanup', phase: 'Release', priority: 3, estimated_time: '4h' }
        ]
    },

    // === Creative & Digital ===
    {
        id: 'music-prod',
        name: 'Music Production (Album/EP)',
        description: 'Composition, recording, mixing, and mastering workflow.',
        category: 'Music',
        tags: ['music', 'production', 'recording', 'art'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['code', 'printing', 'bom', 'safety_qa', 'tools', 'blueprint', 'specs']
        },
        defaultTasks: [
            { title: 'Composition / Songwriting', phase: 'Planning', priority: 5, estimated_time: '10h' },
            { title: 'Demo Recording (Scratch)', phase: 'Planning', priority: 4, estimated_time: '4h' },
            { title: 'Tracking (Drums/Bass/Gtr)', phase: 'Fabrication', priority: 5, estimated_time: '12h' },
            { title: 'Overdubs & Vocals', phase: 'Fabrication', priority: 5, estimated_time: '8h' },
            { title: 'Editing & Comping', phase: 'Design', priority: 4, estimated_time: '6h' },
            { title: 'Mixing', phase: 'Testing', priority: 5, estimated_time: '8h' },
            { title: 'Mastering', phase: 'Release', priority: 4, estimated_time: '2h' },
            { title: 'Artwork & Distribution', phase: 'Release', priority: 3, estimated_time: '4h' }
        ]
    },
    {
        id: 'software-app',
        name: 'Software Application',
        description: 'Full-stack development lifecycle.',
        category: 'Software',
        tags: ['code', 'dev', 'app'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['manuscript', 'production', 'printing', 'safety_qa', 'tools', 'assets', 'bom']
        },
        defaultTasks: [
            { title: 'Requirements & Specs', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Repo & Env Setup', phase: 'Planning', priority: 3, estimated_time: '1h' },
            { title: 'Core Implementation', phase: 'Fabrication', priority: 5, estimated_time: '10h' },
            { title: 'Testing & Debugging', phase: 'Testing', priority: 4, estimated_time: '4h' },
            { title: 'Deployment', phase: 'Release', priority: 5, estimated_time: '1h' }
        ]
    },
    {
        id: 'video-prod',
        name: 'Video Production',
        description: 'Script to Publish workflow.',
        category: 'Creative',
        tags: ['video', 'youtube', 'content'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['code', 'printing', 'bom', 'safety_qa', 'tools', 'blueprint', 'specs']
        },
        defaultTasks: [
            { title: 'Concept & Script', phase: 'Planning', priority: 5, estimated_time: '3h' },
            { title: 'Filming / Recording', phase: 'Fabrication', priority: 5, estimated_time: '4h' },
            { title: 'Editing & Timeline', phase: 'Design', priority: 4, estimated_time: '6h' },
            { title: 'Color & Sound', phase: 'Testing', priority: 3, estimated_time: '2h' },
            { title: 'Export & Upload', phase: 'Release', priority: 5, estimated_time: '1h' }
        ]
    },
    {
        id: 'writing-content',
        name: 'Writing / Content',
        description: 'Articles, books, or documentation.',
        category: 'Creative',
        tags: ['writing', 'text', 'docs'],
        priority: 3,
        status: 'active',
        settings: {
            hidden_tabs: ['production', 'bom', 'tools', 'safety_qa', 'printing', 'code', 'specs', 'blueprint']
        },
        defaultTasks: [
            { title: 'Outline & Thesis', phase: 'Planning', priority: 5, estimated_time: '2h' },
            { title: 'Research', phase: 'Planning', priority: 4, estimated_time: '4h' },
            { title: 'First Draft', phase: 'Fabrication', priority: 5, estimated_time: '6h' },
            { title: 'Editing & Review', phase: 'Testing', priority: 4, estimated_time: '2h' },
            { title: 'Final Polish', phase: 'Release', priority: 3, estimated_time: '1h' }
        ]
    }
];

// Compat export
export const BLUEPRINTS = DEFAULT_BLUEPRINTS;

export class BlueprintService {
    static async getAll(): Promise<Blueprint[]> {
        // Force-sync DB with Code Defaults
        // This ensures new templates appear and existing defaults are updated
        for (const bp of DEFAULT_BLUEPRINTS) {
            // v47: Use slug for identifying default templates (since id is auto-inc number in DB)
            const slug = bp.id.toString();
            const existing = await db.project_templates.where('slug').equals(slug).first();

            // Upsert if it doesn't exist OR if it's a default (not custom)
            // This allows us to push updates to standard templates
            if (!existing || !existing.is_custom) {
                // Prepare payload, excluding the string 'id' from Blueprint interface
                const { id, ...bpData } = bp;

                await db.project_templates.put({
                    ...bpData,
                    id: existing?.id, // Preserve numeric ID if exists
                    slug: slug,       // Store the string ID as slug
                    // Map legacy fields if needed, but here we strictly follow interface
                    tasks: bp.defaultTasks,
                    // Ensure we don't accidentally mark defaults as custom
                    is_custom: false,
                    // Preserve created_at if exists
                    created_at: existing?.created_at || new Date()
                });
            }
        }

        // Fetch ALL from DB (including any customs the user made)
        const records = await db.project_templates.toArray();
        return records.map(c => ({
            // Return either the slug (for defaults) or the numeric ID (for customs) as the ID
            id: c.slug || c.id!,
            name: c.name,
            description: c.description,
            category: c.category,
            defaultTasks: c.tasks,
            tags: c.tags || [],
            priority: c.priority || 3,
            status: c.status || 'active',
            github_repo: c.github_repo,
            // New fields
            kingdom: c.kingdom,
            phylum: c.phylum,
            taxonomy_path: c.taxonomy_path,
            domains: c.domains,
            label_color: c.label_color,
            time_estimate_active: c.time_estimate_active,
            time_estimate_passive: c.time_estimate_passive,
            financial_budget: c.financial_budget,
            total_theorized_hours: c.total_theorized_hours,
            design_status: c.design_status,
            build_status: c.build_status,
            risk_level: c.risk_level,
            hazards: c.hazards,
            external_links: c.external_links,
            io_spec: c.io_spec,
            design_philosophy: c.design_philosophy,
            settings: c.settings,
            isCustom: c.is_custom
        }));
    }

    static async getBlueprint(id: string | number): Promise<Blueprint | undefined> {
        const all = await this.getAll();
        // Loose comparison to match string "5" with number 5 if needed, though usually it's string vs string
        return all.find(b => b.id == id);
    }
}
