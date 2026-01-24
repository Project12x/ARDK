/**
 * Universal Card Variants
 * Type-safe variant system using class-variance-authority (cva).
 * This replaces scattered ternary class logic with a clean, composable API.
 */

import { cva, type VariantProps } from 'class-variance-authority';

// ============================================================================
// CARD VARIANTS
// ============================================================================

export const cardVariants = cva(
    // Base styles applied to all cards
    [
        'group relative rounded-lg border transition-all duration-200 overflow-hidden',
        'bg-surface backdrop-blur-sm',
    ],
    {
        variants: {
            // Layout variant
            variant: {
                default: 'p-4 flex flex-col gap-3',
                moderate: 'p-0 flex flex-col gap-3 h-auto',
                text: 'p-0 flex flex-col gap-3 min-h-[14rem] h-auto',
                compact: 'p-0 flex flex-col gap-3 bg-white/5 hover:bg-white/10 h-52',
                media: 'p-0 overflow-hidden flex flex-col',
                list: 'p-2 flex flex-row items-center gap-2 rounded-md',
                kanban: 'p-3 flex flex-col gap-2 min-h-[100px]',
                minimal: 'p-2 flex flex-col gap-1',
                dense: 'p-0 flex flex-col bg-[#050505] border-accent/20 hover:border-accent overflow-hidden h-full',
            },
            // Status-based styling
            status: {
                active: 'border-accent/30 hover:border-accent/60',
                pending: 'border-yellow-500/30 hover:border-yellow-500/60',
                completed: 'border-green-500/30 hover:border-green-500/60 opacity-75',
                archived: 'border-gray-500/30 opacity-50',
                error: 'border-red-500/50 bg-red-500/5',
                default: 'border-white/10 hover:border-accent/50',
            },
            // Size variant
            size: {
                sm: 'text-xs',
                md: 'text-sm',
                lg: 'text-base',
            },
            // Interactive states
            interactive: {
                true: 'cursor-pointer hover:shadow-lg hover:-translate-y-0.5',
                false: '',
            },
            // Dragging state
            dragging: {
                true: 'opacity-30 scale-95 ring-2 ring-accent shadow-2xl',
                false: '',
            },
            // Selected state
            selected: {
                true: 'ring-2 ring-accent shadow-[0_0_20px_rgba(var(--accent-rgb),0.2)]',
                false: '',
            },
            // Collapsed state
            collapsed: {
                true: 'h-14 min-h-0 overflow-hidden',
                false: '',
            },
            // Has background image
            hasBackground: {
                true: 'min-h-[16rem]',
                false: '',
            },
        },
        defaultVariants: {
            variant: 'default',
            status: 'default',
            size: 'md',
            interactive: true,
            dragging: false,
            selected: false,
            collapsed: false,
            hasBackground: false,
        },
        // Compound variants for complex combinations
        compoundVariants: [
            {
                variant: 'media',
                hasBackground: true,
                className: 'min-h-[20rem]',
            },
            {
                collapsed: true,
                variant: 'default',
                className: 'flex-row items-center p-2 pl-4',
            },
        ],
    }
);

// ============================================================================
// STATUS STRIPE VARIANTS
// ============================================================================

export const statusStripeVariants = cva(
    'absolute left-0 top-0 bottom-0 z-20 transition-all shadow-[0_0_10px_currentColor]',
    {
        variants: {
            size: {
                sm: 'w-0.5',
                md: 'w-1 group-hover:w-1.5',
                lg: 'w-1.5 group-hover:w-2',
            },
            interactive: {
                true: 'cursor-row-resize',
                false: '',
            },
        },
        defaultVariants: {
            size: 'md',
            interactive: true,
        },
    }
);

// ============================================================================
// BADGE VARIANTS
// ============================================================================

export const badgeVariants = cva(
    'inline-flex items-center gap-1 rounded font-bold uppercase tracking-wider',
    {
        variants: {
            size: {
                xs: 'text-[8px] px-1 py-0.5',
                sm: 'text-[9px] px-1.5 py-0.5',
                md: 'text-[10px] px-2 py-1',
            },
            variant: {
                default: 'bg-white/10 text-gray-300 border border-white/10',
                accent: 'bg-accent/20 text-accent border border-accent/30',
                success: 'bg-green-500/20 text-green-400 border border-green-500/30',
                warning: 'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
                error: 'bg-red-500/20 text-red-400 border border-red-500/30',
                info: 'bg-blue-500/20 text-blue-400 border border-blue-500/30',
            },
        },
        defaultVariants: {
            size: 'sm',
            variant: 'default',
        },
    }
);

// ============================================================================
// ACTION BUTTON VARIANTS
// ============================================================================

export const cardActionVariants = cva(
    'p-1.5 rounded transition-all opacity-0 group-hover:opacity-100',
    {
        variants: {
            variant: {
                default: 'text-gray-400 hover:text-white hover:bg-white/10',
                success: 'text-green-400 hover:text-green-300 hover:bg-green-500/20',
                danger: 'text-red-400 hover:text-red-300 hover:bg-red-500/20',
                warning: 'text-yellow-400 hover:text-yellow-300 hover:bg-yellow-500/20',
                accent: 'text-accent hover:text-white hover:bg-accent/20',
            },
            size: {
                sm: 'h-6 w-6',
                md: 'h-7 w-7',
                lg: 'h-8 w-8',
            },
        },
        defaultVariants: {
            variant: 'default',
            size: 'sm',
        },
    }
);

// ============================================================================
// TYPE EXPORTS
// ============================================================================

export type CardVariantsProps = VariantProps<typeof cardVariants>;
export type StatusStripeVariantsProps = VariantProps<typeof statusStripeVariants>;
export type BadgeVariantsProps = VariantProps<typeof badgeVariants>;
export type CardActionVariantsProps = VariantProps<typeof cardActionVariants>;
