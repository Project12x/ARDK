import { useState, useRef, useEffect } from 'react';
import { toast } from 'sonner';
import { Card } from '../ui/Card';
import { Button } from '../ui/Button';
import { Download, Upload, RefreshCw, AlertTriangle, Loader2, HardDrive, GitBranch, Database } from 'lucide-react';
import { clsx } from 'clsx';
import { BackupService } from '../../lib/backup';
import { StorageService } from '../../lib/storage';
import { VaultService } from '../../services/VaultService';
import { useNavigate } from 'react-router-dom';

export function GeneralSettings() {
    const navigate = useNavigate();
    const [isWorking, setIsWorking] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    const handleFactoryReset = async () => {
        if (!confirm("CRITICAL WARNING: This will WIPE ALL DATA.\\n\\nProjects, Files, and Settings will be permanently lost.\\n\\nAre you sure?")) return;
        if (!confirm("Double Check: There is no undo. Proceed with Factory Reset?")) return;

        setIsWorking(true);
        try {
            await BackupService.factoryReset();
            toast.success("System Reset Complete. Refreshing...");
            navigate('/');
            window.location.reload();
        } catch (e) {
            console.error(e);
            toast.error("Reset Failed.");
        } finally {
            setIsWorking(false);
        }
    };

    const handleExport = async () => {
        setIsWorking(true);
        try {
            await BackupService.exportToZip();
        } catch (e) {
            console.error(e);
            toast.error("Export Failed.");
        } finally {
            setIsWorking(false);
        }
    };



    const handleImport = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        if (!confirm("WARNING: Importing a backup will OVERWRITE/WIPE existing data.\\n\\nEnsure you have an export of your current state if needed.\\n\\nProceed?")) {
            e.target.value = ''; // Reset
            return;
        }

        setIsWorking(true);
        try {
            await BackupService.importFromZip(file);
            toast.success("Import Successful! Reloading...");
            window.location.reload();
        } catch (e) {
            console.error(e);
            toast.error("Import Failed: " + (e as Error).message);
        } finally {
            setIsWorking(false);
            if (fileInputRef.current) fileInputRef.current.value = '';
        }
    };

    const [vaultHandle, setVaultHandle] = useState<FileSystemDirectoryHandle | null>(null);

    // Load initial state
    useEffect(() => {
        StorageService.getVaultHandle().then(setVaultHandle);
    }, []);

    const handleInitVault = async () => {
        try {
            // @ts-expect-error - File System Access API is experimental
            const handle = await window.showDirectoryPicker();
            await StorageService.setVaultRoot(handle);
            setVaultHandle(handle);

            // Trigger Initial Sync using the FRESH handle from the picker
            // This bypasses any database round-trip lag or permission loss
            const count = await VaultService.syncAll(handle);

            toast.success(`Vault Initialized: ${handle.name}`, { description: `Synced ${count} projects to local folder.` });
        } catch (err) {
            console.error(err);
            toast.error("Vault Initialization Failed: " + (err as Error).message);
        }
    };

    const handleForceSync = async () => {
        if (!vaultHandle) return;
        setIsWorking(true);
        try {
            const count = await VaultService.syncAll(vaultHandle);
            toast.success("Sync Complete", { description: `${count} projects updated` });
        } catch (e) {
            console.error(e);
            toast.error("Sync Failed");
        } finally {
            setIsWorking(false);
        }
    }

    const handleGitCommit = async () => {
        setIsWorking(true);
        try {
            const sha = await VaultService.commit("Manual Snapshot by User");
            if (sha) {
                toast.success("Git Snapshot Created", { description: `Commit: ${sha.slice(0, 7)}` });
            } else {
                toast.error("Commit Failed (Check Console)");
            }
        } catch (e) {
            console.error(e);
            toast.error("Git Operation Failed");
        } finally {
            setIsWorking(false);
        }
    };

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <Card title="Data Management">
                <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <Button variant="outline" onClick={handleExport} disabled={isWorking}>
                            {isWorking ? <Loader2 className="animate-spin mr-2" size={16} /> : <Download size={16} className="mr-2" />}
                            Backup to ZIP
                        </Button>
                        <Button variant="outline" onClick={() => fileInputRef.current?.click()} disabled={isWorking}>
                            {isWorking ? <Loader2 className="animate-spin mr-2" size={16} /> : <Upload size={16} className="mr-2" />}
                            Restore from ZIP
                        </Button>
                        <input
                            type="file"
                            ref={fileInputRef}
                            onChange={handleImport}
                            accept=".zip"
                            className="hidden"
                        />
                    </div>

                    <div className="bg-white/5 p-4 rounded-lg border border-white/5 space-y-3">
                        <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                            <HardDrive size={14} /> Local Vault
                        </h4>
                        <Button variant="ghost" onClick={handleInitVault} className="w-full justify-between border border-white/10">
                            <span>{vaultHandle ? 'Vault Active' : 'Initialize Vault'}</span>
                            <span className={clsx("text-[10px] font-mono truncate max-w-[100px]", vaultHandle ? "text-green-400" : "text-gray-500")}>
                                {vaultHandle ? vaultHandle.name : 'Not Configured'}
                            </span>
                        </Button>
                        {vaultHandle && (
                            <Button variant="outline" onClick={handleForceSync} disabled={isWorking} className="w-full text-xs">
                                <RefreshCw className={clsx("mr-2 h-3 w-3", isWorking && "animate-spin")} /> Force Full Sync
                            </Button>
                        )}
                        <p className="text-[10px] text-gray-500">
                            * The Vault mirrors your database to a local folder. Your projects and data are saved as readable JSON files.
                        </p>
                    </div>

                    {vaultHandle && (
                        <div className="bg-white/5 p-4 rounded-lg border border-white/5 space-y-3">
                            <h4 className="text-xs font-bold text-gray-400 uppercase tracking-widest flex items-center gap-2">
                                <GitBranch size={14} /> Version Control
                            </h4>
                            <div className="flex gap-2">
                                <Button variant="outline" onClick={handleGitCommit} disabled={isWorking} className="w-full">
                                    {isWorking ? <Loader2 className="animate-spin mr-2" size={16} /> : <GitBranch size={16} className="mr-2" />}
                                    Create Tracepoint (Commit)
                                </Button>
                            </div>
                            <p className="text-[10px] text-gray-500">
                                * Creates a local git commit of your vault state. This allows for history tracking and rollbacks using external tools.
                            </p>
                        </div>
                    )}

                    <div className="border-t border-white/5 pt-6 space-y-4">
                        <h4 className="text-sm font-bold text-red-400 uppercase tracking-widest flex items-center gap-2">
                            <AlertTriangle size={14} /> Danger Zone
                        </h4>
                        <div className="flex gap-4">
                            <Button variant="danger" onClick={handleFactoryReset} disabled={isWorking} className="bg-red-950/50 border-red-900 hover:bg-red-900 w-full md:w-auto">
                                <RefreshCw className="mr-2" size={16} />
                                Factory Reset System
                            </Button>
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
}
