import { Plus } from 'lucide-react';

interface CreateButtonProps {
    onClick: () => void;
    disabled?: boolean;
}

export function CreateButton({ onClick, disabled }: CreateButtonProps) {
    return (
        <button
            onClick={disabled ? undefined : onClick}
            disabled={disabled}
            className={`w-full h-full flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-accent/20 to-accent/10 border border-accent/20 rounded-xl transition-all group ${disabled
                    ? 'opacity-50 pointer-events-none'
                    : 'hover:from-accent/40 hover:to-accent/30 hover:border-accent/40 cursor-pointer'
                }`}
        >
            <Plus size={24} className="text-accent group-hover:text-white transition-colors" />
            <span className="text-xs font-mono uppercase text-accent group-hover:text-white tracking-wider">
                New Project
            </span>
        </button>
    );
}
