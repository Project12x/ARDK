/**
 * useChat Hook - Conversational AI Interface
 * 
 * @module lib/ai/useChat
 * @description
 * React hook for conversational AI with message history management.
 * Built on top of useLLM for provider-agnostic chat functionality.
 * 
 * @example
 * ```typescript
 * const { messages, sendMessage, isLoading, clearHistory } = useChat({
 *   systemPrompt: 'You are a helpful project assistant.',
 *   model: 'gemini:gemini-2.5-flash',
 * });
 * 
 * await sendMessage('What tasks need attention?');
 * ```
 */
import { useState, useCallback } from 'react';
import type { CoreMessage } from 'ai';
import { useLLM } from './useLLM';

// ============================================================================
// Types
// ============================================================================

export interface ChatMessage {
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
}

export interface UseChatOptions {
    /** Initial system prompt */
    systemPrompt?: string;
    /** Model to use */
    model?: string;
    /** Initial messages */
    initialMessages?: ChatMessage[];
    /** Callback when response is received */
    onResponse?: (message: ChatMessage) => void;
    /** Whether to stream responses */
    stream?: boolean;
}

export interface UseChatReturn {
    /** All messages in the conversation */
    messages: ChatMessage[];
    /** Send a user message and get response */
    sendMessage: (content: string) => Promise<ChatMessage>;
    /** Loading state */
    isLoading: boolean;
    /** Error state */
    error: Error | null;
    /** Clear chat history */
    clearHistory: () => void;
    /** Add a message without sending to LLM */
    addMessage: (role: 'user' | 'assistant' | 'system', content: string) => void;
    /** Current streaming text (if streaming) */
    streamingText: string;
}

// ============================================================================
// Helper Functions
// ============================================================================

function generateId(): string {
    return `msg_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

function toCoreMessages(messages: ChatMessage[]): CoreMessage[] {
    return messages
        .filter(m => m.role !== 'system') // System handled separately
        .map(m => ({
            role: m.role as 'user' | 'assistant',
            content: m.content,
        }));
}

// ============================================================================
// Hook Implementation
// ============================================================================

export function useChat(options: UseChatOptions = {}): UseChatReturn {
    const {
        systemPrompt,
        model,
        initialMessages = [],
        onResponse,
        stream = true,
    } = options;

    const [messages, setMessages] = useState<ChatMessage[]>(initialMessages);
    const [streamingText, setStreamingText] = useState('');
    const { chat, isLoading, error, clearError } = useLLM();

    const clearHistory = useCallback(() => {
        setMessages([]);
        setStreamingText('');
        clearError();
    }, [clearError]);

    const addMessage = useCallback((role: 'user' | 'assistant' | 'system', content: string) => {
        const message: ChatMessage = {
            id: generateId(),
            role,
            content,
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, message]);
    }, []);

    const sendMessage = useCallback(async (content: string): Promise<ChatMessage> => {
        // Add user message
        const userMessage: ChatMessage = {
            id: generateId(),
            role: 'user',
            content,
            timestamp: new Date(),
        };
        setMessages(prev => [...prev, userMessage]);
        setStreamingText('');

        // Build message history for LLM
        const coreMessages = toCoreMessages([...messages, userMessage]);

        // Get response
        const responseText = await chat({
            messages: coreMessages,
            model,
            systemPrompt,
            stream,
            onChunk: stream ? (chunk) => {
                setStreamingText(prev => prev + chunk);
            } : undefined,
        });

        // Create assistant message
        const assistantMessage: ChatMessage = {
            id: generateId(),
            role: 'assistant',
            content: responseText,
            timestamp: new Date(),
        };

        setMessages(prev => [...prev, assistantMessage]);
        setStreamingText('');

        // Callback
        if (onResponse) {
            onResponse(assistantMessage);
        }

        return assistantMessage;
    }, [messages, chat, model, systemPrompt, stream, onResponse]);

    return {
        messages,
        sendMessage,
        isLoading,
        error,
        clearHistory,
        addMessage,
        streamingText,
    };
}
