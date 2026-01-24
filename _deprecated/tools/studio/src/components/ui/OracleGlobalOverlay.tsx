import { useUIStore } from '../../store/useStore';
import { OracleActionCard } from './OracleActionCard';
import { useState } from 'react';

export function OracleGlobalOverlay() {
    const { oracleProposal, setOracleProposal } = useUIStore();
    const [isSubmitting, setIsSubmitting] = useState(false);

    if (!oracleProposal) return null;

    const handleConfirm = async () => {
        setIsSubmitting(true);
        try {
            await oracleProposal.onConfirm();
            setOracleProposal(null);
        } catch (e) {
            console.error(e);
        } finally {
            setIsSubmitting(false);
        }
    };

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="w-full max-w-2xl px-4">
                <OracleActionCard
                    title={oracleProposal.title}
                    description={oracleProposal.description}
                    proposedData={oracleProposal.data}
                    onConfirm={handleConfirm}
                    onCancel={() => setOracleProposal(null)}
                    isSubmitting={isSubmitting}
                />
            </div>
        </div>
    );
}
