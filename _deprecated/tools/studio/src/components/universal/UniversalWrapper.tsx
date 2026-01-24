import React from 'react';
import { UniversalCard, UniversalCardProps } from './UniversalCard';

/**
 * UniversalWrapper
 * 
 * The "Escape Hatch" for bespoke widgets that need the Universal Shell (DnD, Resizing)
 * but fully custom internal rendering.
 * 
 * Use this when 'cardConfig' is mostly insufficient and you need to render
 * complex custom React components (e.g. 3D canvasses, complex dashboards).
 */
export function UniversalWrapper({ children, ...props }: UniversalCardProps) {
    return (
        <UniversalCard
            {...props}
            noDefaultStyles={true}
            className={`universal-wrapper ${props.className || ''}`}
        >
            {/* 
                We render children directly. 
                UniversalCard's shell (handles, DnD) will wrap this.
            */}
            {children}
        </UniversalCard>
    );
}
