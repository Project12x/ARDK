/**
 * NewAIService - Vercel AI SDK Based Service
 * 
 * @module lib/ai/NewAIService
 * @description
 * New AI service implementation using Vercel AI SDK.
 * Provides 1:1 feature parity with legacy AIService.ts.
 * 
 * ## Parity Tracking
 * 
 * | Legacy Function           | New Implementation | Status |
 * |---------------------------|-------------------|--------|
 * | getOllamaModels()         | getOllamaModels() | ✅ |
 * | chat()                    | chat()            | ✅ |
 * | chatWithGemini()          | chat()            | ✅ (unified) |
 * | analyzeDocumentForAsset() | analyzeDocumentForAsset() | 🔄 TODO |
 * | analyzeInventory()        | analyzeInventory() | 🔄 TODO |
 * | parseInboxItem()          | parseInboxItem()  | 🔄 TODO |
 * | analyzeAssetImage()       | analyzeAssetImage() | 🔄 TODO |
 * | chatWithProject()         | chatWithProject() | 🔄 TODO |
 * | parsePortfolio()          | parsePortfolio()  | 🔄 TODO |
 * | classifyUpload()          | classifyUpload()  | 🔄 TODO |
 * | analyzeMusicData()        | analyzeMusicData() | 🔄 TODO |
 * | analyzeFile()             | analyzeFile()     | 🔄 TODO |
 * | fileToGenerativePart()    | (internal)        | ✅ (handled by SDK) |
 */
import { generateText } from 'ai';
import { getModel, detectProvider, createOllamaProvider } from './providers';
import type { PromptBuilder, SystemContext } from '../ai-types';

// ============================================================================
// Types
// ============================================================================

export interface ChatOptions {
    modelId?: string;
    image?: File;
    jsonMode?: boolean;
}

// ============================================================================
// Service Implementation
// ============================================================================

export const NewAIService = {
    /**
     * Get available Ollama models (local)
     */
    async getOllamaModels(): Promise<string[]> {
        try {
            const response = await fetch('http://localhost:11434/api/tags');
            if (!response.ok) return [];

            const data = await response.json();
            return data.models?.map((m: { name: string }) => m.name) ?? [];
        } catch {
            console.warn('[NewAIService] Ollama not available');
            return [];
        }
    },

    /**
     * Unified chat interface - routes to appropriate provider based on model ID.
     * 
     * @param message - User message
     * @param context - Optional system context for prompt building
     * @param options - Model selection and other options
     */
    async chat(
        message: string,
        context?: SystemContext,
        options?: ChatOptions
    ): Promise<string> {
        const modelId = options?.modelId || 'gemini:gemini-2.5-flash';

        // Build system prompt if context provided
        let systemPrompt: string | undefined;
        if (context) {
            // Use PromptBuilder if available
            try {
                const { PromptBuilder } = await import('../ai-types');
                systemPrompt = PromptBuilder.buildSystemPrompt(context);
            } catch {
                // Fallback: simple context stringify
                systemPrompt = JSON.stringify(context);
            }
        }

        try {
            const model = getModel(modelId);

            const result = await generateText({
                model,
                prompt: message,
                system: systemPrompt,
            });

            return result.text;
        } catch (error: any) {
            console.error('[NewAIService] Chat error:', error);

            // Handle rate limits
            if (error.message?.includes('429')) {
                return 'System Overload (Rate Limit). Please try again in a moment.';
            }

            return `Oracle Connection Error: ${error.message}`;
        }
    },

    /**
     * Placeholder: Analyze document for asset registry entry
     * TODO: Implement with structured output
     */
    async analyzeDocumentForAsset(
        _input: string,
        _title?: string
    ): Promise<{
        name: string;
        category: string;
        description: string;
        make?: string;
        model?: string;
        specs_technical?: Record<string, any>;
        tags: string[];
    }> {
        // TODO: Implement with zod schema + generateObject
        throw new Error('[NewAIService] analyzeDocumentForAsset not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Analyze inventory from photo or list
     * TODO: Implement with vision + structured output
     */
    async analyzeInventory(_input: string | File): Promise<any[]> {
        throw new Error('[NewAIService] analyzeInventory not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Parse inbox item into actions
     * TODO: Implement with structured output
     */
    async parseInboxItem(_content: string): Promise<any> {
        throw new Error('[NewAIService] parseInboxItem not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Extract tool details from photo
     * TODO: Implement with vision
     */
    async analyzeAssetImage(_file: File): Promise<any> {
        throw new Error('[NewAIService] analyzeAssetImage not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Chat with project context
     * TODO: Implement with project-aware system prompt
     */
    async chatWithProject(_message: string, _project: any, _file?: File): Promise<string> {
        throw new Error('[NewAIService] chatWithProject not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Parse portfolio document
     * TODO: Implement with structured output
     */
    async parsePortfolio(_input: string | File): Promise<any[]> {
        throw new Error('[NewAIService] parsePortfolio not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Classify upload type
     * TODO: Implement with vision
     */
    async classifyUpload(_file: File): Promise<any> {
        throw new Error('[NewAIService] classifyUpload not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Analyze music file
     * TODO: Implement with audio processing
     */
    async analyzeMusicData(_file: File): Promise<any> {
        throw new Error('[NewAIService] analyzeMusicData not yet implemented - use legacy AIService');
    },

    /**
     * Placeholder: Generic file analysis
     * TODO: Implement with vision/document processing
     */
    async analyzeFile(_file: File): Promise<any> {
        throw new Error('[NewAIService] analyzeFile not yet implemented - use legacy AIService');
    },
};
