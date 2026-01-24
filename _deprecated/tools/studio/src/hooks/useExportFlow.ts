import { useState, useCallback } from 'react';
import type { ExportStrategy } from '../types/export';

export function useExportFlow<T>() {
    const [isExportOpen, setIsExportOpen] = useState(false);
    const [activeContext, setActiveContext] = useState<any>(undefined);

    const openExport = useCallback((context?: any) => {
        setActiveContext(context);
        setIsExportOpen(true);
    }, []);

    const closeExport = useCallback(() => {
        setIsExportOpen(false);
        setActiveContext(undefined);
    }, []);

    return {
        isExportOpen,
        openExport,
        closeExport,
        exportContext: activeContext
    };
}
