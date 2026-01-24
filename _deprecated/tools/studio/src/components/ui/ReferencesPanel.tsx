import { useState, useEffect, useCallback } from 'react';
import { db } from '../../lib/db';
import { Link } from 'react-router-dom';
import {
    LinkIcon,
    FolderOpen,
    Package,
    FileText,
    Wrench,
    ChevronDown,
    ChevronRight,
    Monitor,
    ClipboardList
} from 'lucide-react';

interface Reference {
    type: 'project' | 'inventory' | 'asset' | 'note' | 'task' | 'bom';
    id: number;
    title: string;
    subtitle?: string;
    link: string;
}

interface ReferencesPanelProps {
    entityType: 'project' | 'inventory' | 'asset' | 'note' | 'task';
    entityId: number;
}

// Icons for each reference type
const typeIcons = {
    project: FolderOpen,
    inventory: Package,
    asset: Monitor,
    note: FileText,
    task: ClipboardList,
    bom: Wrench,
};

const typeLabels = {
    project: 'Projects',
    inventory: 'Inventory',
    asset: 'Assets',
    note: 'Notes',
    task: 'Tasks',
    bom: 'Bills of Materials',
};

export function ReferencesPanel({ entityType, entityId }: ReferencesPanelProps) {
    const [references, setReferences] = useState<Reference[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isExpanded, setIsExpanded] = useState(true);

    const findReferences = useCallback(async () => {
        setIsLoading(true);
        const refs: Reference[] = [];

        try {
            if (entityType === 'asset') {
                // Find projects that reference this asset (via linked_asset_id)
                const projectsWithAsset = await db.projects
                    .filter(p => p.linked_asset_id === entityId)
                    .toArray();
                for (const p of projectsWithAsset) {
                    refs.push({
                        type: 'project',
                        id: p.id!,
                        title: p.title,
                        subtitle: 'Linked asset',
                        link: `/projects/${p.id}`
                    });
                }

                // Find notebook entries mentioning this asset
                const allNotes = await db.notebook.toArray();
                for (const note of allNotes) {
                    if (note.content?.includes(`data-id="${entityId}"`) &&
                        note.content?.includes('data-type="asset"')) {
                        const project = await db.projects.get(note.project_id);
                        refs.push({
                            type: 'note',
                            id: note.id!,
                            title: note.title || 'Untitled Note',
                            subtitle: project?.title || `Project #${note.project_id}`,
                            link: `/projects/${note.project_id}`
                        });
                    }
                }
            } else if (entityType === 'inventory') {
                // Find BOMs that use this inventory item
                const bomsWithItem = await db.project_bom
                    .filter(b => b.inventory_item_id === entityId)
                    .toArray();
                for (const bom of bomsWithItem) {
                    const project = await db.projects.get(bom.project_id);
                    if (project) {
                        refs.push({
                            type: 'bom',
                            id: bom.id!,
                            title: project.title,
                            subtitle: `${bom.quantity_required}x ${bom.part_name}`,
                            link: `/projects/${bom.project_id}`
                        });
                    }
                }

                // Find notebook entries mentioning this inventory item
                const allNotesInv = await db.notebook.toArray();
                for (const note of allNotesInv) {
                    if (note.content?.includes(`data-id="${entityId}"`) &&
                        note.content?.includes('data-type="inventory"')) {
                        const project = await db.projects.get(note.project_id);
                        refs.push({
                            type: 'note',
                            id: note.id!,
                            title: note.title || 'Untitled Note',
                            subtitle: project?.title,
                            link: `/projects/${note.project_id}`
                        });
                    }
                }
            } else if (entityType === 'project') {
                // Find projects that depend on this one (upstream_dependencies)
                const dependentProjects = await db.projects
                    .filter(p => p.upstream_dependencies?.includes(entityId) ?? false)
                    .toArray();
                for (const p of dependentProjects) {
                    refs.push({
                        type: 'project',
                        id: p.id!,
                        title: p.title,
                        subtitle: 'Depends on this project',
                        link: `/projects/${p.id}`
                    });
                }

                // Find projects that have this as related
                const relatedProjects = await db.projects
                    .filter(p => p.related_projects?.includes(entityId) ?? false)
                    .toArray();
                for (const p of relatedProjects) {
                    if (!dependentProjects.find(dp => dp.id === p.id)) {
                        refs.push({
                            type: 'project',
                            id: p.id!,
                            title: p.title,
                            subtitle: 'Related project',
                            link: `/projects/${p.id}`
                        });
                    }
                }

                // Find notebook entries mentioning this project
                const allNotesProj = await db.notebook.toArray();
                for (const note of allNotesProj) {
                    if (note.project_id !== entityId &&
                        note.content?.includes(`data-id="${entityId}"`) &&
                        note.content?.includes('data-type="project"')) {
                        const project = await db.projects.get(note.project_id);
                        refs.push({
                            type: 'note',
                            id: note.id!,
                            title: note.title || 'Untitled Note',
                            subtitle: project?.title,
                            link: `/projects/${note.project_id}`
                        });
                    }
                }
            } else if (entityType === 'task') {
                // Find tasks that depend on this one
                const dependentTasks = await db.project_tasks
                    .filter(t => t.upstream_task_ids?.includes(entityId) ?? false)
                    .toArray();
                for (const t of dependentTasks) {
                    const project = await db.projects.get(t.project_id);
                    refs.push({
                        type: 'task',
                        id: t.id!,
                        title: t.title,
                        subtitle: project?.title,
                        link: `/projects/${t.project_id}`
                    });
                }
            }
        } catch (e) {
            console.error('Error finding references:', e);
        }

        setReferences(refs);
        setIsLoading(false);
    }, [entityType, entityId]);

    useEffect(() => {
        findReferences();
    }, [findReferences]);

    // Group references by type
    const groupedRefs = references.reduce((acc, ref) => {
        if (!acc[ref.type]) acc[ref.type] = [];
        acc[ref.type].push(ref);
        return acc;
    }, {} as Record<string, Reference[]>);

    if (isLoading) {
        return (
            <div className="border border-white/10 rounded-lg p-4 bg-black/20">
                <div className="flex items-center gap-2 text-gray-500 text-sm">
                    <LinkIcon size={14} className="animate-pulse" />
                    <span>Finding references...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="border border-white/10 rounded-lg bg-black/20 overflow-hidden">
            {/* Header */}
            <button
                onClick={() => setIsExpanded(!isExpanded)}
                className="w-full px-4 py-3 flex items-center justify-between hover:bg-white/5 transition-colors"
            >
                <div className="flex items-center gap-2">
                    <LinkIcon size={14} className="text-accent" />
                    <span className="text-xs font-bold uppercase tracking-wider text-gray-400">
                        References
                    </span>
                    {references.length > 0 && (
                        <span className="px-1.5 py-0.5 text-[10px] bg-accent/20 text-accent rounded-full">
                            {references.length}
                        </span>
                    )}
                </div>
                {isExpanded ? <ChevronDown size={14} className="text-gray-500" /> : <ChevronRight size={14} className="text-gray-500" />}
            </button>

            {/* Content */}
            {isExpanded && (
                <div className="px-4 pb-4">
                    {references.length === 0 ? (
                        <div className="text-center py-6 text-gray-600">
                            <LinkIcon size={24} className="mx-auto mb-2 opacity-30" />
                            <p className="text-xs">No references found</p>
                            <p className="text-[10px] text-gray-700 mt-1">
                                This {entityType} isn&apos;t linked from anywhere else yet.
                            </p>
                        </div>
                    ) : (
                        <div className="space-y-4">
                            {Object.entries(groupedRefs).map(([type, refs]) => {
                                const Icon = typeIcons[type as keyof typeof typeIcons] || LinkIcon;
                                return (
                                    <div key={type}>
                                        <div className="flex items-center gap-2 mb-2">
                                            <Icon size={12} className="text-gray-500" />
                                            <span className="text-[10px] uppercase font-bold text-gray-500">
                                                {typeLabels[type as keyof typeof typeLabels] || type} ({refs.length})
                                            </span>
                                        </div>
                                        <div className="space-y-1 pl-4">
                                            {refs.map(ref => (
                                                <Link
                                                    key={`${ref.type}-${ref.id}`}
                                                    to={ref.link}
                                                    className="block p-2 rounded hover:bg-white/5 transition-colors group"
                                                >
                                                    <div className="text-sm text-white group-hover:text-accent transition-colors truncate">
                                                        {ref.title}
                                                    </div>
                                                    {ref.subtitle && (
                                                        <div className="text-[10px] text-gray-600 truncate">
                                                            {ref.subtitle}
                                                        </div>
                                                    )}
                                                </Link>
                                            ))}
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
