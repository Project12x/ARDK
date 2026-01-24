import { useState, useRef, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';

export function DashboardNotesWidget() {
    const notes = useLiveQuery(() =>
        db.global_notes.where('category').equals('dashboard_scratchpad').toArray()
    );
    const [content, setContent] = useState('');
    const textareaRef = useRef<HTMLTextAreaElement>(null);

    // Initialize or load note
    useEffect(() => {
        if (notes && notes.length > 0) {
            // Only update checks if content matches to avoid loop/cursor jump
            // But actually, we just want to set it initially or when switching notes
            // For a single scratchpad, we can just use the db content directly if we didn't have local state
            // But local state is good for typing performance.
            // Let's just set it if it's the *first* load
            if (content === '' && notes[0].content !== '') {
                setContent(notes[0].content);
            }
        } else if (notes && notes.length === 0) {
            // Create default note if none exists
            db.global_notes.add({
                title: 'Scratchpad',
                category: 'dashboard_scratchpad',
                content: '',
                created_at: new Date(),
                updated_at: new Date(),
                pinned: true
            });
        }
    }, [notes]);

    const handleSave = async (newContent: string) => {
        setContent(newContent);
        if (notes && notes.length > 0) {
            await db.global_notes.update(notes[0].id!, {
                content: newContent,
                updated_at: new Date()
            });
        }
    };

    return (
        <div className="bg-neutral-900/50 border border-white/10 rounded-xl p-6 flex flex-col h-[300px] hover:border-accent/50 transition-colors group relative overflow-hidden">
            <div className="absolute top-0 right-0 p-2 opacity-0 group-hover:opacity-50 text-[10px] font-mono text-accent pointer-events-none">
                <div className="bg-accent/10 px-2 py-1 rounded">SCRATCHPAD</div>
            </div>
            <textarea
                ref={textareaRef}
                value={content}
                onChange={(e) => handleSave(e.target.value)}
                placeholder="Type anything here..."
                className="flex-1 bg-transparent border-none resize-none focus:outline-none text-gray-300 font-mono text-sm leading-relaxed placeholder-gray-700"
                spellCheck={false}
            />
        </div>
    );
}
