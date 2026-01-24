import React, { useEffect, useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { X, Save, AlertCircle, Loader2 } from 'lucide-react';
import { toast } from 'sonner';
import clsx from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';

import { ENTITY_REGISTRY } from '../../../lib/registry/entityRegistry';
import type { FormFieldConfig, FormSection, EntityDefinition } from '../../../lib/registry/entityRegistry';
import { UpdateEntityCommand, getEntityById } from '../../../lib/commands';
import type { UniversalEntity } from '../../../lib/universal/types';
import * as LucideIcons from 'lucide-react';

// Specialized Forms (Override Generic)
import { ProjectEditForm } from '../../projects/ProjectEditForm';

interface UniversalEditModalProps {
    entityType: string;
    entityId?: string;
    onClose: () => void;
}

export function UniversalEditModal({ entityType, entityId, onClose }: UniversalEditModalProps) {
    const [isLoading, setIsLoading] = useState(true);
    const [entity, setEntity] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const definition = ENTITY_REGISTRY[entityType];

    // Load Data
    useEffect(() => {
        async function load() {
            if (!entityId) {
                setIsLoading(false);
                return;
            }
            try {
                const data = await getEntityById(entityType, entityId);
                if (data) {
                    setEntity(data);
                } else {
                    setError('Entity not found');
                }
            } catch (err) {
                console.error(err);
                setError('Failed to load entity');
            } finally {
                setIsLoading(false);
            }
        }
        load();
    }, [entityType, entityId]);

    // Handle Escape Key
    useEffect(() => {
        const handleEsc = (e: KeyboardEvent) => {
            if (e.key === 'Escape') onClose();
        };
        window.addEventListener('keydown', handleEsc);
        return () => window.removeEventListener('keydown', handleEsc);
    }, [onClose]);

    // -------------------------------------------------------------------------
    // RENDER: Specialized Overrides
    // -------------------------------------------------------------------------

    // Project: Use the specialized Tabbed Form (it handles its own saving/fetching usually, 
    // but we might need to wrap it if it expects props. 
    // Looking at ProjectEditForm usage in Legacy Card: <ProjectEditForm project={project} onClose={...} />)
    if (entityType === 'project' && !isLoading && entity) {
        // ProjectEditForm handles its own mutations historically, 
        // but ideally we migrate it to use commands internally eventually.
        // For now, we delegate UI to it.
        // unpack UniversalEntity.data to match Project interface
        return (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4">
                <ProjectEditForm project={entity.data} onClose={onClose} />
            </div>
        );
    }

    // -------------------------------------------------------------------------
    // RENDER: Generic Auto-Form
    // -------------------------------------------------------------------------

    // Schema-based Generic Form
    // If we have a Zod schema, use it.
    const Schema = definition?.schema;

    // Form Hook
    const {
        register,
        handleSubmit,
        watch,
        formState: { errors, isSubmitting }
    } = useForm({
        resolver: Schema ? zodResolver(Schema) : undefined,
        values: entity, // Auto-fill when entity loads
    });

    const onSubmit = async (data: any) => {
        if (!entityId) return; // Create not supported yet in this specific modal logic (TODO)

        try {
            const command = new UpdateEntityCommand(
                entityType,
                entityId,
                data,
                { actor: 'user', timestamp: new Date() }
            );

            const result = await command.execute();

            if (result.success) {
                toast.success(`${definition.icon} Updated`);
                onClose();
            } else {
                toast.error('Update Failed');
                console.error(result.error);
            }
        } catch (e) {
            toast.error('An error occurred');
            console.error(e);
        }
    };

    if (isLoading) {
        return (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
                <Loader2 className="animate-spin text-accent" size={32} />
            </div>
        );
    }

    if (error || !definition) {
        return (
            <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm">
                <div className="bg-zinc-900 border border-red-900/50 p-6 rounded-lg max-w-sm w-full">
                    <div className="flex items-center gap-2 text-red-500 mb-2">
                        <AlertCircle size={20} />
                        <h3 className="font-bold">Error</h3>
                    </div>
                    <p className="text-gray-400 text-sm mb-4">{error || `Unknown entity type: ${entityType}`}</p>
                    <button onClick={onClose} className="w-full py-2 bg-white/5 hover:bg-white/10 rounded">Close</button>
                </div>
            </div>
        );
    }

    // Auto-Generate Fields from Schema Shape (if ZodObject)
    // Note: Zod schema introspection is tricky. For MVP, we render JSON dump if no schema, 
    // or known fields if schema is present.
    // Simpler: Use `editFields` from definition if available, else keys of entity.

    const fieldsToRender = definition.editFields || (Schema && (Schema as any).shape ? Object.keys((Schema as any).shape) : Object.keys(entity || {}));

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm p-4 overflow-y-auto">
            <motion.div
                initial={{ opacity: 0, scale: 0.95 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.95 }}
                className="bg-[#09090b] border border-white/10 w-full max-w-2xl rounded-xl shadow-2xl overflow-hidden flex flex-col max-h-[90vh]"
            >
                {/* Header */}
                <div className="flex items-center justify-between px-6 py-4 border-b border-white/5 bg-white/[0.02]">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-accent/10 rounded-lg text-accent">
                            {/* Icon would go here if we dynamically loaded it, e.g. using Lucide map */}
                            <span className="font-mono font-bold text-lg">EDIT</span>
                        </div>
                        <div>
                            <h2 className="text-lg font-bold text-white leading-none mb-1">Edit {definition.primaryField ? entity[definition.primaryField] : entityType}</h2>
                            <span className="text-xs text-gray-500 font-mono uppercase tracking-wider">{entityType} • {entityId}</span>
                        </div>
                    </div>
                    <button onClick={onClose} className="text-gray-500 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6 custom-scrollbar">
                    <form id="universal-edit-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">

                        {/* FORM BUILDER: Config Driven */}
                        {definition.form ? (
                            <FormBuilder definition={definition} register={register} errors={errors} watch={watch} />
                        ) : (
                            /* FALLBACK: Legacy Auto-Render */
                            <div className="space-y-4">
                                {fieldsToRender.map(field => (
                                    <div key={field} className="space-y-1.5">
                                        <label className="text-xs font-bold text-gray-400 uppercase tracking-wide">{field.replace(/_/g, ' ')}</label>
                                        <input
                                            {...register(field)}
                                            className="w-full bg-black/20 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all font-mono"
                                        />
                                        {errors[field] && (
                                            <span className="text-red-500 text-xs">{(errors[field] as any)?.message}</span>
                                        )}
                                    </div>
                                ))}
                                {!Schema && (
                                    <div className="p-4 bg-yellow-500/10 border border-yellow-500/20 rounded text-yellow-500 text-xs mt-4">
                                        ⚠ No Form Config or Schema defined. Rendering raw fields.
                                    </div>
                                )}
                            </div>
                        )}

                    </form>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 border-t border-white/5 bg-white/[0.02] flex justify-end gap-3">
                    <button
                        type="button"
                        onClick={onClose}
                        className="px-4 py-2 rounded text-sm font-medium text-gray-400 hover:text-white hover:bg-white/5 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        form="universal-edit-form"
                        disabled={isSubmitting}
                        className="flex items-center gap-2 px-4 py-2 rounded text-sm font-bold bg-accent text-black hover:bg-white hover:scale-105 active:scale-95 transition-all shadow-lg shadow-accent/20 disabled:opacity-50 disabled:pointer-events-none"
                    >
                        {isSubmitting ? <Loader2 size={16} className="animate-spin" /> : <Save size={16} />}
                        Save Changes
                    </button>
                </div>
            </motion.div>
        </div>
    );
}

