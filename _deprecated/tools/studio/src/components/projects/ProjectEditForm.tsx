import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { toast } from 'sonner';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { Button } from '../ui/Button';
import { X, Save, ExternalLink, Box, List, Calendar, Layers, Link as LinkIcon, Settings, Github } from 'lucide-react';
import { db } from '../../lib/db';
import type { Project } from '../../lib/db';
import { safeDateStr } from '../../lib/utils';
import { ProjectSchema, type ProjectFormData } from '../../lib/schemas';

export function ProjectEditForm({
    project,
    onClose,
    className
}: {
    project: Project;
    onClose: () => void;
    className?: string;
}) {
    const navigate = useNavigate();
    const [section, setSection] = React.useState<'general' | 'details' | 'planning' | 'taxonomy' | 'assets'>('general');

    const { register, handleSubmit, watch, formState: { errors } } = useForm<any>({
        resolver: zodResolver(ProjectSchema),
        defaultValues: {
            title: project.title,
            status: project.status,
            priority: project.priority,
            intrusiveness: project.intrusiveness,
            project_code: project.project_code || '',
            target_completion_date: project.target_completion_date ? safeDateStr(project.target_completion_date) : undefined,
            total_theorized_hours: project.total_theorized_hours,
            time_estimate_active: project.time_estimate_active,
            risk_level: project.risk_level || 'low',
            // Extended Fields
            rationale: project.rationale || '',
            status_description: project.status_description || '',
            tags: project.tags?.join(', ') || '',
            category: project.category || '',
            kingdom: project.kingdom || '',
            phylum: project.phylum || '',
            image_url: project.image_url || '',
            github_repo: project.github_repo || '',
            external_links: project.external_links || []
        }
    });

    const onSubmit = async (data: ProjectFormData) => {
        // Handle tags string to array conversion manually if needed, 
        // though Zod schema transform 'tags' usually handles it.
        // But useForm might return string if input is text.
        // We rely on Zod transform or pre-process? 
        // Zod schema: tags: z.union([string, array]).transform(...)
        // So passing string is fine!

        await db.projects.update(project.id!, {
            ...data,
            updated_at: new Date()
        });
        toast.success('Project updated');
        onClose();
    };

    const sections = [
        { id: 'general', label: 'General', icon: <Box size={12} /> },
        { id: 'details', label: 'Details', icon: <List size={12} /> },
        { id: 'planning', label: 'Planning', icon: <Calendar size={12} /> },
        { id: 'taxonomy', label: 'Taxonomy', icon: <Layers size={12} /> },
        { id: 'assets', label: 'Assets', icon: <LinkIcon size={12} /> },
    ];

    return (
        <div className={clsx("border border-accent/20 bg-black/95 backdrop-blur-xl p-0 flex flex-col shadow-2xl z-20 relative animate-in fade-in zoom-in-95 duration-200 rounded-lg overflow-hidden h-full max-h-[600px]", className)} onClick={e => e.stopPropagation()}>
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col h-full">

                {/* Header */}
                <div className="flex justify-between items-center border-b border-white/10 p-3 bg-white/5">
                    <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded bg-accent/20 flex items-center justify-center text-accent">
                            <Settings size={16} />
                        </div>
                        <div>
                            <div className="text-[10px] text-gray-400 font-mono uppercase tracking-wider">Editing Project</div>
                            <div className="font-bold text-white text-sm">{project.title}</div>
                        </div>
                    </div>
                    <Button type="button" variant="ghost" size="sm" onClick={onClose}><X size={16} /></Button>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 p-2 border-b border-white/10 bg-black/40 overflow-x-auto">
                    {sections.map(s => (
                        <button
                            key={s.id}
                            type="button"
                            onClick={() => setSection(s.id as any)}
                            className={clsx(
                                "flex items-center gap-1.5 px-3 py-1.5 rounded text-[10px] font-bold uppercase tracking-wider transition-colors",
                                section === s.id ? "bg-accent text-black" : "text-gray-500 hover:text-white hover:bg-white/5"
                            )}
                        >
                            {s.icon} {s.label}
                        </button>
                    ))}
                </div>

                {/* Scrollable Content */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">

                    {/* SECTION: GENERAL */}
                    {section === 'general' && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Title</label>
                                <input {...register('title')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-accent outline-none font-bold" autoFocus />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Project Code</label>
                                    <input {...register('project_code')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs font-mono text-accent uppercase focus:border-accent outline-none" placeholder="CODEX" />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Status</label>
                                    <select {...register('status')} className="w-full bg-white/5 border border-white/10 rounded px-2 py-2 text-xs text-white uppercase [&>option]:bg-black outline-none">
                                        <option value="active">Active</option>
                                        <option value="on-hold">On Hold</option>
                                        <option value="completed">Completed</option>
                                        <option value="rnd_long">R&D Long</option>
                                        <option value="legacy">Legacy</option>
                                        <option value="archived">Archived</option>
                                    </select>
                                </div>
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold flex justify-between">Priority <span className="text-accent">{watch('priority')}</span></label>
                                    <input type="range" min="1" max="5" {...register('priority')} className="w-full accent-red-500 h-1 bg-white/10 rounded appearance-none cursor-pointer mt-2" />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold flex justify-between">Intrusiveness <span className="text-blue-400">{watch('intrusiveness')}</span></label>
                                    <input type="range" min="1" max="5" {...register('intrusiveness')} className="w-full accent-blue-500 h-1 bg-white/10 rounded appearance-none cursor-pointer mt-2" />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Risk Level</label>
                                <div className="flex gap-2">
                                    {['low', 'medium', 'high'].map(r => (
                                        <label key={r} className={clsx("flex-1 cursor-pointer border rounded py-1.5 text-center text-[10px] uppercase font-bold transition-colors",
                                            watch('risk_level') === r
                                                ? (r === 'high' ? "bg-red-500/20 border-red-500 text-red-500" : r === 'medium' ? "bg-amber-500/20 border-amber-500 text-amber-500" : "bg-green-500/20 border-green-500 text-green-500")
                                                : "border-white/10 text-gray-500 hover:border-white/30"
                                        )}>
                                            <input type="radio" value={r} {...register('risk_level')} className="hidden" />
                                            {r}
                                        </label>
                                    ))}
                                </div>
                            </div>
                        </div>
                    )}

                    {/* SECTION: DETAILS */}
                    {section === 'details' && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Description / Rationale</label>
                                <textarea {...register('rationale')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-gray-300 focus:border-accent outline-none h-24 resize-none" placeholder="Why this project exists..." />
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Status Narrative</label>
                                <textarea {...register('status_description')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-gray-300 focus:border-accent outline-none h-20 resize-none" placeholder="Current state of affairs..." />
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Tags (comma separated)</label>
                                <input {...register('tags')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white focus:border-accent outline-none" placeholder="3d-printing, hardware, urgent" />
                            </div>
                        </div>
                    )}

                    {/* SECTION: PLANNING */}
                    {section === 'planning' && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Target Completion</label>
                                <input type="date" {...register('target_completion_date')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" />
                            </div>
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Est. Total Hours</label>
                                    <input type="number" {...register('total_theorized_hours')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Active Hours Logged</label>
                                    <input type="number" {...register('time_estimate_active')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Financial Budget ($)</label>
                                <input type="number" {...register('financial_budget')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" placeholder="0.00" />
                            </div>
                        </div>
                    )}

                    {/* SECTION: TAXONOMY */}
                    {section === 'taxonomy' && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Category</label>
                                    <input {...register('category')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" placeholder="e.g. Work" />
                                </div>
                                <div>
                                    <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Kindgom</label>
                                    <input {...register('kingdom')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" placeholder="e.g. Electronics" />
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Phylum</label>
                                <input {...register('phylum')} className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-white outline-none" placeholder="e.g. Microcontrollers" />
                            </div>
                        </div>
                    )}

                    {/* SECTION: ASSETS */}
                    {section === 'assets' && (
                        <div className="space-y-4 animate-in fade-in slide-in-from-right-4 duration-300">
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">Cover Image URL</label>
                                <div className="flex gap-2">
                                    <input {...register('image_url')} className="flex-1 bg-white/5 border border-white/10 rounded px-3 py-2 text-xs text-accent font-mono outline-none" placeholder="https://..." />
                                    {watch('image_url') && <div className="w-8 h-8 rounded bg-cover bg-center border border-white/20" style={{ backgroundImage: `url(${watch('image_url')})` }} />}
                                </div>
                            </div>
                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold mb-1 block">GitHub Repository</label>
                                <div className="relative">
                                    <Github size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                                    <input {...register('github_repo')} className="w-full bg-white/5 border border-white/10 rounded pl-9 pr-3 py-2 text-xs text-white font-mono outline-none" placeholder="username/repo" />
                                </div>
                            </div>
                        </div>
                    )}

                </div>

                {/* Footer Actions */}
                <div className="flex justify-between items-center p-3 border-t border-white/10 bg-white/5">
                    <Button type="button" variant="ghost" className="text-gray-500 hover:text-white" onClick={() => navigate(`/projects/${project.id}`)}><ExternalLink size={14} className="mr-1" /> Full Details</Button>
                    <div className="flex gap-2">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                        <Button type="submit" className="bg-accent text-black hover:bg-white border-0"><Save size={14} className="mr-1" /> Save Changes</Button>
                    </div>
                </div>
            </form>
        </div>
    );
}
