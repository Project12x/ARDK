/**
 * MSW Handlers Index
 * 
 * Aggregates all mock handlers for the test environment.
 * Import this file to get all handlers at once.
 */
import { geminiHandlers } from './geminiHandlers';
import { openaiHandlers } from './openaiHandlers';
import { aiSdkHandlers } from './aiSdkHandlers';

export const handlers = [
    ...geminiHandlers,
    ...openaiHandlers,
    ...aiSdkHandlers,
];
