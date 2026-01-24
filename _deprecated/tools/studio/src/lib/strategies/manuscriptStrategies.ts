
import type { ExportStrategy } from '../../types/export';
import { db, type ProjectDocument } from '../db';
import { textToBlob } from '../../utils/exportTransformers';

// Helper to fetch documents
async function fetchManuscript(projectId: number): Promise<ProjectDocument[]> {
    return await db.project_documents
        .where('project_id').equals(projectId)
        .sortBy('order');
}

export const StandardManuscriptStrategy: ExportStrategy<ProjectDocument> = {
    id: 'manuscript-standard',
    name: 'Manuscript (Compiled)',
    description: 'Exports all chapters as a single document.',
    supportedFormats: [
        { id: 'markdown', label: 'Markdown', extension: 'md' },
        { id: 'json', label: 'JSON (Raw)', extension: 'json' }
    ],
    getData: (context: { projectId: number }) => fetchManuscript(context.projectId),

    transform: async (data, format) => {
        if (format === 'json') {
            return textToBlob(JSON.stringify(data, null, 2), 'application/json');
        }

        // Markdown Compilation
        const compiled = data.map(doc => {
            return `# ${doc.title}\n\n${doc.content}\n`;
        }).join('\n---\n\n');

        return textToBlob(compiled, 'text/markdown');
    }
};

export const PublisherManuscriptStrategy: ExportStrategy<ProjectDocument> = {
    id: 'manuscript-publisher',
    name: 'Publisher Pack',
    description: 'Formats for submission (Standard Manuscript Format).',
    supportedFormats: [
        { id: 'markdown', label: 'Markdown (Clean)', extension: 'md' }
    ],
    getData: (context: { projectId: number }) => fetchManuscript(context.projectId),

    // Placeholder for AI Enrichment (e.g., "Fix Grammar")
    enrichData: async (data) => {
        // In a real implementation, we would send chunks to LLM here
        // for "Proofreading". returning identity for now.
        return data;
    },

    transform: async (data, format) => {
        // Just standard markdown for now, but conceptual placeholder for different formatting
        const compiled = data.map(doc => {
            return `# ${doc.title.toUpperCase()}\n\n${doc.content}\n`;
        }).join('\n\n# ***\n\n'); // Scene break

        return textToBlob(compiled, 'text/markdown');
    }
};
