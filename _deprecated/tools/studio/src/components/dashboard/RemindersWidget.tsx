import { useState, useRef, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { Check, Plus, Trash2 } from 'lucide-react';
import clsx from 'clsx';

export function RemindersWidget() {
    const reminders = useLiveQuery(() =>
        db.reminders.orderBy('created_at').reverse().toArray()
    );
    const [newItem, setNewItem] = useState('');
    const [listRef] = useAutoAnimate();
    const [editingId, setEditingId] = useState<number | null>(null);

    const handleAdd = async (e?: React.FormEvent) => {
        e?.preventDefault();
        if (!newItem.trim()) return;

        await db.reminders.add({
            content: newItem.trim(),
            is_completed: false,
            priority: 1,
            created_at: new Date()
        });
        setNewItem('');
    };

    const handleToggle = async (id: number, current: boolean) => {
        await db.reminders.update(id, { is_completed: !current });
    };

    const handleDelete = async (id: number) => {
        await db.reminders.delete(id);
    };

    const handleUpdate = async (id: number, content: string) => {
        if (!content.trim()) return handleDelete(id);
        await db.reminders.update(id, { content: content.trim() });
        setEditingId(null);
    };

    return (
        <div className="bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col h-full min-h-[140px] hover:border-accent/50 transition-colors relative overflow-hidden">
            {/* Background Gradient */}
            <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-transparent via-accent/50 to-transparent opacity-20" />

            <div className="flex items-center justify-between mb-4">
                <h2 className="text-xs font-mono font-bold uppercase tracking-widest text-gray-400">Front of Mind</h2>
                <div className="flex items-center gap-2">
                    <span className="text-[10px] bg-white/10 px-1.5 py-0.5 rounded text-gray-500 font-mono">
                        {reminders?.filter(r => !r.is_completed).length || 0} ACTIVE
                    </span>
                </div>
            </div>

            <div ref={listRef} className="space-y-1 flex-1 overflow-y-auto max-h-[200px] pr-1 custom-scrollbar">
                {reminders?.filter(r => !r.is_completed).map(r => (
                    <ReminderItem
                        key={r.id}
                        item={r}
                        isEditing={editingId === r.id}
                        onToggle={() => handleToggle(r.id!, r.is_completed)}
                        onEdit={(val) => handleUpdate(r.id!, val)}
                        setEditing={() => setEditingId(r.id!)}
                        onDelete={() => handleDelete(r.id!)}
                    />
                ))}

                {(!reminders || reminders.filter(r => !r.is_completed).length === 0) && (
                    <div className="text-center py-4 text-gray-600 text-xs italic">
                        No active reminders.
                    </div>
                )}
            </div>

            {/* Input */}
            <form onSubmit={handleAdd} className="mt-4 relative">
                <input
                    type="text"
                    value={newItem}
                    onChange={(e) => setNewItem(e.target.value)}
                    placeholder="Add reminder..."
                    className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-sm text-white placeholder-gray-600 focus:outline-none focus:border-accent focus:bg-white/10 transition-all pr-8"
                />
                <button
                    type="submit"
                    disabled={!newItem.trim()}
                    className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-accent disabled:opacity-50 transition-colors"
                >
                    <Plus size={14} />
                </button>
            </form>
        </div>
    );
}

interface ReminderItemProps {
    item: any;
    isEditing: boolean;
    onToggle: () => void;
    onEdit: (val: string) => void;
    setEditing: () => void;
    onDelete: () => void;
}

function ReminderItem({ item, isEditing, onToggle, onEdit, setEditing, onDelete }: ReminderItemProps) {
    const inputRef = useRef<HTMLInputElement>(null);

    useEffect(() => {
        if (isEditing && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isEditing]);

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter') {
            onEdit(inputRef.current?.value || '');
        } else if (e.key === 'Escape') {
            setEditing(); // Cancel
        }
    };

    return (
        <div className="flex items-center gap-3 group px-2 py-1 rounded hover:bg-white/5 transition-colors">
            <button
                onClick={onToggle}
                className={clsx(
                    "w-4 h-4 rounded border flex items-center justify-center transition-all",
                    item.is_completed
                        ? "bg-green-500/20 border-green-500 text-green-500"
                        : "border-white/20 hover:border-accent"
                )}
            >
                {item.is_completed && <Check size={10} />}
            </button>

            <div className="flex-1 min-w-0">
                {isEditing ? (
                    <input
                        ref={inputRef}
                        defaultValue={item.content}
                        onBlur={(e) => onEdit(e.target.value)}
                        onKeyDown={handleKeyDown}
                        className="w-full bg-black/50 border border-accent/30 rounded px-2 py-1 text-sm text-white focus:outline-none"
                    />
                ) : (
                    <span
                        onClick={!item.is_completed ? setEditing : undefined}
                        className={clsx(
                            "text-sm cursor-text hover:text-white transition-colors block truncate",
                            item.is_completed ? "text-gray-600 line-through" : "text-gray-300"
                        )}
                    >
                        {item.content}
                    </span>
                )}
            </div>

            <button
                onClick={onDelete}
                className="opacity-0 group-hover:opacity-100 text-gray-600 hover:text-red-400 transition-all"
            >
                <Trash2 size={12} />
            </button>
        </div>
    )
}
