import { db } from './db';
import { toast } from 'sonner';

export interface ActionPayload {
    intent: string;
    payload?: any;
    data?: any;
}

export class ActionService {
    static prepareProposal(action: ActionPayload, context: { projectId?: number }): { title: string, description: string, data: any, handler: () => Promise<void> } | null {

        switch (action.intent) {

            case 'UPDATE_TASK':
                return {
                    title: 'Update Task',
                    description: `Update fields for Task #${action.payload.id}.`,
                    data: {
                        ID: action.payload.id,
                        ...action.payload
                    },
                    handler: async () => {
                        if (!action.payload.id) return;
                        const cleanPayload = { ...action.payload };

                        if (cleanPayload.title) {
                            try {
                                const { NeurolinkService } = await import('./neurolinks');
                                cleanPayload.title = await NeurolinkService.processLLMOutput(cleanPayload.title);
                            } catch { /* linkify optional */ }
                        }

                        delete cleanPayload.id;
                        await db.project_tasks.update(action.payload.id, cleanPayload);
                        toast.success("Task Updated!");
                    }
                };

            case 'CREATE_PROJECT':
                return {
                    title: 'Create New Project',
                    description: 'Initialize a new project with the following details.',
                    data: {
                        Title: action.payload?.title,
                        Category: action.payload?.category,
                        Description: action.payload?.description,
                        // Pass through other creative fields (e.g. Genre, Premise)
                        ...Object.fromEntries(
                            Object.entries(action.payload || {})
                                .filter(([k]) => !['title', 'category', 'description', 'status', 'priority'].includes(k))
                        )
                    },
                    handler: async () => {
                        if (!action.payload?.title) return;

                        let linkedDescription = action.payload.description || '';
                        try {
                            const { NeurolinkService } = await import('./neurolinks');
                            linkedDescription = await NeurolinkService.processLLMOutput(linkedDescription);
                        } catch (e) { console.warn("Auto-link failed for project creation", e); }

                        const newId = await db.projects.add({
                            title: action.payload.title,
                            status_description: linkedDescription,
                            status: action.payload.status || 'active',
                            priority: action.payload.priority || 3,
                            category: action.payload.category || 'General',
                            version: '0.0.1',
                            tags: [],
                            created_at: new Date(),
                            updated_at: new Date()
                        });

                        // CREATIVE PROJECT SCAFFOLDING
                        // Automatically create documents for creative fields
                        const creativeFields: Record<string, string> = {
                            'plot': 'chapter',
                            'outline': 'chapter',
                            'characters': 'research',
                            'setting': 'research',
                            'theme': 'research',
                            'notes': 'article'
                        };

                        const docsToAdd: any[] = [];

                        // Check payload for these keys
                        Object.entries(action.payload).forEach(([key, value]) => {
                            const lowerKey = key.toLowerCase();
                            if (creativeFields[lowerKey] && typeof value === 'string' && value.length > 5) {
                                docsToAdd.push({
                                    project_id: newId,
                                    title: key.charAt(0).toUpperCase() + key.slice(1), // Capitalize "Plot", "Characters"
                                    content: value, // The content proposed by AI
                                    order: docsToAdd.length,
                                    type: creativeFields[lowerKey],
                                    status: 'draft',
                                    updated_at: new Date()
                                });
                            }
                        });

                        if (docsToAdd.length > 0) {
                            await db.project_documents.bulkAdd(docsToAdd);
                            toast.success(`Project Created with ${docsToAdd.length} starter documents!`);
                        } else {
                            toast.success(`Project "${action.payload.title}" Created! (ID: ${newId})`);
                        }
                    }
                };

            case 'UPDATE_PROJECT':
                return {
                    title: 'Update Project',
                    description: `Update details for Project #${action.payload.id}.`,
                    data: {
                        ID: action.payload.id,
                        Updates: JSON.stringify(action.payload, null, 2)
                    },
                    handler: async () => {
                        if (!action.payload.id) return;

                        // Handle Description Linking
                        const updates = { ...action.payload };
                        if ((updates.description || updates.status_description)) {
                            try {
                                const { NeurolinkService } = await import('./neurolinks');
                                const raw = updates.description || updates.status_description;
                                updates.status_description = await NeurolinkService.processLLMOutput(raw);
                                delete updates.description; // Ensure mapped to correct field
                            } catch (e) {
                                console.warn("Linkify failed for update project", e);
                            }
                        }

                        await db.projects.update(action.payload.id, updates);
                        toast.success("Project Updated!");
                    }
                };

            case 'ADD_TASK':
                return {
                    title: 'Add New Task',
                    description: `This will add a new task to the current project context #${context.projectId}.`,
                    data: {
                        Task: action.payload.title,
                        Priority: `${action.payload.priority}/5`,
                        Phase: 'Planning',
                        Status: 'Pending'
                    },
                    handler: async () => {
                        if (!context.projectId) throw new Error("No Project ID");

                        let linkedTitle = action.payload.title;
                        try {
                            // Linkify Title too (since we render it as HTML now)
                            const { NeurolinkService } = await import('./neurolinks');
                            linkedTitle = await NeurolinkService.processLLMOutput(linkedTitle);
                        } catch { /* linkify optional */ }

                        await db.project_tasks.add({
                            project_id: context.projectId,
                            title: linkedTitle,
                            priority: action.payload.priority || 3,
                            status: 'pending',
                            phase: 'Planning'
                        });
                        toast.success("Task Added to Project!");
                    }
                };

            case 'INVENTORY_ADD':
                return {
                    title: 'Import Inventory',
                    description: `Batch import ${action.data?.length || 0} items into inventory.`,
                    data: {
                        Items: action.data ? `${action.data.length} items to import` : 'No items',
                        Sample: action.data && action.data.length > 0 ? action.data[0].name : 'N/A'
                    },
                    handler: async () => {
                        // This one usually requires a dedicated UI (the InventoryIngestModal).
                        // Unlike the others which are atomic DB ops, this one launches a modal.
                        // Ideally, we return a handler that opens that modal?
                        // Or we use the OracleOverlay to CONFIRM, and THEN it adds them?
                        // Adding items blindly is risky. 
                        // Let's assume the handler adds them directly for now, OR we handle this specially in the consumer.

                        // For SAFETY, let's just add them. The OracleActionCard is the Review step.
                        // Wait, InventoryIngestModal IS a review step with editable rows.
                        // If we use GlobalActionCard, we lose the row-by-row editing.
                        // For now, let's map this to "Auto Add" but maybe we shouldn't.

                        // User request: "Universal action card behavior".
                        // Use the card to CONFIRM, then maybe just bulk add.
                        if (!action.data) return;
                        await db.inventory.bulkAdd(action.data.map((i: any) => ({
                            ...i,
                            quantity: i.quantity || 1,
                            last_updated: new Date()
                        })));
                        toast.success(`${action.data.length} Items Imported!`);
                    }
                };

            case 'LINKIFY_PROJECT':
                return {
                    title: 'Auto-Link Project Details',
                    description: `Scan Project #${action.payload.projectId} details and notebook for Neurolinks.`,
                    data: {
                        ProjectID: action.payload.projectId,
                        Scope: 'Description & Notebook'
                    },
                    handler: async () => {
                        const projectId = action.payload.projectId;
                        if (!projectId) return;

                        // 1. Linkify Project Description
                        const project = await db.projects.get(projectId);
                        if (project && project.status_description) {
                            const { NeurolinkService } = await import('./neurolinks');
                            const linkedDesc = await NeurolinkService.linkify(project.status_description);
                            if (linkedDesc !== project.status_description) {
                                await db.projects.update(projectId, { status_description: linkedDesc });
                                toast.success("Project Description Linked");
                            }
                        }

                        // 2. Linkify Notebook Entries (Last 20)
                        const notes = await db.notebook.where('project_id').equals(projectId).reverse().limit(20).toArray();
                        let notesUpdated = 0;
                        const { NeurolinkService } = await import('./neurolinks');

                        for (const note of notes) {
                            const linkedContent = await NeurolinkService.linkify(note.content);
                            if (linkedContent !== note.content) {
                                await db.notebook.update(note.id!, { content: linkedContent });
                                notesUpdated++;
                            }
                        }

                        if (notesUpdated > 0) {
                            toast.success(`Linked ${notesUpdated} Notebook Entries`);
                        } else {
                            toast.info("No new links found.");
                        }
                    }
                };

            case 'CREATE_GOAL':
                return {
                    title: 'Establish New Goal',
                    description: `Create a ${action.payload.level || 'strategic'} goal with ${action.payload.success_criteria?.length || 0} success criteria.`,
                    data: {
                        Title: action.payload.title,
                        Level: action.payload.level,
                        Motivation: action.payload.motivation || 'N/A'
                    },
                    handler: async () => {
                        if (!action.payload.title) return;
                        await db.goals.add({
                            title: action.payload.title,
                            level: action.payload.level || 'monthly',
                            status: 'active',
                            progress: 0,
                            motivation: action.payload.motivation,
                            success_criteria: action.payload.success_criteria || [],
                            review_cadence: action.payload.review_cadence || 'monthly',
                            created_at: new Date(),
                            updated_at: new Date()
                        });
                        toast.success("Goal Established Successfully!");
                    }
                };

            default:
                return null;
        }
    }
}
