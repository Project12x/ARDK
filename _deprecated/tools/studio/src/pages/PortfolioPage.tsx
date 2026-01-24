
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { db } from '../lib/db';
import { Button } from '../components/ui/Button';
import { Card } from '../components/ui/Card';
import { Upload, Download, RefreshCw } from 'lucide-react';
import { AIService } from '../lib/AIService';
import { PortfolioService } from '../lib/portfolio';
import { useNavigate } from 'react-router-dom';
import { useUIStore } from '../store/useStore';

export function PortfolioPage() {
    const navigate = useNavigate();
    const projects = useLiveQuery(() => db.projects.filter(p => !p.deleted_at).toArray());
    const { isIngesting } = useUIStore();


    // Stats
    const total = projects?.length || 0;
    const active = projects?.filter(p => p.status === 'active' || (p.status as any) === 'active (core build)').length || 0;
    const legacy = projects?.filter(p => p.status === 'legacy').length || 0;
    const rnd = projects?.filter(p => p.status === 'rnd_long').length || 0;

    const handleIngest = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        const { setIngesting } = useUIStore.getState();
        setIngesting(true, 'Parsing Master Index...');
        try {
            const text = await file.text(); // Assuming text file for Master Index
            const extracted = await AIService.parsePortfolio(text);

            const result = await PortfolioService.syncPortfolio(extracted);
            toast.success(`Portfolio Synced`, { description: `Created: ${result.created}, Updated: ${result.updated}, Errors: ${result.errors}` });

            // Save the log
            await db.logs.add({
                project_id: -1, // System log
                version: 'SYSTEM',
                date: new Date(),
                summary: `Portfolio Sync: ${result.updated} updated, ${result.created} new.`,
                type: 'auto'
            });

        } catch (err) {
            console.error(err);
            toast.error("Failed to ingest portfolio. See console.");
        } finally {
            setIngesting(false);
        }
    };

    const handleDownload = async () => {
        const text = await PortfolioService.generateMasterIndex();
        const blob = new Blob([text], { type: 'text/plain' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `Master Index v${new Date().toISOString().split('T')[0]}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
    };

    return (
        <div className="space-y-8 p-8 max-w-7xl mx-auto print:p-0 print:max-w-none">
            {/* Header / Actions - Hidden in Print */}
            <div className="flex justify-between items-end border-b border-white/10 pb-6 print:hidden">
                <div>
                    <h1 className="text-4xl font-black text-white uppercase tracking-tighter mb-2">Portfolio Manager</h1>
                    <p className="text-gray-400 font-mono text-sm max-w-md">
                        Master Index Management. Sync with text files or generate new reports.
                    </p>
                </div>
                <div className="flex gap-4">
                    <div className="relative">
                        <input
                            type="file"
                            accept=".txt,.md"
                            onChange={handleIngest}
                            className="absolute inset-0 opacity-0 cursor-pointer"
                            disabled={isIngesting}
                        />
                        <Button variant="outline" disabled={isIngesting}>
                            {isIngesting ? <RefreshCw className="animate-spin mr-2" /> : <Upload className="mr-2" size={16} />}
                            {isIngesting ? 'SYNCING...' : 'INGEST INDEX'}
                        </Button>
                    </div>

                    <Button variant="outline" onClick={handleDownload}>
                        <Download className="mr-2" size={16} /> DOWNLOAD
                    </Button>
                </div>
            </div>

            {/* Stats Cards - Hidden in Print */}
            <div className="grid grid-cols-4 gap-4 print:hidden">
                <Card className="bg-white/5 border-white/10 p-4">
                    <div className="text-3xl font-black text-white">{total}</div>
                    <div className="text-xs font-mono text-gray-500 uppercase">Total Projects</div>
                </Card>
                <Card className="bg-accent/10 border-accent/20 p-4">
                    <div className="text-3xl font-black text-accent">{active}</div>
                    <div className="text-xs font-mono text-accent/70 uppercase">Active</div>
                </Card>
                <Card className="bg-blue-900/10 border-blue-500/20 p-4">
                    <div className="text-3xl font-black text-blue-400">{legacy}</div>
                    <div className="text-xs font-mono text-blue-400/70 uppercase">Legacy</div>
                </Card>
                <Card className="bg-purple-900/10 border-purple-500/20 p-4">
                    <div className="text-3xl font-black text-purple-400">{rnd}</div>
                    <div className="text-xs font-mono text-purple-400/70 uppercase">R&D</div>
                </Card>
            </div>

            {/* Portfolio Matrix - Improved for Print */}
            <div className="space-y-6">
                <h2 className="text-xl font-bold text-white mb-4 uppercase tracking-wider print:text-black">Project Matrix</h2>

                <div className="grid grid-cols-1 gap-2">
                    {projects?.map(p => (
                        <div key={p.id} className="grid grid-cols-12 gap-4 items-center bg-black border border-white/10 p-3 hover:border-accent/50 transition-colors print:bg-white print:border-gray-300 print:text-black">
                            <div className="col-span-1 font-mono text-xs text-gray-500 print:text-gray-600">
                                {p.project_code || `P-${p.id}`}
                            </div>
                            <div className="col-span-4">
                                <h3
                                    className="font-bold text-white cursor-pointer hover:underline print:text-black cursor:pointer"
                                    onClick={() => navigate(`/projects/${p.id}`)}
                                >
                                    {p.title}
                                </h3>
                                {p.role && <p className="text-xs text-gray-400 font-mono truncate print:text-gray-600">{p.role}</p>}
                            </div>
                            <div className="col-span-2">
                                <span className={`text-[10px] font-bold uppercase px-2 py-0.5 rounded border border-white/10 ${p.status?.includes('active') ? 'bg-accent/10 text-accent border-accent/20' :
                                    p.status === 'legacy' ? 'bg-blue-900/20 text-blue-400 border-blue-500/20' :
                                        'bg-gray-800 text-gray-400'
                                    } print:border-black print:text-black print:bg-transparent`}>
                                    {p.status}
                                </span>
                            </div>
                            <div className="col-span-3 flex flex-wrap gap-1">
                                {p.tags?.slice(0, 3).map(tag => (
                                    <span key={tag} className="text-[9px] bg-white/5 border border-white/10 px-1 rounded text-gray-400 print:border-gray-400 print:text-black">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                            <div className="col-span-2 text-right">
                                <span className="text-[10px] font-mono text-gray-600 print:text-gray-400">
                                    {p.design_status || '-'} / {p.build_status || '-'}
                                </span>
                            </div>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
