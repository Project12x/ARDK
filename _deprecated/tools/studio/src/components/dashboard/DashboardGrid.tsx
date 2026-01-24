import { useState, useMemo } from 'react';
// @ts-ignore - CJS interop
import RGL from 'react-grid-layout';
const Responsive = RGL.Responsive;
const WidthProvider = RGL.WidthProvider;
import 'react-grid-layout/css/styles.css';
import 'react-resizable/css/styles.css';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { useNavigate } from 'react-router-dom';

// Widgets
import { WorkshopWeather } from '../ui/WorkshopWeather';
import { WorkshopAudioDeck } from '../ui/WorkshopAudioDeck';
import { RemindersWidget } from './RemindersWidget';
import { DashboardNotesWidget } from './DashboardNotesWidget';
import { DashboardGoalsWidget } from './DashboardGoalsWidget';
import { RoutinesWidget } from './RoutinesWidget';
import { WorkshopLog } from '../ui/WorkshopLog';
import { ErrorBoundary } from '../ui/ErrorBoundary';
import { FocusCard } from './widgets/FocusCard';
import { IngestButton } from './widgets/IngestButton';
import { CreateButton } from './widgets/CreateButton';
import { PomodoroWidget } from './widgets/PomodoroWidget';
import { BlockersWidget } from './widgets/BlockersWidget';
import { ProjectStatsWidget } from './widgets/ProjectStatsWidget';
import { GitHubActivityWidget } from './widgets/GitHubActivityWidget';
import { AVAILABLE_WIDGETS } from './WidgetPicker';

const ResponsiveGridLayout = WidthProvider(Responsive);

// Default layout based on user's custom arrangement
const DEFAULT_LAYOUTS = {
    lg: [
        { i: 'focus1', x: 0, y: 0, w: 4, h: 5 },
        { i: 'focus2', x: 4, y: 0, w: 4, h: 5 },
        { i: 'focus3', x: 8, y: 0, w: 4, h: 5 },
        { i: 'weather', x: 0, y: 5, w: 2, h: 3 },
        { i: 'ingest', x: 2, y: 5, w: 2, h: 2 },
        { i: 'create', x: 4, y: 5, w: 2, h: 2 },
        { i: 'audio', x: 6, y: 5, w: 6, h: 3 },
        { i: 'notes', x: 0, y: 8, w: 3, h: 5 },
        { i: 'goals', x: 3, y: 7, w: 3, h: 5 },
        { i: 'stats', x: 6, y: 8, w: 3, h: 5 },
        { i: 'routines', x: 9, y: 8, w: 3, h: 2 },
        { i: 'activity', x: 9, y: 10, w: 3, h: 3 },
        { i: 'pomodoro', x: 0, y: 13, w: 3, h: 4 },
        { i: 'blockers', x: 3, y: 12, w: 3, h: 4 },
        { i: 'projectStats', x: 6, y: 13, w: 3, h: 4 },
        { i: 'github', x: 9, y: 13, w: 3, h: 4 },
    ],
    md: [
        { i: 'focus1', x: 0, y: 4, w: 2, h: 5 },
        { i: 'focus2', x: 2, y: 4, w: 2, h: 5 },
        { i: 'focus3', x: 4, y: 4, w: 2, h: 5 },
        { i: 'weather', x: 0, y: 0, w: 2, h: 4 },
        { i: 'pomodoro', x: 2, y: 0, w: 2, h: 4 },
        { i: 'ingest', x: 4, y: 0, w: 1, h: 2 },
        { i: 'create', x: 5, y: 0, w: 1, h: 2 },
        { i: 'audio', x: 4, y: 2, w: 2, h: 2 },
        { i: 'stats', x: 6, y: 0, w: 2, h: 4 },
        { i: 'routines', x: 8, y: 0, w: 2, h: 4 },
        { i: 'blockers', x: 6, y: 4, w: 2, h: 5 },
        { i: 'activity', x: 8, y: 4, w: 2, h: 5 },
        { i: 'notes', x: 0, y: 9, w: 6, h: 5 },
        { i: 'projectStats', x: 6, y: 9, w: 2, h: 5 },
        { i: 'github', x: 8, y: 9, w: 2, h: 5 },
        { i: 'goals', x: 7, y: 14, w: 3, h: 5 },
    ],
    sm: [
        { i: 'focus1', x: 0, y: 0, w: 4, h: 5 },
        { i: 'focus2', x: 4, y: 0, w: 4, h: 5 },
        { i: 'focus3', x: 8, y: 0, w: 4, h: 5 },
        { i: 'weather', x: 0, y: 5, w: 2, h: 3 },
        { i: 'ingest', x: 2, y: 5, w: 2, h: 2 },
        { i: 'create', x: 4, y: 5, w: 2, h: 2 },
        { i: 'audio', x: 6, y: 5, w: 6, h: 3 },
        { i: 'notes', x: 0, y: 8, w: 3, h: 5 },
        { i: 'goals', x: 3, y: 8, w: 3, h: 5 },
        { i: 'stats', x: 6, y: 8, w: 3, h: 5 },
        { i: 'routines', x: 9, y: 8, w: 3, h: 2 },
        { i: 'activity', x: 9, y: 10, w: 3, h: 3 },
        { i: 'pomodoro', x: 0, y: 13, w: 3, h: 4 },
        { i: 'blockers', x: 3, y: 13, w: 3, h: 4 },
        { i: 'projectStats', x: 0, y: 17, w: 3, h: 4 },
        { i: 'github', x: 3, y: 17, w: 3, h: 4 },
    ]
};

