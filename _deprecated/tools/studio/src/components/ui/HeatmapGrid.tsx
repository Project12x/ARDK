import React from 'react';
import { ResponsiveHeatMap } from '@nivo/heatmap';
import clsx from 'clsx';

interface HeatmapGridProps {
    data?: { id: string; data: { x: string; y: number }[] }[];
    rows?: number;
    cols?: number;
    color?: 'green' | 'amber' | 'accent';
    className?: string;
}

const COLOR_SCHEMES = {
    green: ['rgba(16, 185, 129, 0.1)', 'rgba(16, 185, 129, 0.9)'],
    amber: ['rgba(245, 158, 11, 0.1)', 'rgba(245, 158, 11, 0.9)'],
    accent: ['rgba(var(--accent-rgb), 0.1)', 'rgba(var(--accent-rgb), 0.9)'],
};

/**
 * HeatmapGrid - Activity heatmap using Nivo.
 * Perfect for commit activity, usage patterns, etc.
 */
export function HeatmapGrid({
    data,
    rows = 2,
    cols = 12,
    color = 'accent',
    className,
}: HeatmapGridProps) {
    // Generate mock data if not provided
    const mockData = React.useMemo(() => {
        if (data) return data;

        const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'].slice(0, cols);
        return Array.from({ length: rows }, (_, rowIdx) => ({
            id: `Row ${rowIdx + 1}`,
            data: months.map((month) => ({
                x: month,
                y: Math.floor(Math.random() * 100),
            })),
        }));
    }, [data, rows, cols]);

    // Get color scheme - fallback to accent colors for CSS variable issues
    const colorScheme = color === 'accent'
        ? ['rgba(255, 107, 0, 0.1)', 'rgba(255, 107, 0, 0.9)'] // Hardcoded accent fallback
        : COLOR_SCHEMES[color];

    return (
        <div className={clsx("w-full", className)} style={{ height: rows * 16 + 8 }}>
            <ResponsiveHeatMap
                data={mockData}
                margin={{ top: 0, right: 0, bottom: 0, left: 0 }}
                axisTop={null}
                axisBottom={null}
                axisLeft={null}
                axisRight={null}
                colors={{
                    type: 'sequential',
                    scheme: 'oranges',
                }}
                emptyColor="rgba(255,255,255,0.05)"
                borderRadius={1}
                borderWidth={1}
                borderColor="rgba(0,0,0,0.3)"
                enableLabels={false}
                motionConfig="gentle"
                hoverTarget="cell"
                cellOpacity={1}
                cellHoverOpacity={0.8}
                tooltip={({ cell }) => (
                    <div className="bg-black/90 text-white text-xs px-2 py-1 rounded shadow-lg">
                        {cell.serieId} / {cell.data.x}: {cell.formattedValue}
                    </div>
                )}
            />
        </div>
    );
}

export default HeatmapGrid;
