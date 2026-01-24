import { useState } from 'react';
// @ts-ignore - CJS interop
import RGL from 'react-grid-layout';
const Responsive = RGL.Responsive;
const WidthProvider = RGL.WidthProvider;
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import type { Project } from '../../lib/db';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Lock, Unlock, RotateCcw } from 'lucide-react';
import { toast } from 'sonner';

// Widgets
import { ProjectCoreWidget } from './widgets/ProjectCoreWidget';
import { ProjectStatsWidget } from './widgets/ProjectStatsWidget';
// Reusing existing components as widgets!
import { ProjectSpecs } from './ProjectSpecs';
import { ProjectSafetyQA } from './ProjectSafetyQA';
import { ErrorBoundary } from '../ui/ErrorBoundary';

const ResponsiveGridLayout = WidthProvider(Responsive);

const DEFAULT_LAYOUT = {
    lg: [
        { i: 'core', x: 0, y: 0, w: 8, h: 4 },
        { i: 'stats', x: 8, y: 0, w: 4, h: 4 },
        { i: 'specs', x: 0, y: 4, w: 6, h: 6 },
        { i: 'safety', x: 6, y: 4, w: 6, h: 6 }
    ]
};

export function ProjectOverviewGrid({ project }: { project: Project }) {
    const [layouts, setLayouts] = useState(() => {
        const saved = localStorage.getItem('PROJECT_OVERVIEW_LAYOUT_V1');
        return saved ? JSON.parse(saved) : DEFAULT_LAYOUT;
    });
    const [isLocked, setIsLocked] = useState(true);

    const handleLayoutChange = (currentLayout: any, allLayouts: any) => {
        setLayouts(allLayouts);
        localStorage.setItem('PROJECT_OVERVIEW_LAYOUT_V1', JSON.stringify(allLayouts));
    };

    const resetLayout = () => {
        setLayouts(DEFAULT_LAYOUT);
        localStorage.setItem('PROJECT_OVERVIEW_LAYOUT_V1', JSON.stringify(DEFAULT_LAYOUT));
        toast.info('Layout Reset');
    };

    return (
        <div className="relative w-full overflow-hidden p-4">
            {/* Controls */}
            <div className="absolute top-2 right-4 z-50 flex gap-2">
                {!isLocked && (
                    <Button variant="ghost" size="sm" onClick={resetLayout} title="Reset Layout" className="bg-black/50 hover:bg-black/80">
                        <RotateCcw size={14} />
                    </Button>
                )}
                <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => setIsLocked(!isLocked)}
                    className={`transition-colors ${isLocked ? 'text-gray-500 hover:text-white' : 'text-accent bg-accent/10'}`}
                >
                    {isLocked ? <Lock size={14} /> : <Unlock size={14} />}
                </Button>
            </div>

            <ResponsiveGridLayout
                className="layout"
                layouts={layouts}
                breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
                cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
                rowHeight={60}
                isDraggable={!isLocked}
                isResizable={!isLocked}
                onLayoutChange={handleLayoutChange}
                margin={[16, 16]}
            >
                <div key="core">
                    <ErrorBoundary name="Core"><ProjectCoreWidget project={project} /></ErrorBoundary>
                </div>
                <div key="stats">
                    <ErrorBoundary name="Stats"><ProjectStatsWidget project={project} /></ErrorBoundary>
                </div>
                <div key="specs" className="bg-black/40 border border-white/10 rounded-xl overflow-y-auto custom-scrollbar">
                    <ErrorBoundary name="Specs">
                        <div className="p-4">
                            <ProjectSpecs
                                project={project}
                                projectId={project.id!}
                                onUpdate={(updates) => db.projects.update(project.id!, updates)}
                            />
                        </div>
                    </ErrorBoundary>
                </div>
                <div key="safety" className="bg-black/40 border border-white/10 rounded-xl overflow-y-auto custom-scrollbar">
                    <ErrorBoundary name="Safety">
                        <div className="p-4">
                            <ProjectSafetyQA
                                project={project}
                                projectId={project.id!}
                            />
                        </div>
                    </ErrorBoundary>
                </div>
            </ResponsiveGridLayout>
        </div>
    );
}
