/**
 * Gemini API Mock Handlers
 * 
 * Provides MSW handlers for mocking Google Gemini API responses in tests.
 * These handlers intercept requests to Gemini endpoints and return mock data.
 */
import { http, HttpResponse } from 'msw';

// Gemini API base URL pattern
const GEMINI_BASE = 'https://generativelanguage.googleapis.com/v1beta/*';

export const geminiHandlers = [
    // Mock Gemini generateContent endpoint
    http.post('https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent', () => {
        return HttpResponse.json({
            candidates: [{
                content: {
                    parts: [{
                        text: 'This is a mock Gemini response for testing purposes.'
                    }],
                    role: 'model'
                },
                finishReason: 'STOP',
                index: 0,
                safetyRatings: []
            }],
            usageMetadata: {
                promptTokenCount: 10,
                candidatesTokenCount: 15,
                totalTokenCount: 25
            }
        });
    }),

    // Mock Gemini generateContent with streaming
    http.post('https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:streamGenerateContent', () => {
        return HttpResponse.json({
            candidates: [{
                content: {
                    parts: [{
                        text: 'Mock streaming Gemini response.'
                    }],
                    role: 'model'
                },
                finishReason: 'STOP',
                index: 0
            }]
        });
    }),

    // Mock Gemini gemini-1.5-flash model
    http.post('https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent', () => {
        return HttpResponse.json({
            candidates: [{
                content: {
                    parts: [{
                        text: 'Mock Gemini 1.5 Flash response.'
                    }],
                    role: 'model'
                },
                finishReason: 'STOP',
                index: 0
            }]
        });
    }),
];
