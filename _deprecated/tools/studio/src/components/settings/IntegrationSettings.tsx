import { useState, useEffect } from 'react';
import { Card } from '../ui/Card';
import { Input } from '../ui/Input';
import { Button } from '../ui/Button';
import { Save, Github, Cpu, Printer, CloudSun, Loader2, Network, GitBranch, Info, CheckCircle2, XCircle, AlertCircle } from 'lucide-react';
import { toast } from 'sonner';
import { GitHubService } from '../../lib/github';
import { PrinterService } from '../../lib/printer';
import { IntegrationService } from '../../lib/IntegrationService';

// Hover Tooltip Component for AI Status
import { createPortal } from 'react-dom';

function ModelStatusTooltip({ provider, apiKey }: { provider: 'gemini' | 'groq' | 'openai' | 'tavily', apiKey: string }) {
    const [status, setStatus] = useState<any[] | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [isHovered, setIsHovered] = useState(false);

    // Portal Positioning State
    const [coords, setCoords] = useState({ top: 0, left: 0 });
    const [triggerNode, setTriggerNode] = useState<HTMLDivElement | null>(null);

    const check = async () => {
        if (loading || status) return;
        setLoading(true);
        try {
            let res: any[] = [];
            if (provider === 'gemini') res = await IntegrationService.checkGeminiModels(apiKey);
            if (provider === 'groq') res = await IntegrationService.checkGroqModels(apiKey);
            if (provider === 'openai') res = await IntegrationService.checkOpenAIModels(apiKey);
            setStatus(res);
        } catch (e: any) {
            setError(e.message);
        }
        setLoading(false);
    };

    const handleEnter = () => {
        if (triggerNode) {
            const rect = triggerNode.getBoundingClientRect();
            // Default: Centered below
            const top = rect.bottom + 10;
            let left = rect.left + (rect.width / 2);

            // Simple Boundary Check (Viewport)
            const tooltipWidth = 256; // approximate w-64

            // If too far right, shift left
            if (left + (tooltipWidth / 2) > window.innerWidth - 20) {
                left = window.innerWidth - (tooltipWidth / 2) - 20;
            }
            // If too far left, shift right
            if (left - (tooltipWidth / 2) < 20) {
                left = (tooltipWidth / 2) + 20;
            }

            setCoords({ top, left });
            setIsHovered(true);
            check();
        }
    };

    const handleLeave = () => {
        setIsHovered(false);
    };

    return (
        <>
            <div
                ref={setTriggerNode}
                className="relative flex flex-col items-center gap-1 cursor-help"
                onMouseEnter={handleEnter}
                onMouseLeave={handleLeave}
            >
                <div className={`w-2 h-2 rounded-full transition-all ${apiKey ? getLightColor(provider) : 'bg-gray-700'}`} />
                <span className="text-[10px] uppercase font-bold text-gray-400">{provider}</span>
            </div>

            {isHovered && createPortal(
                <div
                    className="fixed z-[9999] w-64 bg-[#111] border border-white/20 rounded-xl shadow-2xl p-3 animate-in fade-in zoom-in-95 duration-200 pointer-events-none"
                    style={{
                        top: coords.top,
                        left: coords.left,
                        transform: 'translateX(-50%)'
                    }}
                >
                    <div className="text-xs font-bold uppercase text-gray-500 mb-2 border-b border-white/10 pb-1 flex justify-between">
                        {provider} Diagnostic
                        {loading && <Loader2 size={12} className="animate-spin text-accent" />}
                    </div>

                    {!apiKey && <div className="text-xs text-red-500">No API Key Configured</div>}

                    {status ? (
                        <div className="space-y-2 max-h-64 overflow-y-auto custom-scrollbar">
                            {status.map((model: any) => (
                                <div key={model.id} className="flex items-start justify-between gap-2 text-[10px]">
                                    <div>
                                        <div className={`font-bold ${model.supported ? 'text-white' : 'text-gray-500 line-through'}`}>
                                            {model.name}
                                        </div>
                                        <div className="text-gray-600 leading-tight">{model.description}</div>
                                    </div>
                                    <div className="shrink-0 text-right">
                                        {model.supported ? (
                                            <div className="text-green-500 flex items-center gap-1">
                                                <CheckCircle2 size={10} />
                                                <span>{model.latency}ms</span>
                                            </div>
                                        ) : (
                                            <div className="text-red-500 flex items-center gap-1" title={model.reason}>
                                                <XCircle size={10} />
                                                <span>Unavail</span>
                                            </div>
                                        )}
                                    </div>
                                </div>
                            ))}
                        </div>
                    ) : (
                        loading ? <div className="text-[10px] text-gray-500">Testing connectivity...</div> : <div className="text-[10px] text-red-400">{error}</div>
                    )}
                </div>,
                document.body
            )}
        </>
    );
}

