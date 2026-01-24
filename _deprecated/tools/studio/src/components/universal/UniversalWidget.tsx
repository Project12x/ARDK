import type { UniversalWidgetDefinition, UniversalEntity } from '../../lib/universal/types';
import { UniversalCard } from './UniversalCard';
import clsx from 'clsx';
import { AreaChart, Area, ResponsiveContainer, XAxis, YAxis, Tooltip } from 'recharts';

interface UniversalWidgetProps {
    definition: UniversalWidgetDefinition;
    className?: string;
    onEntityClick?: (entity: UniversalEntity) => void;
}

export function UniversalWidget({ definition, className, onEntityClick }: UniversalWidgetProps) {
    const { type, title, data } = definition;

    return (
        <div className={clsx("bg-black/40 border border-white/5 rounded-xl overflow-hidden backdrop-blur-sm", className)}>
            {/* Header */}
            <div className="px-4 py-3 border-b border-white/5 flex justify-between items-center">
                <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400">{title}</h3>
                {definition.action && (
                    <button className="text-xs text-accent hover:text-white transition-colors">
                        {definition.action.label}
                    </button>
                )}
            </div>

            {/* Content */}
            <div className="p-4">
                {type === 'stat' && (
                    <div className="flex items-baseline gap-2">
                        <span className="text-3xl font-bold text-white">{data.value || data.count || 0}</span>
                        {data.trend && (
                            <span className={clsx("text-xs font-medium",
                                data.trend > 0 ? "text-green-400" : "text-red-400"
                            )}>
                                {data.trend > 0 ? "+" : ""}{data.trend}%
                            </span>
                        )}
                        {data.label && <span className="text-xs text-gray-500">{data.label}</span>}
                    </div>
                )}

                {type === 'chart' && (
                    <div className="h-32 w-full">
                        {data.series ? (
                            <ResponsiveContainer width="100%" height="100%">
                                <AreaChart data={data.series}>
                                    <defs>
                                        <linearGradient id={`grad-${definition.id}`} x1="0" y1="0" x2="0" y2="1">
                                            <stop offset="5%" stopColor="var(--accent, #a855f7)" stopOpacity={0.3} />
                                            <stop offset="95%" stopColor="var(--accent, #a855f7)" stopOpacity={0} />
                                        </linearGradient>
                                    </defs>
                                    <XAxis dataKey="name" hide />
                                    <YAxis hide />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: '#000', borderColor: '#333' }}
                                        itemStyle={{ color: '#fff' }}
                                    />
                                    <Area
                                        type="monotone"
                                        dataKey="value"
                                        stroke="var(--accent, #a855f7)"
                                        fillOpacity={1}
                                        fill={`url(#grad-${definition.id})`}
                                    />
                                </AreaChart>
                            </ResponsiveContainer>
                        ) : (
                            <div className="h-full flex items-center justify-center text-xs text-gray-500">
                                No chart data
                            </div>
                        )}
                    </div>
                )}

                {type === 'list' && (
                    <div className="flex flex-col gap-2">
                        {data.items?.slice(0, 5).map((item: UniversalEntity) => (
                            <div
                                key={item.urn}
                                onClick={() => onEntityClick?.(item)}
                                className="flex items-center gap-2 p-2 rounded hover:bg-white/5 cursor-pointer group"
                            >
                                <div className="w-1.5 h-1.5 rounded-full bg-accent/50 group-hover:bg-accent" />
                                <span className="text-sm text-gray-300 truncate flex-1">{item.title}</span>
                                <span className="text-xs text-gray-600">{item.type}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Fallback for other types */}
                {type === 'calendar' && (
                    <div className="text-center py-4 text-xs text-gray-500">
                        Calendar widget placeholder
                    </div>
                )}

                {type === 'progress' && (
                    <div className="space-y-2">
                        <div className="flex justify-between text-xs">
                            <span className="text-gray-400">{data.label || 'Progress'}</span>
                            <span className="text-white">{data.percent || 0}%</span>
                        </div>
                        <div className="h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className="h-full bg-accent transition-all duration-500"
                                style={{ width: `${data.percent || 0}%` }}
                            />
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}
