import { Component, type ErrorInfo, type ReactNode } from 'react';
import { AlertTriangle } from 'lucide-react';

interface Props {
    children: ReactNode;
    fallback?: ReactNode;
    name?: string;
}

interface State {
    hasError: boolean;
    error: Error | null;
}

export class ErrorBoundary extends Component<Props, State> {
    public state: State = {
        hasError: false,
        error: null
    };

    public static getDerivedStateFromError(error: Error): State {
        return { hasError: true, error };
    }

    public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
        console.error(`Uncaught error in ${this.props.name || 'component'}:`, error, errorInfo);
    }

    public render() {
        if (this.state.hasError) {
            if (this.props.fallback) {
                return this.props.fallback;
            }

            return (
                <div className="p-4 border border-red-500/30 bg-red-500/10 rounded-lg flex items-start gap-3">
                    <AlertTriangle className="text-red-500 shrink-0 mt-0.5" size={18} />
                    <div>
                        <h3 className="text-sm font-bold text-red-500 uppercase tracking-wider mb-1">
                            {this.props.name || 'Component'} Failure
                        </h3>
                        <p className="text-xs text-red-300 font-mono">
                            {this.state.error?.message || 'Unknown error occurred.'}
                        </p>
                    </div>
                </div>
            );
        }

        return this.props.children;
    }
}