const getLightColor = (provider: string) => {
    switch (provider) {
        case 'gemini': return 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.6)]';
        case 'groq': return 'bg-purple-500 shadow-[0_0_8px_rgba(168,85,247,0.6)]';
        case 'openai': return 'bg-green-500 shadow-[0_0_8px_rgba(34,197,94,0.6)]';
        case 'tavily': return 'bg-pink-500 shadow-[0_0_8px_rgba(236,72,153,0.6)]';
        default: return 'bg-gray-500';
    }
}

export function IntegrationSettings() {
    // --- State ---
    const [geminiKey, setGeminiKey] = useState(() => localStorage.getItem('GEMINI_API_KEY') || '');
    const [groqKey, setGroqKey] = useState(() => localStorage.getItem('GROQ_API_KEY') || '');
    const [openaiKey, setOpenaiKey] = useState(() => localStorage.getItem('OPENAI_API_KEY') || '');
    const [tavilyKey, setTavilyKey] = useState(() => localStorage.getItem('TAVILY_API_KEY') || '');
    const [githubToken, setGithubToken] = useState(() => localStorage.getItem('GITHUB_TOKEN') || '');
    const [githubRepo, setGithubRepo] = useState(() => localStorage.getItem('GITHUB_REPO') || '');
    const [gitBranch, setGitBranch] = useState(() => localStorage.getItem('GIT_BRANCH') || 'main');
    const [gitProxy, setGitProxy] = useState(() => localStorage.getItem('GIT_PROXY') || '');
    const [ollamaUrl, setOllamaUrl] = useState(() => localStorage.getItem('OLLAMA_URL') || 'http://localhost:11434');

    // Printer State
    const [printerIp, setPrinterIp] = useState(() => localStorage.getItem('PRINTER_IP') || '');
    const [printerApiKey, setPrinterApiKey] = useState(() => localStorage.getItem('PRINTER_API_KEY') || '');
    const [isTestingPrinter, setIsTestingPrinter] = useState(false);

    const [githubUser, setGithubUser] = useState<{ login: string, avatar_url: string } | null>(null);
    const [isSaving, setIsSaving] = useState(false);

    // Initial Load
    useEffect(() => {
        const load = async () => {
            const user = await GitHubService.getUser();
            if (user) setGithubUser(user);
        };
        load();
    }, []);

    const saveGemini = () => {
        localStorage.setItem('GEMINI_API_KEY', geminiKey);
        toast.success('Gemini API Key Saved');
    };

    const saveGroq = () => {
        localStorage.setItem('GROQ_API_KEY', groqKey);
        toast.success('Groq API Key Saved');
    };

    const saveOpenAI = () => {
        localStorage.setItem('OPENAI_API_KEY', openaiKey);
        toast.success('OpenAI API Key Saved');
    };

    const saveTavily = () => {
        localStorage.setItem('TAVILY_API_KEY', tavilyKey);
        toast.success('Tavily API Key Saved');
    };

    const saveOllama = () => {
        localStorage.setItem('OLLAMA_URL', ollamaUrl);
        toast.success('Ollama URL Saved');
    };

    const handleSaveGitHub = async () => {
        setIsSaving(true);
        if (!githubToken) {
            toast.error("Please enter a token");
            setIsSaving(false);
            return;
        }

        const user = await GitHubService.verifyToken(githubToken);
        if (user) {
            setGithubUser(user);
            toast.success(`Connected as ${user.login}`);
        } else {
            toast.error("Invalid GitHub Token");
        }
        setIsSaving(false);
    };

    const saveGitConfig = () => {
        localStorage.setItem('GITHUB_REPO', githubRepo);
        localStorage.setItem('GIT_BRANCH', gitBranch);
        localStorage.setItem('GIT_PROXY', gitProxy);
        toast.success('Git Configuration Saved');
    };

    const handleDisconnectGitHub = () => {
        GitHubService.logout();
        setGithubUser(null);
        setGithubToken('');
        toast.success("Disconnected from GitHub");
    };

    const handleSavePrinter = async () => {
        setIsTestingPrinter(true);
        if (!printerIp || !printerApiKey) {
            toast.error("IP and API Key required");
            setIsTestingPrinter(false);
            return;
        }

        const success = await PrinterService.testConnection(printerIp, printerApiKey);
        if (success) {
            localStorage.setItem('PRINTER_IP', printerIp);
            localStorage.setItem('PRINTER_API_KEY', printerApiKey);
            toast.success("Printer Connected & Saved");
        } else {
            toast.error("Connection Failed. Check IP/Key.");
        }
        setIsTestingPrinter(false);
    }

    return (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
            {/* AI Integrations */}
            <Card title="Artificial Intelligence">
                {/* Status Dashboard */}
                <div className="mb-6 p-4 bg-black/40 rounded-lg border border-white/10 grid grid-cols-2 md:grid-cols-4 gap-4">
                    <ModelStatusTooltip provider="gemini" apiKey={geminiKey} />
                    <ModelStatusTooltip provider="groq" apiKey={groqKey} />
                    <ModelStatusTooltip provider="openai" apiKey={openaiKey} />
                    <ModelStatusTooltip provider="tavily" apiKey={tavilyKey} />
                </div>

                <div className="space-y-6">
                    {/* Gemini */}
                    <div className="space-y-2">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Cpu size={16} className="text-blue-400" /> Google Gemini
                        </h4>
                        <div className="flex gap-2">
                            <Input
                                type="password"
                                placeholder="AIzaSy..."
                                value={geminiKey}
                                onChange={e => setGeminiKey(e.target.value)}
                                className="font-mono text-sm"
                            />
                            <Button onClick={saveGemini} size="sm"><Save size={16} /></Button>
                        </div>
                        <p className="text-xs text-gray-500">Required for Project Ingestion and Analysis.</p>
                    </div>

                    <div className="h-px bg-white/5" />

                    {/* Groq */}
                    <div className="space-y-2">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Cpu size={16} className="text-purple-400" /> Groq (Llama3 / Mixtral)
                        </h4>
                        <div className="flex gap-2">
                            <Input
                                type="password"
                                placeholder="gsk_..."
                                value={groqKey}
                                onChange={e => setGroqKey(e.target.value)}
                                className="font-mono text-sm"
                            />
                            <Button onClick={saveGroq} size="sm"><Save size={16} /></Button>
                        </div>
                        <p className="text-xs text-gray-500">Ultra-fast inference for chat and quick logic.</p>
                    </div>

                    <div className="h-px bg-white/5" />

                    {/* OpenAI */}
                    <div className="space-y-2">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Cpu size={16} className="text-green-400" /> OpenAI
                        </h4>
                        <div className="flex gap-2">
                            <Input
                                type="password"
                                placeholder="sk-..."
                                value={openaiKey}
                                onChange={e => setOpenaiKey(e.target.value)}
                                className="font-mono text-sm"
                            />
                            <Button onClick={saveOpenAI} size="sm"><Save size={16} /></Button>
                        </div>
                        <p className="text-xs text-gray-500">Access GPT-4o-mini and other OpenAI models.</p>
                    </div>

                    <div className="h-px bg-white/5" />

                    {/* Tavily */}
                    <div className="space-y-2">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Network size={16} className="text-pink-400" /> Tavily Search
                        </h4>
                        <div className="flex gap-2">
                            <Input
                                type="password"
                                placeholder="Tvly-..."
                                value={tavilyKey}
                                onChange={e => setTavilyKey(e.target.value)}
                                className="font-mono text-sm"
                            />
                            <Button onClick={saveTavily} size="sm"><Save size={16} /></Button>
                        </div>
                        <p className="text-xs text-gray-500">Enables Web Search capabilities for the Oracle.</p>
                    </div>

                    <div className="h-px bg-white/5" />

                    {/* Ollama */}
                    <div className="space-y-2">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Cpu size={16} className="text-orange-400" /> Ollama (Local AI)
                        </h4>
                        <div className="flex gap-2">
                            <Input
                                type="text"
                                placeholder="http://localhost:11434"
                                value={ollamaUrl}
                                onChange={e => setOllamaUrl(e.target.value)}
                                className="font-mono text-sm"
                            />
                            <Button onClick={saveOllama} size="sm"><Save size={16} /></Button>
                        </div>
                        <p className="text-xs text-gray-500">Use local LLMs for privacy. Requires Ollama running locally.</p>
                    </div>
                </div>
            </Card>

            {/* Version Control */}
            <Card title="Version Control">
                <div className="space-y-4">
                    <div className="flex items-center justify-between">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Github size={16} className="text-white" /> GitHub
                        </h4>
                        {githubUser && (
                            <div className="flex items-center gap-2 bg-green-500/10 border border-green-500/20 px-2 py-1 rounded-full">
                                <img src={githubUser.avatar_url} alt={githubUser.login} className="w-4 h-4 rounded-full" />
                                <span className="text-green-400 text-xs font-mono">{githubUser.login}</span>
                            </div>
                        )}
                    </div>

                    {!githubUser ? (
                        <div className="space-y-2">
                            <div className="flex gap-2">
                                <Input
                                    type="password"
                                    placeholder="ghp_..."
                                    value={githubToken}
                                    onChange={e => setGithubToken(e.target.value)}
                                    className="font-mono text-sm"
                                />
                                <Button onClick={handleSaveGitHub} size="sm" disabled={isSaving}>
                                    {isSaving ? <Loader2 className="animate-spin" size={16} /> : <Save size={16} />}
                                </Button>
                            </div>
                            <p className="text-xs text-gray-500">Personal Access Token (Classic). Scope: `repo`, `gist`.</p>
                        </div>
                    ) : (
                        <div className="flex items-center justify-between bg-white/5 p-3 rounded border border-white/10">
                            <span className="text-xs font-mono text-gray-400">Token Active & Valid</span>
                            <Button variant="danger" size="sm" onClick={handleDisconnectGitHub}>Disconnect</Button>
                        </div>
                    )}
                </div>

                <div className="h-px bg-white/5 my-4" />

                <div className="space-y-4">
                    <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                        <GitBranch size={16} className="text-white" /> Vault Configuration
                    </h4>
                    <div className="space-y-2">
                        <div>
                            <label className="text-[10px] uppercase font-bold text-gray-500">Repository</label>
                            <Input
                                placeholder="username/repo"
                                value={githubRepo}
                                onChange={e => setGithubRepo(e.target.value)}
                                className="font-mono text-sm"
                            />
                        </div>
                        <div className="grid grid-cols-2 gap-2">
                            <div>
                                <label className="text-[10px] uppercase font-bold text-gray-500">Branch</label>
                                <Input
                                    placeholder="main"
                                    value={gitBranch}
                                    onChange={e => setGitBranch(e.target.value)}
                                    className="font-mono text-sm"
                                />
                            </div>
                            <div>
                                <label className="text-[10px] uppercase font-bold text-gray-500">CORS Proxy (Optional)</label>
                                <Input
                                    placeholder="Default"
                                    value={gitProxy}
                                    onChange={e => setGitProxy(e.target.value)}
                                    className="font-mono text-sm"
                                />
                            </div>
                        </div>
                        <Button onClick={saveGitConfig} size="sm" className="w-full">
                            <Save size={14} className="mr-2" /> Save Config
                        </Button>
                    </div>
                </div>
            </Card>

            {/* Workshop */}
            <Card title="Workshop">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {/* 3D Printer */}
                    <div className="space-y-2 p-4 border border-white/10 rounded bg-white/5">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <Printer size={16} className="text-industrial" /> OctoPrint / Moonraker
                        </h4>
                        <div className="space-y-2 pt-2">
                            <Input
                                placeholder="192.168.1.xxx"
                                value={printerIp}
                                onChange={e => setPrinterIp(e.target.value)}
                                className="font-mono text-xs"
                                leftIcon={<Network size={12} className="text-gray-500" />}
                            />
                            <div className="flex gap-2">
                                <Input
                                    type="password"
                                    placeholder="API Key..."
                                    value={printerApiKey}
                                    onChange={e => setPrinterApiKey(e.target.value)}
                                    className="font-mono text-xs"
                                />
                                <Button onClick={handleSavePrinter} size="sm" disabled={isTestingPrinter}>
                                    {isTestingPrinter ? <Loader2 className="animate-spin" size={14} /> : <Save size={14} />}
                                </Button>
                            </div>
                        </div>
                        <p className="text-[10px] text-gray-500">Enable monitoring of print status and temperatures.</p>
                    </div>

                    {/* Weather (Placeholder / Skipped) */}
                    <div className="space-y-2 p-4 border border-white/5 rounded bg-white/5 opacity-50 grayscale cursor-not-allowed">
                        <h4 className="flex items-center gap-2 font-bold text-sm text-gray-300">
                            <CloudSun size={16} className="text-yellow-400" /> OpenWeather
                        </h4>
                        <div className="h-20 flex items-center justify-center text-[10px] text-gray-600 border border-white/5 border-dashed rounded">
                            Integration Skipped
                        </div>
                    </div>
                </div>
            </Card>
        </div>
    );
}
