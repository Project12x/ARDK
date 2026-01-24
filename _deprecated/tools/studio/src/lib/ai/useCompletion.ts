/**
 * useCompletion Hook - Text Completion Interface
 * 
 * @module lib/ai/useCompletion
 * @description
 * React hook for simple text completion (non-conversational).
 * Useful for form field auto-complete, suggestions, and single-shot generation.
 * 
 * @example
 * ```typescript
 * const { complete, completion, isLoading } = useCompletion({
 *   model: 'gemini:gemini-2.5-flash',
 * });
 * 
 * // Get a completion
 * await complete('Suggest a project name for a guitar pedal that...');
 * // completion now contains the result
 * ```
 */
import { useState, useCallback } from 'react';
import { useLLM } from './useLLM';

// ============================================================================
// Types
// ============================================================================

export interface UseCompletionOptions {
    /** Model to use */
    model?: string;
    /** System prompt */
    systemPrompt?: string;
    /** Temperature (0-1) */
    temperature?: number;
    /** Max tokens */
    maxTokens?: number;
    /** Whether to stream */
    stream?: boolean;
}

export interface UseCompletionReturn {
    /** Current completion result */
    completion: string;
    /** Trigger a completion */
    complete: (prompt: string) => Promise<string>;
    /** Loading state */
    isLoading: boolean;
    /** Error state */
    error: Error | null;
    /** Clear the completion */
    clear: () => void;
    /** Streaming text (while generating) */
    streamingText: string;
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useCompletion(options: UseCompletionOptions = {}): UseCompletionReturn {
    const {
        model,
        systemPrompt,
        temperature = 0.7,
        maxTokens,
        stream = true,
    } = options;

    const [completion, setCompletion] = useState('');
    const [streamingText, setStreamingText] = useState('');
    const { generate, isLoading, error, clearError } = useLLM();

    const clear = useCallback(() => {
        setCompletion('');
        setStreamingText('');
        clearError();
    }, [clearError]);

    const complete = useCallback(async (prompt: string): Promise<string> => {
        setStreamingText('');

        const result = await generate({
            prompt,
            model,
            systemPrompt,
            temperature,
            maxTokens,
            stream,
            onChunk: stream ? (chunk) => {
                setStreamingText(prev => prev + chunk);
            } : undefined,
        });

        setCompletion(result);
        setStreamingText('');

        return result;
    }, [generate, model, systemPrompt, temperature, maxTokens, stream]);

    return {
        completion,
        complete,
        isLoading,
        error,
        clear,
        streamingText,
    };
}
