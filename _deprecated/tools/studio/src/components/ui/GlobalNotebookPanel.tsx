import { useUIStore } from '../../store/useStore';
import { ProjectNotebook } from '../ProjectNotebook';
import { Button } from './Button';
import { X, Book } from 'lucide-react';
import clsx from 'clsx';
import { useEffect, useState } from 'react';

export function GlobalNotebookPanel() {
    const { isNotebookPanelOpen, setNotebookPanelOpen, currentProjectId } = useUIStore();
    const [isVisible, setIsVisible] = useState(false);

    // Handle animation state
    useEffect(() => {
        if (isNotebookPanelOpen) {
            setIsVisible(true);
        } else {
            const timer = setTimeout(() => setIsVisible(false), 300);
            return () => clearTimeout(timer);
        }
    }, [isNotebookPanelOpen]);

    if (!isVisible && !isNotebookPanelOpen) return null;

    return (
        <>
            {/* Backdrop */}
            {isNotebookPanelOpen && (
                <div
                    className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[99990] animate-in fade-in duration-300"
                    onClick={() => setNotebookPanelOpen(false)}
                />
            )}

            {/* Slide-over Panel */}
            <div
                className={clsx(
                    "fixed inset-y-0 right-0 w-full max-w-lg bg-gray-950 border-l border-white/10 z-[99991] shadow-2xl transform transition-transform duration-300 ease-in-out p-6 flex flex-col",
                    isNotebookPanelOpen ? "translate-x-0" : "translate-x-full"
                )}
            >
                {/* Header */}
                <div className="flex items-center justify-between mb-6 shrink-0">
                    <div className="flex items-center gap-2 text-white">
                        <Book className="text-accent" />
                        <h2 className="text-lg font-bold">Project Notebook</h2>
                    </div>
                    <Button variant="ghost" size="sm" onClick={() => setNotebookPanelOpen(false)}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto min-h-0 custom-scrollbar pr-2">
                    {currentProjectId ? (
                        <ProjectNotebook projectId={currentProjectId} />
                    ) : (
                        <div className="flex flex-col items-center justify-center h-full text-gray-500 gap-4">
                            <Book size={48} className="opacity-20" />
                            <p>No active project selected.</p>
                            <p className="text-xs max-w-xs text-center">Open a project to access its lab notebook entries.</p>
                        </div>
                    )}
                </div>
            </div>
        </>
    );
}
