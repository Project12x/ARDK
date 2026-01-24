import { useState } from 'react';
import { toast } from 'sonner';
import { Plus, CheckSquare, StickyNote, Zap } from 'lucide-react';
import { Button } from '../ui/Button';
// Note: We'll add more modals later (Task, Note)

import { useUIStore } from '../../store/useStore';

export function QuickActionHUD() {
    const { setCreateProjectOpen } = useUIStore();
    const [isOpen, setIsOpen] = useState(false);

    return (
        <div className="relative">
            {/* Modal now handled globally in Layout */}

            <div className="flex items-center gap-2">
                <Button
                    size="sm"
                    variant="primary"
                    className="bg-accent text-black hover:bg-white font-bold shadow-[0_0_15px_rgba(59,130,246,0.2)] rounded-full w-8 h-8 flex items-center justify-center p-0"
                    onClick={() => setIsOpen(!isOpen)}
                    title="Create"
                    onBlur={() => setTimeout(() => setIsOpen(false), 200)} // Delay close for clicks
                >
                    <Plus size={18} />
                </Button>
            </div>

            {/* Dropdown Menu */}
            {isOpen && (
                <div className="absolute top-full right-0 mt-2 w-48 bg-black border border-white/20 rounded-lg shadow-2xl z-50 animate-in slide-in-from-top-2 fade-in duration-200 overflow-hidden">
                    <button
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 text-left text-sm font-mono transition-colors group"
                        onMouseDown={() => setCreateProjectOpen(true)}
                    >
                        <Zap size={16} className="text-accent group-hover:text-white" />
                        <span>New Project</span>
                    </button>
                    <button
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 text-left text-sm font-mono transition-colors group"
                        onMouseDown={() => toast.info("Global Task Creation Coming Soon")}
                    >
                        <CheckSquare size={16} className="text-green-500 group-hover:text-white" />
                        <span>New Task</span>
                    </button>
                    <button
                        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-white/10 text-left text-sm font-mono transition-colors group"
                        onMouseDown={() => toast.info("Quick Note Coming Soon")}
                    >
                        <StickyNote size={16} className="text-yellow-500 group-hover:text-white" />
                        <span>Quick Note</span>
                    </button>
                </div>
            )}
        </div>
    );
}
