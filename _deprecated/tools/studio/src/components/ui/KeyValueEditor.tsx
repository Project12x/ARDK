import { useState, useEffect } from 'react';
import { Button } from './Button';
import { Input } from './Input';
import { Trash2, Plus } from 'lucide-react';

interface KeyValueEditorProps {
    data: Record<string, string>;
    onChange: (data: Record<string, string>) => void;
    title?: string;
    description?: string;
    placeholderKey?: string;
    placeholderValue?: string;
    isReadOnly?: boolean;
}

export function KeyValueEditor({
    data,
    onChange,
    title,
    description,
    placeholderKey = "Key (e.g. Voltage)",
    placeholderValue = "Value (e.g. 5V)",
    isReadOnly = false
}: KeyValueEditorProps) {
    // Convert object to array of {key, value} for stable editing
    const [entries, setEntries] = useState<Array<{ key: string; value: string }>>([]);

    useEffect(() => {
        // Construct what the current local entries represents
        const currentValidObj = entries.reduce((acc, curr) => {
            if (curr.key.trim()) acc[curr.key] = curr.value;
            return acc;
        }, {} as Record<string, string>);

        // Check if incoming data is effectively different from our local valid state
        // This prevents blowing away "draft" rows (empty keys) when DB syncs unchanged data
        const incoming = data || {};
        const isDifferent = JSON.stringify(incoming) !== JSON.stringify(currentValidObj);

        if (isDifferent) {
            setEntries(Object.entries(incoming).map(([key, value]) => ({ key, value: String(value) })));
        }
    }, [data]);

    const handleUpdate = (newEntries: Array<{ key: string; value: string }>) => {
        setEntries(newEntries);
        // Debounce or direct update? Direct for now, parent handles save debounce
        const newObj = newEntries.reduce((acc, curr) => {
            if (curr.key.trim()) {
                acc[curr.key] = curr.value;
            }
            return acc;
        }, {} as Record<string, string>);
        onChange(newObj);
    };

    const addRow = () => {
        handleUpdate([...entries, { key: '', value: '' }]);
    };

    const removeRow = (index: number) => {
        const newEntries = [...entries];
        newEntries.splice(index, 1);
        handleUpdate(newEntries);
    };

    const editRow = (index: number, field: 'key' | 'value', text: string) => {
        const newEntries = [...entries];
        newEntries[index][field] = text;
        handleUpdate(newEntries);
    };

    return (
        <div className="space-y-3 border border-white/10 rounded-lg p-4 bg-white/5">
            {(title || description) && (
                <div className="mb-2">
                    {title && <h4 className="font-semibold text-white">{title}</h4>}
                    {description && <p className="text-sm text-gray-400">{description}</p>}
                </div>
            )}

            <div className="space-y-2">
                {entries.map((entry, index) => (
                    <div key={index} className="flex gap-2 items-start">
                        <div className="flex-1">
                            <Input
                                value={entry.key}
                                onChange={(e) => editRow(index, 'key', e.target.value)}
                                placeholder={placeholderKey}
                                className="bg-black/20 border-white/10 h-9 text-sm"
                                disabled={isReadOnly}
                            />
                        </div>
                        <div className="flex-1">
                            <Input
                                value={entry.value}
                                onChange={(e) => editRow(index, 'value', e.target.value)}
                                placeholder={placeholderValue}
                                className="bg-black/20 border-white/10 h-9 text-sm"
                                disabled={isReadOnly}
                            />
                        </div>
                        {!isReadOnly && (
                            <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => removeRow(index)}
                                className="text-red-400 hover:text-red-300 h-9 w-9 px-0"
                                title="Remove item"
                            >
                                <Trash2 size={16} />
                            </Button>
                        )}
                    </div>
                ))}
            </div>

            {!isReadOnly && (
                <Button
                    variant="outline"
                    size="sm"
                    onClick={addRow}
                    className="w-full border-dashed border-white/20 text-gray-400 hover:text-white hover:border-white/40 mt-2"
                >
                    <Plus size={14} className="mr-2" /> Add Field
                </Button>
            )}

            {entries.length === 0 && isReadOnly && (
                <p className="text-sm text-gray-500 italic">No data specified.</p>
            )}
        </div>
    );
}
