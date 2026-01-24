/**
 * MSW Handlers for Vercel AI SDK
 * 
 * These handlers mock the streaming responses used by the Vercel AI SDK.
 * The SDK uses a specific text stream format for streaming responses.
 * 
 * @see https://sdk.vercel.ai/docs
 */
import { http, HttpResponse } from 'msw';

/**
 * Creates a mock text stream response in the format expected by the AI SDK.
 * The SDK uses a simple text format where each chunk is plain text.
 */
function createStreamResponse(text: string): ReadableStream<Uint8Array> {
    const encoder = new TextEncoder();
    const chunks = text.split(' ').map(word => word + ' ');

    return new ReadableStream({
        async start(controller) {
            for (const chunk of chunks) {
                controller.enqueue(encoder.encode(chunk));
                await new Promise(resolve => setTimeout(resolve, 10));
            }
            controller.close();
        }
    });
}

/**
 * Creates a non-streaming JSON response for generateText.
 */
function createTextResponse(text: string) {
    return {
        id: 'mock-response-id',
        object: 'chat.completion',
        created: Date.now(),
        model: 'mock-model',
        choices: [{
            index: 0,
            message: {
                role: 'assistant',
                content: text,
            },
            finish_reason: 'stop',
        }],
        usage: {
            prompt_tokens: 10,
            completion_tokens: 20,
            total_tokens: 30,
        },
    };
}

// Default mock responses by provider
const MOCK_RESPONSES = {
    gemini: 'This is a mock response from Gemini AI for testing purposes.',
    openai: 'This is a mock response from OpenAI GPT for testing purposes.',
    anthropic: 'This is a mock response from Anthropic Claude for testing purposes.',
    groq: 'This is a mock response from Groq for testing purposes.',
    ollama: 'This is a mock response from Ollama local model for testing purposes.',
};

/**
 * Anthropic Claude API handlers
 * Uses messages API: POST /v1/messages
 */
export const anthropicSdkHandlers = [
    // Non-streaming
    http.post('https://api.anthropic.com/v1/messages', async ({ request }) => {
        const body = await request.json() as { stream?: boolean };

        if (body.stream) {
            // Streaming response
            return new HttpResponse(createStreamResponse(MOCK_RESPONSES.anthropic), {
                headers: {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                },
            });
        }

        // Non-streaming response
        return HttpResponse.json({
            id: 'msg_mock',
            type: 'message',
            role: 'assistant',
            content: [{
                type: 'text',
                text: MOCK_RESPONSES.anthropic,
            }],
            model: 'claude-3-sonnet-20240229',
            stop_reason: 'end_turn',
            usage: {
                input_tokens: 10,
                output_tokens: 20,
            },
        });
    }),
];

/**
 * Groq API handlers
 * Uses OpenAI-compatible API: POST /openai/v1/chat/completions
 */
export const groqSdkHandlers = [
    http.post('https://api.groq.com/openai/v1/chat/completions', async ({ request }) => {
        const body = await request.json() as { stream?: boolean };

        if (body.stream) {
            return new HttpResponse(createStreamResponse(MOCK_RESPONSES.groq), {
                headers: {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                },
            });
        }

        return HttpResponse.json(createTextResponse(MOCK_RESPONSES.groq));
    }),
];

/**
 * Ollama API handlers (local)
 * Uses: POST http://localhost:11434/api/chat
 */
export const ollamaSdkHandlers = [
    // Chat endpoint
    http.post('http://localhost:11434/api/chat', async ({ request }) => {
        const body = await request.json() as { stream?: boolean };

        if (body.stream !== false) {
            // Ollama streams by default
            return new HttpResponse(createStreamResponse(MOCK_RESPONSES.ollama), {
                headers: {
                    'Content-Type': 'application/x-ndjson',
                },
            });
        }

        return HttpResponse.json({
            model: 'llama2',
            message: {
                role: 'assistant',
                content: MOCK_RESPONSES.ollama,
            },
            done: true,
        });
    }),

    // Tags endpoint (list models)
    http.get('http://localhost:11434/api/tags', () => {
        return HttpResponse.json({
            models: [
                { name: 'llama2', size: 3791730596 },
                { name: 'mistral', size: 4109854935 },
                { name: 'codellama', size: 3791730596 },
            ],
        });
    }),
];

/**
 * Google Gemini API handlers for AI SDK
 * Uses: POST https://generativelanguage.googleapis.com/v1beta/models/...
 */
export const geminiSdkHandlers = [
    // generateContent endpoint (non-streaming)
    http.post(/generativelanguage\.googleapis\.com.*generateContent/, () => {
        return HttpResponse.json({
            candidates: [{
                content: {
                    parts: [{ text: MOCK_RESPONSES.gemini }],
                    role: 'model',
                },
                finishReason: 'STOP',
            }],
            usageMetadata: {
                promptTokenCount: 10,
                candidatesTokenCount: 20,
                totalTokenCount: 30,
            },
        });
    }),

    // streamGenerateContent endpoint (streaming)
    http.post(/generativelanguage\.googleapis\.com.*streamGenerateContent/, () => {
        return new HttpResponse(createStreamResponse(MOCK_RESPONSES.gemini), {
            headers: {
                'Content-Type': 'text/event-stream',
                'Cache-Control': 'no-cache',
            },
        });
    }),
];

/**
 * OpenAI API handlers for AI SDK
 * Uses: POST https://api.openai.com/v1/chat/completions
 */
export const openaiSdkHandlers = [
    http.post('https://api.openai.com/v1/chat/completions', async ({ request }) => {
        const body = await request.json() as { stream?: boolean };

        if (body.stream) {
            return new HttpResponse(createStreamResponse(MOCK_RESPONSES.openai), {
                headers: {
                    'Content-Type': 'text/event-stream',
                    'Cache-Control': 'no-cache',
                },
            });
        }

        return HttpResponse.json(createTextResponse(MOCK_RESPONSES.openai));
    }),
];

/**
 * All Vercel AI SDK handlers combined
 */
export const aiSdkHandlers = [
    ...geminiSdkHandlers,
    ...openaiSdkHandlers,
    ...anthropicSdkHandlers,
    ...groqSdkHandlers,
    ...ollamaSdkHandlers,
];
