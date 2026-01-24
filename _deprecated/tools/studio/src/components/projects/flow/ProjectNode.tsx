import { memo } from 'react';
import { Handle, Position, type NodeProps } from 'reactflow';
import clsx from 'clsx';
import { Zap, AlertTriangle, Github } from 'lucide-react';
import type { Project } from '../../../lib/db';

// Define the data expected by the node
export interface ProjectNodeData {
    project: Project;
    label_color?: string;
    is_blocked?: boolean; // Display red border?
}

export const ProjectNode = memo(({ data, selected }: NodeProps<ProjectNodeData>) => {
    const { project, label_color, is_blocked } = data;

    const colorValue = label_color || (project.status === 'active' ? '#10b981' : '#6b7280');
    const isHex = colorValue.startsWith('#') || colorValue.startsWith('rgb');

    return (
        <div className={clsx(
            "w-[280px] bg-neutral-900 rounded-lg shadow-xl overflow-hidden group transition-all duration-300",
            selected ? "ring-2 ring-accent shadow-[0_0_20px_rgba(59,130,246,0.3)]" : "border border-white/10 hover:border-accent/50",
            is_blocked && "border-red-500/50"
        )}>
            {/* Input Handle (Target) - Left Side */}
            <Handle
                type="target"
                position={Position.Left}
                className="!w-3 !h-6 !bg-neutral-800 !border-2 !border-white/20 !rounded-sm !-left-2 hover:!bg-accent hover:!border-accent transition-colors"
            />

            <div className="flex h-[90px]">
                {/* Status Stripe */}
                <div
                    className="w-2 h-full shrink-0"
                    style={{ backgroundColor: isHex ? colorValue : undefined }}
                />

                <div className="flex-1 p-3 flex flex-col justify-between relative">
                    {/* Header */}
                    <div className="flex justify-between items-start">
                        <div className="min-w-0 pr-2">
                            <div className="flex items-center gap-2 mb-0.5">
                                <span className="text-[10px] text-accent font-mono tracking-wider">{project.project_code || `P-${project.id}`}</span>
                                {project.priority && (
                                    <span className="flex items-center gap-0.5 text-[9px] text-gray-500">
                                        <Zap size={8} className="text-red-500" />{project.priority}
                                    </span>
                                )}
                            </div>
                            <div className="font-bold text-white text-sm leading-tight line-clamp-2" title={project.title}>
                                {project.title}
                            </div>
                        </div>
                    </div>

                    {/* Footer */}
                    <div className="flex justify-between items-center mt-2">
                        <span className="text-[10px] text-gray-500 font-mono uppercase bg-white/5 px-1.5 py-0.5 rounded">
                            {project.status}
                        </span>
                        {/* Risk Badge if high */}
                        {project.risk_level === 'high' && (
                            <span className="flex items-center gap-1 text-[9px] text-red-400 bg-red-900/20 px-1.5 py-0.5 rounded border border-red-900/30">
                                <AlertTriangle size={8} /> RISK
                            </span>
                        )}
                        {project.github_repo && (
                            <span className="text-gray-500 ml-1 opacity-70" title="Linked Repo">
                                <Github size={12} />
                            </span>
                        )}
                    </div>
                </div>
            </div>

            {/* Output Handle (Source) - Right Side */}
            <Handle
                type="source"
                position={Position.Right}
                className="!w-4 !h-4 !bg-neutral-800 !border-2 !border-white/20 !rounded-full !-right-2 hover:!bg-accent hover:!border-accent hover:!scale-110 transition-all flex items-center justify-center"
            >
                {/* Optional Icon inside handle, though styling allows just simple dot */}
            </Handle>
        </div>
    );
});
