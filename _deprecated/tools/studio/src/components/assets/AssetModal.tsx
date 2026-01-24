import { useState, useEffect } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { X, Save, AlertTriangle, Monitor, Package, PenTool, Box, Smartphone, Upload } from 'lucide-react';
import { db, type Asset } from '../../lib/db';
import { toast } from 'sonner';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import clsx from 'clsx';
import { createPortal } from 'react-dom';

const assetSchema = z.object({
    name: z.string().min(1, "Name is required"),
    category: z.string().min(1, "Category is required"),
    status: z.enum(['active', 'maintenance', 'broken', 'retired']),
    value: z.preprocess(
        (val) => (val === '' || val === null || isNaN(Number(val)) ? 0 : Number(val)),
        z.number().min(0, "Value must be positive").optional()
    ),
    location: z.string().optional(),
    description: z.string().optional(),
    make: z.string().optional(),
    model: z.string().optional(),
    serial_number: z.string().optional(),
    purchase_date: z.string().optional(),
    // Computer Specs
    cpu: z.string().optional(),
    ram: z.string().optional(),
    gpu: z.string().optional(),
    os: z.string().optional(),
    hostname: z.string().optional(),
});

type AssetFormData = z.infer<typeof assetSchema>;

interface AssetModalProps {
    isOpen: boolean;
    onClose: () => void;
    assetToEdit?: Asset; // If provided, we are in Edit mode
    defaultProjectId?: number;
    defaultCategory?: string;
}

