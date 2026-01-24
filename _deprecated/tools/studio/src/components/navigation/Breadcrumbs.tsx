import { useLocation, Link, useSearchParams } from 'react-router-dom';
import { ChevronRight, LayoutDashboard, Folder, Workflow, Box, Sliders, MoreHorizontal, Target } from 'lucide-react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';

export function Breadcrumbs() {
    const location = useLocation();
    const [searchParams] = useSearchParams();
    const activeTab = searchParams.get('tab');
    const pathnames = location.pathname.split('/').filter(x => x);

    // Dynamic Title Resolution
    const projectId = pathnames.length > 1 && pathnames[0] === 'projects' && !isNaN(Number(pathnames[1]))
        ? Number(pathnames[1])
        : null;

    const currentProject = useLiveQuery(
        async () => projectId ? await db.projects.get(projectId) : null,
        [projectId]
    );

    const getBreadcrumbName = (value: string, index: number) => {
        if (value === 'projects') return 'Projects';
        if (value === 'flow') return 'Flow';
        if (value === 'inventory') return 'Inventory';
        if (value === 'settings') return 'Settings';
        if (value === 'dashboard') return 'Dashboard';
        if (index === 1 && currentProject) return currentProject.title;
        if (!isNaN(Number(value))) return `#${value}`;
        return value.charAt(0).toUpperCase() + value.slice(1);
    };

    const getBreadcrumbIcon = (value: string, index: number) => {
        if (value === 'projects') return Folder;
        if (value === 'flow') return Workflow;
        if (value === 'inventory') return Box;
        if (value === 'settings') return Sliders;
        if (value === 'dashboard') return LayoutDashboard;

        // Context-aware icons
        if (index > 0) {
            const parent = pathnames[index - 1];
            if (parent === 'projects') return Folder; // Project Detail
            if (parent === 'goals') return Target;
        }

        return null;
    };

    if (pathnames.length === 0) {
        return (
            <nav className="flex items-center text-sm font-mono text-gray-500">
                <span className="flex items-center gap-1.5 text-white font-bold uppercase tracking-wide">
                    <LayoutDashboard size={14} />
                    <span>FOCUS</span>
                </span>
            </nav>
        );
    }

    // Collapse middle items if path is too deep (> 3 levels)
    const shouldCollapse = pathnames.length > 3;

    const visibleBreadcrumbs = shouldCollapse
        ? [
            pathnames[0], // First
            '...', // Collapsed indicator
            pathnames[pathnames.length - 1] // Last
        ]
        : pathnames;

    const getActualIndex = (displayIndex: number) => {
        if (!shouldCollapse) return displayIndex;
        if (displayIndex === 0) return 0;
        if (displayIndex === 1) return -1; // ellipsis
        return pathnames.length - 1;
    };

    return (
        <nav className="flex items-center text-xs font-mono text-gray-500 max-w-[400px]">
            {visibleBreadcrumbs.map((value, displayIndex) => {
                const actualIndex = getActualIndex(displayIndex);

                // Handle the ellipsis
                if (value === '...') {
                    return (
                        <div key="ellipsis" className="flex items-center">
                            <span className="text-gray-600 px-1">
                                <MoreHorizontal size={12} />
                            </span>
                            <ChevronRight size={12} className="mx-1 text-white/20" />
                        </div>
                    );
                }

                const to = `/${pathnames.slice(0, actualIndex + 1).join('/')}`;
                // It is "last" (highlighted) only if it's the last path item AND there is no active tab query param
                const isVisuallyLast = displayIndex === visibleBreadcrumbs.length - 1 && !activeTab;

                const Icon = getBreadcrumbIcon(value, actualIndex);
                const displayName = getBreadcrumbName(value, actualIndex);

                // Truncate long names
                const truncatedName = displayName.length > 20
                    ? displayName.substring(0, 20) + '...'
                    : displayName;

                return (
                    <div key={to} className="flex items-center">
                        {isVisuallyLast ? (
                            <span className="flex items-center gap-1.5 text-white font-bold text-xs uppercase tracking-wide truncate" title={displayName}>
                                {Icon && <Icon size={14} className="shrink-0" />}
                                <span className="truncate">{truncatedName}</span>
                            </span>
                        ) : (
                            <Link
                                to={to}
                                className="hover:text-white transition-colors hover:underline decoration-white/20 underline-offset-4 truncate flex items-center gap-1.5"
                                title={displayName}
                            >
                                {Icon && <Icon size={14} className="shrink-0 opacity-50" />}
                                <span className="truncate">{truncatedName}</span>
                            </Link>
                        )}
                        {(displayIndex < visibleBreadcrumbs.length - 1 || activeTab) && <ChevronRight size={12} className="mx-1 text-white/20 shrink-0" />}
                    </div>
                );
            })}

            {/* Active Tab Breadcrumb */}
            {activeTab && (
                <span className="flex items-center gap-1.5 text-accent font-bold text-xs uppercase tracking-wide truncate animate-in fade-in slide-in-from-left-1">
                    <span className="truncate max-w-[100px]">{activeTab}</span>
                </span>
            )}
        </nav>
    );
}
