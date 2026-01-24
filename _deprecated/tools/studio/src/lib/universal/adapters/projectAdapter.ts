/**
 * Project Entity Adapter
 * Transforms raw DB Project objects into UniversalEntity<Project> with zero data loss.
 */

import type { Project, ProjectTask, ProjectFile, ProjectBOM, EntityLink } from '../../db';
import type { UniversalEntity, UniversalFile, UniversalAction } from '../types';

// Related data that can be fetched and attached
export interface ProjectRelatedData {
    tasks?: ProjectTask[];
    files?: ProjectFile[];
    bom?: ProjectBOM[];
    links?: EntityLink[];
}

/**
 * Convert a raw Project to a UniversalEntity<Project>
 * Preserves full data fidelity in the `data` payload while extracting
 * common fields for universal display.
 */
export function toUniversalProject(
    project: Project,
    related?: ProjectRelatedData
): UniversalEntity<Project> {
    return {
        // Core Identity
        urn: `project:${project.id}`,
        id: project.id!,
        type: 'project',

        // Presentation
        title: project.title,
        subtitle: project.project_code || project.status,
        icon: 'Folder', // Default icon, can be overridden based on category
        color: project.label_color,
        status: project.status,
        tags: project.tags || [],
        createdAt: project.created_at,
        updatedAt: project.updated_at,

        // Full Fidelity Payload
        data: project,

        // Extended Fields
        progress: calculateProgress(project, related?.tasks),
        links: related?.links,
        relatedData: {
            tasks: related?.tasks || [],
            bom: related?.bom || [],
        },
        metadata: {
            specs_technical: project.specs_technical,
            specs_performance: project.specs_performance,
            specs_environment: project.specs_environment,
            safety_data: project.safety_data,
            signal_chain: project.signal_chain,
            market_context: project.market_context,
            universal_data: project.universal_data,
        },
        thumbnail: project.image_url,
        files: mapProjectFiles(related?.files),
        // Actions can be populated by the consuming component
        actions: undefined,

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Project',
            backgroundImage: project.image_url,
            statusStripe: getStatusColor(project.status),
            statusGlow: project.status === 'active' || project.status === 'in-progress',
            collapsible: true,
            defaultCollapsed: project.status === 'completed' || project.status === 'archived' || project.status === 'on_hold',

            metaGrid: [
                { label: 'Code', value: project.project_code || 'N/A' },
                { label: 'Priority', value: project.priority || 'Normal' },
                { label: 'Deadline', value: project.target_completion_date ? new Date(project.target_completion_date).toLocaleDateString() : 'None' }
            ].filter(item => item.value !== 'N/A' && item.value !== 'None'),

            ratings: [
                { label: 'Progress', value: calculateProgress(project, related?.tasks), max: 100, color: '#10b981' }
            ]
        }
    };
}

/**
 * Helper to map status to color hex
 */
function getStatusColor(status: string): string {
    switch (status) {
        case 'active': return '#10b981'; // Green
        case 'in-progress': return '#3b82f6'; // Blue
        case 'planning': return '#f59e0b'; // Amber
        case 'on_hold': return '#f43f5e'; // Rose
        case 'completed': return '#8b5cf6'; // Violet
        case 'archived': return '#64748b'; // Slate
        default: return '#94a3b8';
    }
}

/**
 * Calculate completion percentage from tasks.
 */
function calculateProgress(project: Project, tasks?: ProjectTask[]): number {
    if (!tasks || tasks.length === 0) return 0;
    const completed = tasks.filter(t => t.status === 'completed').length;
    return Math.round((completed / tasks.length) * 100);
}

/**
 * Map ProjectFile[] to UniversalFile[] for standardized rendering.
 */
function mapProjectFiles(files?: ProjectFile[]): UniversalFile[] | undefined {
    if (!files || files.length === 0) return undefined;

    return files.map(file => {
        const fileType = getFileType(file.type);
        return {
            id: file.id!,
            name: file.name,
            type: fileType,
            mimeType: file.type,
            // Size and URL require blob handling, placeholder for now
            size: undefined,
            url: undefined, // Would be URL.createObjectURL(file.content) if needed
            thumbnailUrl: fileType === 'image' ? undefined : undefined, // Can generate thumbnail
            createdAt: file.created_at,
            metadata: file.extracted_metadata,
        };
    });
}

/**
 * Determine UniversalFile type from MIME type string.
 */
function getFileType(mimeType: string): UniversalFile['type'] {
    if (mimeType.startsWith('image/')) return 'image';
    if (mimeType.startsWith('video/')) return 'video';
    if (mimeType.startsWith('audio/')) return 'audio';
    if (mimeType.includes('zip') || mimeType.includes('tar') || mimeType.includes('rar')) return 'archive';
    if (mimeType.includes('pdf') || mimeType.includes('document') || mimeType.includes('text')) return 'document';
    return 'other';
}
