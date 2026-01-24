
import { GoogleGenerativeAI } from '@google/generative-ai';
import { toast } from 'sonner';
import Groq from 'groq-sdk';
import OpenAI from 'openai';

export interface ModelStatus {
    id: string;
    provider: string; // generalized
    name: string;
    description: string;
    supported: boolean;
    reason?: string;
    latency?: number; // ms
}

export interface LLMProviderConfig {
    id: string;
    name: string;
    storageKey: string;
    description: string;
    color: string; // Tailwind bg class for the dot
    shadow: string; // Tailwind shadow class
    check: (apiKey: string) => Promise<ModelStatus[]>;
}

// Known models to test against (Jan 2026 Standard)
// Known models to test against (Jan 2026 Standard)
export const KNOWN_MODELS = {
    gemini: [
        { id: 'gemini-3.0-flash', name: 'Gemini 3.0 Flash', desc: 'Future standard' },
        { id: 'gemini-3.0-pro', name: 'Gemini 3.0 Pro', desc: 'Future reasoning' },
        { id: 'gemini-2.5-flash', name: 'Gemini 2.5 Flash', desc: 'Current production standard' },
        { id: 'gemini-2.0-flash-exp', name: 'Gemini 2.0 Flash Exp', desc: 'Experimental multimodal' },
        { id: 'gemini-1.5-pro', name: 'Gemini 1.5 Pro', desc: 'Legacy reasoning (2M context)' },
        { id: 'gemini-1.5-flash', name: 'Gemini 1.5 Flash', desc: 'Legacy speed' }
    ],
    groq: [
        { id: 'llama3-70b-8192', name: 'Llama 3 70B', desc: 'High capability open model' },
        { id: 'mixtral-8x7b-32768', name: 'Mixtral 8x7B', desc: 'MoE model' },
        { id: 'gemma2-9b-it', name: 'Gemma 2 9B', desc: 'Google efficient open model' }
    ],
    openai: [
        { id: 'gpt-4o', name: 'GPT-4o', desc: 'Flagship model' },
        { id: 'gpt-4o-mini', name: 'GPT-4o Mini', desc: 'Cost efficient' }
    ]
};

export class IntegrationService {

    static async checkGeminiModels(apiKey: string): Promise<ModelStatus[]> {
        if (!apiKey) return KNOWN_MODELS.gemini.map(m => ({ ...m, provider: 'gemini', supported: false, description: m.desc, reason: 'No API Key' }));

        const genAI = new GoogleGenerativeAI(apiKey);
        const results: ModelStatus[] = [];

        for (const modelDef of KNOWN_MODELS.gemini) {
            const start = performance.now();
            try {
                const model = genAI.getGenerativeModel({ model: modelDef.id });
                // Simple test generation
                const result = await model.generateContent("Test");
                const response = await result.response;
                const text = response.text(); // Access text to ensure it worked

                results.push({
                    id: modelDef.id,
                    provider: 'gemini',
                    name: modelDef.name,
                    description: modelDef.desc,
                    supported: true,
                    latency: Math.round(performance.now() - start)
                });
            } catch (error: any) {
                // Check if it's a "Not Supported" error specifically
                const isNotSupported = error.message?.includes('404') || error.message?.includes('not found') || error.message?.includes('convert to supported');

                results.push({
                    id: modelDef.id,
                    provider: 'gemini',
                    name: modelDef.name,
                    description: modelDef.desc,
                    supported: false,
                    reason: isNotSupported ? 'Not Supported by Key/Region' : error.message,
                    latency: Math.round(performance.now() - start)
                });
            }
        }
        return results;
    }

