/**
 * useLLM Hook - Unified LLM Interface
 * 
 * @module lib/ai/useLLM
 * @description
 * React hook for LLM operations using the Vercel AI SDK.
 * Provides a unified interface for all providers with streaming support.
 * 
 * @example
 * ```typescript
 * const { generate, isLoading, error } = useLLM();
 * 
 * const response = await generate({
 *   prompt: 'Analyze this project...',
 *   model: 'gemini:gemini-2.5-flash',
 *   systemPrompt: 'You are a helpful assistant.',
 * });
 * ```
 */
import { useState, useCallback } from 'react';
import { generateText, streamText, CoreMessage } from 'ai';
import { getModel, detectProvider, isProviderAvailable, type AIProviderType } from './providers';

// ============================================================================
// Types
// ============================================================================

export interface LLMGenerateOptions {
    /** User prompt/message */
    prompt: string;
    /** Model ID (e.g., 'gemini:gemini-2.5-flash' or just 'gpt-4o') */
    model?: string;
    /** System prompt for context */
    systemPrompt?: string;
    /** Temperature (0-1) */
    temperature?: number;
    /** Max tokens to generate */
    maxTokens?: number;
    /** Whether to stream the response */
    stream?: boolean;
    /** Callback for streaming chunks */
    onChunk?: (chunk: string) => void;
}

export interface LLMChatOptions {
    /** Chat history */
    messages: CoreMessage[];
    /** Model ID */
    model?: string;
    /** System prompt */
    systemPrompt?: string;
    /** Temperature */
    temperature?: number;
    /** Whether to stream */
    stream?: boolean;
    /** Callback for streaming chunks */
    onChunk?: (chunk: string) => void;
}

export interface UseLLMReturn {
    /** Generate text from a prompt */
    generate: (options: LLMGenerateOptions) => Promise<string>;
    /** Chat with message history */
    chat: (options: LLMChatOptions) => Promise<string>;
    /** Loading state */
    isLoading: boolean;
    /** Error state */
    error: Error | null;
    /** Clear error */
    clearError: () => void;
    /** Check if a provider is available */
    isProviderAvailable: (provider: AIProviderType) => boolean;
}

// ============================================================================
// Hook Implementation
// ============================================================================

const DEFAULT_MODEL = 'gemini:gemini-2.5-flash';

export function useLLM(): UseLLMReturn {
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<Error | null>(null);

    const clearError = useCallback(() => setError(null), []);

    /**
     * Generate text from a single prompt
     */
    const generate = useCallback(async (options: LLMGenerateOptions): Promise<string> => {
        const {
            prompt,
            model = DEFAULT_MODEL,
            systemPrompt,
            temperature = 0.7,
            maxTokens,
            stream = false,
            onChunk,
        } = options;

        setIsLoading(true);
        setError(null);

        try {
            const modelInstance = getModel(model);

            if (stream && onChunk) {
                // Streaming mode
                const result = await streamText({
                    model: modelInstance,
                    prompt,
                    system: systemPrompt,
                    temperature,
                    maxTokens,
                });

                let fullText = '';
                for await (const chunk of result.textStream) {
                    fullText += chunk;
                    onChunk(chunk);
                }
                return fullText;
            } else {
                // Non-streaming mode
                const result = await generateText({
                    model: modelInstance,
                    prompt,
                    system: systemPrompt,
                    temperature,
                    maxTokens,
                });

                return result.text;
            }
        } catch (err) {
            const error = err instanceof Error ? err : new Error(String(err));
            setError(error);
            throw error;
        } finally {
            setIsLoading(false);
        }
    }, []);

    /**
     * Chat with message history
     */
    const chat = useCallback(async (options: LLMChatOptions): Promise<string> => {
        const {
            messages,
            model = DEFAULT_MODEL,
            systemPrompt,
            temperature = 0.7,
            stream = false,
            onChunk,
        } = options;

        setIsLoading(true);
        setError(null);

        try {
            const modelInstance = getModel(model);

            if (stream && onChunk) {
                // Streaming mode
                const result = await streamText({
                    model: modelInstance,
                    messages,
                    system: systemPrompt,
                    temperature,
                });

                let fullText = '';
                for await (const chunk of result.textStream) {
                    fullText += chunk;
                    onChunk(chunk);
                }
                return fullText;
            } else {
                // Non-streaming mode
                const result = await generateText({
                    model: modelInstance,
                    messages,
                    system: systemPrompt,
                    temperature,
                });

                return result.text;
            }
        } catch (err) {
            const error = err instanceof Error ? err : new Error(String(err));
            setError(error);
            throw error;
        } finally {
            setIsLoading(false);
        }
    }, []);

    return {
        generate,
        chat,
        isLoading,
        error,
        clearError,
        isProviderAvailable,
    };
}

// ============================================================================
// Standalone Functions (for non-hook usage)
// ============================================================================

/**
 * Generate text without React hook (for services/commands)
 */
export async function generateLLMText(options: LLMGenerateOptions): Promise<string> {
    const {
        prompt,
        model = DEFAULT_MODEL,
        systemPrompt,
        temperature = 0.7,
        maxTokens,
    } = options;

    const modelInstance = getModel(model);

    const result = await generateText({
        model: modelInstance,
        prompt,
        system: systemPrompt,
        temperature,
        maxTokens,
    });

    return result.text;
}
