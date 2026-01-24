/**
 * AutoEditForm
 * Schema-driven form component that auto-generates UI from Zod schemas.
 * Uses existing react-hook-form + zod infrastructure.
 */

import { useForm, type FieldValues, type DefaultValues, type Path } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import type { ZodObject, ZodRawShape, ZodTypeAny } from 'zod';
import { Save, X } from 'lucide-react';
import { Button } from '../../components/ui/Button';
import clsx from 'clsx';

// ============================================================================
// TYPES
// ============================================================================

export interface FieldConfig {
    /** Override the label */
    label?: string;
    /** Add placeholder text */
    placeholder?: string;
    /** Hide this field */
    hidden?: boolean;
    /** Make field read-only */
    readOnly?: boolean;
    /** Custom component to render */
    component?: 'input' | 'textarea' | 'select' | 'range' | 'checkbox' | 'date';
    /** Options for select fields */
    options?: Array<{ value: string; label: string }>;
    /** Min/max for range inputs */
    min?: number;
    max?: number;
    /** Grid column span */
    colSpan?: 1 | 2;
    /** Help text */
    helpText?: string;
}

export interface AutoEditFormProps<T extends FieldValues> {
    /** Zod schema for validation */
    schema: ZodObject<ZodRawShape>;
    /** Default values */
    defaultValues: DefaultValues<T>;
    /** Submit handler */
    onSubmit: (data: T) => Promise<void>;
    /** Cancel handler */
    onCancel?: () => void;
    /** Field-specific configuration */
    fieldConfig?: Partial<Record<keyof T, FieldConfig>>;
    /** Only show these fields */
    includeFields?: Array<keyof T>;
    /** Hide these fields */
    excludeFields?: Array<keyof T>;
    /** Form title */
    title?: string;
    /** Loading state */
    loading?: boolean;
    /** Compact mode */
    compact?: boolean;
}

// ============================================================================
// HELPERS
// ============================================================================

function getFieldType(zodType: ZodTypeAny): string {
    const typeName = zodType._def.typeName;

    switch (typeName) {
        case 'ZodString': return 'text';
        case 'ZodNumber': return 'number';
        case 'ZodBoolean': return 'checkbox';
        case 'ZodDate': return 'date';
        case 'ZodEnum': return 'select';
        case 'ZodOptional':
        case 'ZodNullable':
            return getFieldType(zodType._def.innerType);
        default: return 'text';
    }
}

