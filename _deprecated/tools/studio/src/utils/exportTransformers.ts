
export function jsonToCsv<T>(data: T[], columns: { key: keyof T, label: string }[]): string {
    if (!data.length) return '';

    // Header
    const header = columns.map(c => `"${c.label}"`).join(',');

    // Rows
    const rows = data.map(item => {
        return columns.map(c => {
            const val = item[c.key];
            const str = val === null || val === undefined ? '' : String(val);
            // Escape quotes
            return `"${str.replace(/"/g, '""')}"`;
        }).join(',');
    });

    return [header, ...rows].join('\n');
}

export function textToBlob(content: string, type: string = 'text/plain'): Blob {
    return new Blob([content], { type: `${type};charset=utf-8` });
}
