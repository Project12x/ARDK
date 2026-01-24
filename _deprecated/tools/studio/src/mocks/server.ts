/**
 * MSW Server for Node.js Test Environment
 * 
 * This server intercepts network requests during tests and returns mock responses.
 * Import and use in test setup files.
 */
import { setupServer } from 'msw/node';
import { handlers } from './handlers';

// Create the MSW server with all handlers
export const server = setupServer(...handlers);
