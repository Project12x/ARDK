import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type InventoryItem } from '../../lib/db';
import { InventoryTable } from './InventoryTable';
import { FilamentDistributionChart } from './FilamentDistributionChart';
import { Search, Plus, Box, List, LayoutGrid } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FilamentSchema, type FilamentFormData } from '../../lib/schemas';
import { FilamentSpoolCard } from './FilamentSpoolCard';

export function FilamentBunker({ viewMode = 'grid' }: { viewMode?: 'grid' | 'table' }) {
    const [searchTerm, setSearchTerm] = useState('');
    const [materialFilter, setMaterialFilter] = useState<string | null>(null);
    const [isAddMode, setIsAddMode] = useState(false);

    const { register, handleSubmit, reset, formState: { errors } } = useForm<FilamentFormData>({
        resolver: zodResolver(FilamentSchema),
        defaultValues: {
            material: 'PLA',
            color: '#ffffff',
            weight: 1000,
            cost: 20,
            temp_nozzle: 200,
            temp_bed: 60
        }
    });

    const filaments = useLiveQuery(
        () => db.inventory
            .filter(i => i.category === 'Filament' || (i.properties?.material !== undefined))
            .toArray()
    );

    const filteredFilaments = filaments?.filter(f => {
        const matchesSearch = f.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            f.properties?.brand?.toLowerCase().includes(searchTerm.toLowerCase());
        const matchesMaterial = materialFilter ? f.properties?.material === materialFilter : true;
        return matchesSearch && matchesMaterial;
    });

    const materials = Array.from(new Set(filaments?.map(f => f.properties?.material).filter(Boolean)));

    const onSubmit = async (data: FilamentFormData) => {
        await db.inventory.add({
            name: data.name,
            category: 'Filament',
            type: 'consumable',
            quantity: data.weight, // Grams
            units: 'g',
            location: 'Bunker',
            min_stock: 100,
            unit_cost: data.cost,
            updated_at: new Date(),
            properties: {
                brand: data.brand || 'Generic',
                material: data.material,
                color_hex: data.color,
                weight_total: data.weight,
                temp_nozzle: data.temp_nozzle,
                temp_bed: data.temp_bed
            }
        });
        setIsAddMode(false);
        reset();
    };

    const handleUpdate = (id: number, updates: Partial<InventoryItem>) => {
        db.inventory.update(id, updates);
    };

    const handleDelete = (id: number) => {
        if (confirm("Recycle this spool?")) {
            db.inventory.delete(id);
        }
    };

    return (
        <div className="h-full flex flex-col gap-6 p-6 overflow-hidden">
            {/* Header */}
            <div className="flex justify-between items-center shrink-0">
                <div>
                    <h2 className="text-2xl font-black uppercase text-white tracking-tighter flex items-center gap-2">
                        <Box className="text-accent" /> THE FILAMENT BUNKER
                    </h2>
                    <p className="text-xs font-mono text-gray-500">
                        {filaments?.length || 0} SPOOLS // {((filaments?.reduce((acc, curr) => acc + curr.quantity, 0) || 0) / 1000).toFixed(1)}KG RESERVE
                    </p>
                </div>
                <button
                    onClick={() => setIsAddMode(!isAddMode)}
                    className="bg-accent hover:bg-accent/80 text-black font-bold uppercase py-2 px-4 rounded flex items-center gap-2 transition-colors"
                >
                    <Plus size={16} /> New Spool
                </button>
            </div>

            {/* Data Visualization Area */}
            {filaments && filaments.length > 0 && (
                <div className="shrink-0">
                    <FilamentDistributionChart items={filaments} />
                </div>
            )}

            {/* Controls */}
            <div className="flex gap-4 items-center shrink-0 bg-white/5 p-2 rounded-lg border border-white/5">
                <div className="relative flex-1">
                    <Search className="absolute left-3 top-2.5 text-gray-500" size={16} />
                    <input
                        className="w-full bg-black border border-white/10 rounded-md py-2 pl-10 pr-4 text-sm text-white focus:outline-none focus:border-accent"
                        placeholder="Search Bunker..."
                        value={searchTerm}
                        onChange={e => setSearchTerm(e.target.value)}
                    />
                </div>
                {/* Visual Material Filter */}
                <div className="flex gap-2">
                    <button
                        onClick={() => setMaterialFilter(null)}
                        className={clsx("px-3 py-1.5 rounded textxs uppercase font-bold text-[10px] border transition-colors", !materialFilter ? "bg-white text-black border-white" : "bg-black text-gray-500 border-white/10 hover:border-white/30")}
                    >
                        ALL
                    </button>
                    {materials.map(m => (
                        <button
                            key={m as string}
                            onClick={() => setMaterialFilter(m as string)}
                            className={clsx("px-3 py-1.5 rounded textxs uppercase font-bold text-[10px] border transition-colors", materialFilter === m ? "bg-accent/20 text-accent border-accent" : "bg-black text-gray-500 border-white/10 hover:border-white/30")}
                        >
                            {m as string}
                        </button>
                    ))}
                </div>

                <div className="w-[1px] h-6 bg-white/10 mx-2" />
            </div>

            {/* Add Panel (Inline) */}
            <AnimatePresence>
                {isAddMode && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: 'auto', opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        className="overflow-hidden shrink-0"
                    >
                        <form onSubmit={handleSubmit(onSubmit)} className="bg-black border border-industrial/20 rounded-lg p-4 grid grid-cols-1 md:grid-cols-6 gap-4 items-start">
                            <div className="md:col-span-2">
                                <label className="text-[10px] uppercase text-gray-500 font-bold block mb-1">Spool Name {errors.name && <span className="text-red-500 ml-1">{errors.name.message}</span>}</label>
                                <input {...register('name')} className="w-full bg-white/5 border border-white/10 rounded p-2 text-sm text-white focus:border-industrial outline-none" placeholder="e.g. PolyLite PLA Pro" />
                            </div>

                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold block mb-1">Material</label>
                                <select {...register('material')} className="w-full bg-white/5 border border-white/10 rounded p-2 text-sm text-white focus:border-industrial outline-none">
                                    <option value="PLA" className="bg-black">PLA</option>
                                    <option value="PETG" className="bg-black">PETG</option>
                                    <option value="ABS" className="bg-black">ABS</option>
                                    <option value="ASA" className="bg-black">ASA</option>
                                    <option value="TPU" className="bg-black">TPU</option>
                                    <option value="Resin" className="bg-black">Resin</option>
                                </select>
                            </div>

                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold block mb-1">Color {errors.color && <span className="text-red-500 text-[9px]">!</span>}</label>
                                <div className="flex gap-2 relative">
                                    <div className="w-10 h-10 rounded border border-white/20 shrink-0 overflow-hidden relative">
                                        <input type="color" {...register('color')} className="absolute -top-2 -left-2 w-16 h-16 p-0 cursor-pointer border-0" />
                                    </div>
                                    <input {...register('color')} className="w-full bg-white/5 border border-white/10 rounded p-2 text-xs text-white uppercase font-mono" />
                                </div>
                            </div>

                            <div>
                                <label className="text-[10px] uppercase text-gray-500 font-bold block mb-1">Weight (g) {errors.weight && <span className="text-red-500 text-[9px]">!</span>}</label>
                                <input type="number" {...register('weight', { valueAsNumber: true })} className="w-full bg-white/5 border border-white/10 rounded p-2 text-sm text-white font-mono" />
                            </div>

                            <div className="flex items-end h-full pt-6 md:pt-0">
                                <button type="submit" className="w-full bg-industrial text-black font-bold uppercase p-2 rounded hover:bg-industrial/80 transition-colors h-10 flex items-center justify-center">
                                    Add Spool
                                </button>
                            </div>
                        </form>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Grid or Table */}
            <div className="flex-1 overflow-y-auto pb-10 pr-2 custom-scrollbar">
                {viewMode === 'table' ? (
                    <InventoryTable
                        data={filteredFilaments || []}
                        onUpdate={handleUpdate}
                        onDelete={handleDelete}
                    />
                ) : (
                    <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-6">
                        {filteredFilaments?.map(item => (
                            <FilamentSpoolCard
                                key={item.id}
                                item={item}
                                onUpdate={handleUpdate}
                                onDelete={handleDelete}
                            />
                        ))}

                        {(!filteredFilaments || filteredFilaments.length === 0) && (
                            <div className="col-span-full py-20 text-center text-gray-600 border border-dashed border-white/5 rounded-xl uppercase tracking-widest text-sm">
                                Bunker Empty {searchTerm && `/ No matches for "${searchTerm}"`}
                            </div>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
}