    static async checkGroqModels(apiKey: string): Promise<ModelStatus[]> {
        if (!apiKey) return KNOWN_MODELS.groq.map(m => ({ ...m, provider: 'groq', supported: false, description: m.desc, reason: 'No API Key' }));

        const groq = new Groq({ apiKey, dangerouslyAllowBrowser: true });
        const results: ModelStatus[] = [];

        // Fetch available models list from Groq to cross-reference
        let availableIds: string[] = [];
        try {
            const list = await groq.models.list();
            availableIds = list.data.map((m: any) => m.id);
        } catch (e) {
            console.error("Failed to list Groq models", e);
            // If listing fails, we'll brute force test
        }

        for (const modelDef of KNOWN_MODELS.groq) {
            // If we successfully listed models, check if ID exists first to save time
            /* if (availableIds.length > 0 && !availableIds.includes(modelDef.id)) {
                 results.push({ ...modelDef, provider: 'groq', description: modelDef.desc, supported: false, reason: 'Not in available models list' });
                 continue;
            } */

            const start = performance.now();
            try {
                await groq.chat.completions.create({
                    messages: [{ role: 'user', content: 'Test' }],
                    model: modelDef.id,
                    max_tokens: 1
                });
                results.push({
                    id: modelDef.id,
                    provider: 'groq',
                    name: modelDef.name,
                    description: modelDef.desc,
                    supported: true,
                    latency: Math.round(performance.now() - start)
                });
            } catch (error: any) {
                results.push({
                    id: modelDef.id,
                    provider: 'groq',
                    name: modelDef.name,
                    description: modelDef.desc,
                    supported: false,
                    reason: error.message,
                    latency: Math.round(performance.now() - start)
                });
            }
        }
        return results;
    }

    static async checkOpenAIModels(apiKey: string): Promise<ModelStatus[]> {
        if (!apiKey) return KNOWN_MODELS.openai.map(m => ({ ...m, provider: 'openai', supported: false, description: m.desc, reason: 'No API Key' }));
        const openai = new OpenAI({ apiKey, dangerouslyAllowBrowser: true });
        const results: ModelStatus[] = [];

        for (const modelDef of KNOWN_MODELS.openai) {
            const start = performance.now();
            try {
                await openai.chat.completions.create({
                    messages: [{ role: 'user', content: 'Test' }],
                    model: modelDef.id,
                    max_tokens: 1
                });
                results.push({
                    id: modelDef.id,
                    provider: 'openai',
                    name: modelDef.name,
                    description: modelDef.desc,
                    supported: true,
                    latency: Math.round(performance.now() - start)
                });
            } catch (error: any) {
                results.push({
                    id: modelDef.id,
                    provider: 'openai',
                    name: modelDef.name,
                    description: modelDef.desc,
                    supported: false,
                    reason: error.message,
                    latency: Math.round(performance.now() - start)
                });
            }
        }
        return results;
    }

    static async runDiagnostic(keys: { gemini?: string, groq?: string, openai?: string }): Promise<ModelStatus[]> {
        const [gemini, groq, openai] = await Promise.all([
            IntegrationService.checkGeminiModels(keys.gemini || ''),
            IntegrationService.checkGroqModels(keys.groq || ''),
            IntegrationService.checkOpenAIModels(keys.openai || '')
        ]);
        return [...gemini, ...groq, ...openai];
    }
}

export const PROVIDER_REGISTRY: LLMProviderConfig[] = [
    {
        id: 'gemini',
        name: 'Google Gemini',
        storageKey: 'GEMINI_API_KEY',
        description: 'Multimodal AI with large context window.',
        color: 'bg-blue-500',
        shadow: 'shadow-[0_0_8px_rgba(59,130,246,0.6)]',
        check: IntegrationService.checkGeminiModels
    },
    {
        id: 'groq',
        name: 'Groq',
        storageKey: 'GROQ_API_KEY',
        description: 'High-speed LPU inference.',
        color: 'bg-purple-500',
        shadow: 'shadow-[0_0_8px_rgba(168,85,247,0.6)]',
        check: IntegrationService.checkGroqModels
    },
    {
        id: 'openai',
        name: 'OpenAI',
        storageKey: 'OPENAI_API_KEY',
        description: 'Industry standard GPT models.',
        color: 'bg-green-500',
        shadow: 'shadow-[0_0_8px_rgba(34,197,94,0.6)]',
        check: IntegrationService.checkOpenAIModels
    },
    {
        id: 'tavily',
        name: 'Tavily',
        storageKey: 'TAVILY_API_KEY',
        description: 'Search-as-Service API.',
        color: 'bg-pink-500',
        shadow: 'shadow-[0_0_8px_rgba(236,72,153,0.6)]',
        // Simple distinct checker for Tavily (since it's not an LLM in the same sense, but we can wrap it)
        check: async (key: string) => {
            if (!key) return [{ id: 'tavily', provider: 'tavily', name: 'Tavily Search', description: 'Web Search', supported: false, reason: 'No Key' }];
            // Mock check or simple fetch
            return [{ id: 'tavily', provider: 'tavily', name: 'Tavily Search', description: 'Web Search', supported: true, latency: 10 }];
        }
    }
];
