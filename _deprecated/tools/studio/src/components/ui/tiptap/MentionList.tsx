
import { forwardRef, useImperativeHandle, useRef, useState } from 'react';
import clsx from 'clsx';
import { CheckSquare, FileText, Folder, Package, Wrench } from 'lucide-react';

 
export const MentionList = forwardRef((props: any, ref) => {
    const [selectedIndex, setSelectedIndex] = useState(0);

    const selectItem = (index: number) => {
        const item = props.items[index];
        if (item) {
            props.command({ id: item.id || item.title, label: item.title });
        }
    };

    const upHandler = () => {
        setSelectedIndex((selectedIndex + props.items.length - 1) % props.items.length);
    };

    const downHandler = () => {
        setSelectedIndex((selectedIndex + 1) % props.items.length);
    };

    const enterHandler = () => {
        selectItem(selectedIndex);
    };

    // Reset selection when items change - use ref to track previous length
    const prevItemsLengthRef = useRef(props.items?.length ?? 0);
    if (props.items?.length !== prevItemsLengthRef.current) {
        prevItemsLengthRef.current = props.items?.length ?? 0;
        if (selectedIndex !== 0) {
            // Deferred to avoid sync setState in render - schedule for next tick
            queueMicrotask(() => setSelectedIndex(0));
        }
    }

    useImperativeHandle(ref, () => ({
        onKeyDown: ({ event }: { event: KeyboardEvent }) => {
            if (event.key === 'ArrowUp') {
                upHandler();
                return true;
            }
            if (event.key === 'ArrowDown') {
                downHandler();
                return true;
            }
            if (event.key === 'Enter') {
                enterHandler();
                return true;
            }
            return false;
        },
    }));

    if (!props.items?.length) {
        return null;
    }

    return (
        <div className="bg-neutral-900 border border-white/20 rounded-lg shadow-xl overflow-hidden min-w-[200px] flex flex-col z-[9999]">
            { }
            {props.items.map((item: any, index: number) => (
                <button
                    className={clsx(
                        "flex items-center gap-2 px-3 py-2 text-sm text-left transition-colors font-mono",
                        index === selectedIndex ? "bg-accent/20 text-accent" : "text-gray-300 hover:bg-white/5"
                    )}
                    key={index}
                    onClick={() => selectItem(index)}
                >
                    {item.type === 'project' && <Folder size={14} />}
                    {item.type === 'task' && <CheckSquare size={14} />}
                    {item.type === 'inventory' && <Package size={14} />}
                    {item.type === 'tool' && <Wrench size={14} />}
                    {(item.type === 'note' || !item.type) && <FileText size={14} />}

                    <span className="truncate max-w-[200px]">{item.title}</span>
                </button>
            ))}
        </div>
    );
});

MentionList.displayName = 'MentionList';
