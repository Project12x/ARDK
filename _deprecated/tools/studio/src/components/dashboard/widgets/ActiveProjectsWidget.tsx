import { useNavigate } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Project } from '../../../lib/db';
import { ArrowRight, Clock, Target, AlertTriangle, Milestone } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { GitHubLink } from '../../projects/ProjectCard';
import { formatVersion } from '../../../lib/utils';
import { Button } from '../../ui/Button';

export function ActiveProjectsWidget() {
    const navigate = useNavigate();

    // Fetch active projects sorted by priority (descending)
    const projects = useLiveQuery(() =>
        db.projects
            .where('status')
            .equals('active')
            .filter(p => !p.is_archived && !p.deleted_at)
            .reverse()
            .sortBy('priority')
    );

    if (!projects) return <div className="p-4 text-white">Loading...</div>;

    const topProjects = projects.slice(0, 3);

    return (
        <div className="h-full flex flex-col bg-black/40 border border-white/10 rounded-xl overflow-hidden">
            <div className="p-2 border-b border-white/10 flex justify-between items-center bg-white/5">
                <span className="text-xs font-bold text-gray-400 uppercase tracking-wider">Active Missions</span>
                <span className="text-[10px] bg-accent/20 text-accent px-1.5 rounded">{projects.length}</span>
            </div>

            <div className="flex-1 overflow-y-auto p-2 space-y-2 custom-scrollbar">
                <AnimatePresence mode="popLayout">
                    {topProjects.map((p, i) => (
                        <motion.div
                            key={p.id}
                            layout
                            initial={{ opacity: 0, x: -20 }}
                            animate={{ opacity: 1, x: 0 }}
                            className="bg-white/5 hover:bg-white/10 border border-white/5 hover:border-accent transition-colors rounded-lg p-3 cursor-pointer group"
                            onClick={() => navigate(`/projects/${p.id}`)}
                        >
                            <div className="flex justify-between items-start mb-2">
                                <div>
                                    <h3 className="font-bold text-white group-hover:text-accent truncate transition-colors">{p.title}</h3>
                                    <div className="flex gap-2 mt-1">
                                        <span className="text-[9px] bg-white/10 px-1 rounded text-gray-400 font-mono">{formatVersion(p.version)}</span>
                                        {p.priority >= 4 && <span className="text-[9px] bg-red-500/20 text-red-400 px-1 rounded font-bold">PRIORITY</span>}
                                    </div>
                                </div>
                                {p.github_repo && <GitHubLink repo={p.github_repo} />}
                            </div>

                            {p.blockers && p.blockers.length > 0 ? (
                                <div className="bg-red-900/10 border border-red-500/20 p-2 rounded flex items-start gap-2">
                                    <AlertTriangle size={12} className="text-red-500 mt-0.5 shrink-0" />
                                    <p className="text-[10px] text-red-200 line-clamp-1">{p.blockers[0]}</p>
                                </div>
                            ) : (
                                <div className="bg-black/20 p-2 rounded flex items-start gap-2">
                                    <Milestone size={12} className="text-gray-500 mt-0.5 shrink-0" />
                                    <p className="text-[10px] text-gray-400 line-clamp-1">{p.next_step || 'No immediate directive.'}</p>
                                </div>
                            )}
                        </motion.div>
                    ))}
                </AnimatePresence>

                {topProjects.length === 0 && (
                    <div className="text-center py-10 text-gray-500 text-xs">No Active Missions</div>
                )}
            </div>
        </div>
    );
}
