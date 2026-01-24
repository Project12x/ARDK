/**
 * Mock Data Generators for Phase 8 Universal Types
 * Used for testing in UniversalTestPage
 */

import type {
    ActivityEntry,
    CommentEntry,
    MetricEntry,
    RelationshipEntry,
    ProcessEntry,
    TemplateEntry,
    CollectionEntry,
    toUniversalProject,
    toUniversalTask
} from '../universal/adapters';
import type {
    Project,
    ProjectTask,
    InventoryItem,
    Asset,
    Goal,
    Song,
    InboxItem,
    PurchaseItem,
    Vendor,
    Reminder,
    GlobalNote,
    Log,
    EntityLink
} from '../db';

// ============================================================================
// MOCK GENERATORS
// ============================================================================

export function generateMockActivities(count: number = 5): ActivityEntry[] {
    const actions: ActivityEntry['action'][] = ['create', 'update', 'delete', 'link', 'complete', 'comment'];
    const entityTypes = ['project', 'task', 'goal', 'inventory'];

    return Array.from({ length: count }, (_, i) => ({
        id: 1000 + i,
        action: actions[i % actions.length],
        entity_type: entityTypes[i % entityTypes.length],
        entity_id: 100 + i,
        entity_title: `Sample ${entityTypes[i % entityTypes.length]} ${i + 1}`,
        actor: i % 2 === 0 ? 'User' : 'System',
        created_at: new Date(Date.now() - i * 3600000),
    }));
}

export function generateMockComments(count: number = 5): CommentEntry[] {
    const parentTypes = ['project', 'task', 'goal'];

    return Array.from({ length: count }, (_, i) => ({
        id: 2000 + i,
        parent_type: parentTypes[i % parentTypes.length],
        parent_id: 100 + i,
        content: `This is a sample comment ${i + 1}. It contains some useful information about the entity.`,
        author: i % 3 === 0 ? 'Alice' : i % 3 === 1 ? 'Bob' : 'Charlie',
        is_pinned: i === 0,
        reactions: i % 2 === 0 ? { '👍': 3, '❤️': 1 } : undefined,
        created_at: new Date(Date.now() - i * 7200000),
    }));
}

export function generateMockMetrics(count: number = 6): MetricEntry[] {
    const metrics = [
        { name: 'Active Projects', category: 'count' as const, value: 12, target: 15, trend: 'up' as const },
        { name: 'Tasks Completed', category: 'percentage' as const, value: 78, trend: 'up' as const },
        { name: 'Hours Logged', category: 'time' as const, value: 156, previous_value: 142, trend: 'up' as const },
        { name: 'Budget Used', category: 'currency' as const, value: 4500, target: 10000, trend: 'stable' as const },
        { name: 'Goals Progress', category: 'percentage' as const, value: 45, trend: 'down' as const },
        { name: 'Items In Stock', category: 'count' as const, value: 234, previous_value: 256, trend: 'down' as const },
    ];

    return metrics.slice(0, count).map((m, i) => ({
        id: 3000 + i,
        ...m,
        created_at: new Date(),
    }));
}

export function generateMockRelationships(count: number = 5): RelationshipEntry[] {
    const relationships: RelationshipEntry['relationship'][] = ['blocks', 'depends_on', 'related', 'supports', 'parent'];
    const entityTypes = ['project', 'task', 'goal'];

    return Array.from({ length: count }, (_, i) => ({
        id: 4000 + i,
        source_type: entityTypes[i % entityTypes.length],
        source_id: 100 + i,
        source_title: `Source ${entityTypes[i % entityTypes.length]} ${i + 1}`,
        target_type: entityTypes[(i + 1) % entityTypes.length],
        target_id: 200 + i,
        target_title: `Target ${entityTypes[(i + 1) % entityTypes.length]} ${i + 1}`,
        relationship: relationships[i % relationships.length],
        created_at: new Date(Date.now() - i * 86400000),
    }));
}

