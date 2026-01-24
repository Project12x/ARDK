import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Switch } from '../Switch';

describe('Switch', () => {
    it('should toggle state on click', () => {
        render(<Switch aria-label="Toggle me" />);

        const switchEl = screen.getByRole('switch', { name: "Toggle me" });
        expect(switchEl).toHaveAttribute('aria-checked', 'false');

        fireEvent.click(switchEl);
        expect(switchEl).toHaveAttribute('aria-checked', 'true');

        fireEvent.click(switchEl);
        expect(switchEl).toHaveAttribute('aria-checked', 'false');
    });

    it('should respect defaultChecked prop', () => {
        render(<Switch defaultChecked aria-label="Checked" />);
        const switchEl = screen.getByRole('switch', { name: "Checked" });
        expect(switchEl).toHaveAttribute('aria-checked', 'true');
    });

    it('should be disabled when disabled prop is set', () => {
        render(<Switch disabled aria-label="Disabled" />);
        const switchEl = screen.getByRole('switch', { name: "Disabled" });
        expect(switchEl).toBeDisabled();
    });
});
