import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { Card } from './ui/Card';
import { Terminal } from 'lucide-react';

interface ProjectChangelogProps {
    projectId: number;
}

export function ProjectChangelog({ projectId }: ProjectChangelogProps) {
    const logs = useLiveQuery(() =>
        db.logs.where({ project_id: projectId }).reverse().sortBy('date') // Descending order
    );

    return (
        <div className="space-y-6">
            <Card title="Project History">
                <div className="border border-border bg-black font-mono text-sm relative">
                    <div className="absolute top-0 left-8 bottom-0 w-px bg-white/10" />

                    <div className="divide-y divide-white/5">
                        {logs?.map((log) => (
                            <div key={log.id} className="flex group hover:bg-white/5 transition-colors">
                                <div className="w-32 shrink-0 p-4 text-gray-500 text-xs text-right pr-8 relative">
                                    {/* Timeline dot */}
                                    <div className="absolute right-[-4px] top-5 w-2 h-2 rounded-full bg-surface border border-gray-600 group-hover:border-accent group-hover:bg-accent transition-colors z-10" />
                                    {(() => {
                                        const d = new Date(log.date);
                                        if (isNaN(d.getTime())) return 'INVALID DATE';
                                        return (
                                            <>
                                                {d.toLocaleDateString()}
                                                <br />
                                                {d.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </>
                                        );
                                    })()}
                                </div>
                                <div className="flex-1 p-4 pl-8">
                                    <div className="flex items-center gap-3 mb-1">
                                        <span className="text-accent font-bold">{log.version}</span>
                                        <span className="text-gray-600 text-xs px-1 border border-gray-800 uppercase">{log.type}</span>
                                    </div>
                                    <p className="text-gray-300">{log.summary}</p>
                                </div>
                            </div>
                        ))}

                        {logs?.length === 0 && (
                            <div className="p-8 flex flex-col items-center justify-center text-gray-600">
                                <Terminal size={32} className="mb-4 opacity-50" />
                                <p>No log history found.</p>
                            </div>
                        )}
                    </div>
                </div>
            </Card>
        </div>
    );
}
