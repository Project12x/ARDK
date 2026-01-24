import { useState, useMemo, useRef } from 'react';
import {
    useReactTable,
    getCoreRowModel,
    getSortedRowModel,
    flexRender,
    createColumnHelper,
    type SortingState,
    type Row,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import type { InventoryItem } from '../../lib/db';
import { clsx } from 'clsx';
import { ArrowUpDown, Box, ArrowRight, GripVertical } from 'lucide-react';
import { useUIStore } from '../../store/useStore';
import { useDraggable } from '@dnd-kit/core';

interface InventoryTableProps {
    data: InventoryItem[];
    onUpdate: (id: number, updates: Partial<InventoryItem>) => void;
    onDelete: (id: number) => void;
}

const columnHelper = createColumnHelper<InventoryItem>();

export function InventoryTable({ data, onUpdate, onDelete, variant = 'filament' }: InventoryTableProps & { variant?: 'filament' | 'general' }) {
    const [sorting, setSorting] = useState<SortingState>([]);
    const parentRef = useRef<HTMLDivElement>(null);
    const { addToStash } = useUIStore();

    const filamentColumns = useMemo(() => [
        columnHelper.accessor('name', {
            header: ({ column }) => (
                <button
                    className="flex items-center gap-1 hover:text-white"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    NAME
                    <ArrowUpDown size={12} className="opacity-50" />
                </button>
            ),
            cell: info => <span className="font-bold text-white">{info.getValue()}</span>,
        }),
        columnHelper.accessor('properties.brand', {
            header: 'BRAND',
            cell: info => <span className="text-gray-400 uppercase text-[10px] tracking-wider">{info.getValue() || '-'}</span>,
        }),
        columnHelper.accessor('properties.material', {
            header: 'MATERIAL',
            cell: info => (
                <span className={clsx(
                    "text-[10px] font-bold px-1.5 py-0.5 rounded border uppercase",
                    info.getValue() === 'PLA' && "text-industrial border-industrial/30 bg-industrial/10",
                    info.getValue() === 'PETG' && "text-orange-400 border-orange-500/30 bg-orange-900/10",
                    info.getValue() === 'TPU' && "text-blue-400 border-blue-500/30 bg-blue-900/10",
                    !['PLA', 'PETG', 'TPU'].includes(info.getValue() || '') && "text-gray-400 border-white/10"
                )}>
                    {info.getValue() || 'UNK'}
                </span>
            ),
        }),
        columnHelper.accessor(row => row.properties?.color_hex, {
            id: 'color',
            header: 'COLOR',
            cell: info => (
                <div className="flex items-center gap-2">
                    <div
                        className="w-4 h-4 rounded-full border border-white/20 shadow-sm"
                        style={{ backgroundColor: info.getValue() || '#333' }}
                    />
                    <span className="font-mono text-[10px] text-gray-500">{info.getValue()?.toUpperCase()}</span>
                </div>
            ),
        }),
        columnHelper.accessor(row => row, { // Using row to calculate percentage
            id: 'weight',
            header: ({ column }) => (
                <button
                    className="flex items-center gap-1 hover:text-white"
                    onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                >
                    WEIGHT
                    <ArrowUpDown size={12} className="opacity-50" />
                </button>
            ),
            cell: info => {
                const item = info.getValue();
                const total = item.properties?.weight_total || 1000;
                const remaining = item.quantity || 0;
                const pct = Math.round((remaining / total) * 100);

                return (
                    <div className="flex items-center gap-2 w-32">
                        <div className="flex-1 h-2 bg-white/10 rounded-full overflow-hidden">
                            <div
                                className={clsx("h-full rounded-full transition-all",
                                    pct > 20 ? "bg-accent" : "bg-red-500"
                                )}
                                style={{ width: `${pct}%` }}
                            />
                        </div>
                        <span className="font-mono text-xs w-12 text-right">{remaining}g</span>
                    </div>
                )
            }
        }),
        columnHelper.accessor(row => row.location, {
            id: 'location',
            header: 'LOCATION',
            cell: info => (
                <div className="flex items-center gap-1 text-gray-500">
                    <Box size={12} />
                    <span className="text-xs">{info.getValue() || 'UNSORTED'}</span>
                </div>
            ),
        }),
        columnHelper.display({
            id: 'actions',
            cell: info => (
                <div className="flex gap-2 justify-end">
                    <button
                        onClick={() => addToStash({
                            id: crypto.randomUUID(),
                            originalId: info.row.original.id!,
                            type: 'inventory',
                            title: info.row.original.name,
                            subtitle: `${info.row.original.quantity} ${info.row.original.units || 'units'}`
                        })}
                        className="text-gray-500 hover:text-neon transition-colors"
                        title="Add to Transporter"
                    >
                        <ArrowRight size={14} />
                    </button>
                    <div className="w-px h-3 bg-white/10 my-auto" />
                    <button onClick={() => onUpdate(info.row.original.id!, { quantity: info.row.original.quantity + 10 })} className="text-[10px] text-gray-500 hover:text-white uppercase transition-colors">Adjust</button>
                    <button onClick={() => onDelete(info.row.original.id!)} className="text-[10px] text-gray-500 hover:text-red-500 uppercase transition-colors">Delete</button>
                </div>
            )
        })
    ], [onUpdate, onDelete, addToStash]);

    const generalColumns = useMemo(() => [
        columnHelper.accessor('name', {
            header: ({ column }) => (
                <button className="flex items-center gap-1 hover:text-white" onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}>
                    NAME <ArrowUpDown size={12} className="opacity-50" />
                </button>
            ),
            cell: info => <span className="font-bold text-white">{info.getValue()}</span>,
        }),
        columnHelper.accessor('domain', {
            header: 'KINGDOM',
            cell: info => <span className="text-gray-400 text-xs uppercase">{info.getValue() || '-'}</span>,
        }),
        columnHelper.accessor('category', {
            header: 'PHYLUM',
            cell: info => <span className="text-gray-400 text-xs uppercase">{info.getValue() || '-'}</span>,
        }),
        columnHelper.accessor('quantity', {
            header: 'QTY',
            cell: info => <span className="font-mono text-accent font-bold">{info.getValue()}</span>,
        }),
        columnHelper.accessor('units', {
            header: 'UNIT',
            cell: info => <span className="text-gray-500 text-[10px] uppercase font-mono">{info.getValue() || 'pcs'}</span>,
        }),
        columnHelper.accessor('location', {
            header: 'LOCATION',
            cell: info => (
                <div className="flex items-center gap-1 text-gray-500">
                    <Box size={12} />
                    <span className="text-xs">{info.getValue() || '-'}</span>
                </div>
            ),
        }),
        columnHelper.display({
            id: 'actions',
            cell: info => (
                <div className="flex gap-2 justify-end">
                    <button
                        onClick={() => addToStash({
                            id: crypto.randomUUID(),
                            originalId: info.row.original.id!,
                            type: 'inventory',
                            title: info.row.original.name,
                            subtitle: `${info.row.original.quantity} ${info.row.original.units || 'units'}`
                        })}
                        className="text-gray-500 hover:text-neon transition-colors"
                        title="Add to Transporter"
                    >
                        <ArrowRight size={14} />
                    </button>
                    <div className="w-px h-3 bg-white/10 my-auto" />
                    <button onClick={() => onDelete(info.row.original.id!)} className="text-[10px] text-gray-500 hover:text-red-500 uppercase transition-colors">Delete</button>
                </div>
            )
        })
    ], [onDelete, addToStash]);

    const columns = useMemo(() => variant === 'filament' ? filamentColumns : generalColumns, [variant, filamentColumns, generalColumns]);

    const table = useReactTable({
        data,
        columns,
        state: {
            sorting,
        },
        onSortingChange: setSorting,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
    });

    const { rows } = table.getRowModel();

    const rowVirtualizer = useVirtualizer({
        count: rows.length,
        getScrollElement: () => parentRef.current,
        estimateSize: () => 48, // Estimate row height
        overscan: 10,
    });

    const virtualItems = rowVirtualizer.getVirtualItems();
    const totalSize = rowVirtualizer.getTotalSize();

    const paddingTop = virtualItems.length > 0 ? virtualItems[0].start : 0;
    const paddingBottom = virtualItems.length > 0 ? totalSize - virtualItems[virtualItems.length - 1].end : 0;

    return (
        <div
            ref={parentRef}
            className="rounded-xl border border-white/10 overflow-auto bg-black/40 backdrop-blur-sm max-h-[800px]" // Fixed height container for virtualization
        >
            <table className="w-full text-left border-collapse">
                <thead className="bg-black/80 backdrop-blur text-[10px] text-gray-500 uppercase font-mono tracking-wider sticky top-0 z-10">
                    {table.getHeaderGroups().map(headerGroup => (
                        <tr key={headerGroup.id}>
                            <th className="p-3 border-b border-white/10 w-8"></th>
                            {headerGroup.headers.map(header => (
                                <th key={header.id} className="p-3 border-b border-white/10 font-bold select-none cursor-pointer hover:bg-white/5 transition-colors">
                                    {header.isPlaceholder
                                        ? null
                                        : flexRender(
                                            header.column.columnDef.header,
                                            header.getContext()
                                        )}
                                </th>
                            ))}
                        </tr>
                    ))}
                </thead>
                <tbody className="divide-y divide-white/5">
                    {paddingTop > 0 && (
                        <tr>
                            <td style={{ height: `${paddingTop}px` }} />
                        </tr>
                    )}
                    {virtualItems.map(virtualRow => {
                        const row = rows[virtualRow.index];
                        return (
                            <DraggableRow key={row.id} row={row} />
                        );
                    })}
                    {paddingBottom > 0 && (
                        <tr>
                            <td style={{ height: `${paddingBottom}px` }} />
                        </tr>
                    )}
                </tbody>
            </table>
            {data.length === 0 && (
                <div className="p-8 text-center text-gray-600 font-mono text-xs uppercase">
                    No items found in Bunker logic.
                </div>
            )}
        </div>
    );
}

