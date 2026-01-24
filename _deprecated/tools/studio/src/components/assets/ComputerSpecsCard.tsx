import { Server, Cpu, HardDrive, Wifi, Monitor, CircuitBoard } from 'lucide-react';
import clsx from 'clsx';
import type { ComputerSpecs } from '../../lib/db';

interface ComputerSpecsCardProps {
    specs: ComputerSpecs;
    className?: string;
}

export function ComputerSpecsCard({ specs, className }: ComputerSpecsCardProps) {
    if (!specs) return null;

    return (
        <div className={clsx("bg-black/40 border border-accent/20 rounded-xl overflow-hidden font-mono", className)}>
            {/* Header */}
            <div className="bg-accent/5 p-3 border-b border-accent/10 flex items-center justify-between">
                <div className="flex items-center gap-2 text-accent">
                    <Server size={18} />
                    <span className="font-bold tracking-wider text-sm">{specs.hostname.toUpperCase()}</span>
                </div>
                <div className="flex items-center gap-2 text-xs text-gray-500">
                    <span className="bg-white/5 px-2 py-0.5 rounded">{specs.os}</span>
                    {specs.network_interfaces?.[0]?.ip && (
                        <span className="bg-white/5 px-2 py-0.5 rounded flex items-center gap-1">
                            <Wifi size={10} /> {specs.network_interfaces[0].ip}
                        </span>
                    )}
                </div>
            </div>

            <div className="p-4 grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* CPU & GPU */}
                <div className="space-y-4">
                    <div>
                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                            <Cpu size={14} /> CENTRAL PROCESSING
                        </div>
                        <div className="text-white font-bold text-sm border-l-2 border-accent/40 pl-2">
                            {specs.cpu}
                        </div>
                    </div>
                    <div>
                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                            <Monitor size={14} /> GRAPHICS / VIDEO
                        </div>
                        <div className="text-white font-bold text-sm border-l-2 border-purple-500/40 pl-2">
                            {specs.gpu}
                        </div>
                    </div>
                    <div>
                        <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                            <CircuitBoard size={14} /> MEMORY
                        </div>
                        <div className="text-white font-bold text-sm border-l-2 border-green-500/40 pl-2">
                            {specs.ram}
                        </div>
                    </div>
                </div>

                {/* Storage */}
                <div className="space-y-3">
                    <div className="flex items-center gap-2 text-gray-400 text-xs mb-1">
                        <HardDrive size={14} /> STORAGE ARRAY
                    </div>
                    {specs.storage_drives.map((drive, i) => (
                        <div key={i} className="bg-white/5 p-2 rounded border border-white/5 relative overflow-hidden group">
                            <div className="relative z-10 flex justify-between items-center text-xs">
                                <span className={clsx("font-bold", drive.type === 'nvme' ? 'text-accent' : 'text-gray-300')}>
                                    {drive.name}
                                </span>
                                <span className="text-gray-500">{drive.capacity}</span>
                            </div>
                            <div className="relative z-10 text-[10px] text-gray-600 uppercase tracking-widest mt-0.5">
                                {drive.type} • {drive.usage || 'General'}
                            </div>
                            {/* Decorative Bar */}
                            <div className="absolute bottom-0 left-0 h-0.5 bg-accent/30 w-full opacity-50" />
                        </div>
                    ))}
                </div>
            </div>

            {/* Peripherals Footer */}
            {specs.peripherals && specs.peripherals.length > 0 && (
                <div className="bg-black/20 p-3 border-t border-white/5 text-[10px] text-gray-500 flex flex-wrap gap-2">
                    {specs.peripherals.map((p, i) => (
                        <span key={i} className="border border-white/10 px-1.5 py-0.5 rounded hover:border-white/20 transition-colors">
                            {p}
                        </span>
                    ))}
                </div>
            )}
        </div>
    );
}
