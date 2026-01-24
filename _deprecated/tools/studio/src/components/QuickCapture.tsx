import { useState, useEffect, useRef } from 'react';
import { toast } from 'sonner';
import { db } from '../lib/db';
import { AIService } from '../lib/AIService';
import { Inbox, Send, X, Loader2, Sparkles } from 'lucide-react';
import { Button } from './ui/Button';
import clsx from 'clsx';

interface QuickCaptureProps {
    isOpen: boolean;
    onClose: () => void;
}

export function QuickCapture({ isOpen, onClose }: QuickCaptureProps) {
    const [content, setContent] = useState('');
    const [isProcessing, setIsProcessing] = useState(false);
    const inputRef = useRef<HTMLInputElement>(null);

    // Focus input when opened
    useEffect(() => {
        if (isOpen && inputRef.current) {
            inputRef.current.focus();
        }
    }, [isOpen]);

    // Global keyboard shortcut
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            // Escape to close
            if (e.key === 'Escape' && isOpen) {
                onClose();
            }
        };

        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen, onClose]);

    const handleSubmit = async () => {
        if (!content.trim()) return;

        setIsProcessing(true);
        try {
            // Detect type from content
            const isLink = /^https?:\/\//.test(content.trim());
            const type = isLink ? 'link' : 'general';

            // Try to get AI suggestion if API key exists
            let suggestion: any = null;
            if (localStorage.getItem('GEMINI_API_KEY')) {
                try {
                    suggestion = await AIService.parseInboxItem(content);
                } catch (e) {
                    console.warn('AI parsing failed, saving without suggestion:', e);
                }
            }

            // Save to inbox
            await db.inbox_items.add({
                content: content.trim(),
                type,
                created_at: new Date(),
                suggested_action: suggestion?.suggested_action,
                suggested_project_id: suggestion?.suggested_project_id,
                suggested_project_title: suggestion?.suggested_project_title,
                extracted_title: suggestion?.extracted_title,
                confidence: suggestion?.confidence
            });

            toast.success('Captured to Inbox', {
                description: suggestion ? `Suggestion: ${suggestion.suggested_action}` : undefined
            });
            setContent('');
            onClose();
        } catch (e) {
            console.error(e);
            toast.error('Failed to capture');
        } finally {
            setIsProcessing(false);
        }
    };

    const handleKeyDown = (e: React.KeyboardEvent) => {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            handleSubmit();
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-start justify-center pt-[20vh]">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/60 backdrop-blur-sm animate-in fade-in duration-150"
                onClick={onClose}
            />

            {/* Capture Card */}
            <div className="relative w-full max-w-2xl mx-4 animate-in slide-in-from-top-4 fade-in duration-200">
                <div className="bg-neutral-900 border border-accent/30 rounded-xl shadow-2xl shadow-accent/10 overflow-hidden">
                    {/* Header */}
                    <div className="flex items-center justify-between px-4 py-3 bg-gradient-to-r from-accent/10 to-transparent border-b border-white/5">
                        <div className="flex items-center gap-2 text-accent">
                            <Inbox size={18} />
                            <span className="font-bold text-sm uppercase tracking-wider">Quick Capture</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-[10px] text-gray-500 font-mono">ESC to close</span>
                            <Button variant="ghost" size="sm" onClick={onClose} className="h-6 w-6 p-0">
                                <X size={14} />
                            </Button>
                        </div>
                    </div>

                    {/* Input */}
                    <div className="p-4">
                        <div className="flex gap-3">
                            <input
                                ref={inputRef}
                                type="text"
                                value={content}
                                onChange={(e) => setContent(e.target.value)}
                                onKeyDown={handleKeyDown}
                                placeholder="Capture an idea, task, link, or note..."
                                className="flex-1 bg-black/50 border border-white/10 rounded-lg px-4 py-3 text-white placeholder-gray-500 focus:outline-none focus:border-accent/50 focus:ring-1 focus:ring-accent/20 transition-all"
                                disabled={isProcessing}
                            />
                            <Button
                                onClick={handleSubmit}
                                disabled={!content.trim() || isProcessing}
                                className={clsx(
                                    "bg-accent text-black font-bold px-6 hover:bg-white transition-colors",
                                    isProcessing && "opacity-50"
                                )}
                            >
                                {isProcessing ? (
                                    <Loader2 size={18} className="animate-spin" />
                                ) : (
                                    <Send size={18} />
                                )}
                            </Button>
                        </div>

                        {/* Hints */}
                        <div className="mt-3 flex items-center gap-4 text-[10px] text-gray-500">
                            <span className="flex items-center gap-1">
                                <Sparkles size={10} className="text-accent" />
                                AI will suggest where this belongs
                            </span>
                            <span>Press <kbd className="bg-white/10 px-1.5 py-0.5 rounded text-white">Enter</kbd> to submit</span>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