export function generateMockProcesses(count: number = 3): ProcessEntry[] {
    return [
        {
            id: 5000,
            name: 'Project Onboarding',
            description: 'Steps to set up a new project',
            status: 'active' as const,
            category: 'setup',
            steps: [
                { id: 1, title: 'Define scope', status: 'completed' as const, order: 1 },
                { id: 2, title: 'Create tasks', status: 'completed' as const, order: 2 },
                { id: 3, title: 'Assign team', status: 'in_progress' as const, order: 3 },
                { id: 4, title: 'Review kickoff', status: 'pending' as const, order: 4 },
            ],
            current_step: 2,
            created_at: new Date(),
        },
        {
            id: 5001,
            name: 'Build Pipeline',
            description: 'Hardware fabrication workflow',
            status: 'active' as const,
            category: 'manufacturing',
            steps: [
                { id: 1, title: 'Design', status: 'completed' as const, order: 1 },
                { id: 2, title: '3D Print', status: 'completed' as const, order: 2 },
                { id: 3, title: 'Assembly', status: 'in_progress' as const, order: 3 },
                { id: 4, title: 'Testing', status: 'pending' as const, order: 4 },
                { id: 5, title: 'QA Review', status: 'pending' as const, order: 5 },
            ],
            current_step: 2,
            created_at: new Date(),
        },
        {
            id: 5002,
            name: 'Content Release',
            description: 'Steps to publish new content',
            status: 'completed' as const,
            category: 'publishing',
            steps: [
                { id: 1, title: 'Write draft', status: 'completed' as const, order: 1 },
                { id: 2, title: 'Review', status: 'completed' as const, order: 2 },
                { id: 3, title: 'Publish', status: 'completed' as const, order: 3 },
            ],
            created_at: new Date(),
        },
    ].slice(0, count);
}

export function generateMockTemplates(count: number = 4): TemplateEntry[] {
    return [
        {
            id: 6000,
            name: 'Hardware Project',
            description: 'Template for electronics/mechanical projects',
            entity_type: 'project',
            template_data: { category: 'hardware', status: 'active' },
            category: 'project',
            is_system: true,
            usage_count: 12,
            created_at: new Date(),
        },
        {
            id: 6001,
            name: 'Software Sprint',
            description: 'Template for 2-week software sprints',
            entity_type: 'project',
            template_data: { category: 'software', duration: 14 },
            category: 'project',
            is_system: true,
            usage_count: 8,
            created_at: new Date(),
        },
        {
            id: 6002,
            name: 'Weekly Goals',
            description: 'Template for weekly goal setting',
            entity_type: 'goal',
            template_data: { level: 'weekly' },
            category: 'goal',
            is_system: false,
            usage_count: 25,
            created_at: new Date(),
        },
        {
            id: 6003,
            name: 'Bug Report',
            description: 'Template for reporting bugs',
            entity_type: 'task',
            template_data: { priority: 'high', tags: ['bug'] },
            category: 'task',
            is_system: false,
            usage_count: 5,
            created_at: new Date(),
        },
    ].slice(0, count);
}

export function generateMockCollections(count: number = 3): CollectionEntry[] {
    return [
        {
            id: 7000,
            name: 'Priority Projects',
            description: 'High-priority items for this quarter',
            category: 'folder' as const,
            is_pinned: true,
            members: [
                { entity_type: 'project', entity_id: 1, order: 1 },
                { entity_type: 'project', entity_id: 2, order: 2 },
                { entity_type: 'goal', entity_id: 1, order: 3 },
            ],
            created_at: new Date(),
        },
        {
            id: 7001,
            name: 'Music Playlist',
            description: 'Songs for the current session',
            category: 'playlist' as const,
            members: [
                { entity_type: 'song', entity_id: 1 },
                { entity_type: 'song', entity_id: 2 },
                { entity_type: 'song', entity_id: 3 },
            ],
            created_at: new Date(),
        },
        {
            id: 7002,
            name: 'Smart: Overdue Tasks',
            description: 'Auto-filtered overdue tasks',
            category: 'group' as const,
            is_smart: true,
            filter_rules: { status: 'pending', due_before: new Date() },
            members: [
                { entity_type: 'task', entity_id: 5 },
                { entity_type: 'task', entity_id: 8 },
            ],
            created_at: new Date(),
        },
    ].slice(0, count);
}

export function generateMockProjects(count: number = 3): Project[] {
    const statuses: Project['status'][] = ['active', 'on-hold', 'completed', 'someday'];
    const now = new Date();

    return Array.from({ length: count }, (_, i) => ({
        // ID not strictly needed for insert (autoincrement) but helpful for types
        title: `Mock Project ${i + 1}`,
        description: `Auto-generated mock project ${i + 1}`,
        status: statuses[i % statuses.length],
        version: '1.0.0',
        tags: ['mock', `tag-${i}`],
        priority: ((i % 5) + 1) as 1 | 2 | 3 | 4 | 5,
        created_at: now,
        updated_at: now,
        is_custom: false,
        tasks: [],
        category: 'mock',
        name: `Mock Project ${i + 1}`,
        slug: `mock-project-${i + 1}`,
        description_short: 'A generated mock project'
    } as unknown as Project));
}

export function generateMockTasks(projectId: number, count: number = 5): ProjectTask[] {
    const statuses: ProjectTask['status'][] = ['pending', 'in-progress', 'completed', 'blocked'];
    const now = new Date();

    return Array.from({ length: count }, (_, i) => ({
        project_id: projectId,
        title: `Mock Task ${i + 1} for Project ${projectId}`,
        status: statuses[i % statuses.length],
        priority: ((i % 5) + 1) as 1 | 2 | 3 | 4 | 5,
        created_at: now,
        is_completed: false
    } as unknown as ProjectTask));
}

