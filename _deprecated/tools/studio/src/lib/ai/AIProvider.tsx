/**
 * AIProvider Context
 * 
 * @module lib/ai/AIProvider
 * @description
 * React context for managing AI configuration across the app.
 * Provides current model selection, provider status, and configuration.
 * 
 * @example
 * ```typescript
 * // In App.tsx
 * <AIProvider defaultModel="gemini:gemini-2.5-flash">
 *   <App />
 * </AIProvider>
 * 
 * // In any component
 * const { currentModel, setModel, availableProviders } = useAIContext();
 * ```
 */
import React, { createContext, useContext, useState, useCallback, useMemo, type ReactNode } from 'react';
import {
    getAvailableProviders,
    isProviderAvailable,
    PROVIDER_CONFIGS,
    type AIProviderType,
    type ProviderConfig
} from './providers';

// ============================================================================
// Types
// ============================================================================

export interface AIContextValue {
    /** Current model ID (e.g., 'gemini:gemini-2.5-flash') */
    currentModel: string;
    /** Set the current model */
    setModel: (model: string) => void;
    /** Current provider type */
    currentProvider: AIProviderType;
    /** All available providers (those with API keys) */
    availableProviders: AIProviderType[];
    /** All provider configurations */
    providerConfigs: Record<AIProviderType, ProviderConfig>;
    /** Check if a provider is available */
    isProviderAvailable: (provider: AIProviderType) => boolean;
    /** Whether we're in offline mode (Ollama only) */
    isOfflineMode: boolean;
    /** Toggle offline mode */
    setOfflineMode: (offline: boolean) => void;
    /** Get available models for a provider */
    getModelsForProvider: (provider: AIProviderType) => string[];
}

// ============================================================================
// Context
// ============================================================================

const AIContext = createContext<AIContextValue | null>(null);

// ============================================================================
// Provider Component
// ============================================================================

export interface AIProviderProps {
    children: ReactNode;
    /** Default model to use */
    defaultModel?: string;
}

export function AIProvider({ children, defaultModel = 'gemini:gemini-2.5-flash' }: AIProviderProps) {
    const [currentModel, setCurrentModel] = useState(defaultModel);
    const [isOfflineMode, setIsOfflineMode] = useState(false);

    // Extract provider from model ID
    const currentProvider = useMemo((): AIProviderType => {
        if (isOfflineMode) return 'ollama';

        const [provider] = currentModel.split(':');
        if (provider in PROVIDER_CONFIGS) {
            return provider as AIProviderType;
        }

        // Detect from model name
        if (currentModel.startsWith('gpt')) return 'openai';
        if (currentModel.startsWith('claude')) return 'anthropic';
        if (currentModel.startsWith('gemini')) return 'gemini';

        return 'gemini'; // Default
    }, [currentModel, isOfflineMode]);

    const setModel = useCallback((model: string) => {
        setCurrentModel(model);
    }, []);

    const setOfflineMode = useCallback((offline: boolean) => {
        setIsOfflineMode(offline);
        if (offline) {
            // Switch to Ollama when going offline
            setCurrentModel('ollama:llama3.2');
        }
    }, []);

    const getModelsForProvider = useCallback((provider: AIProviderType): string[] => {
        return PROVIDER_CONFIGS[provider]?.models ?? [];
    }, []);

    const value = useMemo((): AIContextValue => ({
        currentModel: isOfflineMode ? 'ollama:llama3.2' : currentModel,
        setModel,
        currentProvider,
        availableProviders: getAvailableProviders(),
        providerConfigs: PROVIDER_CONFIGS,
        isProviderAvailable,
        isOfflineMode,
        setOfflineMode,
        getModelsForProvider,
    }), [currentModel, currentProvider, isOfflineMode, setModel, setOfflineMode, getModelsForProvider]);

    return (
        <AIContext.Provider value={value}>
            {children}
        </AIContext.Provider>
    );
}

// ============================================================================
// Hook
// ============================================================================

/**
 * Access AI context values
 */
export function useAIContext(): AIContextValue {
    const context = useContext(AIContext);
    if (!context) {
        throw new Error('useAIContext must be used within an AIProvider');
    }
    return context;
}

/**
 * Check if AI is available (any provider configured)
 */
export function useIsAIAvailable(): boolean {
    const context = useContext(AIContext);
    if (!context) return false;
    return context.availableProviders.length > 0;
}
