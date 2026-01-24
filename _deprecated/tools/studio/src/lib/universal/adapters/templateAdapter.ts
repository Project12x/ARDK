/**
 * Template Adapter
 * Converts templates/blueprints to UniversalEntity format.
 * Templates are reusable patterns for creating new entities.
 */

import type { UniversalEntity } from '../types';

// ============================================================================
// TEMPLATE SCHEMA
// ============================================================================

export interface TemplateEntry {
    id: number;
    /** Template name */
    name: string;
    /** Description */
    description?: string;
    /** Entity type this template creates */
    entity_type: string;
    /** Template data/structure */
    template_data: Record<string, any>;
    /** Template category */
    category?: string;
    /** Is this a system template or custom */
    is_system?: boolean;
    /** Is this template active/available */
    is_active?: boolean;
    /** Usage count */
    usage_count?: number;
    /** Preview image */
    preview_url?: string;
    /** Tags */
    tags?: string[];
    /** Timestamps */
    created_at: Date;
    updated_at?: Date;
}

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalTemplate(template: TemplateEntry): UniversalEntity<TemplateEntry> {
    return {
        urn: `template:${template.id}`,
        id: template.id,
        type: 'template',
        title: template.name,
        subtitle: `${template.entity_type} template`,
        icon: 'FileTemplate',
        color: template.is_system ? '#a855f7' : '#06b6d4',
        status: template.is_active ? 'active' : 'inactive',
        tags: template.tags,
        thumbnail: template.preview_url,
        createdAt: template.created_at,
        updatedAt: template.updated_at,
        data: template,
        metadata: {
            entityType: template.entity_type,
            category: template.category,
            isSystem: template.is_system,
            usageCount: template.usage_count,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Template',
            statusStripe: template.is_system ? '#a855f7' : '#06b6d4',
            statusGlow: template.is_active,
            collapsible: true, // Collapsible for template details

            metaGrid: [
                { label: 'Type', value: template.entity_type },
                { label: 'Usage', value: template.usage_count || 0 },
                { label: 'Category', value: template.category || 'Custom' }
            ],

            nextAction: template.is_active ? {
                label: 'Use Template',
                icon: 'Copy'
            } : undefined
        }
    };
}

export function toUniversalTemplateBatch(templates: TemplateEntry[]): UniversalEntity<TemplateEntry>[] {
    return templates.map(toUniversalTemplate);
}
