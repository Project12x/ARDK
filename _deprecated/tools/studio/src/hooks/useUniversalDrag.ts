

import { useCallback } from 'react';

export type DraggableType = 'project' | 'goal' | 'routine' | 'task' | 'inventory' | 'asset';

export function useUniversalDrag(type: DraggableType, id: number | string) {
    const handleDragStart = useCallback((e: React.DragEvent) => {
        e.dataTransfer.setData(`application/${type}-id`, String(id));
        e.dataTransfer.effectAllowed = 'copy';
        // Optional: Custom Drag Image or other setup
    }, [type, id]);

    return {
        draggable: true,
        onDragStart: handleDragStart
    };
}
