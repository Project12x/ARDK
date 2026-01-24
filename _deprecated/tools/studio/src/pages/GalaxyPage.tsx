import { useRef } from 'react';
import { GalaxyGraph } from '../components/galaxy/GalaxyGraph';
import { FullscreenToggleButton } from '../components/ui/FullscreenToggleButton';

export function GalaxyPage() {
    const containerRef = useRef<HTMLDivElement>(null);

    return (
        <div className="h-full flex flex-col p-4 overflow-hidden relative" ref={containerRef}>
            <div className="mb-4 flex justify-between items-start">
                <div>
                    <h1 className="text-3xl font-black tracking-tight text-white mb-1 uppercase">The Galaxy</h1>
                    <p className="text-gray-400 text-sm">Visualizing the Neural Network of your Second Brain.</p>
                </div>
                <FullscreenToggleButton targetRef={containerRef} />
            </div>
            <div className="flex-1 min-h-0 bg-black/20 rounded-xl overflow-hidden border border-white/5 relative">
                <GalaxyGraph />
            </div>
        </div>
    );
}