// Draggable row component for inventory items
function DraggableRow({ row }: { row: Row<InventoryItem> }) {
    const item = row.original;

    const { attributes, listeners, setNodeRef, transform, isDragging } = useDraggable({
        id: `inventory-row-${item.id}`,
        data: {
            type: 'inventory-item',
            item: {
                id: item.id,
                name: item.name,
                quantity: item.quantity,
                units: item.units,
            }
        }
    });

    const style = transform ? {
        transform: `translate3d(${transform.x}px, ${transform.y}px, 0)`,
        zIndex: 1000,
    } : undefined;

    return (
        <tr
            ref={setNodeRef}
            style={style}
            className={clsx(
                "hover:bg-white/5 transition-colors group",
                isDragging && "opacity-50 bg-neon/10"
            )}
        >
            {/* Drag Handle Column */}
            <td className="p-2 w-8">
                <div
                    {...listeners}
                    {...attributes}
                    className="cursor-grab active:cursor-grabbing p-1 rounded hover:bg-white/10 text-gray-600 hover:text-neon transition-colors"
                    title="Drag to Transporter"
                >
                    <GripVertical size={14} />
                </div>
            </td>
            {row.getVisibleCells().map(cell => (
                <td key={cell.id} className="p-3 text-sm">
                    {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
            ))}
        </tr>
    );
}
