import { useState, useEffect, useCallback } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { db, type InboxItem } from '../lib/db';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import {
    Inbox,
    Trash2,
    Zap,
    ListTodo,
    BookOpen,
    Clock,
    Sparkles,
    ChevronRight,
    AlertCircle
} from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
import { TriageMode } from '../components/inbox/TriageMode';

export function InboxPage() {
    const inboxItems = useLiveQuery(() =>
        db.inbox_items
            .filter(item => !item.triaged_at)
            .reverse()
            .toArray()
    );

    const [isTriageMode, setIsTriageMode] = useState(false);
    const [listRef] = useAutoAnimate();

    const handleDelete = async (id: number) => {
        await db.inbox_items.update(id, {
            triaged_at: new Date(),
            triaged_to: 'deleted'
        });
        toast.success('Item dismissed');
    };

    const actionIcons = {
        create_project: <Zap size={14} className="text-accent" />,
        add_task: <ListTodo size={14} className="text-green-400" />,
        reference: <BookOpen size={14} className="text-blue-400" />,
        someday: <Clock size={14} className="text-purple-400" />
    };

    const actionLabels = {
        create_project: 'New Project',
        add_task: 'Add Task',
        reference: 'Reference',
        someday: 'Someday'
    };

    if (isTriageMode && inboxItems && inboxItems.length > 0) {
        return (
            <TriageMode
                items={inboxItems}
                onComplete={() => setIsTriageMode(false)}
                onExit={() => setIsTriageMode(false)}
            />
        );
    }

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-white/10 pb-6">
                <div className="flex items-center gap-4">
                    <div className="p-3 bg-accent/10 rounded-xl">
                        <Inbox size={28} className="text-accent" />
                    </div>
                    <div>
                        <h1 className="text-3xl font-black text-white uppercase tracking-tight">Inbox</h1>
                        <p className="text-gray-400 text-sm font-mono">
                            {inboxItems?.length || 0} items waiting for triage
                        </p>
                    </div>
                </div>

                {inboxItems && inboxItems.length > 0 && (
                    <Button
                        onClick={() => setIsTriageMode(true)}
                        className="bg-accent text-black font-bold hover:bg-white"
                    >
                        <Sparkles size={16} className="mr-2" />
                        ENTER TRIAGE MODE
                    </Button>
                )}
            </div>

            {/* Empty State */}
            {(!inboxItems || inboxItems.length === 0) && (
                <div className="flex flex-col items-center justify-center py-20 text-center">
                    <div className="p-6 bg-white/5 rounded-full mb-6">
                        <Inbox size={48} className="text-gray-600" />
                    </div>
                    <h2 className="text-xl font-bold text-white mb-2">Inbox Zero!</h2>
                    <p className="text-gray-500 max-w-md">
                        Your inbox is empty. Use <kbd className="bg-white/10 px-2 py-0.5 rounded text-xs">Ctrl+Shift+Space</kbd> to quickly capture ideas anywhere.
                    </p>
                </div>
            )}

            {/* Item List */}
            <div ref={listRef} className="space-y-3">
                {inboxItems?.map(item => (
                    <Card
                        key={item.id}
                        className="p-4 hover:border-white/20 transition-all group"
                    >
                        <div className="flex items-start gap-4">
                            {/* Suggestion Badge */}
                            <div className="flex-shrink-0 pt-1">
                                {item.suggested_action ? (
                                    <div className={clsx(
                                        "flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold uppercase",
                                        item.confidence && item.confidence > 0.7
                                            ? "bg-white/10 border border-white/20"
                                            : "bg-white/5 border border-white/10"
                                    )}>
                                        {actionIcons[item.suggested_action]}
                                        {actionLabels[item.suggested_action]}
                                    </div>
                                ) : (
                                    <div className="flex items-center gap-1.5 px-2 py-1 rounded-full text-[10px] font-bold uppercase bg-white/5 border border-white/10 text-gray-500">
                                        <AlertCircle size={12} />
                                        Untriaged
                                    </div>
                                )}
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <p className="text-white font-medium truncate">
                                    {item.extracted_title || item.content}
                                </p>
                                {item.extracted_title && item.content !== item.extracted_title && (
                                    <p className="text-xs text-gray-500 truncate mt-1">
                                        {item.content}
                                    </p>
                                )}
                                {item.suggested_project_title && (
                                    <p className="text-xs text-accent mt-1">
                                        → {item.suggested_project_title}
                                    </p>
                                )}
                            </div>

                            {/* Actions */}
                            <div className="flex-shrink-0 flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity">
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => handleDelete(item.id!)}
                                    className="h-8 w-8 p-0 text-gray-500 hover:text-red-400"
                                >
                                    <Trash2 size={14} />
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    className="h-8 text-xs"
                                    onClick={() => setIsTriageMode(true)}
                                >
                                    Triage <ChevronRight size={12} className="ml-1" />
                                </Button>
                            </div>
                        </div>

                        {/* Timestamp */}
                        <div className="mt-2 text-[10px] text-gray-600 font-mono">
                            {new Date(item.created_at).toLocaleString()}
                        </div>
                    </Card>
                ))}
            </div>
        </div>
    );
}
