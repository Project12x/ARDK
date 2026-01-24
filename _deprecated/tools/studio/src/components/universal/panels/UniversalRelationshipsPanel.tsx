import { useLiveQuery } from 'dexie-react-hooks';
import { LinkService } from '../../../services/LinkService';
import { getEntityById } from '../../../lib/commands';
import type { EntityLink } from '../../../lib/db';
import type { EntityType } from '../../../lib/universal';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowRight, ArrowLeft, Archive, Database, Link as LinkIcon } from 'lucide-react';
import clsx from 'clsx';
import { ENTITY_REGISTRY } from '../../../lib/registry/entityRegistry';

interface UniversalRelationshipsPanelProps {
    entityType: EntityType;
    entityId: string | number;
}

export function UniversalRelationshipsPanel({ entityType, entityId }: UniversalRelationshipsPanelProps) {
    const links = useLiveQuery(() => LinkService.getAllConnections(entityType, Number(entityId)), [entityType, entityId]) || [];
    const navigate = useNavigate();

    // Grouping could be added later (e.g. Dependencies vs Related), simple list for now

    return (
        <div className="space-y-4 p-4 animate-in fade-in slide-in-from-bottom-2">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-accent/80 font-mono">
                    <LinkIcon size={16} />
                    <h3 className="text-sm font-bold tracking-wider">NETWORK ({links.length})</h3>
                </div>
                <button
                    onClick={() => {
                        // TODO: Open Link Creator Modal
                    }}
                    className="text-xs text-gray-400 hover:text-white hover:underline disabled:opacity-50"
                    disabled
                >
                    + ADD LINK
                </button>
            </div>

            <div className="grid grid-cols-1 gap-2">
                {links.length === 0 ? (
                    <div className="text-gray-600 italic text-sm py-4 text-center border border-dashed border-white/10 rounded-lg">
                        No connections found.
                    </div>
                ) : (
                    links.map(link => (
                        <RelatedEntityCard
                            key={link.id}
                            link={link}
                            currentType={entityType}
                            currentId={entityId}
                        />
                    ))
                )}
            </div>
        </div>
    );
}

function RelatedEntityCard({ link, currentType, currentId }: { link: EntityLink, currentType: EntityType, currentId: string | number }) {
    // Determine which side is "Other"
    // Using loose equality for ID to handle string/number mismatch
    const isSource = link.source_type === currentType && String(link.source_id) === String(currentId);

    const otherType = isSource ? link.target_type : link.source_type;
    const otherId = isSource ? link.target_id : link.source_id;
    const relationship = link.relationship;

    // Fetch Other Entity Details
    const otherEntity = useLiveQuery(
        () => getEntityById(otherType, otherId),
        [otherType, otherId]
    );

    const config = ENTITY_REGISTRY[otherType];
    const Icon = config?.icon || Database;

    if (!otherEntity) {
        return (
            <div className="flex items-center gap-3 p-3 rounded-lg bg-black/20 border border-white/5 animate-pulse">
                <div className="w-8 h-8 rounded-full bg-white/5" />
                <div className="h-4 w-24 bg-white/5 rounded" />
            </div>
        );
    }

    return (
        <Link
            to={`/entity/${otherType}/${otherId}`}
            className="flex items-center gap-3 p-3 rounded-lg bg-black/20 border border-white/5 hover:bg-white/5 hover:border-accent/30 transition-all group relative overflow-hidden"
        >
            {/* Direction Indicator */}
            <div className={clsx(
                "absolute left-0 top-0 bottom-0 w-1",
                isSource ? "bg-blue-500/50" : "bg-emerald-500/50" // Blue = Outgoing, Emerald = Incoming
            )} />

            {/* Icon */}
            <div className="shrink-0 p-2 rounded-md bg-white/5 text-gray-400 group-hover:text-white transition-colors">
                <Icon size={18} />
            </div>

            {/* Info */}
            <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                    <span className="font-medium text-sm text-gray-200 group-hover:text-accent truncate">
                        {otherEntity.title || otherEntity.name || `Unititled ${otherType}`}
                    </span>
                    <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-white/5 text-gray-500">
                        {otherType}
                    </span>
                </div>
                <div className="flex items-center gap-1.5 text-xs text-gray-500 mt-0.5 font-mono">
                    {isSource ? (
                        <>
                            <span>This</span>
                            <ArrowRight size={10} className="text-blue-400" />
                            <span className="text-blue-300">{relationship.replace('_', ' ')}</span>
                            <ArrowRight size={10} className="text-blue-400" />
                            <span>That</span>
                        </>
                    ) : (
                        <>
                            <span>That</span>
                            <ArrowRight size={10} className="text-emerald-400" />
                            <span className="text-emerald-300">{relationship.replace('_', ' ')}</span>
                            <ArrowRight size={10} className="text-emerald-400" />
                            <span>This</span>
                        </>
                    )}
                </div>
            </div>

            {/* Status (if available) */}
            {otherEntity.status && (
                <div className="shrink-0 text-[10px] bg-white/5 px-2 py-1 rounded text-gray-400">
                    {otherEntity.status}
                </div>
            )}
        </Link>
    );
}
