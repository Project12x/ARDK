import type { Meta, StoryObj } from '@storybook/react';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';

const meta = {
    title: 'UI/Card',
    component: Card,
    parameters: {
        layout: 'padded',
    },
    tags: ['autodocs'],
    argTypes: {
        title: { control: 'text' },
    },
} satisfies Meta<typeof Card>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
    args: {
        children: <div className="text-gray-400">Card content goes here.</div>,
    },
};

export const WithTitle: Story = {
    args: {
        title: 'Project Details',
        children: <div className="text-gray-400">Card content with a title header.</div>,
    },
};

export const WithAction: Story = {
    args: {
        title: 'Deployment',
        action: <Button size="sm" variant="outline">Deploy</Button>,
        children: <div className="text-gray-400">Manage your deployments here.</div>,
    },
};

export const Complex: Story = {
    args: {
        title: 'System Status',
        children: (
            <div className="space-y-4">
                <div className="flex justify-between items-center bg-black/20 p-2 rounded">
                    <span className="text-sm">CPU Usage</span>
                    <span className="text-accent font-mono">42%</span>
                </div>
                <div className="flex justify-between items-center bg-black/20 p-2 rounded">
                    <span className="text-sm">Memory</span>
                    <span className="text-green-500 font-mono">1.2GB</span>
                </div>
            </div>
        ),
    },
};
