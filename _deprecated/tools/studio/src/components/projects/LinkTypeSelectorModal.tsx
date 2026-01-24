import { toast } from 'sonner';
import { db } from '../../lib/db';
import { ArrowRight, ArrowLeft, Link2, X } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';

interface LinkTypeSelectorModalProps {
    sourceId: number;
    targetId: number;
    onClose: () => void;
    onComplete: () => void;
}

export function LinkTypeSelectorModal({ sourceId, targetId, onClose, onComplete }: LinkTypeSelectorModalProps) {
    const source = useLiveQuery(() => db.projects.get(sourceId));
    const target = useLiveQuery(() => db.projects.get(targetId));

    if (!source || !target) return null;

    const handleLink = async (type: 'blocks' | 'blocked-by' | 'related') => {
        try {
            if (type === 'blocks') {
                // Source BLOCKS Target (Source -> Target)
                // Source is UPSTREAM of Target
                const current = target.upstream_dependencies || [];
                if (!current.includes(sourceId)) {
                    await db.projects.update(targetId, { upstream_dependencies: [...current, sourceId] });
                }
            } else if (type === 'blocked-by') {
                // Source is BLOCKED BY Target (Target -> Source)
                // Target is UPSTREAM of Source
                const current = source.upstream_dependencies || [];
                if (!current.includes(targetId)) {
                    await db.projects.update(sourceId, { upstream_dependencies: [...current, targetId] });
                }
            } else if (type === 'related') {
                // Mutual soft link (Related)
                // Add to BOTH
                const currentSourceRelated = source.related_projects || [];
                const currentTargetRelated = target.related_projects || [];

                if (!currentSourceRelated.includes(targetId)) {
                    await db.projects.update(sourceId, { related_projects: [...currentSourceRelated, targetId] });
                }
                if (!currentTargetRelated.includes(sourceId)) {
                    await db.projects.update(targetId, { related_projects: [...currentTargetRelated, sourceId] });
                }
            }
            onComplete();
        } catch (e) {
            console.error(e);
            toast.error("Failed to link projects");
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-neutral-900 border border-white/10 rounded-xl p-6 max-w-lg w-full shadow-2xl animate-in fade-in zoom-in duration-200">
                <div className="flex justify-between items-start mb-6">
                    <h2 className="text-xl font-bold text-white uppercase tracking-tight">Define Relationship</h2>
                    <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={20} /></button>
                </div>

                <div className="flex items-center justify-center gap-8 mb-8">
                    <div className="text-center w-1/3">
                        <div className="font-mono text-xs text-accent mb-1">SOURCE</div>
                        <div className="font-bold text-white truncate px-2 py-1 bg-white/5 rounded border border-white/10">{source.title}</div>
                    </div>
                    <div className="text-gray-500 font-mono text-xs">VS</div>
                    <div className="text-center w-1/3">
                        <div className="font-mono text-xs text-blue-400 mb-1">TARGET</div>
                        <div className="font-bold text-white truncate px-2 py-1 bg-white/5 rounded border border-white/10">{target.title}</div>
                    </div>
                </div>

                <div className="grid gap-4">
                    <button onClick={() => handleLink('blocks')} className="group flex items-center gap-4 p-4 rounded-lg border border-white/10 hover:border-accent hover:bg-accent/5 transition-all text-left">
                        <div className="bg-white/5 p-3 rounded-full text-white group-hover:bg-accent group-hover:text-black transition-colors">
                            <ArrowRight size={24} />
                        </div>
                        <div>
                            <div className="font-bold text-white group-hover:text-accent">BLOCKS TARGET</div>
                            <div className="text-xs text-gray-400">Source must be done BEFORE Target starts. (Dependency)</div>
                        </div>
                    </button>

                    <button onClick={() => handleLink('blocked-by')} className="group flex items-center gap-4 p-4 rounded-lg border border-white/10 hover:border-blue-400 hover:bg-blue-400/5 transition-all text-left">
                        <div className="bg-white/5 p-3 rounded-full text-white group-hover:bg-blue-400 group-hover:text-black transition-colors">
                            <ArrowLeft size={24} />
                        </div>
                        <div>
                            <div className="font-bold text-white group-hover:text-blue-400">IS BLOCKED BY TARGET</div>
                            <div className="text-xs text-gray-400">Target must be done BEFORE Source starts. (Reverse Dependency)</div>
                        </div>
                    </button>

                    <button onClick={() => handleLink('related')} className="group flex items-center gap-4 p-4 rounded-lg border border-white/10 hover:border-purple-400 hover:bg-purple-400/5 transition-all text-left">
                        <div className="bg-white/5 p-3 rounded-full text-white group-hover:bg-purple-400 group-hover:text-black transition-colors">
                            <Link2 size={24} />
                        </div>
                        <div>
                            <div className="font-bold text-white group-hover:text-purple-400">RELATED / SEE ALSO</div>
                            <div className="text-xs text-gray-400">Projects are related but have no strict order.</div>
                        </div>
                    </button>
                </div>
            </div>
        </div>
    );
}
