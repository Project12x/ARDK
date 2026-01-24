import React from 'react';
import clsx from 'clsx';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'outline' | 'ghost' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
}

export function Button({
    className,
    variant = 'primary',
    size = 'md',
    isLoading,
    children,
    disabled,
    ...props
}: ButtonProps) {
    return (
        <button
            className={clsx(
                "inline-flex items-center justify-center font-bold tracking-wide transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed uppercase",
                {
                    'bg-accent text-white hover:bg-white hover:text-black border border-transparent': variant === 'primary',
                    'border border-border text-white hover:border-accent hover:text-accent bg-transparent': variant === 'outline',
                    'text-gray-400 hover:text-white bg-transparent hover:bg-white/5': variant === 'ghost',
                    'bg-red-600 text-white hover:bg-red-700': variant === 'danger',

                    'px-3 py-1 text-xs': size === 'sm',
                    'px-4 py-2 text-sm': size === 'md',
                    'px-6 py-3 text-base': size === 'lg',
                },
                className
            )}
            disabled={disabled || isLoading}
            {...props}
        >
            {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
            {children}
        </button>
    );
}
