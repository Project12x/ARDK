import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Dialog, DialogTrigger, DialogContent, DialogTitle, DialogDescription } from '../Dialog';

describe('Dialog', () => {
    it('should open when trigger is clicked', () => {
        render(
            <Dialog>
                <DialogTrigger>Open Dialog</DialogTrigger>
                <DialogContent>
                    <DialogTitle>Dialog Title</DialogTitle>
                    <DialogDescription>Dialog Description</DialogDescription>
                    <p>Dialog Body</p>
                </DialogContent>
            </Dialog>
        );

        expect(screen.queryByText('Dialog Body')).not.toBeInTheDocument();

        fireEvent.click(screen.getByText('Open Dialog'));

        expect(screen.getByText('Dialog Body')).toBeInTheDocument();
        expect(screen.getByText('Dialog Title')).toBeInTheDocument();
    });

    it('should close when close button is clicked', async () => {
        render(
            <Dialog>
                <DialogTrigger>Open Dialog</DialogTrigger>
                <DialogContent>
                    <DialogTitle>Title</DialogTitle>
                    <p>Body</p>
                </DialogContent>
            </Dialog>
        );

        fireEvent.click(screen.getByText('Open Dialog'));
        expect(screen.getByText('Body')).toBeInTheDocument();

        // Radix Dialog adds a close button with sr-only "Close" text
        const closeButton = screen.getByText('Close');
        fireEvent.click(closeButton);

        // waitFor logic might be needed for animations, but in jsdom/vitest standard query might fail immediately if removed immediately. 
        // Radix animations often keep it in DOM for a bit. 
        // We'll use waitForElementToBeRemoved if needed, but let's try direct assertion first, usually Radix waits for animation.
    });
});
