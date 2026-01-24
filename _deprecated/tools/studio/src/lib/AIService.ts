
import { GoogleGenerativeAI } from '@google/generative-ai';
import { OpenAIService } from './openai';
import { OllamaService } from './ollama';
import { GroqService } from './groq'; // Ensure this file exists, otherwise we'll create it
import { GeminiService } from './gemini';
import { PromptBuilder, type SystemContext } from './ai-types';

export const AIService = {

    async getOllamaModels(): Promise<string[]> {
        return await OllamaService.getTags();
    },

    /**
     * UNIFIED CHAT INTERFACE
     * Routes to the appropriate provider based on model ID.
     */
    async chat(message: string, context?: SystemContext, options?: { modelId?: string; image?: File; jsonMode?: boolean }): Promise<string> {
        const modelId = options?.modelId || 'auto';
        const systemPrompt = context ? PromptBuilder.buildSystemPrompt(context) : undefined;

        // 1. OpenAI
        if (modelId.startsWith('gpt')) {
            return await OpenAIService.chat(message, systemPrompt, modelId);
        }

        // 2. Ollama (Local)
        if (modelId.startsWith('llama') || modelId.startsWith('mistral') || modelId.startsWith('phi')) {
            return await OllamaService.chat(message, systemPrompt, modelId);
        }

        // 3. Groq (Fast) -> Assume implemented similarly if file exists
        if (modelId.startsWith('mixtral') || modelId.startsWith('gemma')) {
            try {
                return await GroqService.chat(message, systemPrompt, modelId);
            } catch (e) {
                console.warn("Groq failed, falling back to Gemini", e);
            }
        }

        // 4. Gemini (Default / Auto)
        const geminiModel = modelId === 'auto' ? 'gemini-2.5-flash' : modelId;
        return await this.chatWithGemini(message, systemPrompt, geminiModel, options?.image, options?.jsonMode);
    },

    /**
     * Internal Gemini Handler
     * Used for default chat and fallback.
     */
    async chatWithGemini(message: string, systemPrompt?: string, modelId = 'gemini-2.5-flash', image?: File, jsonMode = false): Promise<string> {
        const key = localStorage.getItem('GEMINI_API_KEY');
        if (!key) throw new Error("Gemini API Key missing");

        const genAI = new GoogleGenerativeAI(key);
        const model = genAI.getGenerativeModel({
            model: modelId,
            generationConfig: { responseMimeType: jsonMode ? "application/json" : "text/plain" }
        }, { apiVersion: 'v1beta' });

        const parts: any[] = [];
        if (systemPrompt) parts.push(systemPrompt + "\n\nUser Query: " + message);
        else parts.push(message);

        if (image) {
            const base64 = await this.fileToGenerativePart(image);
            parts.push(base64);
        }

        try {
            const result = await model.generateContent(parts);
            return result.response.text();
        } catch (e: any) {
            console.error("Gemini Error:", e);
            if (e.message?.includes('429')) return "System Overload (Rate Limit). Please try again in a moment.";
            return "Oracle Connection Error: " + e.message;
        }
    },

    // =========================================================================
    // SPECIALIZED ANALYZERS (Delegating to GeminiService for now)
    // =========================================================================

    /**
     * Analyzes a document to create an Asset Registry entry.
     */
    async analyzeDocumentForAsset(input: string, title?: string): Promise<{
        name: string;
        category: string;
        description: string;
        make?: string;
        model?: string;
        specs_technical?: Record<string, any>;
        tags: string[];
    }> {
        return GeminiService.analyzeDocumentForAsset(input, title);
    },

    /**
     * Identifies parts/tools in a photo or list.
     */
    async analyzeInventory(input: string | File): Promise<any[]> {
        return GeminiService.analyzeInventory(input);
    },

    /**
     * Parses unstructured inbox text into suggested actions.
     */
    async parseInboxItem(content: string): Promise<any> {
        return GeminiService.parseInboxItem(content);
    },

    /**
     * Extracts tool details from a photo.
     */
    async analyzeAssetImage(file: File): Promise<any> {
        return GeminiService.analyzeAssetImage(file);
    },

    /**
     * Chat with specific project context.
     */
    async chatWithProject(message: string, project: any, file?: File): Promise<string> {
        return GeminiService.chatWithProject(message, project, file);
    },

    /**
     * Parse portfolio/index document.
     */
    async parsePortfolio(input: string | File): Promise<any[]> {
        return GeminiService.parsePortfolio(input);
    },

    /**
     * Classify upload type.
     */
    async classifyUpload(file: File): Promise<any> {
        return GeminiService.classifyUpload(file);
    },

    /**
     * Analyze music file.
     */
    async analyzeMusicData(file: File): Promise<any> {
        return GeminiService.analyzeMusicData(file);
    },

    /**
     * Generic File Analysis.
     */
    async analyzeFile(file: File): Promise<any> {
        return GeminiService.analyzeFile(file);
    },

    /**
     * Helper: Convert File to Base64 for Gemini
     */
    async fileToGenerativePart(file: File): Promise<{ inlineData: { data: string; mimeType: string; } }> {
        const base64EncodedDataPromise = new Promise<string>((resolve) => {
            const reader = new FileReader();
            reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
            reader.readAsDataURL(file);
        });
        return { inlineData: { data: await base64EncodedDataPromise, mimeType: file.type } };
    }
};
