import { useState, ReactNode } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ChevronDown, MoreVertical } from 'lucide-react';
import clsx from 'clsx';
import type { UniversalAction } from '../../lib/universal/types';
import { UniversalActionBar } from './UniversalActionBar';

interface UniversalPanelProps {
    title: string;
    icon?: any;
    defaultExpanded?: boolean;
    actions?: UniversalAction[];
    children: ReactNode;
    className?: string;
    headerClassName?: string;
    variant?: 'default' | 'card' | 'glass';
}

export function UniversalPanel({
    title,
    icon: Icon,
    defaultExpanded = true,
    actions = [],
    children,
    className,
    headerClassName,
    variant = 'default'
}: UniversalPanelProps) {
    const [isExpanded, setIsExpanded] = useState(defaultExpanded);

    const variants = {
        default: "",
        card: "bg-black/20 border border-white/5 rounded-xl overflow-hidden",
        glass: "bg-white/5 border border-white/10 rounded-xl overflow-hidden backdrop-blur-md"
    };

    return (
        <div className={clsx("flex flex-col", variants[variant], className)}>
            {/* Header */}
            <div
                className={clsx(
                    "flex items-center justify-between px-4 py-3 cursor-pointer hover:bg-white/5 transition-colors select-none",
                    !isExpanded && "rounded-b-xl",
                    headerClassName
                )}
                onClick={() => setIsExpanded(!isExpanded)}
            >
                <div className="flex items-center gap-3">
                    <motion.div
                        animate={{ rotate: isExpanded ? 0 : -90 }}
                        className="text-gray-400"
                    >
                        <ChevronDown size={16} />
                    </motion.div>
                    {Icon && <Icon size={18} className="text-gray-400" />}
                    <h3 className="font-bold text-sm tracking-wide">{title}</h3>
                </div>

                {actions.length > 0 && (
                    <div className="flex items-center gap-2" onClick={e => e.stopPropagation()}>
                        <UniversalActionBar
                            actions={actions.slice(0, 3)}
                            size="sm"
                            variant="ghost"
                        />
                        {actions.length > 3 && (
                            <button className="text-gray-500 hover:text-white p-1">
                                <MoreVertical size={16} />
                            </button>
                        )}
                    </div>
                )}
            </div>

            {/* Content */}
            <AnimatePresence>
                {isExpanded && (
                    <motion.div
                        initial={{ height: 0, opacity: 0 }}
                        animate={{ height: "auto", opacity: 1 }}
                        exit={{ height: 0, opacity: 0 }}
                        transition={{ duration: 0.2, ease: "easeInOut" }}
                        className="overflow-hidden"
                    >
                        <div className="p-4 pt-0">
                            {children}
                        </div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
