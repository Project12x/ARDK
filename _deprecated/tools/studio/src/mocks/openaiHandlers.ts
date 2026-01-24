/**
 * OpenAI API Mock Handlers
 * 
 * Provides MSW handlers for mocking OpenAI API responses in tests.
 * These handlers intercept requests to OpenAI endpoints and return mock data.
 */
import { http, HttpResponse } from 'msw';

export const openaiHandlers = [
    // Mock OpenAI chat completions endpoint
    http.post('https://api.openai.com/v1/chat/completions', () => {
        return HttpResponse.json({
            id: 'chatcmpl-mock-id',
            object: 'chat.completion',
            created: Date.now(),
            model: 'gpt-4',
            choices: [{
                index: 0,
                message: {
                    role: 'assistant',
                    content: 'This is a mock OpenAI response for testing purposes.'
                },
                finish_reason: 'stop'
            }],
            usage: {
                prompt_tokens: 10,
                completion_tokens: 15,
                total_tokens: 25
            }
        });
    }),

    // Mock OpenAI completions endpoint (legacy)
    http.post('https://api.openai.com/v1/completions', () => {
        return HttpResponse.json({
            id: 'cmpl-mock-id',
            object: 'text_completion',
            created: Date.now(),
            model: 'gpt-3.5-turbo-instruct',
            choices: [{
                text: 'Mock OpenAI completion response.',
                index: 0,
                finish_reason: 'stop'
            }],
            usage: {
                prompt_tokens: 5,
                completion_tokens: 10,
                total_tokens: 15
            }
        });
    }),

    // Mock OpenAI embeddings endpoint
    http.post('https://api.openai.com/v1/embeddings', () => {
        return HttpResponse.json({
            object: 'list',
            data: [{
                object: 'embedding',
                embedding: Array(1536).fill(0).map(() => Math.random() * 2 - 1),
                index: 0
            }],
            model: 'text-embedding-ada-002',
            usage: {
                prompt_tokens: 8,
                total_tokens: 8
            }
        });
    }),
];
