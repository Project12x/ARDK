import { FileUp, PlusCircle } from 'lucide-react';

export function QuickActionsWidget({ onIngest, onCreate }: { onIngest: () => void, onCreate: () => void }) {
    return (
        <div className="h-full grid grid-cols-2 gap-2">
            <button
                onClick={onIngest}
                className="flex flex-col items-center justify-center p-2 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-accent group transition-all rounded-xl h-full"
            >
                <FileUp size={24} className="text-gray-400 group-hover:text-accent mb-2 transition-colors" />
                <span className="text-xs font-bold text-white uppercase">Ingest</span>
            </button>
            <button
                onClick={onCreate}
                className="flex flex-col items-center justify-center p-2 bg-white/5 border border-white/10 hover:bg-white/10 hover:border-accent group transition-all rounded-xl h-full"
            >
                <PlusCircle size={24} className="text-gray-400 group-hover:text-accent mb-2 transition-colors" />
                <span className="text-xs font-bold text-white uppercase">New</span>
            </button>
        </div>
    );
}
