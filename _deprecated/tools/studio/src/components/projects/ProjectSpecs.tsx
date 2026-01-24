import { useState } from 'react';
import type { Project } from '../../lib/db';
import { db } from '../../lib/db';
import { useLiveQuery } from 'dexie-react-hooks';
import { KeyValueEditor } from '../ui/KeyValueEditor';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Info, Plus, X, Ruler } from 'lucide-react';

interface ProjectSpecsProps {
    project: Project;
    projectId: number;
    onUpdate: (updates: Partial<Project>) => void;
}

export function ProjectSpecs({ project, projectId, onUpdate }: ProjectSpecsProps) {
    // Helper to check domains safely (hybrid support)
    const hasDomain = (domain: string) => {
        if (!project.domains || project.domains.length === 0) {
            // Fallback to old kingdom/category if domains not set
            const legacy = (project.kingdom || project.category || '').toLowerCase();
            return legacy.includes(domain.toLowerCase());
        }
        return project.domains.some(d => d.toLowerCase().includes(domain.toLowerCase()));
    };

    const updateDomains = (domainString: string) => {
        const domains = domainString.split(',').map(s => s.trim()).filter(Boolean);
        onUpdate({ domains });
    };

    return (
        <div className="space-y-8 animate-in fade-in duration-300">
            {/* Key Measurements (From Workbench) */}
            <div className="bg-black/40 border border-white/10 p-6 rounded-xl">
                <h3 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                    <Ruler size={18} className="text-accent" /> Key Measurements
                </h3>
                <KeySpecs projectId={projectId} />
            </div>

            {/* Header / Domain Control */}
            <div className="bg-black/40 border border-white/10 p-6 rounded-xl">
                <div className="flex items-start justify-between gap-4">
                    <div className="flex-1">
                        <h3 className="text-xl font-bold text-white mb-2 flex items-center gap-2">
                            Project Domains
                            <div className="group relative">
                                <Info size={16} className="text-gray-500 cursor-help" />
                                <div className="absolute left-0 bottom-full mb-2 w-64 p-2 bg-gray-900 border border-white/20 rounded text-xs text-gray-300 hidden group-hover:block z-50">
                                    Defines which spec sheets are relevant. (e.g. "Electronics, DIY, Chemistry")
                                </div>
                            </div>
                        </h3>
                        <p className="text-gray-400 text-sm mb-4">
                            These tags determine the "Magic Fields" available below.
                        </p>
                        <Input
                            value={project.domains?.join(', ') || ''}
                            onChange={(e) => updateDomains(e.target.value)}
                            placeholder="e.g. Electronics, Luthierie, Software"
                            className="bg-black/50 border-white/20"
                        />
                    </div>
                </div>
            </div>

            {/* 1. Technical Specs (Hard Constraints) */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <KeyValueEditor
                        title="Technical Specifications"
                        description="Hard constraints and requirements."
                        data={project.specs_technical || {}}
                        onChange={(data) => onUpdate({ specs_technical: data })}
                        placeholderKey={hasDomain('electronics') ? "e.g. Voltage" : "e.g. Material"}
                        placeholderValue={hasDomain('electronics') ? "e.g. 9VDC" : "e.g. Walnut"}
                    />
                </div>

                {/* 2. Performance Specs (Measurables) */}
                <div className="space-y-2">
                    <KeyValueEditor
                        title="Performance Targets"
                        description=" measurable goals and metrics."
                        data={project.specs_performance || {}}
                        onChange={(data) => onUpdate({ specs_performance: data })}
                        placeholderKey="e.g. Noise Floor"
                        placeholderValue="e.g. -90dB"
                    />
                </div>
            </div>

            {/* 3. Safety & Environment (v19) */}
            <div className="bg-red-900/10 border border-red-500/20 p-6 rounded-xl space-y-4">
                <h3 className="text-lg font-bold text-red-400 flex items-center gap-2">
                    Safety & Environment
                </h3>

                {/* Hazards */}
                <div className="space-y-2">
                    <label className="text-xs uppercase font-bold text-gray-500">Hazards & Risks (Comma Separated)</label>
                    <Input
                        value={project.hazards?.join(', ') || ''}
                        onChange={(e) => {
                            const val = e.target.value;
                            const arr = val.split(',').map(s => s.trim()).filter(Boolean);
                            onUpdate({ hazards: arr.length > 0 ? arr : undefined }); // undefined to clean up if empty? or []
                        }}
                        placeholder="e.g. Fumes, Biohazard, High Voltage, Sharp Edges"
                        className="bg-black/50 border-red-500/20 text-red-300 placeholder:text-red-900/50"
                    />
                    <p className="text-xs text-gray-500">These will appear as warnings on the Project Details.</p>
                </div>

                {/* Environmental Specs */}
                <div className="mt-4">
                    <KeyValueEditor
                        title="Environmental Constraints"
                        description="Weather, Temp, Humidity, Drying Times."
                        data={project.specs_environment || {}}
                        onChange={(data) => onUpdate({ specs_environment: data })}
                        placeholderKey="e.g. Min Temp"
                        placeholderValue="e.g. 65F"
                    />
                </div>
            </div>

            {/* 4. Context & Signal Chain */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-2">
                    <KeyValueEditor
                        title="Market Context & Use-Cases"
                        description="User personas, scenes, and non-goals."
                        data={project.market_context || {}}
                        onChange={(data) => onUpdate({ market_context: data })}
                        placeholderKey="e.g. Target User"
                        placeholderValue="e.g. Session Musician"
                    />
                </div>

                <div className="space-y-2">
                    <KeyValueEditor
                        title="Signal Chain / Flow"
                        description="Input, Output, and Routing context."
                        data={project.signal_chain || {}}
                        onChange={(data) => onUpdate({ signal_chain: data })}
                        placeholderKey="e.g. Input Source"
                        placeholderValue="e.g. Piezo Pickup"
                    />
                </div>
            </div>

            {/* 5. MAGIC FIELDS (Universal Data) */}
            {/* This captures any unaccounted data from ingestion or advanced users */}
            <div className="bg-purple-900/10 border border-purple-500/20 p-6 rounded-xl space-y-2">
                <h3 className="text-lg font-bold text-purple-400 flex items-center gap-2">
                    <Zap size={18} className="text-purple-400" />
                    Universal Data (Magic Fields)
                </h3>
                <p className="text-sm text-gray-400 mb-4">
                    Unstructured data, custom properties, or AI-ingested extras that don't fit elsewhere.
                </p>
                <KeyValueEditor
                    title="Universal Properties"
                    description="Custom key-value pairs."
                    data={project.universal_data || {}}
                    onChange={(data) => onUpdate({ universal_data: data })}
                    placeholderKey="e.g. Extracted ID"
                    placeholderValue="e.g. 123-ABC"
                />
            </div>

        </div>
    );
}

function KeySpecs({ projectId }: { projectId: number }) {
    const specs = useLiveQuery(() => db.project_measurements.where('project_id').equals(projectId).toArray());
    const [newSpec, setNewSpec] = useState({ label: '', value: '', unit: '' });

    const addSpec = async () => {
        if (!newSpec.label || !newSpec.value) return;
        await db.project_measurements.add({
            project_id: projectId,
            ...newSpec,
            is_verified: false
        });
        setNewSpec({ label: '', value: '', unit: '' });
    };

    const deleteSpec = (id: number) => db.project_measurements.delete(id);

    return (
        <div className="space-y-6">
            <div className="border border-white/10 rounded overflow-hidden">
                <table className="w-full text-left">
                    <thead className="bg-white/5 text-xs uppercase text-gray-500 font-mono">
                        <tr>
                            <th className="p-3">Specification</th>
                            <th className="p-3">Value</th>
                            <th className="p-3">Unit</th>
                            <th className="p-3 w-10"></th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-white/5">
                        {specs?.map(spec => (
                            <tr key={spec.id} className="group hover:bg-white/5">
                                <td className="p-3 font-bold text-gray-300">{spec.label}</td>
                                <td className="p-3 font-mono text-accent">{spec.value}</td>
                                <td className="p-3 text-xs text-gray-500">{spec.unit}</td>
                                <td className="p-3 text-right">
                                    <button onClick={() => deleteSpec(spec.id!)} className="text-red-900 group-hover:text-red-500 transition-colors">
                                        <X size={14} />
                                    </button>
                                </td>
                            </tr>
                        ))}
                        <tr className="bg-black/20">
                            <td className="p-2">
                                <Input placeholder="Label (e.g. Vcc)" value={newSpec.label} onChange={e => setNewSpec({ ...newSpec, label: e.target.value })} className="h-8 text-xs" />
                            </td>
                            <td className="p-2">
                                <Input placeholder="Value (e.g. 5)" value={newSpec.value} onChange={e => setNewSpec({ ...newSpec, value: e.target.value })} className="h-8 text-xs" />
                            </td>
                            <td className="p-2">
                                <Input placeholder="Unit (e.g. V)" value={newSpec.unit} onChange={e => setNewSpec({ ...newSpec, unit: e.target.value })} className="h-8 text-xs" />
                            </td>
                            <td className="p-2 text-right">
                                <Button size="sm" onClick={addSpec} className="h-8 w-8 p-0"><Plus size={14} /></Button>
                            </td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </div>
    );
}
