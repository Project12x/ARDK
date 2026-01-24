import { useState } from 'react';
import { ChevronRight, ChevronDown, FileText, Database, Layers, Book, AlertTriangle, Info } from 'lucide-react';

interface BlueprintNodeProps {
    data: any;
    label: string;
    level?: number;
}

// Recursive component to render JSON tree
function BlueprintNode({ data, label, level = 0 }: BlueprintNodeProps) {
    const [expanded, setExpanded] = useState(level < 2); // Auto-expand top levels

    const isObject = data && typeof data === 'object' && !Array.isArray(data);
    const isArray = Array.isArray(data);
    const hasChildren = (isObject && Object.keys(data).length > 0) || (isArray && data.length > 0);

    const getIcon = (key: string) => {
        if (key.includes('overview')) return <Info size={14} className="text-blue-400" />;
        if (key.includes('design')) return <Layers size={14} className="text-purple-400" />;
        if (key.includes('bom')) return <Database size={14} className="text-yellow-400" />;
        if (key.includes('notebook')) return <Book size={14} className="text-green-400" />;
        if (key.includes('hazards') || key.includes('critical')) return <AlertTriangle size={14} className="text-red-400" />;
        return <FileText size={14} className="text-gray-500" />;
    };

    if (!data) return null;

    if (hasChildren) {
        return (
            <div className="ml-4 border-l border-white/10 pl-2">
                <div
                    className="flex items-center gap-2 py-1 cursor-pointer hover:bg-white/5 rounded px-2 transition-colors group"
                    onClick={() => setExpanded(!expanded)}
                >
                    <span className="text-accent/70 group-hover:text-accent transition-colors">
                        {expanded ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
                    </span>
                    {getIcon(label.toLowerCase())}
                    <span className="font-mono text-sm font-bold text-gray-300 group-hover:text-white uppercase tracking-wider">
                        {label.replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-gray-600 bg-white/5 px-1 rounded">
                        {isArray ? `[${data.length}]` : '{ }'}
                    </span>
                </div>

                {expanded && (
                    <div className="animate-in slide-in-from-top-2 fade-in duration-200">
                        {isObject && Object.entries(data).map(([key, value]) => (
                            <BlueprintNode key={key} label={key} data={value} level={level + 1} />
                        ))}
                        {isArray && data.map((item: any, index: number) => (
                            <BlueprintNode key={index} label={`${index + 1}`} data={item} level={level + 1} />
                        ))}
                    </div>
                )}
            </div>
        );
    }

    return (
        <div className="ml-8 flex items-start gap-3 py-1 text-sm border-l border-white/5 pl-2 hover:bg-white/5 rounded transition-colors pr-2">
            <span className="text-gray-500 font-mono text-xs mt-1 min-w-[100px] text-right overflow-hidden text-ellipsis whitespace-nowrap">
                {label.replace(/_/g, ' ')}:
            </span>
            <span className="text-gray-300 font-sans whitespace-pre-wrap leading-relaxed flex-1">
                {typeof data === 'boolean' ? (data ? 'TRUE' : 'FALSE') : String(data)}
            </span>
        </div>
    );
}

export function ProjectBlueprint({ data }: { data: any }) {
    if (!data || Object.keys(data).length === 0) {
        return (
            <div className="flex flex-col items-center justify-center p-12 text-center text-gray-500 bg-white/5 rounded-xl border border-dashed border-white/10 m-4">
                <Database size={48} className="mb-4 opacity-50" />
                <h3 className="text-lg font-medium text-gray-300">No Blueprint Data</h3>
                <p className="text-sm mt-2 max-w-md">
                    Upload an MDBD document to generate a deep map of this project's structure.
                </p>
            </div>
        );
    }

    return (
        <div className="p-6 bg-black/40 min-h-[500px] rounded-xl border border-white/5 shadow-inner">
            <div className="flex items-center gap-3 mb-6 pb-4 border-b border-white/10">
                <div className="bg-accent/20 p-2 rounded-lg text-accent">
                    <Database size={24} />
                </div>
                <div>
                    <h2 className="text-xl font-bold text-white tracking-tight">Project Blueprint</h2>
                    <p className="text-xs text-accent font-mono">UNIVERSAL DATA MAP</p>
                </div>
            </div>

            <div className="space-y-1">
                {Object.entries(data).sort().map(([key, value]) => (
                    <BlueprintNode key={key} label={key} data={value} />
                ))}
            </div>
        </div>
    );
}
