import React from 'react';
import { ResponsiveRadialBar } from '@nivo/radial-bar';
import clsx from 'clsx';

interface RadialGaugeProps {
    value: number;
    max?: number;
    size?: 'sm' | 'md' | 'lg';
    color?: 'green' | 'amber' | 'red' | 'blue' | 'accent';
    label?: string;
    showValue?: boolean;
    className?: string;
}

const COLOR_MAP = {
    green: '#10b981',
    amber: '#f59e0b',
    red: '#ef4444',
    blue: '#3b82f6',
    accent: 'var(--accent)',
};

const SIZE_MAP = {
    sm: { width: 50, height: 50, fontSize: 'text-[10px]', labelSize: 'text-[8px]' },
    md: { width: 70, height: 70, fontSize: 'text-sm', labelSize: 'text-[9px]' },
    lg: { width: 90, height: 90, fontSize: 'text-lg', labelSize: 'text-[10px]' },
};

/**
 * RadialGauge - A circular progress/gauge component using Nivo.
 * Perfect for displaying metrics like completion percentage, budget usage, etc.
 */
export function RadialGauge({
    value,
    max = 100,
    size = 'md',
    color = 'accent',
    label,
    showValue = true,
    className,
}: RadialGaugeProps) {
    const { width, height, fontSize, labelSize } = SIZE_MAP[size];
    const percentage = Math.min(Math.round((value / max) * 100), 100);
    const gaugeColor = COLOR_MAP[color];

    const data = [
        {
            id: 'gauge',
            data: [{ x: 'value', y: percentage }],
        },
    ];

    return (
        <div className={clsx("flex flex-col items-center gap-1", className)}>
            <div className="relative" style={{ width, height }}>
                <ResponsiveRadialBar
                    data={data}
                    maxValue={100}
                    startAngle={-135}
                    endAngle={135}
                    innerRadius={0.65}
                    padding={0.3}
                    cornerRadius={2}
                    colors={[gaugeColor]}
                    enableTracks={true}
                    tracksColor="rgba(255,255,255,0.08)"
                    enableRadialGrid={false}
                    enableCircularGrid={false}
                    radialAxisStart={null}
                    circularAxisOuter={null}
                    motionConfig="gentle"
                    transitionMode="startAngle"
                />
                {showValue && (
                    <div className={clsx("absolute inset-0 flex items-center justify-center font-bold font-mono text-white", fontSize)}>
                        {percentage}%
                    </div>
                )}
            </div>
            {label && (
                <span className={clsx("text-gray-400 uppercase font-bold tracking-wide", labelSize)}>
                    {label}
                </span>
            )}
        </div>
    );
}

export default RadialGauge;
