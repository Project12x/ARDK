import { forwardRef, useRef, useImperativeHandle, type ReactNode } from 'react';
import clsx from 'clsx';
import { Mic } from 'lucide-react';
import { useSpeechToText } from '../../hooks/useSpeechToText';

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    leftIcon?: ReactNode;
    enableSpeech?: boolean;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ className, label, error, leftIcon, enableSpeech = true, ...props }, ref) => {
        const internalRef = useRef<HTMLInputElement>(null);

        // Merge the external ref with our internal ref
        useImperativeHandle(ref, () => internalRef.current!, []);

        const { isListening, toggleListening, isSupported } = useSpeechToText({
            onTranscript: (text) => {
                if (internalRef.current) {
                    const currentValue = internalRef.current.value;
                    const newValue = currentValue ? `${currentValue} ${text}` : text;

                    const nativeInputValueSetter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set;
                    nativeInputValueSetter?.call(internalRef.current, newValue);

                    const event = new Event('input', { bubbles: true });
                    internalRef.current.dispatchEvent(event);
                }
            }
        });

        return (
            <div className="w-full">
                {label && <label className="block text-xs font-bold text-gray-500 mb-1 uppercase tracking-wider">{label}</label>}
                <div className="relative flex items-center">
                    {leftIcon && (
                        <div className="absolute left-3 text-gray-500 pointer-events-none flex items-center">
                            {leftIcon}
                        </div>
                    )}
                    <input
                        ref={internalRef}
                        className={clsx(
                            "bg-surface border border-border p-2 text-white w-full focus:outline-none focus:border-accent font-mono transition-colors",
                            leftIcon && "pl-9",
                            enableSpeech && "pr-9",
                            error && "border-red-500",
                            className
                        )}
                        {...props}
                    />

                    {enableSpeech && isSupported && (
                        <button
                            type="button"
                            onClick={toggleListening}
                            className={clsx(
                                "absolute right-2 p-1 rounded-full transition-colors",
                                isListening ? "text-red-500 animate-pulse bg-red-500/10" : "text-gray-500 hover:text-white"
                            )}
                            title="Speech input"
                        >
                            <Mic size={14} />
                        </button>
                    )}
                </div>
                {error && <span className="text-red-500 text-xs mt-1 block">{error}</span>}
            </div>
        );
    }
);

Input.displayName = 'Input';
