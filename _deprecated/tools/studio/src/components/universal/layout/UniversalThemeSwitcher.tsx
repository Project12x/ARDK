import React from 'react';
import { useUIStore } from '../../../store/useStore';
import { UniversalTabs } from './UniversalTabs';
import { Moon, Sun, Music, Zap, Leaf } from 'lucide-react';

interface UniversalThemeSwitcherProps {
    className?: string;
    variant?: 'line' | 'pill';
}

export function UniversalThemeSwitcher({ className, variant = 'pill' }: UniversalThemeSwitcherProps) {
    const { mainTheme, setMainTheme } = useUIStore();

    const themes = [
        { id: 'light', label: 'Light', icon: Sun },
        { id: 'midnight', label: 'Dark', icon: Moon },
        { id: 'music', label: 'Studio', icon: Music },
        { id: 'synthwave', label: 'Synth', icon: Zap },
        { id: 'forest', label: 'Forest', icon: Leaf },
    ];

    return (
        <UniversalTabs
            tabs={themes}
            activeTab={mainTheme}
            onChange={(id) => setMainTheme(id as any)}
            variant={variant}
            className={className}
        />
    );
}
