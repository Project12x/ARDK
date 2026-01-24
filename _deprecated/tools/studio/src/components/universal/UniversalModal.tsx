import { ReactNode } from 'react';
import { Drawer } from 'vaul';
import { X } from 'lucide-react';
import clsx from 'clsx';

interface UniversalModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    title?: string;
    description?: string;
    children: ReactNode;
    trigger?: ReactNode;
    className?: string;
}

export function UniversalModal({
    open,
    onOpenChange,
    title,
    description,
    children,
    trigger,
    className
}: UniversalModalProps) {
    return (
        <Drawer.Root open={open} onOpenChange={onOpenChange}>
            {trigger && <Drawer.Trigger asChild>{trigger}</Drawer.Trigger>}
            <Drawer.Portal>
                <Drawer.Overlay className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50" />
                <Drawer.Content className={clsx(
                    "bg-zinc-900 flex flex-col rounded-t-2xl h-[90vh] mt-24 fixed bottom-0 left-0 right-0 z-50 border-t border-white/10 outline-none",
                    className
                )}>
                    {/* Visual Handle */}
                    <div className="mx-auto w-12 h-1.5 flex-shrink-0 rounded-full bg-zinc-700 mt-4 mb-4" />

                    {/* Header */}
                    <div className="px-6 pb-4 border-b border-white/5 flex justify-between items-start">
                        <div>
                            {title && <Drawer.Title className="font-bold text-xl text-white mb-1">{title}</Drawer.Title>}
                            {description && <p className="text-sm text-zinc-400">{description}</p>}
                        </div>
                        <button
                            onClick={() => onOpenChange(false)}
                            className="p-2 bg-white/5 rounded-full hover:bg-white/10 transition-colors text-zinc-400 hover:text-white"
                        >
                            <X size={20} />
                        </button>
                    </div>

                    {/* Scrollable Content */}
                    <div className="flex-1 overflow-y-auto p-6">
                        {children}
                    </div>
                </Drawer.Content>
            </Drawer.Portal>
        </Drawer.Root>
    );
}
