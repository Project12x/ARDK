import {
    useReactTable,
    getCoreRowModel,
    flexRender,
    getSortedRowModel,
    getFilteredRowModel,
} from '@tanstack/react-table';
import type { ColumnDef, SortingState } from '@tanstack/react-table';
import { useState } from 'react';
import type { UniversalEntity } from '../../lib/universal/types';
import { ArrowUpDown, Search } from 'lucide-react';

interface UniversalTableProps {
    data: UniversalEntity[];
    columns?: ColumnDef<UniversalEntity>[];
    onRowClick?: (entity: UniversalEntity) => void;
    className?: string;
    searchable?: boolean;
}

export function UniversalTable({
    data,
    columns: userColumns,
    onRowClick,
    className,
    searchable = true
}: UniversalTableProps) {
    const [sorting, setSorting] = useState<SortingState>([]);
    const [globalFilter, setGlobalFilter] = useState('');

    // Default columns if none provided
    const defaultColumns: ColumnDef<UniversalEntity>[] = [
        {
            accessorKey: 'title',
            header: ({ column }) => {
                return (
                    <button
                        className="flex items-center gap-1 hover:text-white"
                        onClick={() => column.toggleSorting(column.getIsSorted() === 'asc')}
                    >
                        Title
                        <ArrowUpDown size={12} className="opacity-50" />
                    </button>
                )
            },
            cell: ({ row }) => (
                <div className="font-bold flex items-center gap-2">
                    {/* Placeholder for icon if we had it easily accessible in entity root */}
                    {row.original.title}
                </div>
            )
        },
        {
            accessorKey: 'type',
            header: 'Type',
            cell: ({ getValue }) => <span className="px-2 py-0.5 rounded-full bg-white/5 text-[10px] uppercase tracking-wider text-gray-400">{getValue() as string}</span>
        },
        {
            accessorKey: 'status',
            header: 'Status',
            cell: ({ getValue }) => {
                const status = getValue() as string;
                if (!status) return <span className="text-gray-600">-</span>;
                return <span className="capitalize text-gray-300">{status.replace(/_/g, ' ')}</span>
            }
        },
        {
            accessorKey: 'priority',
            header: 'Priority',
            cell: ({ getValue }) => {
                const priority = getValue() as string;
                if (!priority) return null;
                const colors: Record<string, string> = {
                    high: 'text-red-400',
                    critical: 'text-red-500 font-bold',
                    medium: 'text-yellow-400',
                    low: 'text-blue-400'
                };
                return <span className={colors[priority.toLowerCase()] || 'text-gray-400'}>{priority}</span>
            }
        }
    ];

    const table = useReactTable({
        data,
        columns: userColumns || defaultColumns,
        getCoreRowModel: getCoreRowModel(),
        getSortedRowModel: getSortedRowModel(),
        getFilteredRowModel: getFilteredRowModel(),
        state: {
            sorting,
            globalFilter,
        },
        onSortingChange: setSorting,
        onGlobalFilterChange: setGlobalFilter,
    });

    return (
        <div className={`space-y-4 ${className}`}>
            {/* Search Bar */}
            {searchable && (
                <div className="relative">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500 h-4 w-4" />
                    <input
                        value={globalFilter ?? ''}
                        onChange={e => setGlobalFilter(e.target.value)}
                        className="bg-black/20 border border-white/10 rounded-lg pl-9 pr-4 py-2 text-sm w-full focus:outline-none focus:border-accent/50 transition-colors placeholder:text-gray-600"
                        placeholder="Filter items..."
                    />
                </div>
            )}

            {/* Table */}
            <div className="rounded-xl border border-white/5 overflow-hidden">
                <table className="w-full text-left bg-black/20 backdrop-blur-sm">
                    <thead className="bg-white/5 text-xs uppercase text-gray-500 font-medium">
                        {table.getHeaderGroups().map(headerGroup => (
                            <tr key={headerGroup.id}>
                                {headerGroup.headers.map(header => (
                                    <th key={header.id} className="px-4 py-3 font-medium select-none">
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
                    <tbody className="divide-y divide-white/5 text-sm text-gray-300">
                        {table.getRowModel().rows.length > 0 ? (
                            table.getRowModel().rows.map(row => (
                                <tr
                                    key={row.id}
                                    onClick={() => onRowClick?.(row.original)}
                                    className={`
                                        group transition-colors 
                                        ${onRowClick ? 'cursor-pointer hover:bg-white/5' : ''}
                                    `}
                                >
                                    {row.getVisibleCells().map(cell => (
                                        <td key={cell.id} className="px-4 py-3">
                                            {flexRender(cell.column.columnDef.cell, cell.getContext())}
                                        </td>
                                    ))}
                                </tr>
                            ))
                        ) : (
                            <tr>
                                <td colSpan={defaultColumns.length} className="px-4 py-8 text-center text-gray-500">
                                    No items found.
                                </td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <div className="text-xs text-gray-500 text-right px-2">
                Showing {table.getRowModel().rows.length} of {data.length} items
            </div>
        </div>
    );
}
