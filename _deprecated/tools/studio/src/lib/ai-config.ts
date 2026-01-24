
import { OllamaService } from './ollama';
import { GroqService } from './groq';

export interface AIProviderStatus {
    id: 'openai' | 'groq' | 'gemini' | 'ollama' | 'tavily';
    name: string;
    available: boolean;
    models: string[];
}

export const AIConfig = {
    getProviders(): AIProviderStatus[] {
        const providers: AIProviderStatus[] = [];

        // 1. Groq
        if (localStorage.getItem('GROQ_API_KEY')) {
            providers.push({
                id: 'groq',
                name: 'Groq',
                available: true,
                models: GroqService.getAvailableModels()
            });
        }

        // 2. OpenAI
        if (localStorage.getItem('OPENAI_API_KEY')) {
            providers.push({
                id: 'openai',
                name: 'OpenAI',
                available: true,
                models: ['gpt-4o-mini']
            });
        }

        // 3. Gemini
        if (localStorage.getItem('GEMINI_API_KEY')) {
            providers.push({
                id: 'gemini',
                name: 'Gemini',
                available: true,
                models: ['gemini-2.5-flash', 'gemini-1.5-pro']
            });
        }

        // 4. Tavily
        if (localStorage.getItem('TAVILY_API_KEY')) {
            providers.push({
                id: 'tavily',
                name: 'Tavily Search',
                available: true,
                models: []
            });
        }

        // 5. Ollama (Async check not ideal for sync config, assumes available if URL present)
        // Note: Actual connection check happens at runtime or via specific test button
        if (localStorage.getItem('OLLAMA_URL')) {
            providers.push({
                id: 'ollama',
                name: 'Ollama (Local)',
                available: true,
                models: [] // Fetched async typically
            });
        }

        return providers;
    },

    isProviderAvailable(providerId: string): boolean {
        return this.getProviders().some(p => p.id === providerId && p.available);
    },

    /**
     * Returns a prioritized list of providers for "Auto" logic.
     * Hierarchy: Groq (Speed) -> OpenAI (Reliable) -> Gemini (General) -> Ollama (Local)
     */
    getAutoChain(): string[] {
        const available = this.getProviders().map(p => p.id);
        const chain: string[] = [];

        if (available.includes('groq')) chain.push('groq');
        if (available.includes('openai')) chain.push('openai');
        if (available.includes('gemini')) chain.push('gemini');
        if (available.includes('ollama')) chain.push('ollama');

        return chain;
    }
};