// ----------------------------------------------------------------------------
// Internal Form Builder Components
// ----------------------------------------------------------------------------

function FormBuilder({ definition, register, errors, watch }: { definition: EntityDefinition, register: any, errors: any, watch: any }) {
    const [activeTab, setActiveTab] = useState<string>(definition.form?.sections?.[0]?.id || 'general');

    // Mode 1: Sections (Tabs)
    if (definition.form?.sections) {
        return (
            <div className="space-y-4">
                {/* Tab Bar */}
                <div className="flex gap-1 border-b border-white/10 overflow-x-auto pb-0">
                    {definition.form.sections.map(section => {
                        const Icon = section.icon ? (LucideIcons as any)[section.icon] : undefined;
                        const isActive = activeTab === section.id;
                        return (
                            <button
                                key={section.id}
                                type="button"
                                onClick={() => setActiveTab(section.id)}
                                className={clsx(
                                    "flex items-center gap-2 px-4 py-2 text-xs font-bold uppercase tracking-wider border-b-2 transition-colors whitespace-nowrap",
                                    isActive ? "border-accent text-accent" : "border-transparent text-gray-500 hover:text-gray-300"
                                )}
                            >
                                {Icon && <Icon size={14} />}
                                {section.title}
                            </button>
                        );
                    })}
                </div>

                {/* Tab Content */}
                <div className="pt-2 animate-in fade-in slide-in-from-right-2 duration-300 min-h-[200px]" key={activeTab}>
                    {definition.form.sections.find(s => s.id === activeTab)?.fields.map((field, idx) => (
                        <UniversalField key={idx} field={field} register={register} errors={errors} watch={watch} />
                    ))}
                </div>
            </div>
        );
    }

    // Mode 2: Flat Fields
    if (definition.form?.fields) {
        return (
            <div className="space-y-4">
                {definition.form.fields.map((field, idx) => (
                    <UniversalField key={idx} field={field} register={register} errors={errors} watch={watch} />
                ))}
            </div>
        );
    }

    return null;
}

