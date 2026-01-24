/**
 * Process Adapter
 * Converts processes/workflows to UniversalEntity format.
 * Processes are multi-step workflows, recipes, or procedures.
 */

import type { UniversalEntity } from '../types';

// ============================================================================
// PROCESS SCHEMA
// ============================================================================

export interface ProcessStep {
    id: number | string;
    title: string;
    description?: string;
    status: 'pending' | 'in_progress' | 'completed' | 'skipped';
    order: number;
    duration_estimate?: number; // minutes
    duration_actual?: number;
    assignee?: string;
    dependencies?: (number | string)[];
}

export interface ProcessEntry {
    id: number;
    /** Process name */
    name: string;
    /** Description */
    description?: string;
    /** Process steps */
    steps: ProcessStep[];
    /** Current step index */
    current_step?: number;
    /** Process status */
    status: 'draft' | 'active' | 'paused' | 'completed' | 'failed';
    /** Category */
    category?: string;
    /** Entity this process is for */
    parent_type?: string;
    parent_id?: number;
    /** Timestamps */
    started_at?: Date;
    completed_at?: Date;
    created_at: Date;
    updated_at?: Date;
}

// ============================================================================
// HELPERS
// ============================================================================

function calculateProcessProgress(process: ProcessEntry): number {
    if (!process.steps || process.steps.length === 0) return 0;
    const completed = process.steps.filter(s => s.status === 'completed').length;
    return Math.round((completed / process.steps.length) * 100);
}

function getProcessColor(status: ProcessEntry['status']): string {
    switch (status) {
        case 'active': return 'text-blue-500';
        case 'completed': return 'text-green-500';
        case 'paused': return 'text-yellow-500';
        case 'failed': return 'text-red-500';
        default: return 'text-gray-400';
    }
}

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalProcess(process: ProcessEntry): UniversalEntity<ProcessEntry> {
    const progress = calculateProcessProgress(process);
    const completedSteps = process.steps.filter(s => s.status === 'completed').length;

    return {
        urn: `process:${process.id}`,
        id: process.id,
        type: 'process',
        title: process.name,
        subtitle: `${completedSteps}/${process.steps.length} steps • ${progress}%`,
        icon: 'Workflow',
        color: getProcessColor(process.status),
        status: process.status,
        progress: progress,
        createdAt: process.created_at,
        updatedAt: process.updated_at,
        data: process,
        metadata: {
            stepCount: process.steps.length,
            completedSteps: completedSteps,
            currentStep: process.current_step,
            category: process.category,
            parentType: process.parent_type,
            parentId: process.parent_id,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Process',
            statusStripe: getProcessColorHex(process.status),
            statusGlow: process.status === 'active',
            collapsible: true,

            metaGrid: [
                { label: 'Step', value: `${(process.current_step || 0) + 1}/${process.steps.length}` },
                { label: 'Current', value: process.steps[process.current_step || 0]?.title || 'Finished' },
                { label: 'Status', value: process.status }
            ],

            ratings: [
                { label: 'Progress', value: progress, max: 100, color: getProcessColorHex(process.status) }
            ],

            nextAction: process.status === 'active' ? {
                label: 'Continue',
                subtitle: process.steps[process.current_step || 0]?.title
            } : undefined
        }
    };
}

function getProcessColorHex(status: string): string {
    switch (status) {
        case 'active': return '#3b82f6';
        case 'completed': return '#22c55e';
        case 'paused': return '#eab308';
        case 'failed': return '#ef4444';
        default: return '#9ca3af';
    }
}

export function toUniversalProcessBatch(processes: ProcessEntry[]): UniversalEntity<ProcessEntry>[] {
    return processes.map(toUniversalProcess);
}
