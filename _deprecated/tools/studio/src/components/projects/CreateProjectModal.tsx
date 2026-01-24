import { useState, useEffect } from 'react';
import { createPortal } from 'react-dom';
import { toast } from 'sonner';
import { db, type Project } from '../../lib/db';
import { Button } from '../ui/Button';
import { Zap, BookTemplate, Check } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { BlueprintService, type Blueprint } from '../../lib/blueprints';

export function CreateProjectModal({ onClose }: { onClose: () => void }) {
    const navigate = useNavigate();
    const [title, setTitle] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const [selectedBlueprintId, setSelectedBlueprintId] = useState<string | number>('empty');

    // Load Blueprints
    const [availableBlueprints, setAvailableBlueprints] = useState<Blueprint[]>([]);

    useEffect(() => {
        BlueprintService.getAll().then(setAvailableBlueprints);
    }, []);

    const handleCreate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!title.trim()) return;

        try {
            setIsLoading(true);
            const blueprint = await BlueprintService.getBlueprint(selectedBlueprintId);

            // Create Project with all template fields
            const id = await db.projects.add({
                title: title.trim(),
                status: (blueprint?.status as Project['status']) || 'active',
                priority: blueprint?.priority || 3,
                created_at: new Date(),
                updated_at: new Date(),
                is_archived: false,
                version: '0.1.0',
                tags: blueprint?.tags || [],
                category: blueprint?.category !== 'Uncategorized' ? blueprint?.category : undefined,
                github_repo: blueprint?.github_repo,
                // Extended template fields
                kingdom: blueprint?.kingdom,
                phylum: blueprint?.phylum,
                taxonomy_path: blueprint?.taxonomy_path,
                domains: blueprint?.domains,
                label_color: blueprint?.label_color,
                time_estimate_active: blueprint?.time_estimate_active,
                time_estimate_passive: blueprint?.time_estimate_passive,
                financial_budget: blueprint?.financial_budget,
                total_theorized_hours: blueprint?.total_theorized_hours,
                design_status: blueprint?.design_status,
                build_status: blueprint?.build_status,
                risk_level: blueprint?.risk_level,
                hazards: blueprint?.hazards,
                external_links: blueprint?.external_links,
                io_spec: blueprint?.io_spec,
                design_philosophy: blueprint?.design_philosophy,
            });

            // Create Tasks from Blueprint
            if (blueprint && blueprint.defaultTasks.length > 0) {
                const tasks = blueprint.defaultTasks.map(t => ({
                    project_id: id as number,
                    title: t.title,
                    status: 'pending' as const, // Cast to literal
                    phase: t.phase,
                    priority: t.priority,
                    estimated_time: t.estimated_time
                }));
                await db.project_tasks.bulkAdd(tasks);
            }

            navigate(`/projects/${id}`);
            onClose();
        } catch (error) {
            console.error(error);
            toast.error("Failed to create project.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        createPortal(
            <div className="fixed inset-0 z-[9999] flex items-center justify-center bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
                <div className="bg-black border border-accent/50 p-6 w-full max-w-2xl shadow-[0_0_50px_rgba(0,0,0,0.5)] relative flex flex-col max-h-[90vh]">
                    <h2 className="text-xl font-black uppercase text-white mb-6 flex items-center gap-2">
                        <Zap className="text-accent" /> Initialize New Project
                    </h2>

                    <form onSubmit={handleCreate} className="space-y-6 flex-1 overflow-y-auto pr-2">
                        {/* Title Input */}
                        <div>
                            <label className="text-[10px] uppercase font-bold text-gray-500 mb-2 block">1. Designation (Title)</label>
                            <input
                                autoFocus
                                type="text"
                                className="w-full bg-white/5 border border-white/10 p-4 text-2xl font-bold text-white focus:border-accent outline-none transition-colors rounded-sm"
                                placeholder="PROJECT_OMEGA..."
                                value={title}
                                onChange={e => setTitle(e.target.value)}
                            />
                        </div>

                        {/* Blueprint Selection */}
                        <div>
                            <label className="text-[10px] uppercase font-bold text-gray-500 mb-3 flex items-center gap-2">
                                <BookTemplate size={12} /> 2. Select Blueprint (Template)
                            </label>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                                {availableBlueprints.map(bp => (
                                    <div
                                        key={bp.id}
                                        onClick={() => setSelectedBlueprintId(bp.id)}
                                        className={clsx(
                                            "cursor-pointer border p-3 rounded transition-all relative group",
                                            selectedBlueprintId === bp.id
                                                ? "bg-accent/10 border-accent"
                                                : "bg-white/5 border-white/5 hover:border-white/20 hover:bg-white/10"
                                        )}
                                    >
                                        <div className="flex justify-between items-start mb-1">
                                            <span className={clsx("font-bold text-sm uppercase", selectedBlueprintId === bp.id ? "text-accent" : "text-gray-300")}>
                                                {bp.name}
                                            </span>
                                            {selectedBlueprintId === bp.id && <Check size={16} className="text-accent" />}
                                        </div>
                                        <p className="text-[11px] text-gray-500 leading-tight mb-2 min-h-[2.5em]">{bp.description}</p>
                                        <div className="flex flex-wrap gap-2">
                                            <span className="text-[9px] uppercase bg-black/50 px-1.5 py-0.5 rounded text-gray-500 border border-white/5">
                                                {bp.defaultTasks.length} Tasks
                                            </span>
                                            {bp.category !== 'Uncategorized' && (
                                                <span className="text-[9px] uppercase bg-blue-900/20 text-blue-400 px-1.5 py-0.5 rounded border border-blue-500/20">
                                                    {bp.category}
                                                </span>
                                            )}
                                            {bp.tags && bp.tags.length > 0 && bp.tags.slice(0, 3).map(tag => (
                                                <span key={tag} className="text-[9px] uppercase bg-white/5 text-gray-400 px-1.5 py-0.5 rounded border border-white/5">
                                                    {tag}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    </form>

                    <div className="flex justify-end gap-3 pt-6 border-t border-white/10 mt-6">
                        <Button type="button" variant="ghost" onClick={onClose}>CANCEL</Button>
                        <Button type="submit" variant="primary" disabled={!title.trim() || isLoading} onClick={handleCreate}>
                            {isLoading ? 'INITIALIZING...' : 'INITIALIZE NODE'}
                        </Button>
                    </div>
                </div>
            </div>,
            document.body
        )
    );
}
