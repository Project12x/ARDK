import { create, insertMultiple, search, type Orama, type Results } from '@orama/orama';
import { db } from './db';

// Generic Schema for universal search
const searchSchema = {
    id: 'string',
    type: 'string', // 'project' | 'inventory' | 'filament' | 'tool' | 'task' | 'note' | 'log'
    title: 'string',
    subtitle: 'string',
    url: 'string',
    keywords: 'string[]',
    content: 'string', // New: Full text content
} as const;

type SearchDoc = {
    id: string;
    type: string;
    title: string;
    subtitle: string;
    url: string;
    keywords: string[];
    content?: string;
};

class SearchService {
    private db: Orama<typeof searchSchema> | null = null;
    private isIndexing = false;

    async init() {
        if (this.db) return;
        this.db = await create({
            schema: searchSchema,
        });
    }

    async indexAll() {
        if (!this.db) await this.init();
        if (this.isIndexing) return;
        this.isIndexing = true;

        const docs: SearchDoc[] = [];

        // Import Registry dynamically to avoid cycle if any, though standard import is fine
        const { ALL_TABLES } = await import('./sync-registry');

        console.log(`[Search] Indexing ${ALL_TABLES.length} tables from Registry...`);

        // Iterate over ALL tables defined in the Registry
        for (const tableName of ALL_TABLES) {
            // @ts-ignore
            const table = db.table(tableName);
            if (!table) {
                console.warn(`[Search] Registry lists '${tableName}' but it is not in Dexie DB instance.`);
                continue;
            }

            const rows = await table.toArray();

            // Dispatch to specific handlers or Fallback
            switch (tableName) {
                case 'projects':
                    rows.forEach((p: any) => {
                        if (p.deleted_at || p.is_archived) return;
                        docs.push({
                            id: `proj-${p.id}`,
                            type: 'project',
                            title: p.title,
                            subtitle: p.project_code || p.status || 'Active',
                            url: `/projects/${p.id}`,
                            keywords: [p.status, p.category || '', p.kingdom || '', ...(p.tags || [])],
                            content: p.status_description || ''
                        });
                    });
                    break;

                case 'inventory':
                    rows.forEach((i: any) => {
                        let type = 'inventory';
                        let url = `/inventory?tab=${i.type || 'part'}`;
                        if (i.category === 'Filament') { type = 'filament'; url = '/inventory?tab=filament'; }
                        else if (i.type === 'tool') { type = 'tool'; url = '/inventory?tab=tool'; }

                        docs.push({
                            id: `inv-${i.id}`,
                            type,
                            title: i.name,
                            subtitle: `${i.quantity} ${i.units || ''} in ${i.location || 'Unknown'}`,
                            url,
                            keywords: [i.category, i.domain || '', i.properties?.material || '', i.properties?.color_hex || ''],
                            content: i.datasheet_url || ''
                        });
                    });
                    break;

                case 'project_tasks':
                    rows.forEach((t: any) => {
                        if (t.status === 'completed') return;
                        docs.push({
                            id: `task-${t.id}`,
                            type: 'task',
                            title: t.title,
                            subtitle: `Priority ${t.priority} • ${t.status}`,
                            url: `/projects/${t.project_id}`,
                            keywords: [t.status, t.phase || ''],
                            content: (t.blockers || []).join(' ')
                        });
                    });
                    break;

                case 'logs':
                    rows.forEach((l: any) => {
                        docs.push({
                            id: `log-${l.id}`,
                            type: 'log',
                            title: `Log ${l.version}`,
                            subtitle: l.summary,
                            url: `/projects/${l.project_id}`,
                            keywords: [l.type],
                            content: l.summary
                        });
                    });
                    break;

                // --- NEW FEATURES (Explicitly Handled) ---
                case 'routines':
                    rows.forEach((r: any) => {
                        docs.push({
                            id: `routine-${r.id}`,
                            type: 'routine',
                            title: r.title,
                            subtitle: `${r.frequency} • Next: ${new Date(r.next_due).toLocaleDateString()}`,
                            url: '/dashboard', // Eventually a routines page?
                            keywords: ['routine', 'maintenance', r.frequency],
                            content: r.description || ''
                        });
                    });
                    break;

                case 'goals':
                    rows.forEach((g: any) => {
                        docs.push({
                            id: `goal-${g.id}`,
                            type: 'goal',
                            title: g.title,
                            subtitle: `${g.status} • ${g.horizon}`,
                            url: `/goals/${g.id}`,
                            keywords: ['goal', g.horizon, g.status, ...(g.success_criteria || [])],
                            content: (g.motivation || '') + ' ' + (g.description || '') + ' ' + (g.success_criteria || []).join(' ')
                        });
                    });
                    break;

                case 'llm_instructions':
                    rows.forEach((i: any) => {
                        docs.push({
                            id: `prompt-${i.id}`,
                            type: 'prompt',
                            title: i.name,
                            subtitle: `System Prompt • ${i.category}`,
                            url: '/settings',
                            keywords: ['ai', 'prompt', i.category],
                            content: i.content.slice(0, 100)
                        });
                    });
                    break;

                case 'project_documents':
                    rows.forEach((d: any) => {
                        // Strip HTML for search content if possible, or just index raw
                        const cleanContent = d.content ? d.content.replace(/<[^>]*>/g, ' ') : '';
                        docs.push({
                            id: `doc-${d.id}`,
                            type: 'note',
                            title: d.title,
                            subtitle: `Manuscript • ${d.type}`,
                            url: `/projects/${d.project_id}`,
                            keywords: ['document', 'manuscript', d.type, d.status],
                            content: cleanContent.slice(0, 200)
                        });
                    });
                    break;

                case 'project_production_items':
                    rows.forEach((p: any) => {
                        docs.push({
                            id: `prod-${p.id}`,
                            type: 'task', // Use 'task' icon for now
                            title: p.name,
                            subtitle: `Production • ${p.type} • ${p.status}`,
                            url: `/projects/${p.project_id}`,
                            keywords: ['production', p.type, p.status, ...(p.metadata ? Object.values(p.metadata) : []) as string[]],
                            content: `Item ${p.name} in ${p.type}`
                        });
                    });
                    break;

                case 'songs':
                    rows.forEach((s: any) => {
                        docs.push({
                            id: `song-${s.id}`,
                            type: 'song',
                            title: s.title,
                            subtitle: `${s.status} • ${s.duration || ''}`,
                            url: `/songs/${s.id}`,
                            keywords: ['song', 'music', s.status, ...(s.tags || [])],
                            content: s.lyrics || ''
                        });
                    });
                    break;

                case 'albums':
                    rows.forEach((a: any) => {
                        docs.push({
                            id: `album-${a.id}`,
                            type: 'album',
                            title: a.title,
                            subtitle: `${a.status}`,
                            url: `/albums/${a.id}`,
                            keywords: ['album', 'music', a.status],
                            content: a.title
                        });
                    });
                    break;

                // --- UNIVERSAL FALLBACK (The "Futureproofer") ---
                default:
                    // Automatically index any table we haven't explicitly handled
                    // Heuristics: Look for title-like fields
                    rows.forEach((row: any) => {
                        const title = row.title || row.name || row.label || row.heading || `Item ${row.id}`;
                        const subtitle = row.subtitle || row.description || row.summary || row.status || row.category || row.type || tableName;
                        // Grab string properties for content index
                        const content = Object.values(row)
                            .filter(v => typeof v === 'string')
                            .join(' ')
                            .slice(0, 200);

                        docs.push({
                            id: `${tableName}-${row.id}`,
                            type: tableName, // Use table name as type
                            title: String(title),
                            subtitle: String(subtitle).slice(0, 50),
                            url: '/', // No specific URL known, go to home
                            keywords: [tableName],
                            content: content
                        });
                    });
                    break;
            }
        }

        // Clear and Re-insert
        this.db = await create({ schema: searchSchema });
        await insertMultiple(this.db, docs);

        this.isIndexing = false;
        console.log(`[Search] Indexed ${docs.length} total items across ${ALL_TABLES.length} tables.`);
    }

