import { useEffect, useState } from 'react';
import { eventBus } from '../../../lib/registry/eventBus';
import { UniversalEditModal } from './UniversalEditModal';
import { AnimatePresence } from 'framer-motion';

export type ModalState = {
    isOpen: boolean;
    modalId: string;
    entityType?: string;
    entityId?: string;
    data?: any;
};

export function UniversalModalManager() {
    const [state, setState] = useState<ModalState>({
        isOpen: false,
        modalId: '',
    });

    useEffect(() => {
        const handleOpen = (payload: any) => {
            console.log('[UniversalModalManager] Opening:', payload);
            setState({
                isOpen: true,
                modalId: payload.modalId,
                entityType: payload.entityType,
                entityId: payload.entityId,
                data: payload.data
            });
        };

        const handleClose = () => {
            setState(s => ({ ...s, isOpen: false }));
        };

        eventBus.on('modal:open', handleOpen);
        eventBus.on('modal:edit', handleOpen); // Alias for convenience
        eventBus.on('modal:close', handleClose);

        return () => {
            eventBus.off('modal:open', handleOpen);
            eventBus.off('modal:edit', handleOpen);
            eventBus.off('modal:close', handleClose);
        };
    }, []);

    if (!state.isOpen) return null;

    return (
        <AnimatePresence>
            {state.isOpen && (
                <>
                    {/* EDIT MODAL */}
                    {(state.modalId === 'edit' || state.modalId === 'create') && state.entityType && (
                        <UniversalEditModal
                            entityType={state.entityType}
                            entityId={state.entityId}
                            onClose={() => setState(s => ({ ...s, isOpen: false }))}
                        />
                    )}

                    {/* DETAIL MODAL (Placeholder) */}
                    {state.modalId === 'detail' && (
                        // <UniversalDetailModal ... />
                        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80">
                            <div className="bg-zinc-900 p-8 rounded text-white border border-white/10">
                                <h2 className="text-xl font-bold mb-4">Detail View: {state.entityType}</h2>
                                <pre className="bg-black/50 p-4 rounded text-xs font-mono">
                                    {JSON.stringify(state, null, 2)}
                                </pre>
                                <button
                                    onClick={() => setState(s => ({ ...s, isOpen: false }))}
                                    className="mt-4 px-4 py-2 bg-white/10 hover:bg-white/20 rounded"
                                >
                                    Close
                                </button>
                            </div>
                        </div>
                    )}
                </>
            )}
        </AnimatePresence>
    );
}
