import { Shield, CheckSquare, AlertTriangle, Lock, Unlock, CheckCircle } from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';
import { useState } from 'react';
import { db, type Project, type SafetyData, type HazardClass } from '../../lib/db';
import { HAZARD_DEFS } from '../../lib/safety';

interface SafetyGateProps {
    project: Project;
}

export function SafetyGate({ project }: SafetyGateProps) {
    const [safetyData, setSafetyData] = useState<SafetyData>(project.safety_data || {
        hazards: [],
        controls: [],
        is_ready: false
    });

    // If no hazards, don't render anything in view mode (or render "Safe")
    // But user wants it at bottom. If empty, maybe just null or a "No Hazards" badge?
    // Let's render "No Hazards Identified" if empty.

    // Sync to DB when local state changes (only for controls now)
    const updateDB = async (newData: SafetyData) => {
        setSafetyData(newData);
        await db.projects.update(project.id!, { safety_data: newData });
    };

    const toggleControl = (controlId: string) => {
        const newControls = safetyData.controls.map(c =>
            c.id === controlId ? { ...c, is_checked: !c.is_checked } : c
        );

        // Check if all are checked
        const allChecked = newControls.every(c => c.is_checked);
        const isReady = allChecked;

        updateDB({
            ...safetyData,
            controls: newControls,
            is_ready: isReady,
            approved_at: isReady ? new Date() : undefined
        });

        if (isReady && !safetyData.is_ready) {
            toast.success("BENCH READY: Safety Protocols Verified");
        }
    };

    const renderGateStatus = () => {
        if (safetyData.hazards.length === 0) return (
            <div className="flex items-center gap-2 text-green-500 text-sm font-bold bg-green-500/10 px-3 py-1 rounded">
                <CheckCircle size={16} /> SAFE / NO HAZARDS DECLARED
            </div>
        );
        if (safetyData.is_ready) return (
            <div className="flex items-center gap-2 text-green-400 text-sm font-bold bg-green-500/10 px-3 py-1 rounded border border-green-500/20">
                <Unlock size={16} /> BENCH READY (CONTROLS ACTIVE)
            </div>
        );
        return (
            <div className="flex items-center gap-2 text-red-500 text-sm font-bold bg-red-500/10 px-3 py-1 rounded border border-red-500/20 animate-pulse">
                <Lock size={16} /> BENCH LOCKED (PROTOCOLS REQUIRED)
            </div>
        );
    };

    return (
        <div className="bg-[#0A0A0A] border border-white/10 rounded-xl overflow-hidden mb-6">
            <div className="bg-white/5 p-4 flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <Shield className={safetyData.hazards.length > 0 ? "text-accent" : "text-gray-500"} size={20} />
                    <h3 className="font-bold text-white">SAFETY PROTOCOLS</h3>
                </div>
                {renderGateStatus()}
            </div>

            <div className="p-4">
                {safetyData.hazards.length === 0 ? (
                    <div className="text-center py-8 text-gray-600 italic">
                        No specific safety hazards identified for this project.
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {/* Render a card/block for each Active Hazard */}
                        {safetyData.hazards.map(hazard => {
                            const def = HAZARD_DEFS[hazard];
                            const controls = safetyData.controls.filter(c => c.hazard === hazard);
                            if (!def) return null;

                            return (
                                <div key={hazard} className="border border-white/10 rounded bg-white/5 p-4 flex flex-col gap-3">
                                    <div className="flex items-center gap-2 border-b border-white/5 pb-2">
                                        <def.icon size={18} className={def.color} />
                                        <span className="font-bold text-sm text-gray-200">{def.label}</span>
                                    </div>

                                    <div className="space-y-2">
                                        {controls.map(control => (
                                            <button
                                                key={control.id}
                                                onClick={() => toggleControl(control.id)}
                                                className="flex items-start gap-2 text-left group w-full"
                                            >
                                                <div className={clsx(
                                                    "mt-0.5 w-4 h-4 rounded border flex items-center justify-center shrink-0 transition-all",
                                                    control.is_checked
                                                        ? "bg-green-500 border-green-500 text-black"
                                                        : "border-gray-600 group-hover:border-white"
                                                )}>
                                                    {control.is_checked && <CheckSquare size={12} />}
                                                </div>
                                                <span className={clsx("text-xs transition-colors", control.is_checked ? "text-gray-500 line-through" : "text-gray-300")}>
                                                    {control.description}
                                                </span>
                                            </button>
                                        ))}
                                        {controls.length === 0 && <span className="text-xs text-gray-600 italic">No specific controls.</span>}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>
        </div>
    );
}



