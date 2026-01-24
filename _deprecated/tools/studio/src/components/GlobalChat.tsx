import { useState, useRef, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useLocation, matchPath } from 'react-router-dom';
import { toast } from 'sonner';
import { useAutoAnimate } from '@formkit/auto-animate/react';
import { AIService } from '../lib/AIService';
import { GeminiService } from '../lib/gemini';
import { PrinterService } from '../lib/printer';
import { InventoryIngestModal } from './InventoryIngestModal';
import { Send, Sparkles, X, Copy, Check, Paperclip, FileText, Mic, MicOff, Volume2, VolumeX } from 'lucide-react';
import { Button } from './ui/Button';
import { db } from '../lib/db';
import { TavilyService } from '../lib/tavily';
import { PromptBuilder } from '../lib/ai-types';
import { AIConfig } from '../lib/ai-config';
import { useCallback } from 'react';
import { ActionService } from '../lib/action-service';
import { useUIStore } from '../store/useStore';
import clsx from 'clsx';

export function GlobalChat({ isOpen, onClose }: { isOpen: boolean, onClose: () => void }) {
    const location = useLocation();
    // Check if we are inside a specific project
    const projectMatch = matchPath('/projects/:id', location.pathname);
    const activeProjectId = projectMatch ? Number(projectMatch.params.id) : null;

    const [messages, setMessages] = useState<Array<{ role: 'user' | 'assistant', content: string, action?: any }>>([
        { role: 'assistant', content: "I am the Workshop Oracle. I can help you organize inventory, plan projects, or query your data." }
    ]);
    const [input, setInput] = useState('');
    const [isTyping, setIsTyping] = useState(false);
    const [justCopied, setJustCopied] = useState(false);
    const scrollRef = useRef<HTMLDivElement | null>(null);

    // Model Management
    interface ModelOption { id: string; name: string; provider: 'groq' | 'gemini' | 'ollama' | 'openai' | 'auto'; }
    const [models, setModels] = useState<ModelOption[]>([{ id: 'auto', name: '✨ Auto (Best Available)', provider: 'auto' }]);
    const [selectedModelId, setSelectedModelId] = useState<string>("auto");

    // Instruction Sets
    const instructions = useLiveQuery(async () => {
        const all = await db.llm_instructions.toArray();
        return all.filter(i => i.is_active);
    }) || [];
    const [selectedInstructionId, setSelectedInstructionId] = useState<number | 'default'>('default');


    // Auto-animate for message list
    const [messagesAnimRef] = useAutoAnimate();

    // Fix Ref Loop
    const setRefs = useCallback((node: HTMLDivElement | null) => {
        scrollRef.current = node;
        messagesAnimRef(node);
    }, [messagesAnimRef]);

    // Handle Pending External Messages
    const { oraclePendingMessage, setOraclePendingMessage } = useUIStore();

    // Voice State
    const [isListening, setIsListening] = useState(false);
    const [isSpeaking, setIsSpeaking] = useState(false); // Toggle for TTS
    const recognitionRef = useRef<any>(null);

    // Initialize Speech Recognition
    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            recognitionRef.current.continuous = false;
            recognitionRef.current.interimResults = true;

            recognitionRef.current.onresult = (event: any) => {
                const transcript = Array.from(event.results)
                    .map((result: any) => result[0].transcript)
                    .join('');
                // Append or replace? Let's replace for now or handle interim
                setInput(transcript);
            };

            recognitionRef.current.onend = () => {
                setIsListening(false);
            };

            recognitionRef.current.onerror = (event: any) => {
                console.warn("Speech Error", event.error);
                setIsListening(false);
            };
        }
    }, []);

    const toggleListening = () => {
        if (!recognitionRef.current) {
            toast.error("Voice input not supported in this browser.");
            return;
        }
        if (isListening) {
            recognitionRef.current.stop();
        } else {
            recognitionRef.current.start();
            setIsListening(true);
        }
    };

    const speak = (text: string) => {
        if (!isSpeaking) return;
        const utterance = new SpeechSynthesisUtterance(text);
        // Stripping markdown/HTML is hard, but we can try simple regex
        utterance.text = text.replace(/<[^>]*>/g, '').replace(/```[\s\S]*?```/g, 'Code block omitted.');
        window.speechSynthesis.speak(utterance);
    };

    useEffect(() => {
        if (oraclePendingMessage) {
            setInput(oraclePendingMessage);
            // Small timeout to allow state to settle or auto-send
            setTimeout(() => {
                // Trigger handleSend logic? 
                // We can't easily call handleSend unless we break it out or simulate it.
                // Actually, handleSend depends on 'input' state, but we just set it.
                // React might not have updated 'input' yet in the closure.
                // Better to set input and let user press Enter? 
                // OR refactor handleSend to take an argument.
            }, 100);

            // Actually, let's just pre-fill it for them to confirm.
            // User: "General actions... called from such as /?"
            // It's safer to let them review before sending 'Drop all database tables'.
            setOraclePendingMessage(null);
        }
    }, [oraclePendingMessage, setOraclePendingMessage]);

    // Load Models on Mount
    useEffect(() => {
        const loadModels = async () => {
            const newModels: ModelOption[] = [{ id: 'auto', name: '✨ Auto (Best Available)', provider: 'auto' }];
            const providers = AIConfig.getProviders();

            for (const p of providers) {
                if (p.id === 'groq') p.models.forEach(m => newModels.push({ id: m, name: `⚡ Groq: ${m}`, provider: 'groq' }));
                if (p.id === 'openai') newModels.push({ id: 'gpt-4o-mini', name: '🧠 OpenAI: GPT-4o Mini', provider: 'openai' });
                if (p.id === 'gemini') {
                    // Check for cached validation
                    let validModels = JSON.parse(localStorage.getItem('GEMINI_VALID_MODELS') || '[]');

                    // If no cache, validate now
                    if (validModels.length === 0) {
                        try {
                            const validation = await GeminiService.validateAvailableModels();
                            validModels = Object.keys(validation).filter(k => validation[k]);
                            localStorage.setItem('GEMINI_VALID_MODELS', JSON.stringify(validModels));
                        } catch {
                            console.warn("Failed to validate Gemini models, using defaults.");
                            validModels = ['gemini-1.5-flash']; // Safe default
                        }
                    }

                    // Map specific friendly names if desired, or just use ID
                    validModels.forEach((m: string) => {
                        newModels.push({ id: m, name: `✨ ${m}`, provider: 'gemini' });
                    });
                }
            }

            // 4. Check Ollama (Keep async for now to fetch tags)
            if (localStorage.getItem('OLLAMA_URL')) {
                const localModels = await AIService.getOllamaModels();
                localModels.forEach(m => newModels.push({ id: m, name: `🦙 Ollama: ${m}`, provider: 'ollama' }));
            }

            setModels(newModels);
        };
        loadModels();
    }, [isOpen]); // Refresh when opened

    // Inventory Action State
    const [inventoryDraft, setInventoryDraft] = useState<any[] | null>(null);

    // File Attachment State
    const [attachedFile, setAttachedFile] = useState<File | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);


    const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (file) {
            setAttachedFile(file);
        }
        e.target.value = ''; // Reset for re-selection
    };

    useEffect(() => {
        if (scrollRef.current) scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }, [messages]);

    const handleCopyContext = async () => {
        if (!activeProjectId) return;

        try {
            const project = await db.projects.get(activeProjectId);
            if (!project) return;

            const tasks = await db.project_tasks.where({ project_id: activeProjectId }).toArray();
            // Optional: Fetch related inventory/bom if needed

            const contextString = `
# PROJECT CONTEXT: ${project.title}
**Status**: ${project.status} | **Priority**: ${project.priority}/5
**Description**: ${project.status_description || 'N/A'}

## TASKS
${tasks.map(t => `- [${t.status}] ${t.title}`).join('\n')}

## FULL JSON DATA
\`\`\`json
${JSON.stringify({ project, tasks }, null, 2)}
\`\`\`

*System Prompt: Use this context to answer questions about the project.*
            `.trim();

            await navigator.clipboard.writeText(contextString);
            setJustCopied(true);
            setTimeout(() => setJustCopied(false), 2000);

            setMessages(prev => [...prev, { role: 'assistant', content: "Project context copied to clipboard! You can now paste this into ChatGPT or Claude." }]);
        } catch (e) {
            console.error("Failed to copy context", e);
        }
    };

    const handleSend = async () => {
        if (!input.trim()) return;
        const userMsg = input;
        setInput('');
        setMessages(prev => [...prev, { role: 'user', content: userMsg }]);
        setIsTyping(true);

        try {
            // 1. Gather Context
            const activeProjects = await db.projects.where('status').equals('active').toArray();
            const recentLogs = await db.logs.orderBy('date').reverse().limit(5).toArray();

            // Fetch Universal Data (Goals & Routines)
            const goals = await db.goals.where('status').notEqual('completed').toArray();
            const routines = await db.routines.toArray();

            // Fetch Music Data
            const songs = await db.songs.toArray();
            const albums = await db.albums.toArray();

            let printerStatus = undefined;

            // Check if printer is configured
            const printerIp = localStorage.getItem('PRINTER_IP');
            const printerApiKey = localStorage.getItem('PRINTER_API_KEY');
            if (printerIp && printerApiKey) {
                try {
                    // Only fetch if configured to avoid hanging
                    printerStatus = await PrinterService.getStatus({ ip: printerIp, apiKey: printerApiKey });
                } catch (e) {
                    console.warn("Oracle failed to sense printer", e);
                }
            }

            const inventoryCount = await db.inventory.count();

            // 2. Prepare Project Context
            let currentProjectContext = undefined;
            if (activeProjectId) {
                const p = await db.projects.get(activeProjectId);
                const t = await db.project_tasks.where({ project_id: activeProjectId }).toArray();
                const d = await db.project_documents.where({ project_id: activeProjectId }).toArray();
                const pi = await db.project_production_items.where({ project_id: activeProjectId }).toArray();

                if (p) {
                    let linkedAsset = undefined;
                    if (p.linked_asset_id) {
                        linkedAsset = await db.assets.get(p.linked_asset_id);
                    }
                    currentProjectContext = {
                        id: p.id!,
                        title: p.title,
                        status: p.status,
                        tasks: t.map(task => ({ id: task.id, title: task.title, status: task.status })),
                        documents: d.map(doc => ({ title: doc.title, type: doc.type })),
                        productionItems: pi.map(item => ({ name: item.name, type: item.type, status: item.status })),
                        linkedAsset
                    };
                }
            }

            // 2.1 Prepare Active Goal Context
            const { activeGoalId } = useUIStore.getState();
            let goalContextStr = "";
            if (activeGoalId) {
                const g = await db.goals.get(activeGoalId);
                const childGoals = await db.goals.where('parent_id').equals(activeGoalId).toArray();
                const goalTasks = await db.project_tasks.where('goal_id').equals(activeGoalId).toArray();

                if (g) {
                    goalContextStr = `
### 🎯 ACTIVE STRATEGY SESSION: GOAL CONTEXT
**Goal**: "${g.title}"
**Level**: ${g.level} | **Status**: ${g.status} | **Progress**: ${g.progress}%
**Motivation (WHY)**: ${g.motivation || 'Not defined'}
**Success Criteria (KPIs)**:
${(g.success_criteria || []).map(k => `- ${k}`).join('\n') || '- None'}

**Description**: ${g.description || ''}

**Sub-Goals**:
${childGoals.map(c => `- ${c.title} (${c.progress}%)`).join('\n')}

**Active Tasks**:
${goalTasks.map(t => `- [${t.status}] ${t.title}`).join('\n')}

INSTRUCTIONS: You are acting as a Strategic Advisor for this specific goal. Help the user refine the "Why", suggestion KPIs, and break down the execution plan.
`;
                }
            }

            // 2.5 Web Search (Tavily)
            let searchContext = "";
            const searchKeywords = ['search', 'find', 'price', 'cost', 'datasheet', 'lookup', 'where to buy', 'stock', 'google', 'browse', 'web', 'internet'];
            // Check if user explicitly wants web search OR if query implies it
            if (localStorage.getItem('TAVILY_API_KEY') && searchKeywords.some(k => userMsg.toLowerCase().includes(k))) {
                try {
                    setMessages(prev => [...prev, { role: 'assistant', content: "🔍 Searching the web..." }]);
                    const results = await TavilyService.search(userMsg);
                    if (results.length > 0) {
                        searchContext = `\n\nWEB SEARCH RESULTS:\n${results.map(r => `- ${r.content} (${r.url})`).join('\n')}\n`;
                    }
                } catch (e) {
                    console.warn("Tavily Search Failed", e);
                }
            }

            const baseSystemPrompt = PromptBuilder.buildSystemPrompt({
                activeProjects: activeProjects.map(p => ({ title: p.title, status: p.status, id: p.id })),
                recentLogs: recentLogs.map(l => ({ summary: l.summary, date: l.date })),
                printerStatus,
                inventoryMetrics: { count: inventoryCount },
                pageContext: location.pathname,
                currentProject: currentProjectContext,
                ancillaryData: {
                    goals: goals.map(g => ({ title: g.title, status: g.status, horizon: g.level })),
                    routines: routines.map(r => ({ title: r.title, frequency: r.frequency, next: r.next_due }))
                }
            });

            // INJECT CUSTOM INSTRUCTION SET
            let customInstructions = "";
            if (selectedInstructionId !== 'default') {
                const instr = await db.llm_instructions.get(selectedInstructionId as number);
                if (instr) {
                    customInstructions = `
\n=== USER OVERRIDE: ${instr.name} (${instr.category}) ===
${instr.content}
===========================================\n
`;
                }
            }

            const systemPrompt = baseSystemPrompt + customInstructions + goalContextStr + searchContext;



            // CHECK FOR COMMANDS
            if (userMsg.trim() === '/test-models') {
                setMessages(prev => [...prev, { role: 'assistant', content: "🧪 Running Diagnostic on all AI Providers..." }]);

                // Fetch Keys
                const keys = {
                    gemini: localStorage.getItem('GEMINI_API_KEY') || undefined,
                    groq: localStorage.getItem('GROQ_API_KEY') || undefined,
                    openai: localStorage.getItem('OPENAI_API_KEY') || undefined
                };

                // Lazy load IntegrationService if not already imported (it's not imported in GlobalChat yet)
                const { IntegrationService } = await import('../lib/IntegrationService');
                const results = await IntegrationService.runDiagnostic(keys);

                const tables = results.map(r =>
                    `| ${r.provider.toUpperCase()} | ${r.name} | ${r.supported ? '✅ Supported' : '❌ Failed'} | ${r.latency}ms |`
                ).join('\n');

                const report = `
**AI Diagnostic Results**
| Provider | Model | Status | Latency |
|----------|-------|--------|---------|
${tables}

*Total Models Tested: ${results.length}*
                `.trim();

                setMessages(prev => [...prev, { role: 'assistant', content: report }]);
                setIsTyping(false);
                return;
            }

            // 4. Execute Chat with Routing & Fallback
            let responseStr: string = "";

            try {
                // Prepare Options
                const options = {
                    modelId: selectedModelId === 'auto' ? 'auto' : selectedModelId,
                    image: attachedFile || undefined,
                    jsonMode: false // Default to text unless specific action needs JSON
                };

                // Append search context to message if present
                const effectiveMsg = searchContext ? (userMsg + "\n\nCONTEXT FROM WEB SEARCH:" + searchContext) : userMsg;

                // Execute via Unified Service
                responseStr = await AIService.chat(effectiveMsg, {
                    activeProjects: activeProjects.map(p => ({ title: p.title, status: p.status, id: p.id })),
                    recentLogs: recentLogs.map(l => ({ summary: l.summary, date: l.date })),
                    printerStatus,
                    inventoryMetrics: { count: inventoryCount },
                    pageContext: location.pathname,
                    currentProject: currentProjectContext,
                    songs: songs.map(s => ({ title: s.title, status: s.status, albumId: s.album_id })),
                    albums: albums.map(a => ({ title: a.title, status: a.status })),
                    ancillaryData: {
                        goals: goals.map(g => ({ title: g.title, status: g.status, horizon: g.level })),
                        routines: routines.map(r => ({ title: r.title, frequency: r.frequency, next: r.next_due }))
                    },
                    // Pass custom instructions content directly as override context if needed, 
                    // or rely on AIService to handle it if we passed the ID. 
                    // Current AIService design takes `SystemContext` object.
                    // We'll append the custom instruction to the system prompt in AIService or here.
                    // Actually, AIService builder handles `SystemContext`. 
                    // Let's pass the raw additional context here if `AIService` doesn't support custom overrides in `SystemContext` yet.
                    // We'll prepend the custom instructions to the message or context.
                }, options);

            } catch (e: any) {
                console.error("AI Service Error:", e);
                toast.error("AI Response Failed: " + e.message);
                throw e;
            }

            // Clear attached file after send
            setAttachedFile(null);
            let data: any = {};
            let finalMessage = responseStr;

            // 1. Try generic JSON parse first (if pure JSON)
            try {
                data = JSON.parse(responseStr);
                finalMessage = data.message || "Processed.";
            } catch {
                // 2. Try extracting from Markdown Code Block
                const jsonMatch = responseStr.match(/```json\n([\s\S]*?)\n```/);
                if (jsonMatch && jsonMatch[1]) {
                    try {
                        data = JSON.parse(jsonMatch[1]);
                        // Strip the code block from the displayed message
                        finalMessage = responseStr.replace(jsonMatch[0], '').trim();
                        // If message became empty/whitespace (AI only output JSON), restore a default or check if JSON has a message
                        if (!finalMessage) finalMessage = data.message || "Action Ready for Review.";
                    } catch (e) {
                        console.warn("Extracted JSON failed to parse", e);
                        data = { message: responseStr };
                    }
                } else {
                    // No JSON block found, treat as pure text
                    data = { message: responseStr };
                }
            }

            // Auto-Linkify text response
            try {
                const { NeurolinkService } = await import('../lib/neurolinks');
                finalMessage = await NeurolinkService.processLLMOutput(finalMessage);
            } catch (err) {
                console.warn("Failed to linkify:", err);
            }

            setMessages(prev => [...prev, {
                role: 'assistant',
                content: finalMessage,
                action: data.intent ? data : undefined
            }]);

            // Speak response if enabled
            speak(finalMessage);

            // Universal Action Handling
            if (data.intent) {
                // Convert Oracle JSON -> Action Service Proposal
                const proposal = ActionService.prepareProposal(data, { projectId: activeProjectId || undefined });
                if (proposal) {
                    useUIStore.getState().setOracleProposal({
                        ...proposal,
                        onConfirm: proposal.handler
                    } as any);
                }
            }

        } catch (e) {
            console.error("Oracle Error:", e);
            setMessages(prev => [...prev, { role: 'assistant', content: "My connection is hazy. Try again." }]);
        } finally {
            setIsTyping(false);
        }
    };

    if (!isOpen) return null;

    return (
        <>
            <div className="fixed bottom-4 right-4 w-[400px] h-[600px] bg-navy/90 backdrop-blur-xl border border-neon/30 rounded-xl shadow-[0_0_30px_rgba(255,68,153,0.1)] z-50 flex flex-col animate-in slide-in-from-bottom-10 fade-in duration-300">
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex justify-between items-center bg-neon/10 rounded-t-xl relative overflow-hidden">
                    <div className="absolute inset-0 bg-gradient-to-r from-neon/20 to-transparent opacity-50" />
                    <div className="flex items-center gap-2 relative z-10">
                        <Sparkles size={18} className="text-neon" />
                        <span className="font-bold text-white tracking-wider drop-shadow-md">ORACLE</span>
                    </div>
                    <div className="flex items-center gap-1 relative z-10">
                        {activeProjectId && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleCopyContext}
                                title="Copy Project Context for GPT/Claude"
                                className={clsx("hover:bg-white/10", justCopied && "text-green-400")}
                            >
                                {justCopied ? <Check size={16} /> : <Copy size={16} />}
                            </Button>
                        )}
                        <Button variant="ghost" size="sm" onClick={onClose} className="hover:text-neon hover:bg-neon/10"><X size={16} /></Button>
                    </div>
                </div>

                {/* Messages */}
                <div className="flex-1 overflow-y-auto p-4 space-y-4" ref={setRefs}>
                    {messages.map((m, i) => (
                        <div key={i} className={clsx("flex flex-col max-w-[85%]", m.role === 'user' ? "self-end items-end" : "self-start items-start")}>
                            <div className={clsx("p-3 rounded-lg text-sm shadow-md",
                                m.role === 'user' ? "bg-white/10 text-white border border-white/5" : "bg-black/40 text-neon-50 border border-neon/20 backdrop-blur-md"
                            )}>
                                {m.role === 'assistant' ? (
                                    <div
                                        className="prose prose-invert prose-sm max-w-none [&_span[data-type=mention]]:align-baseline"
                                        dangerouslySetInnerHTML={{ __html: m.content.replace(/\n/g, '<br/>') }}
                                    />
                                ) : (
                                    m.content
                                )}
                            </div>
                            {/* Action Feedback in Chat */}
                            {m.action && (
                                <div className="mt-1 text-[10px] text-gray-500 flex items-center gap-1">
                                    <Sparkles size={10} />
                                    <span>Proposed Action: {m.action.intent} (See Overlay)</span>
                                </div>
                            )}
                        </div>
                    ))}
                    {isTyping && <div className="text-xs text-neon/50 italic p-2 animate-pulse">Thinking...</div>}
                </div>

                {/* Input */}
                <div className="p-4 border-t border-white/10 bg-black/20 backdrop-blur-sm rounded-b-xl">
                    {/* File Preview */}
                    {attachedFile && (
                        <div className="mb-2 flex items-center gap-2 bg-black/40 p-2 rounded border border-neon/30">
                            {attachedFile.type.startsWith('image/') ? (
                                <img src={URL.createObjectURL(attachedFile)} alt="Preview" className="w-12 h-12 object-cover rounded" />
                            ) : (
                                <div className="w-12 h-12 bg-white/10 rounded flex items-center justify-center text-neon">
                                    <FileText size={24} />
                                </div>
                            )}
                            <div className="flex flex-col flex-1 overflow-hidden">
                                <span className="text-xs text-gray-300 truncate font-bold">{attachedFile.name}</span>
                                <span className="text-[10px] text-gray-500 uppercase">{attachedFile.type.split('/')[1] || 'FILE'}</span>
                            </div>
                            <button onClick={() => setAttachedFile(null)} className="text-red-400 hover:text-red-300"><X size={14} /></button>
                        </div>
                    )}
                    <div className="flex gap-2">
                        <input
                            type="file"
                            accept="image/*,application/pdf,text/plain,text/csv,application/json"
                            ref={fileInputRef}
                            onChange={handleFileSelect}
                            className="hidden"
                        />
                        <div className="flex flex-col gap-1 w-full">
                            {/* Model Selector */}
                            {!attachedFile && (
                                <select
                                    value={selectedModelId}
                                    onChange={e => setSelectedModelId(e.target.value)}
                                    className="bg-black/40 text-[10px] text-gray-400 border border-white/5 rounded px-2 py-0.5 outline-none mb-1 w-fit hover:text-white max-w-[200px] truncate"
                                >
                                    {models.map(m => (
                                        <option key={m.id} value={m.id}>{m.name}</option>
                                    ))}
                                </select>
                            )}

                            {/* Instruction Selector */}
                            <select
                                value={selectedInstructionId}
                                onChange={e => setSelectedInstructionId(e.target.value === 'default' ? 'default' : Number(e.target.value))}
                                className="bg-black/40 text-[10px] text-accent border border-accent/20 rounded px-2 py-0.5 outline-none mb-1 w-fit hover:border-accent max-w-[200px] truncate"
                            >
                                <option value="default">Default Oracle Persona</option>
                                {instructions?.map(i => (
                                    <option key={i.id} value={i.id}>{i.name}</option>
                                ))}
                            </select>
                            <div className="flex gap-2">
                                <Button
                                    variant="ghost"
                                    onClick={() => fileInputRef.current?.click()}
                                    className={clsx("bg-white/5 hover:bg-neon/20", attachedFile && "text-neon")}
                                    title="Attach File (Image or PDF)"
                                >
                                    <Paperclip size={16} />
                                </Button>
                                <input
                                    className="flex-1 bg-black/50 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-neon outline-none transition-colors placeholder:text-gray-600"
                                    placeholder={attachedFile ? `Ask about this ${attachedFile.type.startsWith('image') ? 'image' : 'file'}...` : "Ask or Command..."}
                                    value={input}
                                    onChange={e => setInput(e.target.value)}
                                    onKeyDown={e => e.key === 'Enter' && handleSend()}
                                />
                                <Button
                                    variant="ghost"
                                    onClick={toggleListening}
                                    className={clsx(
                                        "transition-all duration-300",
                                        isListening ? "bg-red-500/20 text-red-500 animate-pulse border-red-500/50" : "bg-white/5 hover:bg-neon/20 hover:text-neon"
                                    )}
                                    title="Voice Input"
                                >
                                    {isListening ? <MicOff size={16} /> : <Mic size={16} />}
                                </Button>
                                <Button
                                    variant="ghost"
                                    onClick={() => setIsSpeaking(!isSpeaking)}
                                    className={clsx(
                                        "transition-all",
                                        isSpeaking ? "text-neon bg-neon/10" : "text-gray-500 hover:text-gray-300"
                                    )}
                                    title="Text-to-Speech Output"
                                >
                                    {isSpeaking ? <Volume2 size={16} /> : <VolumeX size={16} />}
                                </Button>
                                <Button onClick={handleSend} disabled={isTyping} variant="ghost" className="bg-white/5 hover:bg-neon hover:text-black hover:shadow-[0_0_10px_rgba(255,68,153,0.4)] transition-all"><Send size={16} /></Button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Inventory Ingest Modal: Kept for specific manual ingest if needed, 
                but ideally ActionService handles it or we map it to generic proposal */}
            <InventoryIngestModal
                isOpen={!!inventoryDraft}
                onClose={() => setInventoryDraft(null)}
                initialData={inventoryDraft || []}
            />
        </>
    );
}
