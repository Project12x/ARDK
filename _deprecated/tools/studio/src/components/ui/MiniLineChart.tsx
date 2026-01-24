import React from 'react';
import { ResponsiveLine } from '@nivo/line';
import clsx from 'clsx';

interface MiniLineChartProps {
    data?: { x: string | number; y: number }[];
    color?: 'green' | 'amber' | 'red' | 'blue' | 'accent';
    label?: string;
    height?: number;
    className?: string;
}

const COLOR_MAP = {
    green: '#10b981',
    amber: '#f59e0b',
    red: '#ef4444',
    blue: '#3b82f6',
    accent: '#ff6b00', // Fallback for CSS variable
};

/**
 * MiniLineChart - A small sparkline-style line chart using Nivo.
 * Perfect for showing trends in velocity, issues, progress over time.
 */
export function MiniLineChart({
    data,
    color = 'accent',
    label,
    height = 40,
    className,
}: MiniLineChartProps) {
    // Generate mock data if not provided
    const mockData = React.useMemo(() => {
        if (data) return data;
        return Array.from({ length: 12 }, (_, i) => ({
            x: i + 1,
            y: Math.floor(Math.random() * 80) + 20,
        }));
    }, [data]);

    const chartData = [
        {
            id: 'trend',
            data: mockData,
        },
    ];

    const lineColor = COLOR_MAP[color];

    return (
        <div className={clsx("w-full", className)}>
            {label && (
                <div className="text-[8px] uppercase text-gray-500 font-bold mb-1">{label}</div>
            )}
            <div style={{ height }}>
                <ResponsiveLine
                    data={chartData}
                    margin={{ top: 4, right: 4, bottom: 4, left: 4 }}
                    xScale={{ type: 'point' }}
                    yScale={{ type: 'linear', min: 0, max: 'auto' }}
                    curve="monotoneX"
                    axisTop={null}
                    axisRight={null}
                    axisBottom={null}
                    axisLeft={null}
                    enableGridX={false}
                    enableGridY={false}
                    colors={[lineColor]}
                    lineWidth={2}
                    enablePoints={false}
                    enableArea={true}
                    areaOpacity={0.15}
                    useMesh={true}
                    crosshairType="bottom"
                    motionConfig="gentle"
                    tooltip={({ point }) => (
                        <div className="bg-black/90 text-white text-xs px-2 py-1 rounded shadow-lg">
                            {point.data.yFormatted}
                        </div>
                    )}
                />
            </div>
        </div>
    );
}

export default MiniLineChart;