function UniversalField({ field, register, errors, watch }: { field: string | FormFieldConfig, register: any, errors: any, watch: any }) {
    // Normalize string shorthand to config object
    const config: FormFieldConfig = typeof field === 'string' ? { key: field, widget: 'text' } : field;
    const { key, label, widget, placeholder, description, options, min, max } = config;

    const error = errors[key];
    const displayLabel = label || key.replace(/_/g, ' ');

    return (
        <div className="mb-4">
            <label className="flex items-center justify-between text-xs font-bold text-gray-400 uppercase tracking-wide mb-1.5">
                <span>{displayLabel}</span>
                {widget === 'range' && <span className="text-accent">{watch(key)}</span>}
            </label>

            {widget === 'textarea' ? (
                <textarea
                    {...register(key)}
                    placeholder={placeholder}
                    className="w-full bg-black/20 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all font-mono min-h-[100px] resize-none"
                />
            ) : widget === 'select' ? (
                <select
                    {...register(key)}
                    className="w-full bg-black/20 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all appearance-none cursor-pointer hover:bg-white/5"
                >
                    {options?.map(opt => (
                        <option key={opt.value} value={opt.value} className="bg-zinc-900">{opt.label}</option>
                    ))}
                </select>
            ) : widget === 'range' ? (
                <input
                    type="range"
                    min={min}
                    max={max}
                    {...register(key)}
                    className="w-full h-1 bg-white/10 rounded-lg appearance-none cursor-pointer accent-accent"
                />
            ) : (
                <input
                    type={widget === 'number' ? 'number' : widget === 'date' ? 'date' : 'text'}
                    {...register(key)}
                    placeholder={placeholder}
                    className="w-full bg-black/20 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-accent/50 focus:outline-none focus:ring-1 focus:ring-accent/50 transition-all font-mono"
                />
            )}

            {description && <p className="text-[10px] text-gray-500 mt-1">{description}</p>}
            {error && <span className="text-red-500 text-xs font-mono mt-1 block">{(error as any)?.message}</span>}
        </div>
    );
}
