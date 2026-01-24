import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { UniversalButton } from './UniversalButton';

interface FallbackProps {
    error: Error;
    resetErrorBoundary: () => void;
}

export function UniversalErrorFallback({ error, resetErrorBoundary }: FallbackProps) {
    return (
        <div className="flex flex-col items-center justify-center min-h-screen bg-black text-white p-6 md:p-12">
            <div className="max-w-md w-full text-center space-y-6">
                <div className="flex justify-center">
                    <div className="p-4 rounded-full bg-red-500/10 border border-red-500/20 shadow-[0_0_30px_rgba(239,68,68,0.2)]">
                        <AlertTriangle size={48} className="text-red-500" />
                    </div>
                </div>

                <h1 className="text-2xl font-bold tracking-tight text-red-500">System Critical Error</h1>

                <div className="bg-red-950/30 border border-red-900/50 rounded-lg p-4 text-left overflow-hidden">
                    <pre className="text-xs text-red-200 font-mono whitespace-pre-wrap break-words">
                        {error.message}
                    </pre>
                    {error.stack && (
                        <details className="mt-2">
                            <summary className="text-xs text-red-400 cursor-pointer hover:text-red-300">View Stack Trace</summary>
                            <pre className="mt-2 text-[10px] text-gray-500 overflow-auto max-h-40">
                                {error.stack}
                            </pre>
                        </details>
                    )}
                </div>

                <p className="text-gray-400 text-sm">
                    The Transport System encountered an unrecoverable anomaly.
                    Please attempt a manual reset or return to base.
                </p>

                <div className="flex gap-4 justify-center">
                    <UniversalButton
                        variant="primary"
                        onClick={resetErrorBoundary}
                        icon={RefreshCw}
                        label="System Reset"
                    />
                    <UniversalButton
                        variant="secondary"
                        onClick={() => window.location.href = '/'}
                        icon={Home}
                        label="Return to Dashboard"
                    />
                </div>
            </div>
        </div>
    );
}