export function generateMockInventory(count: number = 5): InventoryItem[] {
    const types = ['component', 'tool', 'material', 'equipment'];
    const locations = ['Lab', 'Warehouse', 'Office', 'Closet'];

    return Array.from({ length: count }, (_, i) => ({
        name: `Mock Item ${i + 1}`,
        category: types[i % types.length],
        domain: 'hardware',
        quantity: Math.floor(Math.random() * 100),
        location: locations[i % locations.length],
        units: 'pcs',
        type: types[i % types.length],
        mpn: `MPN-${1000 + i}`,
        manufacturer: 'MockMfg',
        barcode: `123456789${i}`
    } as unknown as InventoryItem));
}

export function generateMockAssets(count: number = 3): Asset[] {
    const statuses: Asset['status'][] = ['active', 'maintenance', 'retired', 'broken'];
    return Array.from({ length: count }, (_, i) => ({
        name: `Mock Asset ${i + 1}`,
        category: 'Electronics',
        status: statuses[i % statuses.length],
        related_project_ids: []
    } as unknown as Asset));
}

export function generateMockGoals(count: number = 3): Goal[] {
    const levels: Goal['level'][] = ['vision', 'year', 'quarter', 'objective'];
    const statuses: Goal['status'][] = ['active', 'achieved', 'paused'];

    return Array.from({ length: count }, (_, i) => ({
        title: `Mock Goal ${i + 1}`,
        level: levels[i % levels.length],
        status: statuses[i % statuses.length],
        priority: 3,
        created_at: new Date(),
        updated_at: new Date()
    } as unknown as Goal));
}

export function generateMockSongs(count: number = 3): Song[] {
    const statuses: Song['status'][] = ['draft', 'idea', 'demo', 'released'];
    return Array.from({ length: count }, (_, i) => ({
        title: `Mock Song ${i + 1}`,
        status: statuses[i % statuses.length],
        lyrics: 'La la la',
        duration: '3:30',
        tags: ['rock', 'mock'],
        created_at: new Date(),
        updated_at: new Date(),
        is_archived: false
    } as unknown as Song));
}

export function generateMockInbox(count: number = 4): InboxItem[] {
    const types: InboxItem['type'][] = ['idea', 'task', 'general'];
    return Array.from({ length: count }, (_, i) => ({
        content: `Inbox item ${i + 1}: Some random thought or task.`,
        type: types[i % types.length],
        created_at: new Date()
    } as unknown as InboxItem));
}

export function generateMockPurchases(count: number = 3): PurchaseItem[] {
    const statuses: PurchaseItem['status'][] = ['planned', 'ordered', 'arrived'];
    return Array.from({ length: count }, (_, i) => ({
        name: `Purchase Item ${i + 1}`,
        quantity_needed: 1,
        status: statuses[i % statuses.length],
        priority: 3,
        created_at: new Date(),
        updated_at: new Date()
    } as unknown as PurchaseItem));
}

export function generateMockVendors(count: number = 2): Vendor[] {
    return Array.from({ length: count }, (_, i) => ({
        name: `Mock Vendor ${i + 1}`,
        website: `https://vendor${i}.com`
    } as unknown as Vendor));
}

export function generateMockReminders(count: number = 3): Reminder[] {
    return Array.from({ length: count }, (_, i) => ({
        content: `Reminder ${i + 1}: Don't forget to test!`,
        is_completed: i % 2 === 0,
        priority: 3,
        created_at: new Date()
    } as unknown as Reminder));
}

export function generateMockGlobalNotes(count: number = 3): GlobalNote[] {
    return Array.from({ length: count }, (_, i) => ({
        title: `Note ${i + 1}`,
        content: `# Mock Note ${i + 1}\n\nThis is some mock content.`,
        category: 'General',
        created_at: new Date(),
        updated_at: new Date(),
        pinned: i === 0
    } as unknown as GlobalNote));
}

export function generateMockLogs(projectId: number, count: number = 5): Log[] {
    const types: Log['type'][] = ['manual', 'auto']; // approximations
    return Array.from({ length: count }, (_, i) => ({
        project_id: projectId,
        branch_id: 0,
        version: '1.0.0',
        date: new Date(),
        type: types[i % types.length] || 'manual',
    } as unknown as Log));
}

export function generateMockLinks(sourceId: number, targetId: number): EntityLink[] {
    return [
        {
            source_type: 'project',
            source_id: sourceId,
            target_type: 'task',
            target_id: targetId,
            relationship: 'relates_to',
            created_at: new Date()
        } as unknown as EntityLink
    ];
}
