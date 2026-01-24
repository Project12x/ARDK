import { useState } from 'react';
import { toast } from 'sonner';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Download, RotateCcw, X, Database } from 'lucide-react';
import { BackupService } from '../../lib/backup';

export function DataManagementModal({ onClose }: { onClose: () => void }) {
    const [isRestoring, setIsRestoring] = useState(false);

    return (
        <div className="fixed inset-0 bg-black/80 backdrop-blur-sm z-50 flex items-center justify-center p-4" onClick={onClose}>
            <div className="bg-neutral-900 border border-white/10 rounded-lg p-6 max-w-md w-full space-y-6 shadow-2xl" onClick={e => e.stopPropagation()}>
                <div className="flex justify-between items-center border-b border-white/10 pb-4">
                    <h2 className="text-xl font-black uppercase text-white flex items-center gap-2">
                        <Database size={24} className="text-accent" /> Data Management
                    </h2>
                    <Button variant="ghost" size="sm" onClick={onClose}><X size={20} /></Button>
                </div>

                <div className="space-y-4">
                    <div className="p-4 bg-white/5 rounded border border-white/10 space-y-2">
                        <h3 className="font-bold text-white flex items-center gap-2"><Download size={16} /> FULL BACKUP</h3>
                        <p className="text-xs text-gray-400">
                            Download a complete archive (.zip) of all projects, tasks, logs, and files (images, PDFs).
                            Safely store this file as a backup.
                        </p>
                        <Button className="w-full bg-accent text-white font-bold" onClick={() => { BackupService.exportArchive(); }}>
                            DOWNLOAD ARCHIVE
                        </Button>
                    </div>

                    <div className="p-4 bg-red-900/10 rounded border border-red-900/30 space-y-2">
                        <h3 className="font-bold text-red-400 flex items-center gap-2"><RotateCcw size={16} /> RESTORE FROM ARCHIVE</h3>
                        <p className="text-xs text-red-300/70">
                            WARNING: This will <strong>WIPE</strong> the current database and replace it with the contents of the archive.
                        </p>
                        <Button
                            className="w-full bg-red-900/50 hover:bg-red-900 text-red-100 border border-red-800"
                            onClick={() => {
                                const input = document.createElement('input');
                                input.type = 'file';
                                input.accept = '.zip';
                                input.onchange = async (e: any) => {
                                    if (e.target.files?.length) {
                                        if (confirm("ARE YOU SURE? This will overwrite all current data.")) {
                                            setIsRestoring(true);
                                            try {
                                                await BackupService.restoreArchive(e.target.files[0]);
                                                toast.success("Restore Complete! Reloading...");
                                                window.location.reload();
                                            } catch (err) {
                                                toast.error("Restore Failed: " + err);
                                            } finally {
                                                setIsRestoring(false);
                                            }
                                        }
                                    }
                                };
                                input.click();
                            }}
                        >
                            {isRestoring ? 'RESTORING...' : 'UPLOAD & RESTORE'}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
}
