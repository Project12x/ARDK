import type { Project } from '../../../lib/db';
import { Clock, DollarSign, Activity } from 'lucide-react';

export function ProjectStatsWidget({ project }: { project: Project }) {
    return (
        <div className="h-full bg-black/40 border border-white/10 rounded-xl p-4 grid grid-cols-2 gap-4">
            {/* Hours */}
            <div className="flex flex-col justify-center p-3 bg-white/5 rounded-lg border-l-2 border-accent/50">
                <div className="flex items-center gap-2 text-gray-400 mb-1">
                    <Clock size={14} />
                    <span className="text-[10px] font-mono uppercase">Timeline</span>
                </div>
                <div className="text-xl font-mono text-white">
                    {project.total_theorized_hours || 0}<span className="text-sm text-gray-500">h</span>
                </div>
            </div>

            {/* Cost */}
            <div className="flex flex-col justify-center p-3 bg-white/5 rounded-lg border-l-2 border-green-500/50">
                <div className="flex items-center gap-2 text-gray-400 mb-1">
                    <DollarSign size={14} />
                    <span className="text-[10px] font-mono uppercase">Budget</span>
                </div>
                <div className="text-xl font-mono text-white">
                    ${project.financial_spend || 0} <span className="text-[10px] text-gray-500">/ ${project.financial_budget || 0}</span>
                </div>
            </div>

            {/* Status - Full Width */}
            <div className="col-span-2 flex items-center justify-between p-2 bg-white/5 rounded border border-white/5">
                <div className="flex items-center gap-2">
                    <Activity size={14} className="text-blue-400" />
                    <span className="text-xs text-gray-300">System Integrity</span>
                </div>
                <span className="text-xs font-bold text-blue-400">98%</span>
            </div>
        </div>
    );
}
