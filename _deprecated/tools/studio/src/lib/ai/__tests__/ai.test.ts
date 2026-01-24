/**
 * AI SDK Unit Tests
 * 
 * Tests for the Vercel AI SDK integration hooks.
 * Uses MSW to mock API responses.
 * 
 * @see src/lib/ai/useLLM.ts
 * @see src/lib/ai/useChat.ts
 */
import { describe, it, expect, beforeEach, vi } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useLLM } from '../useLLM';
import { useChat } from '../useChat';
import {
    detectProvider,
    isProviderAvailable,
    PROVIDER_CONFIGS
} from '../providers';

// Mock localStorage for API keys
const mockLocalStorage = {
    getItem: vi.fn(),
    setItem: vi.fn(),
    clear: vi.fn(),
    removeItem: vi.fn(),
    length: 0,
    key: vi.fn(),
};

Object.defineProperty(window, 'localStorage', {
    value: mockLocalStorage,
});

describe('AI Providers', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('PROVIDER_CONFIGS', () => {
        it('should have all 5 providers configured', () => {
            expect(Object.keys(PROVIDER_CONFIGS)).toHaveLength(5);
            expect(PROVIDER_CONFIGS).toHaveProperty('gemini');
            expect(PROVIDER_CONFIGS).toHaveProperty('openai');
            expect(PROVIDER_CONFIGS).toHaveProperty('anthropic');
            expect(PROVIDER_CONFIGS).toHaveProperty('groq');
            expect(PROVIDER_CONFIGS).toHaveProperty('ollama');
        });

        it('should have required fields for each provider', () => {
            Object.values(PROVIDER_CONFIGS).forEach(config => {
                expect(config).toHaveProperty('id');
                expect(config).toHaveProperty('name');
                expect(config).toHaveProperty('models');
                expect(config).toHaveProperty('defaultModel');
                expect(config).toHaveProperty('requiresApiKey');
                expect(config).toHaveProperty('isLocal');
            });
        });

        it('should have Ollama marked as local', () => {
            expect(PROVIDER_CONFIGS.ollama.isLocal).toBe(true);
            expect(PROVIDER_CONFIGS.ollama.requiresApiKey).toBe(false);
        });
    });

    describe('PROVIDER_CONFIGS access', () => {
        it('should return correct config for each provider', () => {
            expect(PROVIDER_CONFIGS.gemini.name).toBe('Google Gemini');
            expect(PROVIDER_CONFIGS.openai.name).toBe('OpenAI');
            expect(PROVIDER_CONFIGS.anthropic.name).toBe('Anthropic Claude');
        });
    });

    describe('detectProvider', () => {
        it('should detect OpenAI models', () => {
            expect(detectProvider('gpt-4o')).toBe('openai');
            expect(detectProvider('gpt-4o-mini')).toBe('openai');
            expect(detectProvider('gpt-3.5-turbo')).toBe('openai');
        });

        it('should detect Anthropic models', () => {
            expect(detectProvider('claude-3-opus')).toBe('anthropic');
            expect(detectProvider('claude-3-sonnet')).toBe('anthropic');
        });

        it('should detect Gemini models', () => {
            expect(detectProvider('gemini-2.5-flash')).toBe('gemini');
            expect(detectProvider('gemini-1.5-pro')).toBe('gemini');
        });

        it('should detect Groq models', () => {
            expect(detectProvider('llama-3.1-70b')).toBe('groq');
            expect(detectProvider('mixtral-8x7b')).toBe('groq');
        });

        it('should detect Ollama models', () => {
            expect(detectProvider('ollama:llama2')).toBe('ollama');
        });

        it('should default to Gemini for unknown models', () => {
            expect(detectProvider('unknown-model')).toBe('gemini');
        });
    });

    describe('isProviderAvailable', () => {
        it('should return false for cloud providers without API key', () => {
            mockLocalStorage.getItem.mockReturnValue(null);
            expect(isProviderAvailable('gemini')).toBe(false);
            expect(isProviderAvailable('openai')).toBe(false);
        });

        it('should return true for cloud providers with API key', () => {
            mockLocalStorage.getItem.mockReturnValue('test-api-key');
            expect(isProviderAvailable('gemini')).toBe(true);
            expect(isProviderAvailable('openai')).toBe(true);
        });

        // Note: Ollama availability depends on local server running
        // Skipping in unit tests as it requires network
    });
});

describe('useLLM Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockLocalStorage.getItem.mockReturnValue('test-api-key');
    });

    it('should initialize with default state', () => {
        const { result } = renderHook(() => useLLM());

        expect(result.current.isLoading).toBe(false);
        expect(result.current.error).toBeNull();
        expect(typeof result.current.generate).toBe('function');
        expect(typeof result.current.chat).toBe('function');
    });

    it('should have generate function that accepts options', () => {
        const { result } = renderHook(() => useLLM());

        // Just verify the function signature exists
        expect(result.current.generate).toBeDefined();
    });

    it('should have chat function that accepts messages', () => {
        const { result } = renderHook(() => useLLM());

        expect(result.current.chat).toBeDefined();
    });

    it('should expose clearError function', () => {
        const { result } = renderHook(() => useLLM());

        // The hook should allow clearing errors
        expect(typeof result.current.clearError).toBe('function');
    });
});

describe('useChat Hook', () => {
    beforeEach(() => {
        vi.clearAllMocks();
        mockLocalStorage.getItem.mockReturnValue('test-api-key');
    });

    it('should initialize with empty messages', () => {
        const { result } = renderHook(() => useChat());

        expect(result.current.messages).toEqual([]);
        expect(result.current.isLoading).toBe(false);
    });

    it('should have sendMessage function', () => {
        const { result } = renderHook(() => useChat());

        expect(typeof result.current.sendMessage).toBe('function');
    });

    it('should have clearHistory function', () => {
        const { result } = renderHook(() => useChat());

        expect(typeof result.current.clearHistory).toBe('function');
    });

    it('should allow setting initial messages', () => {
        const initialMessages = [
            { id: '1', role: 'user' as const, content: 'Hello', timestamp: new Date() },
            { id: '2', role: 'assistant' as const, content: 'Hi there!', timestamp: new Date() },
        ];

        const { result } = renderHook(() =>
            useChat({ initialMessages })
        );

        expect(result.current.messages).toHaveLength(2);
    });

    it('should clear messages when clearHistory is called', async () => {
        const initialMessages = [
            { id: '1', role: 'user' as const, content: 'Hello', timestamp: new Date() },
        ];

        const { result } = renderHook(() =>
            useChat({ initialMessages })
        );

        expect(result.current.messages).toHaveLength(1);

        act(() => {
            result.current.clearHistory();
        });

        expect(result.current.messages).toHaveLength(0);
    });
});

describe('Provider Integration', () => {
    it('should export all required functions from providers', async () => {
        const providers = await import('../providers');

        expect(providers.getProvider).toBeDefined();
        expect(providers.getModel).toBeDefined();
        expect(providers.detectProvider).toBeDefined();
        expect(providers.isProviderAvailable).toBeDefined();
        expect(providers.PROVIDER_CONFIGS).toBeDefined();
    });

    it('should export all required functions from useLLM', async () => {
        const llm = await import('../useLLM');

        expect(llm.useLLM).toBeDefined();
    });

    it('should export all required functions from useChat', async () => {
        const chat = await import('../useChat');

        expect(chat.useChat).toBeDefined();
    });
});
