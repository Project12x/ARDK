import { describe, it, expect } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import { Popover, PopoverTrigger, PopoverContent } from '../Popover';

describe('Popover', () => {
    it('should open content on click', () => {
        render(
            <Popover>
                <PopoverTrigger>Open Popover</PopoverTrigger>
                <PopoverContent>Popover Body</PopoverContent>
            </Popover>
        );

        expect(screen.queryByText('Popover Body')).not.toBeInTheDocument();

        fireEvent.click(screen.getByText('Open Popover'));

        expect(screen.getByText('Popover Body')).toBeInTheDocument();
    });
});
