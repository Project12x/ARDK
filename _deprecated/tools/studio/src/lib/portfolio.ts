import { db, type Project } from './db';

export class PortfolioService {

    /**
     * Generates a Comprehensive Master Index from the current DB state.
     * Includes Goals, Projects (Grouped), Assets, and Music.
     */
    static async generateMasterIndex(): Promise<string> {
        const [projects, goals, assets, songs] = await Promise.all([
            db.projects.toArray(),
            db.goals.toArray(),
            db.assets.toArray(),
            db.songs.toArray()
        ]);

        const active = projects.filter(p => !p.is_archived && p.status !== 'legacy' && p.status !== 'rnd_long');
        const legacy = projects.filter(p => p.status === 'legacy');

        // Group Active by Domain/Kingdom
        const grouped: Record<string, Project[]> = {};
        active.forEach(p => {
            const key = p.kingdom || (p.domains && p.domains[0]) || 'Uncategorized';
            if (!grouped[key]) grouped[key] = [];
            grouped[key].push(p);
        });

        let text = `# Project Portfolio Master Index\n` +
            `> Generated: ${new Date().toLocaleDateString()} | System: WorkshopOS\n\n`;

        // 1. HIGH LEVEL STRATEGY
        if (goals.length > 0) {
            text += `## 1.0 GOALS & STRATEGY\n------------------------------------------------------------\n`;
            const activeGoals = goals.filter(g => g.status === 'active');
            activeGoals.forEach(g => {
                text += `- **[${g.level?.toUpperCase()}]** ${g.title} (Target: ${g.target_date?.toLocaleDateString() || 'Ongoing'})\n`;
            });
            text += `\n`;
        }

        // 2. ACTIVE PROJECTS
        text += `## 2.0 ACTIVE PROJECTS\n------------------------------------------------------------\n`;
        for (const [domain, list] of Object.entries(grouped)) {
            if (list.length === 0) continue;
            text += `\n### 2.${domain.substring(0, 3).toUpperCase()} - ${domain}\n`;

            list.forEach(p => {
                text += `#### ${p.title} [${p.project_code || 'ID'}]\n`;
                text += `- **Status**: ${p.status.toUpperCase()} (${p.design_status || ''}/${p.build_status || ''})\n`;
                text += `- **Risk**: ${p.risk_level || 'Unknown'}\n`;
                if (p.next_step) text += `- **Next**: ${p.next_step}\n`;
                if (p.specs_custom) {
                    text += `- **Specs**: ${JSON.stringify(p.specs_custom)}\n`;
                }
                text += `\n`;
            });
        }

        // 3. ASSET REGISTRY (High Value / Tools)
        if (assets.length > 0) {
            text += `\n## 3.0 ASSET REGISTRY\n------------------------------------------------------------\n`;
            const highValue = assets.filter(a => (a.value && a.value > 500) || a.category === 'computer');
            text += `*High Value & Critical Infrastructure*\n\n`;
            highValue.forEach(a => {
                text += `- **${a.name}** (${a.make} ${a.model || ''}) - $${a.value}\n`;
                if (a.specs_computer) text += `  - ${a.specs_computer.cpu} / ${a.specs_computer.gpu}\n`;
            });
        }

        // 4. CREATIVE OUTPUT (Music)
        if (songs.length > 0) {
            text += `\n## 4.0 DISCOGRAPHY / SONGS\n------------------------------------------------------------\n`;
            songs.forEach(s => {
                text += `- **${s.title}** [${s.key || '?'}, ${s.bpm || '?'} BPM] (${s.status})\n`;
            });
        }

        text += `\n## 5.0 LEGACY ARCHIVE\n------------------------------------------------------------\n`;
        text += `Total Archived: ${legacy.length} items.\n`;

        return text;
    }

