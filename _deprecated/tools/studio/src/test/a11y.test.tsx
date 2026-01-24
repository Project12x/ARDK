/**
 * Accessibility Test Suite
 * 
 * Uses vitest-axe to run automated accessibility checks on components.
 * These tests help catch WCAG violations early.
 */
import { render } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { axe } from 'vitest-axe';

describe('Accessibility Tests', () => {
    it('validates a basic accessible component has no violations', async () => {
        const { container } = render(
            <main>
                <h1>WalrusPM Accessibility Test</h1>
                <button type="button">Click me</button>
                <a href="/test">Test Link</a>
            </main>
        );

        const results = await axe(container);
        expect(results).toHaveNoViolations();
    });

    it('catches accessibility violations (negative test)', async () => {
        const { container } = render(
            <div>
                {/* Image without alt text - should fail */}
                <img src="/test.png" />
                {/* Button with no accessible name - should be caught */}
                <button type="button"></button>
            </div>
        );

        const results = await axe(container);
        // This test verifies that axe catches violations
        // We expect violations here, so we check that count > 0
        expect(results.violations.length).toBeGreaterThan(0);
    });
});
