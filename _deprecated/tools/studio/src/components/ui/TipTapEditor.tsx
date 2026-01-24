import { createPortal } from 'react-dom';
import { useEditor, EditorContent } from '@tiptap/react';
import StarterKit from '@tiptap/starter-kit';
import Placeholder from '@tiptap/extension-placeholder';
import Typography from '@tiptap/extension-typography';
import Image from '@tiptap/extension-image';
import Mention from '@tiptap/extension-mention';
import suggestion from './tiptap/suggestion';
import 'tippy.js/dist/tippy.css';
import {
    Bold, Italic, Code, Heading1, Heading2, List, ListOrdered, Quote,
    Image as ImageIcon, Undo, Redo
} from 'lucide-react';
import clsx from 'clsx';
import { useEffect } from 'react';

interface TipTapEditorProps {
    value: string;
    onChange: (content: string) => void;
    onSave?: () => void;
    placeholder?: string;
    className?: string;
    editable?: boolean;
    toolbarContainer?: HTMLDivElement | null;
}

export function TipTapEditor({ value, onChange, onSave, placeholder = 'Write something...', className, editable = true, toolbarContainer }: TipTapEditorProps) {
    const addImage = (file: File) => {
        const reader = new FileReader();
        reader.onload = (e) => {
            if (typeof e.target?.result === 'string') {
                editor?.chain().focus().setImage({ src: e.target.result }).run();
            }
        };
        reader.readAsDataURL(file);
    };

    const editor = useEditor({
        extensions: [
            StarterKit,
            Placeholder.configure({
                placeholder,
            }),
            Typography,
            Image,
            Mention.configure({
                HTMLAttributes: {
                    class: 'bg-accent/20 text-accent px-1 py-0.5 rounded font-bold no-underline cursor-pointer border border-accent/30 text-xs align-middle hover:bg-accent/30 transition-colors',
                },
                suggestion,
                renderLabel({ options, node }) {
                    return `${node.attrs.label ?? node.attrs.id}`;
                },
            }),
        ],
        content: value,
        editable,
        onUpdate: ({ editor }) => {
            onChange(editor.getHTML());
        },
        editorProps: {
            attributes: {
                class: 'prose prose-invert max-w-none focus:outline-none min-h-[100px] p-4 text-gray-200 text-sm font-mono',
            },
            handleKeyDown: (_view, event) => {
                if (event.key === 'Enter' && (event.ctrlKey || event.metaKey)) {
                    onSave?.();
                    return true;
                }
                return false;
            },
            handlePaste: (_view, event, _slice) => {
                const items = Array.from(event.clipboardData?.items || []);
                const images = items.filter(item => item.type.indexOf('image') === 0);

                if (images.length > 0) {
                    event.preventDefault();
                    images.forEach(item => {
                        const file = item.getAsFile();
                        if (file) addImage(file);
                    });
                    return true;
                }
                return false;
            },
            handleDrop: (_view, event, _slice, moved) => {
                if (!moved && event.dataTransfer && event.dataTransfer.files && event.dataTransfer.files.length > 0) {
                    const files = Array.from(event.dataTransfer.files);
                    const images = files.filter(file => file.type.indexOf('image') === 0);

                    if (images.length > 0) {
                        event.preventDefault();
                        images.forEach(file => addImage(file));
                        return true;
                    }
                }
                return false;
            }
        },
    });

    // Reset content if value prop changes externally (e.g. clear after save)
    useEffect(() => {
        if (editor && value === '' && editor.getText() !== '') {
            editor.commands.clearContent();
        }
    }, [value, editor]);

    if (!editor) return null;

    const Toolbar = (
        <div className={clsx(
            "flex items-center gap-1 overflow-x-auto no-scrollbar",
            !toolbarContainer && "p-2 border-b border-white/20 bg-neutral-800/80 backdrop-blur-sm sticky top-0 z-10"
        )}>
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleBold().run()}
                isActive={editor.isActive('bold')}
                icon={<Bold size={14} />}
                title="Bold (Ctrl+B)"
            />
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleItalic().run()}
                isActive={editor.isActive('italic')}
                icon={<Italic size={14} />}
                title="Italic (Ctrl+I)"
            />
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleCode().run()}
                isActive={editor.isActive('code')}
                icon={<Code size={14} />}
                title="Code (Ctrl+E)"
            />

            <div className="w-px h-4 bg-white/10 mx-1" />

            <ToolbarButton
                onClick={() => editor.chain().focus().toggleHeading({ level: 1 }).run()}
                isActive={editor.isActive('heading', { level: 1 })}
                icon={<Heading1 size={14} />}
                title="H1"
            />
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleHeading({ level: 2 }).run()}
                isActive={editor.isActive('heading', { level: 2 })}
                icon={<Heading2 size={14} />}
                title="H2"
            />

            <div className="w-px h-4 bg-white/10 mx-1" />

            <ToolbarButton
                onClick={() => editor.chain().focus().toggleBulletList().run()}
                isActive={editor.isActive('bulletList')}
                icon={<List size={14} />}
                title="Bullet List"
            />
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleOrderedList().run()}
                isActive={editor.isActive('orderedList')}
                icon={<ListOrdered size={14} />}
                title="Ordered List"
            />
            <ToolbarButton
                onClick={() => editor.chain().focus().toggleBlockquote().run()}
                isActive={editor.isActive('blockquote')}
                icon={<Quote size={14} />}
                title="Quote"
            />

            <div className="w-px h-4 bg-white/10 mx-1" />

            <ToolbarButton
                onClick={() => {
                    const url = window.prompt('Image URL');
                    if (url) editor.chain().focus().setImage({ src: url }).run();
                }}
                icon={<ImageIcon size={14} />}
                title="Insert Image"
            />

            <div className="flex-1" />

            <ToolbarButton
                onClick={() => editor.chain().focus().undo().run()}
                disabled={!editor.can().undo()}
                icon={<Undo size={14} />}
                title="Undo (Ctrl+Z)"
            />
            <ToolbarButton
                onClick={() => editor.chain().focus().redo().run()}
                disabled={!editor.can().redo()}
                icon={<Redo size={14} />}
                title="Redo (Ctrl+Y)"
            />
        </div>
    );

    return (
        <div className={clsx("bg-black/50 border border-white/10 rounded-lg overflow-hidden group focus-within:ring-1 focus-within:ring-accent transition-all", className)}>
            {/* Toolbar - Portalled or Inline */}
            {editable && (
                toolbarContainer
                    ? createPortal(Toolbar, toolbarContainer)
                    : Toolbar
            )}

            {/* Editor Content */}
            <EditorContent editor={editor} />
        </div>
    );
}

function ToolbarButton({ onClick, isActive, icon, title, disabled }: { onClick: () => void, isActive?: boolean, icon: React.ReactNode, title?: string, disabled?: boolean }) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            title={title}
            className={clsx(
                "p-1.5 rounded transition-all flex items-center justify-center",
                isActive
                    ? "bg-accent text-black shadow-sm"
                    : "text-gray-400 hover:text-white hover:bg-white/10",
                disabled && "opacity-30 cursor-not-allowed hover:bg-transparent hover:text-gray-400"
            )}
        >
            {icon}
        </button>
    );
}
