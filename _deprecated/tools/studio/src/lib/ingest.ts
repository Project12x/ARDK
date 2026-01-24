import { db } from './db';
import { AIService } from './AIService';

import { DOMAIN_COLORS } from './constants';

import { PortfolioService } from './portfolio';

export const CATEGORY_COLORS = DOMAIN_COLORS;

function assignDefaultColor(category?: string, domain?: string): string {
    // Try category first
    if (category && CATEGORY_COLORS[category]) return CATEGORY_COLORS[category];
    // Then domain
    if (domain && CATEGORY_COLORS[domain]) return CATEGORY_COLORS[domain];

    // Fuzzy match if strict mismatch
    const key = (category || domain || '').toLowerCase();

    // Technical
    if (key.match(/electr|circuit|pcb|solder/)) return CATEGORY_COLORS['Electronics'];
    if (key.match(/code|soft|web|app|dev|program/)) return CATEGORY_COLORS['Software'];
    if (key.match(/wood|lumber|furniture|cabinet/)) return CATEGORY_COLORS['Woodworking'];
    if (key.match(/metal|weld|machine/)) return CATEGORY_COLORS['Metalworking'];
    if (key.match(/print|3d|cad|stl/)) return CATEGORY_COLORS['3D Printing'];
    if (key.match(/cnc|mill|lathe/)) return CATEGORY_COLORS['CNC'];

    // Creative
    if (key.match(/writ|book|article|blog|novel/)) return CATEGORY_COLORS['Writing'];
    if (key.match(/photo|camera|shoot/)) return CATEGORY_COLORS['Photography'];
    if (key.match(/video|film|youtube|edit/)) return CATEGORY_COLORS['Video'];
    if (key.match(/music|audio|sound|song/)) return CATEGORY_COLORS['Music'];
    if (key.match(/art|paint|draw|sculpt/)) return CATEGORY_COLORS['Art'];
    if (key.match(/design|ui|ux|graphic/)) return CATEGORY_COLORS['Design'];

    // Knowledge
    if (key.match(/research|study|academ|paper/)) return CATEGORY_COLORS['Research'];
    if (key.match(/edu|learn|teach|course/)) return CATEGORY_COLORS['Education'];
    if (key.match(/science|experiment|lab/)) return CATEGORY_COLORS['Science'];

    // Life
    if (key.match(/personal|goal|habit|self/)) return CATEGORY_COLORS['Personal'];
    if (key.match(/health|medical|wellness/)) return CATEGORY_COLORS['Health'];
    if (key.match(/fitness|workout|exercise/)) return CATEGORY_COLORS['Fitness'];
    if (key.match(/travel|trip|vacation/)) return CATEGORY_COLORS['Travel'];
    if (key.match(/cook|recipe|food|meal/)) return CATEGORY_COLORS['Cooking'];
    if (key.match(/home|house|diy/)) return CATEGORY_COLORS['Home'];

    // Business
    if (key.match(/event|party|conference|wedding/)) return CATEGORY_COLORS['Event Planning'];
    if (key.match(/business|startup|company/)) return CATEGORY_COLORS['Business'];
    if (key.match(/finance|money|budget|invest/)) return CATEGORY_COLORS['Finance'];
    if (key.match(/market|promo|advertis/)) return CATEGORY_COLORS['Marketing'];

    // Maintenance
    if (key.match(/repair|fix|restore|service/)) return CATEGORY_COLORS['Repair'];
    if (key.match(/car|auto|vehicle/)) return CATEGORY_COLORS['Automotive'];

    return CATEGORY_COLORS['Other'];
}