    /**
     * Smartly merges new data into an existing project.
     */
    static mergeProject(existing: Project, updates: Partial<Project>): Partial<Project> {
        const result: any = { ...updates, updated_at: new Date() };

        // 1. Status: Prefer new if valid, else keep old
        if (!updates.status) delete result.status;

        // 2. Tags: Union
        if (updates.tags && updates.tags.length > 0) {
            const mergedTags = new Set([...(existing.tags || []), ...updates.tags]);
            result.tags = Array.from(mergedTags);
        }

        // 3. Hazards: Replace or Union? Union is safer for safety warnings.
        if (updates.hazards && updates.hazards.length > 0) {
            const mergedHazards = new Set([...(existing.hazards || []), ...updates.hazards]);
            result.hazards = Array.from(mergedHazards);
        }

        // 4. Domains: Union
        if (updates.domains && updates.domains.length > 0) {
            const mergedDomains = new Set([...(existing.domains || []), ...updates.domains]);
            result.domains = Array.from(mergedDomains);
        }

        // 5. Specs (JSON): Leaf Merge
        if (updates.specs_technical) {
            result.specs_technical = { ...(existing.specs_technical || {}), ...updates.specs_technical };
        }
        if (updates.specs_environment) {
            result.specs_environment = { ...(existing.specs_environment || {}), ...updates.specs_environment };
        }
        if (updates.specs_performance) {
            result.specs_performance = { ...(existing.specs_performance || {}), ...updates.specs_performance };
        }
        if (updates.market_context) {
            result.market_context = { ...(existing.market_context || {}), ...updates.market_context };
        }
        if (updates.signal_chain) {
            result.signal_chain = { ...(existing.signal_chain || {}), ...updates.signal_chain };
        }

        // 6. Safety Data (v37): Overwrite if provided, or merge hazards
        if (updates.safety_data) {
            // Logic: New extraction might be better. Or should we merge?
            // Let's assume Portfolio update is authoritative for now.
            result.safety_data = updates.safety_data;
        }

        return result;
    }

    /**
     * Bulk Ingests extracted project data.
     * Implements "Smart Merge": Updates if ID match, creates if new.
     */
    static async syncPortfolio(extractedProjects: Partial<Project>[]): Promise<{ created: number, updated: number, errors: number }> {
        let created = 0;
        let updated = 0;
        let errors = 0;

        for (const p of extractedProjects) {
            try {
                // Try to find existing project by Code or Title
                let existing: Project | undefined;
                let projectId: number | undefined;

                if (p.project_code) {
                    existing = await db.projects.where('project_code').equals(p.project_code).first();
                }

                if (!existing && p.title) {
                    existing = await db.projects.where('title').equals(p.title).first();
                }

                if (existing) {
                    // Smart Merge
                    projectId = existing.id!;
                    const updates = PortfolioService.mergeProject(existing, p);
                    await db.projects.update(projectId, updates);
                    updated++;
                } else {
                    // Create New
                    projectId = await db.projects.add({
                        title: p.title || 'Untitled Project',
                        status: (p.status?.toLowerCase() as any) || 'active',
                        version: 'v0.0.1',
                        date: new Date(),
                        updated_at: new Date(),
                        created_at: new Date(), // Required
                        project_code: p.project_code,
                        role: p.role,
                        description: p.status_description || '',
                        status_description: p.status_description || '',
                        design_status: p.design_status as any,
                        build_status: p.build_status as any,
                        exp_cv_usage: p.exp_cv_usage,
                        tags: p.tags || [],
                        type: 'manual',
                        // Defaults
                        intrusiveness: 1,
                        priority: 3,
                        domains: [],
                    } as Project);
                    created++;
                }

                // 2. Add New Tasks (If provided and project active/new)
                const data = p as any;
                if (projectId && data.tasks && Array.isArray(data.tasks)) {
                    const newTasks = data.tasks.map((t: string) => ({
                        project_id: projectId!,
                        title: (t as any).title || t,
                        status: 'pending',
                        priority: 3,
                        created_at: new Date(),
                        // v37
                        energy_level: (t as any).energy_level || 'medium',
                        sensory_load: (t as any).sensory_load || []
                    }));
                    if (newTasks.length > 0) {
                        await db.project_tasks.bulkAdd(newTasks);
                    }
                }

                // 3. Add New BOM Items
                if (projectId && data.bom && Array.isArray(data.bom)) {
                    const newBom = data.bom.map((b: string) => ({
                        project_id: projectId!,
                        part_name: b,
                        status: 'missing',
                        quantity_required: 1 // Default
                    }));
                    if (newBom.length > 0) {
                        await db.project_bom.bulkAdd(newBom);
                    }
                }

            } catch (e) {
                console.error("Sync Error for:", p, e);
                errors++;
            }
        }
        return { created, updated, errors };
    }
}
