import React, { useState } from 'react';
import type { InventoryItem } from '../../lib/db'; // Make sure db.ts is updated
import { motion } from 'framer-motion';
import { Thermometer, Trash2, Minus, Maximize2 } from 'lucide-react';

interface FilamentSpoolCardProps {
    item: InventoryItem;
    onUpdate: (id: number, updates: Partial<InventoryItem>) => void;
    onDelete: (id: number) => void;
}

export function FilamentSpoolCard({ item, onUpdate, onDelete }: FilamentSpoolCardProps) {
    const props = item.properties || {};
    const color = props.color_hex || '#FFFFFF';
    const material = props.material || 'PLA';
    const initialWeight = props.weight_total || 1000;
    const remaining = item.quantity; // in grams
    const percentage = Math.min(100, Math.max(0, (remaining / initialWeight) * 100));

    // Spool Radius for SVG
    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (percentage / 100) * circumference;

    const [useAmount, setUseAmount] = useState<string>('');

    const handleConsume = (e: React.FormEvent) => {
        e.preventDefault();
        const amount = parseInt(useAmount);
        if (amount > 0) {
            onUpdate(item.id!, { quantity: Math.max(0, remaining - amount) });
            setUseAmount('');
        }
    };

    return (
        <motion.div
            className="relative bg-black border border-white/10 rounded-xl overflow-hidden shadow-lg group hover:border-white/30 transition-all w-full aspect-[4/5] flex flex-col"
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
        >
            {/* Top Bar: Brand & Material */}
            <div className="absolute top-0 left-0 right-0 p-3 flex justify-between items-start z-10 bg-gradient-to-b from-black/80 to-transparent">
                <div>
                    <span className="text-[10px] uppercase font-bold text-gray-400 block tracking-wider">{props.brand || 'GENERIC'}</span>
                    <span className="text-xl font-black uppercase text-white tracking-tight drop-shadow-md" style={{ color: color }}>
                        {material}
                    </span>
                </div>
                <div className="flex gap-1 text-[9px] font-mono text-gray-500 bg-black/50 p-1 rounded backdrop-blur-sm border border-white/5">
                    <span className="flex items-center gap-0.5"><Thermometer size={10} /> {props.temp_nozzle || '200'}°</span>
                    <span className="text-gray-700">|</span>
                    <span className="flex items-center gap-0.5"><Maximize2 size={10} /> {props.temp_bed || '60'}°</span>
                </div>
            </div>

            {/* Center: Spool Visualization */}
            <div className="flex-1 flex items-center justify-center relative">
                {/* Visual Spool Ring */}
                <div className="relative w-40 h-40 flex items-center justify-center">
                    {/* Background Circle (Empty Spool) */}
                    <svg className="absolute inset-0 w-full h-full -rotate-90 transform">
                        <circle
                            cx="50%"
                            cy="50%"
                            r={radius}
                            fill="transparent"
                            stroke="#1a1a1a"
                            strokeWidth="12"
                        />
                        {/* Filament Circle */}
                        <circle
                            cx="50%"
                            cy="50%"
                            r={radius}
                            fill="transparent"
                            stroke={color}
                            strokeWidth="12"
                            strokeDasharray={circumference}
                            strokeDashoffset={offset}
                            strokeLinecap="round"
                            className="transition-all duration-1000 ease-out drop-shadow-[0_0_10px_rgba(255,255,255,0.2)]"
                        />
                    </svg>

                    {/* Inner Info */}
                    <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                        <span className="text-2xl font-black text-white tabular-nums tracking-tighter">
                            {percentage.toFixed(0)}<span className="text-xs text-gray-500 font-normal">%</span>
                        </span>
                        <span className="text-[10px] text-gray-400 font-mono mt-[-2px]">{remaining}g</span>
                    </div>
                </div>
            </div>

            {/* Bottom Actions (Consume) */}
            <div className="p-3 bg-white/5 border-t border-white/10 backdrop-blur-sm">
                <form onSubmit={handleConsume} className="flex gap-2">
                    <div className="relative flex-1">
                        <input
                            type="number"
                            className="w-full bg-black border border-white/20 rounded p-1.5 pl-2 text-xs text-white focus:outline-none focus:border-accent font-mono"
                            placeholder="Use (g)"
                            value={useAmount}
                            onChange={e => setUseAmount(e.target.value)}
                        />
                        <span className="absolute right-2 top-1.5 text-[10px] text-gray-500 pointer-events-none">g</span>
                    </div>
                    <button
                        type="submit"
                        disabled={!useAmount}
                        className="bg-white/10 hover:bg-white/20 disabled:opacity-50 text-white rounded p-1.5 px-3 transition-colors flex items-center justify-center"
                    >
                        <Minus size={14} />
                    </button>
                    <button
                        type="button"
                        onClick={() => onDelete(item.id!)}
                        className="bg-red-900/20 hover:bg-red-900/40 text-red-400 rounded p-1.5 px-2 transition-colors border border-red-900/30"
                    >
                        <Trash2 size={14} />
                    </button>
                </form>
            </div>
        </motion.div>
    );
}
