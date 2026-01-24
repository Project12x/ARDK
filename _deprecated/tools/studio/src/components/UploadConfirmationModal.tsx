import { X, AlertTriangle, FileText, Archive } from 'lucide-react';
import { Button } from './ui/Button';

interface UploadConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: (isNewest: boolean) => void;
    fileName: string;
    detectedVersion?: string;
}

export function UploadConfirmationModal({ isOpen, onClose, onConfirm, fileName, detectedVersion }: UploadConfirmationModalProps) {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/80 backdrop-blur-sm">
            <div className="w-full max-w-md bg-black border border-accent rounded-lg shadow-2xl p-6 relative">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 text-gray-500 hover:text-white transition-colors"
                >
                    <X size={20} />
                </button>

                <div className="flex items-center gap-3 mb-6 text-accent">
                    <AlertTriangle size={24} />
                    <h2 className="text-xl font-bold font-mono uppercase tracking-wider">Version Control</h2>
                </div>

                <div className="space-y-4 mb-8">
                    <p className="text-gray-300">
                        You are uploading <span className="text-white font-mono font-bold bg-white/10 px-1">{fileName}</span>.
                    </p>
                    {detectedVersion && (
                        <p className="text-sm text-gray-400 font-mono border-l-2 border-gray-600 pl-3">
                            Detected Version: <span className="text-accent">{detectedVersion}</span>
                        </p>
                    )}
                    <p className="text-white font-bold text-lg">
                        Is this the <span className="text-accent underline decoration-wavy">newest version</span> of the project?
                    </p>
                </div>

                <div className="grid grid-cols-1 gap-3">
                    <Button
                        variant="primary"
                        onClick={() => onConfirm(true)}
                        className="w-full py-4 text-center justify-center text-black font-bold"
                    >
                        <FileText size={18} className="mr-2" />
                        YES - UPDATE PROJECT & PARSE DATA
                    </Button>
                    <p className="text-[10px] text-gray-500 text-center uppercase tracking-widest font-mono mb-2">
                        Updates Version, Status, Tasks, BOM, Logs
                    </p>

                    <Button
                        variant="outline"
                        onClick={() => onConfirm(false)}
                        className="w-full py-3 justify-center text-gray-400 hover:text-white border-gray-700"
                    >
                        <Archive size={18} className="mr-2" />
                        NO - JUST ARCHIVE FILE
                    </Button>
                </div>
            </div>
        </div>
    );
}
