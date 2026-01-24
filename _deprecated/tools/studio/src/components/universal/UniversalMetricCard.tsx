/**
 * UniversalMetricCard
 * Displays metrics/statistics with trend indicators.
 */

import { useDraggable } from '@dnd-kit/core';
import clsx from 'clsx';
import { GripVertical, TrendingUp, TrendingDown, Minus, Target } from 'lucide-react';
import type { UniversalEntity } from '../../lib/universal/types';
import type { MetricEntry } from '../../lib/universal/adapters/metricAdapter';

interface UniversalMetricCardProps {
    entity: UniversalEntity<MetricEntry>;
    onClick?: () => void;
    className?: string;
    variant?: 'default' | 'compact' | 'large';
}

export function UniversalMetricCard({ entity, onClick, className, variant = 'default' }: UniversalMetricCardProps) {
    const metric = entity.data;
    const change = entity.metadata?.change as number | undefined;
    const progress = entity.progress;

    const TrendIcon = metric.trend === 'up' ? TrendingUp : metric.trend === 'down' ? TrendingDown : Minus;
    const trendColor = metric.trend === 'up' ? 'text-green-500' : metric.trend === 'down' ? 'text-red-500' : 'text-gray-500';

    const { attributes, listeners, setNodeRef, isDragging } = useDraggable({
        id: entity.urn,
        data: { type: 'universal-card', entity, origin: 'grid' }
    });

    const formatValue = () => {
        switch (metric.category) {
            case 'percentage': return `${metric.value}%`;
            case 'currency': return `$${metric.value.toLocaleString()}`;
            case 'time': return `${metric.value}h`;
            default: return metric.value.toLocaleString();
        }
    };

    if (variant === 'compact') {
        return (
            <div
                ref={setNodeRef}
                onClick={onClick}
                className={clsx(
                    "flex items-center gap-3 p-3 rounded-lg border border-white/5 bg-black/40 hover:border-white/20 transition-all",
                    isDragging && "opacity-50",
                    className
                )}
            >
                <div className={clsx("text-2xl font-bold", entity.color || 'text-white')}>
                    {formatValue()}
                </div>
                <div className="flex-1">
                    <div className="text-xs text-gray-400">{metric.name}</div>
                </div>
                <TrendIcon size={16} className={trendColor} />
            </div>
        );
    }

    return (
        <div
            ref={setNodeRef}
            onClick={onClick}
            className={clsx(
                "group relative p-4 rounded-xl border border-white/5 bg-black/40 hover:border-white/20 transition-all",
                isDragging && "opacity-50 scale-95",
                className
            )}
        >
            {/* Drag Handle */}
            <div
                {...attributes}
                {...listeners}
                className="absolute top-2 right-2 p-1 rounded cursor-grab text-gray-500 hover:text-white opacity-0 group-hover:opacity-100"
            >
                <GripVertical size={14} />
            </div>

            {/* Label */}
            <div className="text-[10px] font-bold uppercase text-gray-500 mb-1">
                {metric.name}
            </div>

            {/* Value */}
            <div className={clsx("text-3xl font-black", entity.color || 'text-white')}>
                {formatValue()}
            </div>

            {/* Trend & Change */}
            <div className="flex items-center gap-2 mt-2">
                <TrendIcon size={14} className={trendColor} />
                {change !== undefined && (
                    <span className={clsx("text-xs font-medium", trendColor)}>
                        {change > 0 ? '+' : ''}{change}%
                    </span>
                )}
            </div>

            {/* Progress to target */}
            {metric.target && progress !== undefined && (
                <div className="mt-3">
                    <div className="flex justify-between text-[10px] text-gray-500 mb-1">
                        <span>Progress</span>
                        <span className="flex items-center gap-1">
                            <Target size={10} />
                            {metric.target}{metric.unit || ''}
                        </span>
                    </div>
                    <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
                        <div
                            className={clsx("h-full rounded-full transition-all", entity.color?.replace('text-', 'bg-') || 'bg-accent')}
                            style={{ width: `${Math.min(100, progress)}%` }}
                        />
                    </div>
                </div>
            )}
        </div>
    );
}
