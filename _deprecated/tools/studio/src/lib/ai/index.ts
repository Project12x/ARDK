/**
 * AI Module Index
 * 
 * @module lib/ai
 * @description
 * Central export for all AI-related functionality.
 * Uses Vercel AI SDK with multi-provider support.
 */

// Provider Configuration
export {
    type AIProviderType,
    type ProviderConfig,
    PROVIDER_CONFIGS,
    getProvider,
    getModel,
    detectProvider,
    isProviderAvailable,
    getAvailableProviders,
    createGeminiProvider,
    createOpenAIProvider,
    createAnthropicProvider,
    createGroqProvider,
    createOllamaProvider,
} from './providers';

// React Hooks
export { useLLM, generateLLMText, type LLMGenerateOptions, type LLMChatOptions } from './useLLM';
export { useChat, type ChatMessage, type UseChatOptions } from './useChat';
export { useCompletion, type UseCompletionOptions } from './useCompletion';

// Context Provider
export { AIProvider, useAIContext, useIsAIAvailable, type AIContextValue } from './AIProvider';