export const IngestionService = {
    /**
     * UNIVERSAL INGESTION ENTRY POINT
     * automatically classifies and routes file to correct domain.
     */
    async ingestUniversal(file: File): Promise<{ type: string, count?: number, id?: number, summary?: string }> {
        // 1. Check for Backup (Deterministic)
        if (file.name.endsWith('.json') && file.type.includes('json')) {
            // Peek at structure? Or just assume Project Backup vs System Backup?
            // Existing logic handles JSON as "Project Backup". Let's try that first.
            try {
                const id = await this.ingestFile(file, 'project'); // Will trigger JSON restore logic
                return { type: 'backup', id, summary: 'Restored from Backup' };
            } catch {
                // Fallthrough if not a project json
            }
        }

        // 2. AI Classification
        console.log("Classifying Drop...");
        const cls = await AIService.classifyUpload(file);
        console.log("Classification Result:", cls);

        // 3. Routing
        switch (cls.type) {
            case 'song':
                return await this.ingestSong(file);
            case 'asset':
                return await this.ingestAsset(file);
            case 'inventory':
                return await this.ingestFile(file, 'inventory');
            case 'goal':
                return await this.ingestFile(file, 'project'); // Map to project for now
            case 'portfolio': {
                const items = await AIService.parsePortfolio(file);
                const res = await PortfolioService.syncPortfolio(items);
                return { type: 'portfolio', count: res.created + res.updated, summary: `Portfolio: ${res.created} new, ${res.updated} updated.` };
            }
            case 'project':
            default: {
                const res = await this.ingestFile(file, 'project');
                return { type: 'project', id: typeof res === 'number' ? res : undefined, summary: 'Project Updated' };
            }
        }
    },

    async ingestSong(file: File) {
        const data = await AIService.analyzeMusicData(file);

        // Add to Songs
        const id = await db.songs.add({
            title: data.title,
            status: 'idea',
            bpm: data.bpm,
            key: data.key,
            tags: data.tags || [],
            lyrics: data.lyrics_snippet || '',
            duration: '0:00', // Need audio element parsing for real duration
            created_at: new Date(),
            updated_at: new Date(),
            is_archived: false,
        });

        // Store File
        await db.song_files.add({
            song_id: Number(id),
            name: file.name,
            type: file.type,
            content: file,
            category: 'attachment',
            created_at: new Date()
        });

        return { type: 'song', id: Number(id), summary: `Song "${data.title}" created.` };
    },

    async ingestAsset(file: File) {
        const data = await AIService.analyzeAssetImage(file);

        const id = await db.assets.add({
            name: data.name,
            make: data.make,
            model: data.model,
            category: data.category,
            description: data.description,
            status: 'active',
            value: data.estimated_value || 0,
            serial_number: data.serial_number,
            images: [], // We store file in related, or base64 here? 
            // Current schema has images: string[]. Let's store as base64 string or skipped for now.
            // Ideally we upload to blob store. For now, let's keep it empty and just track metadata.
            manuals: [],
            symptoms: [],
            related_project_ids: [],
            created_at: new Date(),
            updated_at: new Date()
        });

        return { type: 'asset', id: Number(id), summary: `Asset "${data.name}" registered.` };
    },

    async ingestFile(file: File, mode: 'project' | 'inventory' | 'portfolio' = 'project'): Promise<any> {
        // --- MODE: INVENTORY ---
        if (mode === 'inventory') {
            const items = await AIService.analyzeInventory(file);
            const validItems = items.filter((i: any) => i.name && i.category);

            if (validItems.length > 0) {
                await db.inventory.bulkAdd(validItems);
                return { count: validItems.length, type: 'inventory' };
            }
            throw new Error("No valid inventory items found.");
        }

        // --- MODE: PORTFOLIO ---
        if (mode === 'portfolio') {
            const projects = await AIService.parsePortfolio(file);
            let count = 0;

            await db.transaction('rw', [db.projects], async () => {
                for (const pData of projects) {
                    if (!pData.title) continue;

                    const exists = await db.projects.where('title').equals(pData.title).first();
                    if (!exists) {
                        await db.projects.add({
                            ...pData,
                            title: pData.title,
                            status: pData.status || 'idea',
                            version: pData.version || '1.0',
                            created_at: new Date(),
                            updated_at: new Date(),
                            tags: pData.tags || [],
                            domains: pData.domains || [],
                            is_archived: false
                        } as any);
                        count++;
                    }
                }
            });
            return { count, type: 'portfolio' };
        }

        // 1. JSON Backup Restore
        if (file.name.endsWith('.json')) {
            const text = await file.text();
            const data = JSON.parse(text);
            if (data.title && data.status) {
                const { id: _unusedId, ...projectData } = data;
                // Check if project exists to prevent duplicates on restore? 
                // For simplified restore, we just add new. User can purge old.
                const newId = await db.projects.add({
                    ...projectData,
                    created_at: new Date(),
                    updated_at: new Date()
                });

                // Restore Sub-tables if present in JSON export
                // v46: Added Tasks, Documents, Production Items support for backups
                if (data.tasks && Array.isArray(data.tasks)) {
                    await db.project_tasks.bulkAdd(data.tasks.map((t: any) => ({ ...t, project_id: newId, id: undefined })));
                }
                if (data.documents && Array.isArray(data.documents)) {
                    await db.project_documents.bulkAdd(data.documents.map((d: any) => ({ ...d, project_id: newId, id: undefined })));
                }
                if (data.productionItems && Array.isArray(data.productionItems)) {
                    await db.project_production_items.bulkAdd(data.productionItems.map((p: any) => ({ ...p, project_id: newId, id: undefined })));
                }

                return newId;
            } else {
                throw new Error("Invalid Project JSON");
            }
        }
        // 2. AI Ingestion (PDF/Images/Text/MDBD)
        else {
            const data = await AIService.analyzeFile(file);

            // A. CHECK FOR EXISTING PROJECT
            // Match by Project Code OR Title (Case Insensitive)
            let existingId: number | undefined;

            if (data.project_code) {
                const p = await db.projects.where('project_code').equals(data.project_code).first();
                if (p) existingId = p.id;
            }
            if (!existingId && data.title) {
                const projects = await db.projects.toArray();
                const p = projects.find(proj => proj.title.toLowerCase() === data.title?.toLowerCase());
                if (p) existingId = p.id;
            }

            // Determine Color
            const labelColor = assignDefaultColor(data.category, data.domains?.[0]);

            // B. UPDATE EXISTING
            if (existingId) {
                const projectId = existingId;
                console.log(`Updating Existing Project: ${projectId}`);

                await db.transaction('rw', [db.projects, db.project_tasks, db.project_bom, db.logs, db.project_files], async () => {
                    // 1. Update Core Fields (Merge logic: Overwrite with new data if present)
                    const updatePayload: any = { ...data };
                    // Fix Date types
                    if (data.target_completion_date) {
                        updatePayload.target_completion_date = new Date(data.target_completion_date);
                    }

                    await db.projects.update(projectId, {
                        ...updatePayload, // Spreads most fields (specs, status, etc)
                        // Universal Data Merge
                        ...(data.specs_custom ? { universal_data: data.specs_custom } : {}),
                        // Domain Overwrite (Trust AI)
                        ...(data.domains ? { domains: data.domains } : {}),
                        updated_at: new Date(),
                    });

                    // 2. SMART MERGE: TASKS
                    if (data.tasks && data.tasks.length > 0) {
                        const existingTasks = await db.project_tasks.where({ project_id: projectId }).toArray();
                        const incomingTitles = new Set(data.tasks.map((t: any) => t.title));

                        // a. Update or Add
                        for (const newTask of data.tasks as any[]) {
                            const match = existingTasks.find(t => t.title === newTask.title);
                            if (match) {
                                // Update existing task
                                await db.project_tasks.update(match.id!, {
                                    priority: newTask.priority || match.priority,
                                    phase: newTask.phase || match.phase,
                                    estimated_time: newTask.estimated_time || match.estimated_time,
                                    // Don't revert 'completed' status unless explicitly checking logic? 
                                    // For now, let's keep status manual unless we want to force reset.
                                    // Use case: File says "Do X", X is done in DB. Keep done.
                                });
                            } else {
                                // Add new task
                                await db.project_tasks.add({
                                    project_id: projectId,
                                    title: newTask.title,
                                    status: 'pending',
                                    priority: newTask.priority || 3,
                                    phase: newTask.phase || 'Planning'
                                });
                            }
                        }

                        // b. PRUNE (Delete tasks not in file)
                        const tasksToDelete = existingTasks.filter(t => !incomingTitles.has(t.title));
                        if (tasksToDelete.length > 0) {
                            await db.project_tasks.bulkDelete(tasksToDelete.map(t => t.id!));
                        }
                    }

                    // 3. SMART MERGE: BOM
                    if (data.bom && data.bom.length > 0) {
                        const existingBom = await db.project_bom.where({ project_id: projectId }).toArray();
                        const incomingNames = new Set(data.bom.map((b: any) => b.name || b.part_name));

                        // a. Update or Add
                        for (const newPart of data.bom as any[]) {
                            const name = newPart.name || newPart.part_name || 'Part';
                            const match = existingBom.find(b => b.part_name === name);

                            if (match) {
                                await db.project_bom.update(match.id!, {
                                    quantity_required: newPart.quantity || match.quantity_required,
                                    est_unit_cost: newPart.est_unit_cost || match.est_unit_cost,
                                    status: newPart.status || match.status
                                });
                            } else {
                                await db.project_bom.add({
                                    project_id: projectId,
                                    part_name: name,
                                    quantity_required: newPart.quantity || 1,
                                    status: 'missing',
                                    est_unit_cost: newPart.est_unit_cost || 0
                                });
                            }
                        }

                        // b. PRUNE
                        const partsToDelete = existingBom.filter(b => !incomingNames.has(b.part_name));
                        if (partsToDelete.length > 0) {
                            await db.project_bom.bulkDelete(partsToDelete.map(b => b.id!));
                        }
                    }

                    // 4. SMART MERGE: DOCUMENTS (Manuscript)
                    if (data.documents && Array.isArray(data.documents)) {
                        const existingDocs = await db.project_documents.where({ project_id: projectId }).toArray();
                        for (const d of data.documents) {
                            const match = existingDocs.find(ed => ed.title === d.title);
                            if (match) {
                                await db.project_documents.update(match.id!, {
                                    content: d.content || match.content,
                                    status: d.status || match.status,
                                    type: d.type || match.type,
                                    updated_at: new Date()
                                });
                            } else {
                                await db.project_documents.add({
                                    project_id: projectId,
                                    title: d.title,
                                    content: d.content || '',
                                    type: d.type || 'chapter',
                                    status: d.status || 'draft',
                                    updated_at: new Date(),
                                    order: 0
                                });
                            }
                        }
                    }

                    // 5. SMART MERGE: PRODUCTION ITEMS
                    if (data.productionItems && Array.isArray(data.productionItems)) {
                        const existingItems = await db.project_production_items.where({ project_id: projectId }).toArray();
                        for (const p of data.productionItems) {
                            const match = existingItems.find(ei => ei.name === p.name);
                            if (match) {
                                await db.project_production_items.update(match.id!, {
                                    status: p.status || match.status,
                                    metadata: p.metadata || match.metadata,
                                    type: p.type || match.type
                                });
                            } else {
                                await db.project_production_items.add({
                                    project_id: projectId,
                                    name: p.name,
                                    type: p.type || 'default',
                                    status: p.status || 'active',
                                    metadata: p.metadata || {},
                                    order: 0
                                });
                            }
                        }
                    }

                    // 6. Log Update
                    await db.logs.add({
                        project_id: projectId,
                        version: data.version || 'v?',
                        date: new Date(),
                        summary: `Project Updated via Ingestion (${file.name})`,
                        type: 'auto'
                    });

                    // 7. Store File
                    await db.project_files.add({
                        project_id: projectId,
                        name: file.name,
                        type: file.type,
                        content: file,
                        created_at: new Date(),
                        extracted_metadata: data
                    });
                });

                return projectId;
            }

            // C. CREATE NEW (Fallback)
            else {
                // Consolidate domain-specific fields into universal_data
                const domainSpecificData = {
                    // Technical domains
                    ...(data.specs_technical && { specs_technical: data.specs_technical }),
                    ...(data.specs_performance && { specs_performance: data.specs_performance }),
                    ...(data.signal_chain && { signal_chain: data.signal_chain }),
                    ...(data.golden_voltages && { golden_voltages: data.golden_voltages }),
                    ...(data.specs_environment && { specs_environment: data.specs_environment }),
                    ...(data.design_philosophy && { design_philosophy: data.design_philosophy }),
                    // Creative domains
                    ...(data.creative_specs && { creative_specs: data.creative_specs }),
                    ...(data.milestones && { milestones: data.milestones }),
                    ...(data.deliverables && { deliverables: data.deliverables }),
                    // Research domains
                    ...(data.research_specs && { research_specs: data.research_specs }),
                    ...(data.literature_notes && { literature_notes: data.literature_notes }),
                    // Event domains
                    ...(data.event_specs && { event_specs: data.event_specs }),
                    ...(data.logistics && { logistics: data.logistics }),
                    // Personal domains
                    ...(data.goal_specs && { goal_specs: data.goal_specs }),
                    // Legacy MDBD map
                    ...(data.universal_map && { mdbd: data.universal_map }),
                };

                const newId = await db.projects.add({
                    title: data.title || file.name,
                    status: 'active',
                    version: data.version || '0.1.0',
                    priority: 3,
                    status_description: data.description,
                    role: data.role,
                    category: data.category,
                    intrusiveness: data.intrusiveness || 1,
                    tags: data.tags || [],
                    target_completion_date: data.target_completion_date ? new Date(data.target_completion_date) : undefined,
                    taxonomy_path: data.taxonomy_path,
                    golden_voltages: data.golden_voltages,
                    io_spec: data.io_spec || [],
                    design_philosophy: data.design_philosophy,
                    created_at: new Date(),
                    updated_at: new Date(),
                    is_archived: false,
                    label_color: labelColor,
                    // v16 Fields
                    project_code: data.project_code || '',
                    design_status: data.design_status || 'idea',
                    build_status: data.build_status || 'unbuilt',
                    exp_cv_usage: data.exp_cv_usage || '',
                    // v17 - Robustness
                    time_estimate_active: data.time_estimate_active || 0,
                    time_estimate_passive: data.time_estimate_passive || 0,
                    financial_budget: data.financial_budget || 0,
                    financial_spend: 0,
                    rationale: data.rationale || '',
                    risk_level: data.risk_level || 'low',
                    // v19 - Universal/Safety
                    hazards: data.hazards || [],
                    domains: data.domains || [],
                    specs_technical: data.specs_technical,
                    specs_performance: data.specs_performance,
                    market_context: data.market_context,
                    signal_chain: data.signal_chain,
                    specs_environment: data.specs_environment,

                    // v40 - Domain-Agnostic Universal Data
                    universal_data: { ...domainSpecificData, ...(data.specs_custom || {}) }
                });

                // Populate Sub-tables if data exists
                if (data.tasks) {
                    await db.project_tasks.bulkAdd(data.tasks.map((t: any) => ({
                        project_id: Number(newId),
                        title: t.title,
                        status: 'pending',
                        priority: t.priority || 3,
                        phase: t.phase || 'Planning',
                        created_at: new Date()
                    })));
                }
                if (data.bom) {
                    await db.project_bom.bulkAdd(data.bom.map((b: any) => ({
                        project_id: Number(newId),
                        part_name: b.name || b.part_name || 'Part',
                        quantity_required: b.quantity || 1,
                        status: 'missing',
                        est_unit_cost: b.est_unit_cost || 0
                    })));
                }
                if (data.initial_notebook_entry) {
                    await db.notebook.add({
                        project_id: Number(newId),
                        title: data.initial_notebook_entry.title,
                        content: data.initial_notebook_entry.content,
                        tags: data.initial_notebook_entry.tags || [],
                        date: new Date()
                    });
                }
                if (data.changelog_history && Array.isArray(data.changelog_history)) {
                    await db.logs.bulkAdd(data.changelog_history.map((c: any) => {
                        let parsedDate = new Date();
                        if (c.date) {
                            const d = new Date(c.date);
                            if (!isNaN(d.getTime())) parsedDate = d;
                        }
                        return {
                            project_id: Number(newId),
                            version: c.version || 'v1.0',
                            date: parsedDate,
                            summary: c.summary,
                            type: 'auto'
                        };
                    }));
                }

                // v46: Handle Documents (Manuscript)
                if (data.documents && Array.isArray(data.documents)) {
                    await db.project_documents.bulkAdd(data.documents.map((d: any) => ({
                        project_id: Number(newId),
                        title: d.title || 'Untitled Doc',
                        content: d.content || '',
                        type: d.type || 'chapter',
                        status: d.status || 'draft',
                        updated_at: new Date(),
                        order: d.order || 0
                    })));
                }

                // v46: Handle Production Items
                if (data.productionItems && Array.isArray(data.productionItems)) {
                    await db.project_production_items.bulkAdd(data.productionItems.map((p: any) => ({
                        project_id: Number(newId),
                        name: p.name || 'Untitled Item',
                        type: p.type || 'default',
                        status: p.status || 'active',
                        metadata: p.metadata || {},
                        order: p.order || 0
                    })));
                }

                // SAVE THE SOURCE FILE
                await db.project_files.add({
                    project_id: Number(newId),
                    name: file.name,
                    type: file.type,
                    content: file,
                    created_at: new Date(),
                    extracted_metadata: data
                });

                return newId;
            }
        }
    }
};