function getEnumOptions(zodType: ZodTypeAny): Array<{ value: string; label: string }> {
    if (zodType._def.typeName === 'ZodEnum') {
        return zodType._def.values.map((v: string) => ({
            value: v,
            label: v.replace(/[-_]/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
        }));
    }
    if (zodType._def.typeName === 'ZodOptional' || zodType._def.typeName === 'ZodNullable') {
        return getEnumOptions(zodType._def.innerType);
    }
    return [];
}

function formatLabel(key: string): string {
    return key
        .replace(/([A-Z])/g, ' $1')
        .replace(/[-_]/g, ' ')
        .replace(/\b\w/g, c => c.toUpperCase())
        .trim();
}

// ============================================================================
// COMPONENT
// ============================================================================

export function AutoEditForm<T extends FieldValues>({
    schema,
    defaultValues,
    onSubmit,
    onCancel,
    fieldConfig = {},
    includeFields,
    excludeFields = [],
    title,
    loading = false,
    compact = false,
}: AutoEditFormProps<T>) {
    const { register, handleSubmit, formState: { errors, isSubmitting }, watch } = useForm<T>({
        resolver: zodResolver(schema) as any,
        defaultValues,
    });

    // Get fields from schema
    const schemaShape = schema.shape;
    const allFields = Object.keys(schemaShape) as Array<keyof T>;

    // Filter fields
    const visibleFields = allFields.filter(key => {
        if (includeFields && !includeFields.includes(key)) return false;
        if (excludeFields.includes(key)) return false;
        if (fieldConfig[key]?.hidden) return false;
        return true;
    });

    const renderField = (key: keyof T) => {
        const zodType = schemaShape[key as string];
        const config = fieldConfig[key] || {};
        const baseType = getFieldType(zodType);
        const component = config.component || (baseType === 'select' ? 'select' : baseType === 'checkbox' ? 'checkbox' : 'input');
        const label = config.label || formatLabel(key as string);
        const error = errors[key as Path<T>];
        const colSpan = config.colSpan || 1;

        const inputClasses = clsx(
            'w-full bg-white/5 border rounded px-2 py-1.5 text-sm text-white focus:border-accent outline-none transition-colors',
            error ? 'border-red-500' : 'border-white/10',
            config.readOnly && 'opacity-50 cursor-not-allowed'
        );

        return (
            <div key={key as string} className={clsx('flex flex-col gap-1', colSpan === 2 && 'col-span-2')}>
                <label className="text-[10px] uppercase text-gray-500 font-bold">{label}</label>

                {component === 'textarea' ? (
                    <textarea
                        {...register(key as Path<T>)}
                        placeholder={config.placeholder}
                        readOnly={config.readOnly}
                        className={clsx(inputClasses, 'min-h-[80px] resize-y')}
                    />
                ) : component === 'select' ? (
                    <select
                        {...register(key as Path<T>)}
                        disabled={config.readOnly}
                        className={clsx(inputClasses, '[&>option]:bg-black')}
                    >
                        {(config.options || getEnumOptions(zodType)).map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                        ))}
                    </select>
                ) : component === 'range' ? (
                    <div className="flex items-center gap-2">
                        <input
                            type="range"
                            min={config.min || 1}
                            max={config.max || 5}
                            {...register(key as Path<T>, { valueAsNumber: true })}
                            className="flex-1 accent-accent h-1 bg-white/10 rounded appearance-none cursor-pointer"
                        />
                        <span className="text-xs text-white w-4 text-center">{watch(key as Path<T>)}</span>
                    </div>
                ) : component === 'checkbox' ? (
                    <div className="flex items-center gap-2 py-1">
                        <input
                            type="checkbox"
                            {...register(key as Path<T>)}
                            disabled={config.readOnly}
                            className="w-4 h-4 rounded border-white/20 bg-white/5 text-accent focus:ring-accent"
                        />
                        {config.helpText && <span className="text-xs text-gray-400">{config.helpText}</span>}
                    </div>
                ) : component === 'date' ? (
                    <input
                        type="date"
                        {...register(key as Path<T>)}
                        readOnly={config.readOnly}
                        className={inputClasses}
                    />
                ) : (
                    <input
                        type={baseType === 'number' ? 'number' : 'text'}
                        {...register(key as Path<T>, baseType === 'number' ? { valueAsNumber: true } : undefined)}
                        placeholder={config.placeholder}
                        readOnly={config.readOnly}
                        className={inputClasses}
                    />
                )}

                {error && <span className="text-red-400 text-[10px]">{String(error.message)}</span>}
                {config.helpText && !error && component !== 'checkbox' && (
                    <span className="text-gray-500 text-[10px]">{config.helpText}</span>
                )}
            </div>
        );
    };

    return (
        <form onSubmit={handleSubmit(onSubmit as any)} className={clsx('flex flex-col gap-3', compact && 'gap-2')}>
            {title && (
                <div className="flex justify-between items-center border-b border-white/10 pb-2 mb-1">
                    <h3 className="text-sm font-bold text-white uppercase">{title}</h3>
                    {onCancel && (
                        <button type="button" onClick={onCancel} className="text-gray-400 hover:text-white">
                            <X size={16} />
                        </button>
                    )}
                </div>
            )}

            <div className={clsx('grid gap-3', compact ? 'grid-cols-2' : 'grid-cols-2')}>
                {visibleFields.map(renderField)}
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-white/10">
                {onCancel && (
                    <Button type="button" variant="ghost" onClick={onCancel} disabled={isSubmitting}>
                        Cancel
                    </Button>
                )}
                <Button type="submit" disabled={isSubmitting || loading} className="bg-accent text-black hover:bg-white">
                    <Save size={14} className="mr-1" />
                    {isSubmitting ? 'Saving...' : 'Save'}
                </Button>
            </div>
        </form>
    );
}
