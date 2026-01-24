/**
 * Metric Adapter
 * Converts metrics/statistics to UniversalEntity format.
 * Metrics are numeric/statistical data for dashboards and tracking.
 */

import type { UniversalEntity } from '../types';

// ============================================================================
// METRIC SCHEMA
// ============================================================================

export interface MetricEntry {
    id: number | string;
    /** Metric name */
    name: string;
    /** Current value */
    value: number;
    /** Previous value (for change calculation) */
    previous_value?: number;
    /** Unit of measurement */
    unit?: string;
    /** Target/goal value */
    target?: number;
    /** Metric category */
    category?: 'count' | 'percentage' | 'currency' | 'time' | 'custom';
    /** Trend direction */
    trend?: 'up' | 'down' | 'stable';
    /** Color for display */
    color?: string;
    /** Icon name */
    icon?: string;
    /** Entity this metric belongs to */
    parent_type?: string;
    parent_id?: number;
    /** Timestamp */
    created_at?: Date;
    updated_at?: Date;
}

// ============================================================================
// HELPERS
// ============================================================================

function formatMetricValue(metric: MetricEntry): string {
    const val = metric.value;
    switch (metric.category) {
        case 'percentage':
            return `${val}%`;
        case 'currency':
            return `$${val.toLocaleString()}`;
        case 'time':
            return `${val}h`;
        default:
            return val.toLocaleString();
    }
}

function calculateChange(current: number, previous?: number): number | undefined {
    if (previous === undefined || previous === 0) return undefined;
    return Math.round(((current - previous) / previous) * 100);
}

// ============================================================================
// ADAPTER
// ============================================================================

export function toUniversalMetric(metric: MetricEntry): UniversalEntity<MetricEntry> {
    const change = calculateChange(metric.value, metric.previous_value);
    const progress = metric.target ? Math.min(100, (metric.value / metric.target) * 100) : undefined;

    let trendColor = 'text-gray-400';
    if (metric.trend === 'up') trendColor = 'text-green-500';
    if (metric.trend === 'down') trendColor = 'text-red-500';

    return {
        urn: `metric:${metric.id}`,
        id: metric.id,
        type: 'metric',
        title: metric.name,
        subtitle: formatMetricValue(metric),
        icon: metric.icon || 'BarChart3',
        color: metric.color || trendColor,
        status: metric.trend || 'stable',
        progress: progress,
        createdAt: metric.created_at,
        updatedAt: metric.updated_at,
        data: metric,
        metadata: {
            value: metric.value,
            previousValue: metric.previous_value,
            target: metric.target,
            change: change,
            unit: metric.unit,
            category: metric.category,
            trend: metric.trend,
        },

        // Phase 11c: Card Configuration
        cardConfig: {
            label: 'Metric',
            statusStripe: metric.color || getTrendColorHex(metric.trend),
            statusGlow: metric.trend === 'up' || (progress && progress >= 100) || false,
            collapsible: false,

            metaGrid: [
                { label: 'Value', value: formatMetricValue(metric) },
                { label: 'Change', value: change ? `${change > 0 ? '+' : ''}${change}%` : '0%' },
                { label: 'Target', value: metric.target ? formatMetricValue({ ...metric, value: metric.target }) : '-' }
            ].filter(i => i.value !== '-'),

            ratings: progress ? [
                { label: 'Target', value: progress, max: 100, color: getTrendColorHex(metric.trend) }
            ] : undefined
        }
    };
}

function getTrendColorHex(trend?: string): string {
    switch (trend) {
        case 'up': return '#22c55e';
        case 'down': return '#ef4444';
        default: return '#9ca3af';
    }
}

export function toUniversalMetricBatch(metrics: MetricEntry[]): UniversalEntity<MetricEntry>[] {
    return metrics.map(toUniversalMetric);
}
