/**
 * Why Did You Render (WDYR) Configuration
 * 
 * Tracks unnecessary re-renders in development mode.
 * Import this file at the very top of main.tsx (before React import).
 * 
 * @see https://github.com/welldone-software/why-did-you-render
 */
import React from 'react';

// Only enable in development
if (import.meta.env.DEV) {
    // Dynamic import to avoid bundling in production
    import('why-did-you-render').then((whyDidYouRender) => {
        whyDidYouRender.default(React, {
            // Track all pure components
            trackAllPureComponents: false,
            // Log to console
            logOnDifferentValues: true,
            // Include component name in logs
            include: [/.*/],
            // Exclude common noise
            exclude: [/^BrowserRouter/, /^Router/, /^Route/],
        });
    });
}

export { };