export function AssetModal({ isOpen, onClose, assetToEdit, defaultProjectId, defaultCategory }: AssetModalProps) {
    const isEditing = !!assetToEdit;

    const { register, handleSubmit, reset, setValue, watch, formState: { errors, isSubmitting } } = useForm<AssetFormData>({
        resolver: zodResolver(assetSchema),
        defaultValues: {
            name: '',
            status: 'active',
            value: 0
        }
    });

    const category = watch('category');

    useEffect(() => {
        if (assetToEdit) {
            setValue('name', assetToEdit.name);
            setValue('category', assetToEdit.category);
            setValue('status', assetToEdit.status);
            setValue('value', assetToEdit.value || 0);
            setValue('location', assetToEdit.location || '');
            setValue('description', assetToEdit.description || '');
            setValue('make', assetToEdit.make || '');
            setValue('model', assetToEdit.model || '');
            setValue('serial_number', assetToEdit.serial_number || '');
            if (assetToEdit.purchaseDate) {
                setValue('purchase_date', new Date(assetToEdit.purchaseDate).toISOString().split('T')[0]);
            }
            // Hydrate computer specs if available
            if (assetToEdit.specs_computer) {
                setValue('cpu', assetToEdit.specs_computer.cpu);
                setValue('ram', assetToEdit.specs_computer.ram);
                setValue('gpu', assetToEdit.specs_computer.gpu);
                setValue('os', assetToEdit.specs_computer.os);
                setValue('hostname', assetToEdit.specs_computer.hostname);
                // Note: Complex fields like drives/network would need more UI work, sticking to basic strings for MVP fix
            }
        } else {
            reset({
                name: '',
                status: 'active',
                value: 0,
                category: defaultCategory || 'hardware'
            });
        }
    }, [assetToEdit, isOpen, setValue, reset, defaultCategory]);

    const onSubmit = async (data: AssetFormData) => {
        try {
            const assetData = {
                name: data.name,
                category: data.category,
                status: data.status,
                value: Number(data.value),
                location: data.location,
                description: data.description,
                make: data.make,
                model: data.model,
                serial_number: data.serial_number,
                purchaseDate: data.purchase_date ? new Date(data.purchase_date) : undefined,
                updated_at: new Date(),
                // Computer Specs Inclusion
                specs_computer: (data.category === 'computer') ? {
                    cpu: data.cpu || '',
                    ram: data.ram || '',
                    gpu: data.gpu || '',
                    os: data.os || '',
                    hostname: data.hostname || '',
                    storage_drives: [], // Placeholder for complex UI
                    network_interfaces: [],
                    peripherals: []
                } : undefined
            };

            if (isEditing && assetToEdit) {
                await db.assets.update(assetToEdit.id!, assetData);
                toast.success("Asset updated successfully");
            } else {
                await db.assets.add({
                    ...assetData,
                    created_at: new Date(),
                    images: [],
                    manuals: [],
                    related_project_ids: defaultProjectId ? [defaultProjectId] : [],
                    symptoms: []
                } as any);
                toast.success("Asset registered successfully");
            }
            onClose();
        } catch (error) {
            console.error("Failed to save asset:", error);
            toast.error("Failed to save asset");
        }
    };

    if (!isOpen) return null;

    return createPortal(
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200"
                onClick={onClose}
            />

            {/* Modal */}
            <div className="relative w-full max-w-2xl bg-[#0A0A0A] border border-white/10 rounded-2xl shadow-2xl flex flex-col max-h-[90vh] animate-in zoom-in-95 duration-200">
                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-white/10">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        {isEditing ? <PenTool className="text-accent" /> : <Package className="text-accent" />}
                        {isEditing ? `Edit Asset: ${assetToEdit.name}` : "Register New Asset"}
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white transition-colors">
                        <X size={20} />
                    </button>
                </div>

                {/* Body */}
                <div className="flex-1 overflow-y-auto p-6 space-y-6">
                    <form id="asset-form" onSubmit={handleSubmit(onSubmit)} className="space-y-6">
                        <div className="grid grid-cols-2 gap-4">
                            <div className="col-span-2">
                                <Input label="Asset Name" {...register('name')} error={errors.name?.message} autoFocus />
                            </div>

                            <div>
                                <label className="block text-xs font-bold uppercase text-gray-500 mb-1">Category</label>
                                <select
                                    {...register('category')}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                                >
                                    <option value="hardware">Hardware</option>
                                    <option value="computer">Computer</option>
                                    <option value="software">Software</option>
                                    <option value="furniture">Furniture</option>
                                    <option value="tool">Tool</option>
                                    <option value="vehicle">Vehicle</option>
                                    <option value="other">Other</option>
                                </select>
                            </div>

                            <div>
                                <label className="block text-xs font-bold uppercase text-gray-500 mb-1">Status</label>
                                <select
                                    {...register('status')}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-accent"
                                >
                                    <option value="active">Active (In Use)</option>
                                    <option value="maintenance">Maintenance</option>
                                    <option value="broken">Broken</option>
                                    <option value="retired">Retired/Sold</option>
                                </select>
                            </div>
                        </div>

                        {/* Computer Specs Section */}
                        {category === 'computer' && (
                            <div className="col-span-2 bg-accent/5 border border-accent/10 rounded-xl p-4 mt-2 mb-2 animate-in fade-in slide-in-from-top-2">
                                <h4 className="text-xs font-bold uppercase text-accent mb-3 flex items-center gap-2">
                                    <Monitor size={14} /> Computer Specifications
                                </h4>
                                <div className="grid grid-cols-2 gap-3">
                                    <Input label="Hostname" placeholder="e.g. WORKSTATION-01" {...register('hostname')} />
                                    <Input label="OS" placeholder="e.g. Windows 11 Pro" {...register('os')} />
                                    <Input label="CPU" placeholder="e.g. Ryzen 9 5950X" {...register('cpu')} />
                                    <Input label="RAM" placeholder="e.g. 64GB DDR4" {...register('ram')} />
                                    <div className="col-span-2">
                                        <Input label="GPU" placeholder="e.g. RTX 3080 Ti" {...register('gpu')} />
                                    </div>
                                </div>
                            </div>
                        )}

                        <div className="grid grid-cols-3 gap-4">
                            <Input label="Value ($)" type="number" step="0.01" {...register('value', { valueAsNumber: true })} />
                            <Input label="Location" placeholder="e.g. Office, Garage" {...register('location')} />
                            <Input label="Purchase Date" type="date" {...register('purchase_date')} />
                        </div>

                        <div className="p-4 bg-white/5 rounded-xl border border-white/5 space-y-4">
                            <h4 className="text-xs font-bold uppercase text-gray-400 flex items-center gap-2">
                                <Monitor size={14} /> Technical Details
                            </h4>
                            <div className="grid grid-cols-3 gap-4">
                                <Input label="Make / Manufacturer" placeholder="e.g. Dell" {...register('make')} />
                                <Input label="Model" placeholder="e.g. XPS 15" {...register('model')} />
                                <Input label="Serial Number" placeholder="S/N..." {...register('serial_number')} />
                            </div>
                        </div>

                        <div>
                            <label className="block text-xs font-bold uppercase text-gray-500 mb-1">Description / Notes</label>
                            <textarea
                                {...register('description')}
                                className="w-full h-24 bg-black/50 border border-white/10 rounded-lg p-3 text-sm text-white focus:outline-none focus:border-accent resize-none"
                                placeholder="Add any additional details, history, or notes here..."
                            />
                        </div>
                    </form>
                </div>

                {/* Footer */}
                <div className="p-6 border-t border-white/10 flex justify-end gap-3 bg-black/20">
                    <Button variant="ghost" onClick={onClose} type="button">Cancel</Button>
                    <Button type="submit" form="asset-form" disabled={isSubmitting}>
                        <Save size={16} />
                        {isEditing ? 'Save Changes' : 'Register Asset'}
                    </Button>
                </div>
            </div>
        </div>,
        document.body
    );
}

