/**
 * AI Provider Configurations (Vercel AI SDK)
 * 
 * @module lib/ai/providers
 * @description
 * Centralized configuration for all LLM providers using the Vercel AI SDK.
 * Each provider exports a configured instance ready for use with generateText, streamText, etc.
 * 
 * ## Supported Providers
 * - Google Gemini (default)
 * - OpenAI GPT-4
 * - Anthropic Claude
 * - Groq (fast inference)
 * - Ollama (local/offline)
 */
import { createGoogleGenerativeAI } from '@ai-sdk/google';
import { createOpenAI } from '@ai-sdk/openai';
import { createAnthropic } from '@ai-sdk/anthropic';
import { createGroq } from '@ai-sdk/groq';
import { createOllama } from 'ollama-ai-provider';

// ============================================================================
// Provider Types
// ============================================================================

export type AIProviderType = 'gemini' | 'openai' | 'anthropic' | 'groq' | 'ollama';

export interface ProviderConfig {
    id: AIProviderType;
    name: string;
    models: string[];
    defaultModel: string;
    requiresApiKey: boolean;
    isLocal: boolean;
}

// ============================================================================
// Provider Configuration Registry
// ============================================================================

export const PROVIDER_CONFIGS: Record<AIProviderType, ProviderConfig> = {
    gemini: {
        id: 'gemini',
        name: 'Google Gemini',
        models: ['gemini-2.5-flash', 'gemini-2.0-flash-exp', 'gemini-1.5-pro'],
        defaultModel: 'gemini-2.5-flash',
        requiresApiKey: true,
        isLocal: false,
    },
    openai: {
        id: 'openai',
        name: 'OpenAI',
        models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-3.5-turbo'],
        defaultModel: 'gpt-4o-mini',
        requiresApiKey: true,
        isLocal: false,
    },
    anthropic: {
        id: 'anthropic',
        name: 'Anthropic Claude',
        models: ['claude-3-5-sonnet-20241022', 'claude-3-haiku-20240307', 'claude-3-opus-20240229'],
        defaultModel: 'claude-3-5-sonnet-20241022',
        requiresApiKey: true,
        isLocal: false,
    },
    groq: {
        id: 'groq',
        name: 'Groq',
        models: ['llama-3.3-70b-versatile', 'mixtral-8x7b-32768', 'gemma2-9b-it'],
        defaultModel: 'llama-3.3-70b-versatile',
        requiresApiKey: true,
        isLocal: false,
    },
    ollama: {
        id: 'ollama',
        name: 'Ollama (Local)',
        models: ['llama3.2', 'mistral', 'phi3', 'codellama'],
        defaultModel: 'llama3.2',
        requiresApiKey: false,
        isLocal: true,
    },
};

// ============================================================================
// Provider Factory Functions
// ============================================================================

/**
 * Get API key from localStorage for a provider
 */
function getApiKey(provider: AIProviderType): string | undefined {
    // 1. Check LocalStorage (User overrides)
    const keyMap: Record<AIProviderType, string> = {
        gemini: 'GEMINI_API_KEY',
        openai: 'OPENAI_API_KEY',
        anthropic: 'ANTHROPIC_API_KEY',
        groq: 'GROQ_API_KEY',
        ollama: '', // No key needed
    };

    const keyName = keyMap[provider];
    if (!keyName) return undefined;

    const localKey = localStorage.getItem(keyName);
    if (localKey) return localKey;

    // 2. Check Environment Variables (Dev convenience)
    // Vite exposes env vars prefixed with VITE_ on import.meta.env
    const envMap: Record<AIProviderType, string> = {
        gemini: 'VITE_GEMINI_API_KEY',
        openai: 'VITE_OPENAI_API_KEY',
        anthropic: 'VITE_ANTHROPIC_API_KEY',
        groq: 'VITE_GROQ_API_KEY',
        ollama: '',
    };

    const envKey = envMap[provider];
    // @ts-ignore - import.meta.env is standard in Vite
    return import.meta.env[envKey] ?? undefined;
}

/**
 * Create a configured Gemini provider instance
 */
export function createGeminiProvider() {
    const apiKey = getApiKey('gemini');
    if (!apiKey) throw new Error('Gemini API key not configured');

    return createGoogleGenerativeAI({
        apiKey,
    });
}

/**
 * Create a configured OpenAI provider instance
 */
export function createOpenAIProvider() {
    const apiKey = getApiKey('openai');
    if (!apiKey) throw new Error('OpenAI API key not configured');

    return createOpenAI({
        apiKey,
    });
}

/**
 * Create a configured Anthropic provider instance
 */
export function createAnthropicProvider() {
    const apiKey = getApiKey('anthropic');
    if (!apiKey) throw new Error('Anthropic API key not configured');

    return createAnthropic({
        apiKey,
    });
}

/**
 * Create a configured Groq provider instance
 */
export function createGroqProvider() {
    const apiKey = getApiKey('groq');
    if (!apiKey) throw new Error('Groq API key not configured');

    return createGroq({
        apiKey,
    });
}

/**
 * Create a configured Ollama provider instance (local)
 */
export function createOllamaProvider(baseURL = 'http://localhost:11434/api') {
    return createOllama({
        baseURL,
    });
}

// ============================================================================
// Unified Provider Access
// ============================================================================

/**
 * Get a provider instance by type
 */
export function getProvider(type: AIProviderType) {
    switch (type) {
        case 'gemini':
            return createGeminiProvider();
        case 'openai':
            return createOpenAIProvider();
        case 'anthropic':
            return createAnthropicProvider();
        case 'groq':
            return createGroqProvider();
        case 'ollama':
            return createOllamaProvider();
        default:
            throw new Error(`Unknown provider: ${type}`);
    }
}

/**
 * Get a model from a provider by full model ID (e.g., 'gemini:gemini-2.5-flash')
 */
export function getModel(fullModelId: string) {
    const [providerPart, modelName] = fullModelId.includes(':')
        ? fullModelId.split(':')
        : ['gemini', fullModelId]; // Default to Gemini

    const provider = getProvider(providerPart as AIProviderType);
    return provider(modelName);
}

/**
 * Detect provider from model ID prefix
 */
export function detectProvider(modelId: string): AIProviderType {
    if (modelId.startsWith('gpt')) return 'openai';
    if (modelId.startsWith('claude')) return 'anthropic';
    if (modelId.startsWith('gemini')) return 'gemini';
    if (modelId.startsWith('llama') || modelId.startsWith('mixtral') || modelId.startsWith('gemma')) return 'groq';
    if (modelId.startsWith('ollama:')) return 'ollama';

    // Check if local model (might be Ollama)
    if (['mistral', 'phi', 'codellama', 'deepseek'].some(prefix => modelId.startsWith(prefix))) {
        return 'ollama';
    }

    return 'gemini'; // Default fallback
}

/**
 * Check if a provider is available (has API key or is local)
 */
export function isProviderAvailable(type: AIProviderType): boolean {
    const config = PROVIDER_CONFIGS[type];
    if (config.isLocal) return true; // Ollama doesn't need key

    return !!getApiKey(type);
}

/**
 * Get all available providers (those with API keys configured)
 */
export function getAvailableProviders(): AIProviderType[] {
    return Object.keys(PROVIDER_CONFIGS).filter(
        (type) => isProviderAvailable(type as AIProviderType)
    ) as AIProviderType[];
}
