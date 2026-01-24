import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Slider } from '../Slider';

// Radix Slider is tricky in JSDOM because it relies on layout measurements (getBoundingClientRect) 
// which are all 0 in JSDOM unless mocked. 
// We will test basic rendering and attribute presence.

describe('Slider', () => {
    it('should render with default values', () => {
        render(<Slider defaultValue={[50]} max={100} step={1} aria-label="Volume" />);

        // Radix slider role is typically on the thumb. 
        // We'll search for any element with role slider.
        const sliders = screen.getAllByRole('slider');
        expect(sliders.length).toBeGreaterThan(0);
        const slider = sliders[0];

        expect(slider).toBeInTheDocument();
        expect(slider).toHaveAttribute('aria-valuenow', '50');
        expect(slider).toHaveAttribute('aria-valuemax', '100');
    });

    it('should accept value prop', () => {
        render(<Slider value={[25]} aria-label="Brightness" />);
        const sliders = screen.getAllByRole('slider');
        expect(sliders[0]).toHaveAttribute('aria-valuenow', '25');
    });
});
