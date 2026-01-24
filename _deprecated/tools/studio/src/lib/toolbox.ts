import { db } from './db';
import { GlobalSearch } from './search';

// --- Tool Definitions (Schema) ---
// Compatible with Gemini "Function Declarations"

export const TOOLS = [
    {
        name: "search_database",
        description: "Search for projects, tasks, or inventory items matching a query.",
        parameters: {
            type: "OBJECT",
            properties: {
                query: { type: "STRING", description: "The search term (e.g. 'filament', 'Project A')" },
                type: { type: "STRING", description: "Optional filter: 'project', 'task', 'inventory'" }
            },
            required: ["query"]
        }
    },
    {
        name: "add_task",
        description: "Add a new task to a specific project.",
        parameters: {
            type: "OBJECT",
            properties: {
                project_id: { type: "NUMBER", description: "The ID of the project" },
                title: { type: "STRING", description: "Title of the task" },
                priority: { type: "NUMBER", description: "1 (Low) to 5 (Urgent)" },
                status: { type: "STRING", description: "pending, in-progress, blocked" }
            },
            required: ["project_id", "title"]
        }
    },
    {
        name: "update_task",
        description: "Update an existing task's status or details.",
        parameters: {
            type: "OBJECT",
            properties: {
                task_id: { type: "NUMBER", description: "The ID of the task to update" },
                status: { type: "STRING", description: "pending, in-progress, completed, blocked" },
                title: { type: "STRING", description: "New title (optional)" },
                priority: { type: "NUMBER", description: "New priority (optional)" }
            },
            required: ["task_id"]
        }
    },
    {
        name: "query_inventory",
        description: "Check stock levels or find items in inventory.",
        parameters: {
            type: "OBJECT",
            properties: {
                category: { type: "STRING", description: "e.g. 'Filament', 'Electronics'" },
                min_quantity: { type: "NUMBER", description: "Find items with at least this amount" },
                low_stock: { type: "BOOLEAN", description: "If true, find items below min_stock" }
            }
        }
    },
    {
        name: "get_project_details",
        description: "Get full details, tasks, and BOM for a project.",
        parameters: {
            type: "OBJECT",
            properties: {
                project_id: { type: "NUMBER", description: "Target Project ID" }
            },
            required: ["project_id"]
        }
    }
];

// --- Tool Executor (The "Actuator") ---

export const Toolbox = {
    async execute(name: string, args: any) {
        console.log(`[Toolbox] Executing ${name}`, args);

        try {
            switch (name) {
                case 'search_database':
                    return await GlobalSearch.search(args.query);

                case 'add_task': {
                    // Verify project exists
                    const project = await db.projects.get(args.project_id);
                    if (!project) throw new Error(`Project ${args.project_id} not found`);

                    const newId = await db.project_tasks.add({
                        project_id: args.project_id,
                        title: args.title,
                        status: args.status || 'pending',
                        priority: args.priority || 3,
                        phase: 'Planning'
                    });
                    return { success: true, task_id: newId, message: `Task "${args.title}" added to Project #${args.project_id}` };
                }

                case 'update_task': {
                    const task = await db.project_tasks.get(args.task_id);
                    if (!task) throw new Error(`Task ${args.task_id} not found`);

                    const updates: any = {};
                    if (args.status) updates.status = args.status;
                    if (args.title) updates.title = args.title;
                    if (args.priority) updates.priority = args.priority;

                    await db.project_tasks.update(args.task_id, updates);
                    return { success: true, message: `Task #${args.task_id} updated` };
                }

                case 'query_inventory': {
                    let collection = db.inventory.toCollection();
                    if (args.category) collection = db.inventory.where('category').equals(args.category);

                    let items = await collection.toArray();

                    if (args.low_stock) {
                        items = items.filter(i => i.quantity <= (i.min_stock || 0));
                    }
                    // Simple text filter if query provided in future
                    return items.slice(0, 20); // Limit results
                }

                case 'get_project_details': {
                    const p = await db.projects.get(args.project_id);
                    if (!p) throw new Error("Project not found");
                    const t = await db.project_tasks.where({ project_id: args.project_id }).toArray();
                    const b = await db.project_bom.where({ project_id: args.project_id }).toArray();
                    return { project: p, tasks: t, bom: b };
                }

                default:
                    throw new Error(`Unknown tool: ${name}`);
            }
        } catch (e: any) {
            console.error(`[Toolbox] Error executing ${name}`, e);
            return { error: e.message };
        }
    }
};