    async search(term: string): Promise<SearchDoc[]> {
        if (!this.db) await this.init();
        if (!term) return [];

        // Ensure index exists if searching before first index
        if (!this.db) return [];

        const results: Results<SearchDoc> = await search(this.db!, {
            term,
            properties: ['title', 'keywords', 'subtitle', 'content'], // Added content to search fields
            limit: 10,
            threshold: 0.2,
        });

        return results.hits.map(h => h.document);
    }
}

export const GlobalSearch = new SearchService();

import { useState, useCallback } from 'react';
import type { Project } from './db';

export function useProjectSearch(projects: Project[] | undefined) {
    const [searchResults, setSearchResults] = useState<Project[] | null>(null);
    const [isIndexing, setIsIndexing] = useState(false);

    const performSearch = useCallback(async (query: string) => {
        if (!query || !projects) {
            setSearchResults(null);
            return;
        }

        setIsIndexing(true);
        // Simulate async to keep API similar if we move to Orama later, 
        // but for now synchronous is fine, just wrapping in timeout to unblock UI
        setTimeout(() => {
            const lowerQuery = query.toLowerCase();
            const results = projects.filter(p => {
                const titleMatch = p.title.toLowerCase().includes(lowerQuery);
                const codeMatch = p.project_code?.toLowerCase().includes(lowerQuery);
                const statusMatch = p.status.toLowerCase().includes(lowerQuery);
                const tagMatch = p.tags?.some(t => t.toLowerCase().includes(lowerQuery));
                const catMatch = p.category?.toLowerCase().includes(lowerQuery);

                return titleMatch || codeMatch || statusMatch || tagMatch || catMatch;
            });
            setSearchResults(results);
            setIsIndexing(false);
        }, 10);
    }, [projects]);

    return { performSearch, searchResults, isIndexing };
}
