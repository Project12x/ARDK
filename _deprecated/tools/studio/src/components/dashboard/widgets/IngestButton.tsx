import { Inbox } from 'lucide-react';

interface IngestButtonProps {
    onClick: () => void;
    disabled?: boolean;
}

export function IngestButton({ onClick, disabled }: IngestButtonProps) {
    return (
        <button
            onClick={disabled ? undefined : onClick}
            disabled={disabled}
            className={`w-full h-full flex flex-col items-center justify-center gap-2 bg-gradient-to-br from-purple-900/20 to-purple-600/10 border border-purple-500/20 rounded-xl transition-all group ${disabled
                    ? 'opacity-50 pointer-events-none'
                    : 'hover:from-purple-900/40 hover:to-purple-600/30 hover:border-purple-500/40 cursor-pointer'
                }`}
        >
            <Inbox size={24} className="text-purple-400 group-hover:text-purple-300 transition-colors" />
            <span className="text-xs font-mono uppercase text-purple-400 group-hover:text-purple-300 tracking-wider">
                Ingest
            </span>
        </button>
    );
}
