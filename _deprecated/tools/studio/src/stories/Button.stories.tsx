import type { Meta, StoryObj } from '@storybook/react';
import { Button } from '../components/ui/Button';

const meta = {
    title: 'UI/Button',
    component: Button,
    parameters: {
        layout: 'centered',
    },
    tags: ['autodocs'],
    argTypes: {
        variant: {
            control: 'select',
            options: ['primary', 'outline', 'ghost', 'danger'],
        },
        size: {
            control: 'radio',
            options: ['sm', 'md', 'lg'],
        },
        disabled: { control: 'boolean' },
        isLoading: { control: 'boolean' },
    },
} satisfies Meta<typeof Button>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Primary: Story = {
    args: {
        variant: 'primary',
        children: 'Action Button',
    },
};

export const Outline: Story = {
    args: {
        variant: 'outline',
        children: 'Secondary Action',
    },
};

export const Ghost: Story = {
    args: {
        variant: 'ghost',
        children: 'Ghost Button',
    },
};

export const Danger: Story = {
    args: {
        variant: 'danger',
        children: 'Delete Item',
    },
};

export const Loading: Story = {
    args: {
        isLoading: true,
        children: 'Please wait',
    },
};

export const Small: Story = {
    args: {
        size: 'sm',
        children: 'Small Button',
    },
};

export const Large: Story = {
    args: {
        size: 'lg',
        children: 'Large Action',
    },
};
