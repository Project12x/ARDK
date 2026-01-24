
import { db } from './db';

export interface NeurolinkEntity {
    id: string; // e.g. "proj-1"
    label: string;
    type: string;
}

export class NeurolinkService {
    static async getAllEntities(): Promise<NeurolinkEntity[]> {
        const [projects, inventory, tasks, assets] = await Promise.all([
            db.projects.toArray(),
            db.inventory.toArray(),
            db.project_tasks.where('status').notEqual('completed').toArray(),
            db.assets.toArray()
        ]);

        const entities: NeurolinkEntity[] = [];

        projects.forEach(p => {
            if (!p.deleted_at && !p.is_archived) {
                entities.push({ id: `proj-${p.id}`, label: p.title, type: 'project' });
            }
        });

        inventory.forEach(i => entities.push({ id: `inv-${i.id}`, label: i.name, type: 'inventory' }));
        tasks.forEach(t => entities.push({ id: `task-${t.id}`, label: t.title, type: 'task' }));
        assets.forEach(a => entities.push({ id: `asset-${a.id}`, label: a.name, type: 'asset' }));

        return entities;
    }

    /**
     * Replaces known entity names in text with TipTap mention HTML
     */
    static async linkify(text: string): Promise<string> {
        if (!text || text.length < 5) return text;

        const entities = await this.getAllEntities();
        // Sort by length desc to match longest phrases first (e.g. "Flux Capacitor" before "Flux")
        entities.sort((a, b) => b.label.length - a.label.length);

        let newText = text;

        // Naive text replacement. 
        // CAUTION: If text contains HTML attributes, this might break them. 
        // Ideally we should parse HTML, but for this "Auto-Link" feature, assuming plain text or simple HTML content.
        // If content is HTML, we should only replace text nodes. 
        // Given complexity, we will attempt a regex replace but avoid matches inside HTML tags.

        for (const entity of entities) {
            // Skip very short words to avoid noise
            if (entity.label.length < 3) continue;

            const escLabel = entity.label.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

            // Regex to match the label but NOT inside HTML tags
            // Lookbehind is not fully supported in all environments, but we can try a simplified approach:
            // Match the text, and checks if it's already part of a mention.

            // Simple heuristic: If the text includes <span data-type="mention" ...>@Label</span>, skip it.
            // But we might be adding it now.

            // Regex: Match word boundary, label, word boundary.
            const regex = new RegExp(`(?<!@)\\b${escLabel}\\b`, 'gi');

            // The Mention extension syntax as rendered by Tiptap logic:
            // <span data-type="mention" class="..." data-id="..." data-label="...">@Label</span>

            const mentionHtml = `<span data-type="mention" class="bg-accent/20 text-accent px-1 py-0.5 rounded font-bold no-underline cursor-pointer border border-accent/30 text-xs align-middle hover:bg-accent/30 transition-colors" data-id="${entity.id}" data-label="${entity.label}">@${entity.label}</span>`;

            // Avoid double linking
            if (newText.includes(`data-label="${entity.label}"`)) continue;

            // Execute replacement
            newText = newText.replace(regex, () => {
                // If match is inside an HTML tag, don't replace.
                // This is hard with regex. 
                // For now, let's assume we are linking PLAIN TEXT content mostly, or content that isn't heavy on unrelated HTML attributes matching the name.
                return mentionHtml;
            });
        }
        return newText;
    }
    /**
     * Specialized linker for LLM output processing.
     * Takes raw text (e.g. from Gemini) and attempts to linkify it before it's even saved.
     */
    static async processLLMOutput(text: string): Promise<string> {
        // reuse same logic for now, but separated for future specific LLM handling (like stripping markdown code blocks first)
        return this.linkify(text);
    }
}