// Default widget list
const DEFAULT_WIDGETS = ['focus1', 'focus2', 'focus3', 'weather', 'audio', 'notes', 'goals', 'stats', 'routines', 'activity', 'ingest', 'create', 'pomodoro', 'blockers', 'projectStats', 'github'];

interface DashboardGridProps {
    onIngest: () => void;
    onCreate: () => void;
    isLocked: boolean;
    layoutKey: string;
    activeWidgets: string[];
}

export function DashboardGrid({ onIngest, onCreate, isLocked, layoutKey, activeWidgets }: DashboardGridProps) {
    const navigate = useNavigate();
    const [layouts, setLayouts] = useState(() => {
        const saved = localStorage.getItem(layoutKey);
        return saved ? JSON.parse(saved) : null;
    });

    // Fetch top 3 active projects for focus cards
    const projects = useLiveQuery(() =>
        db.projects
            .where('status')
            .equals('active')
            .filter(p => !p.is_archived && !p.deleted_at)
            .reverse()
            .sortBy('priority')
    );

    const topProjects = (projects || []).slice(0, 3);

    // Build layouts based on active widgets
    const effectiveLayouts = useMemo(() => {
        const breakpoints = ['lg', 'md', 'sm'];
        const result: Record<string, any[]> = {};

        for (const bp of breakpoints) {
            const savedLayout = layouts?.[bp] || [];
            const layoutItems: any[] = [];

            // Find the maximum Y position in existing layout to place new widgets below
            let maxY = 0;
            savedLayout.forEach((item: any) => {
                if (activeWidgets.includes(item.i)) {
                    maxY = Math.max(maxY, item.y + item.h);
                }
            });

            // Track used positions for new widgets
            let newWidgetX = 0;
            let newWidgetY = maxY;
            const cols = (bp === 'lg' || bp === 'md' || bp === 'sm') ? 12 : bp === 'xs' ? 6 : 4;

            activeWidgets.forEach((widgetId) => {
                // Check if widget exists in saved layout
                const existing = savedLayout.find((item: any) => item.i === widgetId);

                if (existing) {
                    layoutItems.push(existing);
                } else {
                    // Get default size from DEFAULT_LAYOUTS or widget config
                    const widgetConfig = AVAILABLE_WIDGETS.find(w => w.id === widgetId);
                    const defaultItem = DEFAULT_LAYOUTS.lg.find(item => item.i === widgetId);
                    const w = defaultItem?.w || widgetConfig?.defaultSize?.w || 3;
                    const h = defaultItem?.h || widgetConfig?.defaultSize?.h || 4;

                    // Place new widget, wrap to next row if needed
                    if (newWidgetX + w > cols) {
                        newWidgetX = 0;
                        newWidgetY += 4; // Move to next row
                    }

                    layoutItems.push({
                        i: widgetId,
                        x: newWidgetX,
                        y: newWidgetY,
                        w,
                        h,
                    });

                    newWidgetX += w;
                }
            });

            result[bp] = layoutItems;
        }

        return result;
    }, [layouts, activeWidgets]);

    const handleLayoutChange = (_currentLayout: any, allLayouts: any) => {
        if (!isLocked) {
            setLayouts(allLayouts);
            localStorage.setItem(layoutKey, JSON.stringify(allLayouts));
        }
    };

    // Widget rendering map
    const renderWidget = (widgetId: string) => {
        switch (widgetId) {
            case 'focus1':
                return <FocusCard project={topProjects[0]} index={0} onNavigate={(id: number) => navigate(`/projects/${id}`)} disabled={!isLocked} />;
            case 'focus2':
                return <FocusCard project={topProjects[1]} index={1} onNavigate={(id: number) => navigate(`/projects/${id}`)} disabled={!isLocked} />;
            case 'focus3':
                return <FocusCard project={topProjects[2]} index={2} onNavigate={(id: number) => navigate(`/projects/${id}`)} disabled={!isLocked} />;
            case 'weather':
                return <WorkshopWeather />;
            case 'audio':
                return <WorkshopAudioDeck />;
            case 'notes':
                return <DashboardNotesWidget />;
            case 'goals':
                return <DashboardGoalsWidget />;
            case 'stats':
                return <RemindersWidget />;
            case 'routines':
                return <RoutinesWidget />;
            case 'activity':
                return <WorkshopLog />;
            case 'ingest':
                return <IngestButton onClick={onIngest} disabled={!isLocked} />;
            case 'create':
                return <CreateButton onClick={onCreate} disabled={!isLocked} />;
            case 'pomodoro':
                return <PomodoroWidget />;
            case 'blockers':
                return <BlockersWidget />;
            case 'projectStats':
                return <ProjectStatsWidget />;
            case 'github':
                return <GitHubActivityWidget />;
            default:
                return <div className="text-gray-500 text-xs p-4">Unknown Widget: {widgetId}</div>;
        }
    };

    return (
        <div className="relative w-full min-h-full">
            <ResponsiveGridLayout
                className="layout"
                layouts={effectiveLayouts}
                breakpoints={{ lg: 1200, md: 996, sm: 640, xs: 480, xxs: 0 }}
                cols={{ lg: 12, md: 12, sm: 12, xs: 6, xxs: 4 }}
                rowHeight={50}
                isDraggable={!isLocked}
                isResizable={!isLocked}
                onLayoutChange={handleLayoutChange}
                margin={[12, 12]}
                containerPadding={[0, 0]}
                resizeHandles={['s', 'w', 'e', 'n', 'sw', 'nw', 'se', 'ne']}
                compactType="vertical"
                preventCollision={false}
            >
                {activeWidgets.map(widgetId => {
                    const widgetInfo = AVAILABLE_WIDGETS.find(w => w.id === widgetId);
                    const isFocusCard = widgetId.startsWith('focus');

                    return (
                        <div
                            key={widgetId}
                            className={isFocusCard ? '' : 'bg-black/30 rounded-xl border border-white/5 h-full overflow-hidden'}
                        >
                            <ErrorBoundary name={widgetInfo?.name || widgetId}>
                                {renderWidget(widgetId)}
                            </ErrorBoundary>
                        </div>
                    );
                })}
            </ResponsiveGridLayout>
        </div>
    );
}
