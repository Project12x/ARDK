import { useDraggable } from '@dnd-kit/core';
import type { UniversalEntity, UniversalDragPayload } from './types';

export function useUniversalDnd(entity: UniversalEntity, origin: UniversalDragPayload['origin'] = 'grid', disabled = false) {
    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `universal-${entity.type}-${entity.id}`,
        data: {
            type: 'universal-card',
            entity,
            origin
        } as UniversalDragPayload,
        disabled
    });

    return {
        attributes,
        listeners,
        setNodeRef,
        transform,
        isDragging
    };
}
