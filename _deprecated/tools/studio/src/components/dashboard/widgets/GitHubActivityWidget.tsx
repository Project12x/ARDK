import { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../../lib/db';
import { Github, GitCommit, Clock, ExternalLink, RefreshCw } from 'lucide-react';
import { formatDistanceToNow } from 'date-fns';

interface RepoActivity {
    repo: string;
    pushedAt: Date;
    defaultBranch: string;
    openIssues: number;
    stars: number;
}

export function GitHubActivityWidget() {
    const [activities, setActivities] = useState<RepoActivity[]>([]);
    const [loading, setLoading] = useState(false);
    const [lastFetch, setLastFetch] = useState<Date | null>(null);

    // Get all projects with github repos
    const projectsWithRepos = useLiveQuery(async () => {
        return db.projects
            .filter(p => !p.deleted_at && !p.is_archived && !!p.github_repo)
            .toArray();
    });

    const fetchGitHubData = async () => {
        if (!projectsWithRepos || projectsWithRepos.length === 0) return;

        setLoading(true);
        const repos = [...new Set(projectsWithRepos.map(p => p.github_repo!))];

        try {
            const results = await Promise.all(
                repos.slice(0, 5).map(async (repo) => { // Limit to 5 repos to avoid rate limits
                    try {
                        const res = await fetch(`https://api.github.com/repos/${repo}`);
                        if (!res.ok) return null;
                        const data = await res.json();
                        return {
                            repo,
                            pushedAt: new Date(data.pushed_at),
                            defaultBranch: data.default_branch,
                            openIssues: data.open_issues_count,
                            stars: data.stargazers_count,
                        };
                    } catch {
                        return null;
                    }
                })
            );

            const validResults = results.filter((r): r is RepoActivity => r !== null);
            validResults.sort((a, b) => b.pushedAt.getTime() - a.pushedAt.getTime());
            setActivities(validResults);
            setLastFetch(new Date());
        } catch (e) {
            console.error('GitHub fetch error:', e);
        }

        setLoading(false);
    };

    // Fetch on mount and when repos change
    useEffect(() => {
        if (projectsWithRepos && projectsWithRepos.length > 0 && !lastFetch) {
            fetchGitHubData();
        }
    }, [projectsWithRepos]);

    const repoCount = projectsWithRepos?.length || 0;

    return (
        <div className="h-full flex flex-col p-4 bg-black/40">
            {/* Header */}
            <div className="flex items-center justify-between mb-3 shrink-0">
                <div className="flex items-center gap-2">
                    <Github size={14} className="text-white" />
                    <span className="text-[10px] font-mono uppercase font-bold text-gray-400">GitHub Activity</span>
                </div>
                <div className="flex items-center gap-2">
                    <span className="text-[9px] font-mono text-gray-600">{repoCount} repos</span>
                    <button
                        onClick={fetchGitHubData}
                        disabled={loading}
                        className="p-1 text-gray-500 hover:text-white transition-colors disabled:opacity-50"
                        title="Refresh"
                    >
                        <RefreshCw size={12} className={loading ? 'animate-spin' : ''} />
                    </button>
                </div>
            </div>

            {/* Activity List */}
            <div className="flex-1 overflow-y-auto custom-scrollbar space-y-2">
                {repoCount === 0 ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 text-center">
                        <Github size={24} className="mb-2 opacity-30" />
                        <span className="text-xs">No linked repos</span>
                        <span className="text-[10px] opacity-50">Add github_repo to projects</span>
                    </div>
                ) : activities.length === 0 && !loading ? (
                    <div className="h-full flex flex-col items-center justify-center text-gray-600 text-center">
                        <RefreshCw size={20} className="mb-2 opacity-30" />
                        <span className="text-xs">Click refresh to load</span>
                    </div>
                ) : (
                    activities.map(activity => {
                        const daysAgo = Math.floor((Date.now() - activity.pushedAt.getTime()) / (1000 * 60 * 60 * 24));
                        const isRecent = daysAgo < 7;

                        return (
                            <a
                                key={activity.repo}
                                href={`https://github.com/${activity.repo}`}
                                target="_blank"
                                rel="noopener noreferrer"
                                className="block p-2 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/10 transition-all group"
                            >
                                <div className="flex items-start justify-between mb-1">
                                    <span className="text-xs font-bold text-white group-hover:text-accent transition-colors truncate flex-1">
                                        {activity.repo.split('/')[1]}
                                    </span>
                                    <ExternalLink size={10} className="text-gray-600 group-hover:text-accent shrink-0 ml-2" />
                                </div>

                                <div className="flex items-center gap-3 text-[9px] text-gray-500">
                                    <span className={`flex items-center gap-1 ${isRecent ? 'text-green-400' : ''}`}>
                                        <GitCommit size={9} />
                                        {formatDistanceToNow(activity.pushedAt, { addSuffix: true })}
                                    </span>
                                    <span>⭐ {activity.stars}</span>
                                    {activity.openIssues > 0 && (
                                        <span className="text-yellow-400">🐛 {activity.openIssues}</span>
                                    )}
                                </div>
                            </a>
                        );
                    })
                )}
            </div>

            {/* Last Fetch */}
            {lastFetch && (
                <div className="mt-2 pt-2 border-t border-white/5 text-[9px] text-gray-600 flex items-center gap-1">
                    <Clock size={9} />
                    Updated {formatDistanceToNow(lastFetch, { addSuffix: true })}
                </div>
            )}
        </div>
    );
}
