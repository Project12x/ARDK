import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import { db, type InboxItem, type GlobalNote } from '../../lib/db';
import { Button } from '../ui/Button';
import {
    Zap,
    ListTodo,
    BookOpen,
    Clock,
    Trash2,
    Check,
    ChevronUp,
    ChevronDown,
    X,
    Sparkles,
    FolderPlus
} from 'lucide-react';
import clsx from 'clsx';

interface TriageModeProps {
    items: InboxItem[];
    onComplete: () => void;
    onExit: () => void;
}

export function TriageMode({ items, onComplete, onExit }: TriageModeProps) {
    const navigate = useNavigate();
    const [currentIndex, setCurrentIndex] = useState(0);
    const [selectingProject, setSelectingProject] = useState(false);
    const [projects, setProjects] = useState<{ id: number; title: string }[]>([]);

    const currentItem = items[currentIndex];
    const isLast = currentIndex >= items.length - 1;

    // Load projects for task assignment
    useEffect(() => {
        db.projects
            .filter(p => !p.deleted_at && p.status !== 'archived' && p.status !== 'someday')
            .toArray()
            .then(p => setProjects(p.map(proj => ({ id: proj.id!, title: proj.title }))));
    }, []);

    const nextItem = useCallback(() => {
        if (isLast) {
            onComplete();
            toast.success('Inbox cleared!');
        } else {
            setCurrentIndex(i => i + 1);
        }
        setSelectingProject(false);
    }, [isLast, onComplete]);

    const prevItem = useCallback(() => {
        if (currentIndex > 0) {
            setCurrentIndex(i => i - 1);
        }
        setSelectingProject(false);
    }, [currentIndex]);

    // Triage actions
    const triageAsProject = async () => {
        const title = currentItem.extracted_title || currentItem.content.substring(0, 100);
        const id = await db.projects.add({
            title,
            status: 'active',
            priority: 3,
            created_at: new Date(),
            updated_at: new Date(),
            version: '0.1.0',
            tags: [],
            is_archived: false
        });
        await db.inbox_items.update(currentItem.id!, {
            triaged_at: new Date(),
            triaged_to: 'project',
            resolved_id: id as number
        });
        toast.success(`Project "${title}" created!`);
        nextItem();
    };

    const triageAsTask = async (projectId: number, projectTitle: string) => {
        const title = currentItem.extracted_title || currentItem.content.substring(0, 100);
        const id = await db.project_tasks.add({
            project_id: projectId,
            title,
            status: 'pending',
            phase: 'Planning',
            priority: 3
        });
        await db.inbox_items.update(currentItem.id!, {
            triaged_at: new Date(),
            triaged_to: 'task',
            resolved_id: id as number
        });
        toast.success(`Task added to "${projectTitle}"`);
        setSelectingProject(false);
        nextItem();
    };

    const triageAsReference = async () => {
        const title = currentItem.extracted_title || currentItem.content.substring(0, 50);
        const id = await db.global_notes.add({
            title,
            content: currentItem.content,
            category: 'Reference',
            created_at: new Date(),
            updated_at: new Date(),
            pinned: false
        });
        await db.inbox_items.update(currentItem.id!, {
            triaged_at: new Date(),
            triaged_to: 'reference',
            resolved_id: id as number
        });
        toast.success('Saved as Reference');
        nextItem();
    };

    const triageAsSomeday = async () => {
        const title = currentItem.extracted_title || currentItem.content.substring(0, 100);
        const id = await db.projects.add({
            title,
            status: 'someday' as any, // Add someday status
            priority: 1,
            created_at: new Date(),
            updated_at: new Date(),
            version: '0.0.0',
            tags: ['someday'],
            is_archived: false
        });
        await db.inbox_items.update(currentItem.id!, {
            triaged_at: new Date(),
            triaged_to: 'someday',
            resolved_id: id as number
        });
        toast.success('Moved to Someday');
        nextItem();
    };

    const triageAsDelete = async () => {
        await db.inbox_items.update(currentItem.id!, {
            triaged_at: new Date(),
            triaged_to: 'deleted'
        });
        toast.success('Deleted');
        nextItem();
    };

    const acceptSuggestion = async () => {
        if (!currentItem.suggested_action) return;

        switch (currentItem.suggested_action) {
            case 'create_project':
                await triageAsProject();
                break;
            case 'add_task':
                if (currentItem.suggested_project_id) {
                    const proj = projects.find(p => p.id === currentItem.suggested_project_id);
                    if (proj) {
                        await triageAsTask(proj.id, proj.title);
                    } else {
                        setSelectingProject(true);
                    }
                } else {
                    setSelectingProject(true);
                }
                break;
            case 'reference':
                await triageAsReference();
                break;
            case 'someday':
                await triageAsSomeday();
                break;
        }
    };

    // Keyboard shortcuts
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if (selectingProject) {
                if (e.key === 'Escape') setSelectingProject(false);
                return;
            }

            switch (e.key.toLowerCase()) {
                case 'p':
                    triageAsProject();
                    break;
                case 't':
                    setSelectingProject(true);
                    break;
                case 'r':
                    triageAsReference();
                    break;
                case 's':
                    triageAsSomeday();
                    break;
                case 'd':
                    triageAsDelete();
                    break;
                case 'y':
                    if (currentItem.suggested_action) acceptSuggestion();
                    break;
                case 'j':
                case 'arrowdown':
                    nextItem();
                    break;
                case 'k':
                case 'arrowup':
                    prevItem();
                    break;
                case 'escape':
                    onExit();
                    break;
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [currentItem, selectingProject, nextItem, prevItem, onExit]);

    if (!currentItem) {
        return (
            <div className="flex flex-col items-center justify-center h-[80vh] text-center">
                <Check size={64} className="text-accent mb-4" />
                <h2 className="text-2xl font-bold text-white mb-2">All Done!</h2>
                <p className="text-gray-400 mb-6">Your inbox is now empty.</p>
                <Button onClick={onComplete}>Back to Inbox</Button>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black z-50 flex flex-col">
            {/* Header */}
            <div className="flex items-center justify-between px-8 py-4 border-b border-white/10 bg-neutral-900/50">
                <div className="flex items-center gap-4">
                    <Sparkles size={24} className="text-accent" />
                    <span className="font-bold text-white uppercase tracking-wider">Triage Mode</span>
                    <span className="text-sm text-gray-500 font-mono">
                        {currentIndex + 1} / {items.length}
                    </span>
                </div>
                <Button variant="ghost" onClick={onExit} className="text-gray-400">
                    <X size={18} className="mr-2" /> Exit (ESC)
                </Button>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex items-center justify-center p-8">
                <div className="max-w-2xl w-full space-y-8">
                    {/* Item Card */}
                    <div className="bg-neutral-900 border border-white/10 rounded-2xl p-8 shadow-2xl">
                        <div className="text-2xl font-bold text-white mb-4">
                            {currentItem.extracted_title || currentItem.content}
                        </div>
                        {currentItem.extracted_title && currentItem.content !== currentItem.extracted_title && (
                            <p className="text-gray-400 text-sm mb-4">{currentItem.content}</p>
                        )}

                        {/* AI Suggestion */}
                        {currentItem.suggested_action && currentItem.confidence && currentItem.confidence > 0.5 && (
                            <div className="flex items-center gap-3 bg-accent/10 border border-accent/20 rounded-lg p-4 mt-6">
                                <Sparkles size={20} className="text-accent" />
                                <div className="flex-1">
                                    <span className="text-accent font-bold uppercase text-sm">AI Suggests: </span>
                                    <span className="text-white">
                                        {currentItem.suggested_action === 'create_project' && 'Create new Project'}
                                        {currentItem.suggested_action === 'add_task' && `Add Task to "${currentItem.suggested_project_title}"`}
                                        {currentItem.suggested_action === 'reference' && 'Save as Reference'}
                                        {currentItem.suggested_action === 'someday' && 'Move to Someday'}
                                    </span>
                                </div>
                                <Button
                                    onClick={acceptSuggestion}
                                    className="bg-accent text-black font-bold"
                                >
                                    Accept (Y)
                                </Button>
                            </div>
                        )}
                    </div>

                    {/* Project Selection Modal */}
                    {selectingProject && (
                        <div className="bg-neutral-800 border border-white/10 rounded-xl p-4 max-h-64 overflow-y-auto">
                            <div className="text-xs font-bold text-gray-500 uppercase mb-3">Select Project for Task</div>
                            {projects.map(proj => (
                                <button
                                    key={proj.id}
                                    onClick={() => triageAsTask(proj.id, proj.title)}
                                    className="w-full text-left px-4 py-3 rounded-lg hover:bg-white/10 text-white font-medium transition-colors"
                                >
                                    {proj.title}
                                </button>
                            ))}
                            <Button
                                variant="ghost"
                                onClick={() => setSelectingProject(false)}
                                className="w-full mt-2 text-gray-500"
                            >
                                Cancel
                            </Button>
                        </div>
                    )}

                    {/* Action Buttons */}
                    {!selectingProject && (
                        <div className="grid grid-cols-5 gap-3">
                            <ActionButton
                                icon={<FolderPlus size={20} />}
                                label="Project"
                                shortcut="P"
                                onClick={triageAsProject}
                                color="text-accent"
                            />
                            <ActionButton
                                icon={<ListTodo size={20} />}
                                label="Task"
                                shortcut="T"
                                onClick={() => setSelectingProject(true)}
                                color="text-green-400"
                            />
                            <ActionButton
                                icon={<BookOpen size={20} />}
                                label="Reference"
                                shortcut="R"
                                onClick={triageAsReference}
                                color="text-blue-400"
                            />
                            <ActionButton
                                icon={<Clock size={20} />}
                                label="Someday"
                                shortcut="S"
                                onClick={triageAsSomeday}
                                color="text-purple-400"
                            />
                            <ActionButton
                                icon={<Trash2 size={20} />}
                                label="Delete"
                                shortcut="D"
                                onClick={triageAsDelete}
                                color="text-red-400"
                            />
                        </div>
                    )}

                    {/* Navigation */}
                    <div className="flex justify-center gap-4">
                        <Button
                            variant="ghost"
                            onClick={prevItem}
                            disabled={currentIndex === 0}
                            className="text-gray-500"
                        >
                            <ChevronUp size={16} className="mr-1" /> Previous (K)
                        </Button>
                        <Button
                            variant="ghost"
                            onClick={nextItem}
                            className="text-gray-500"
                        >
                            Skip / Next (J) <ChevronDown size={16} className="ml-1" />
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}

function ActionButton({
    icon,
    label,
    shortcut,
    onClick,
    color
}: {
    icon: React.ReactNode;
    label: string;
    shortcut: string;
    onClick: () => void;
    color: string;
}) {
    return (
        <button
            onClick={onClick}
            className={clsx(
                "flex flex-col items-center gap-2 p-4 rounded-xl border border-white/10 bg-white/5",
                "hover:bg-white/10 hover:border-white/20 transition-all group"
            )}
        >
            <div className={clsx("transition-colors", color)}>{icon}</div>
            <span className="text-sm font-bold text-white">{label}</span>
            <kbd className="text-[10px] bg-white/10 px-2 py-0.5 rounded text-gray-500 group-hover:text-white">
                {shortcut}
            </kbd>
        </button>
    );
}
