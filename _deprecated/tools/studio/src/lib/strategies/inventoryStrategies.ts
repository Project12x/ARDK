
import type { ExportStrategy } from '../../types/export';
import { db, type InventoryItem } from '../db';
import { jsonToCsv, textToBlob } from '../../utils/exportTransformers';

async function fetchInventory(): Promise<InventoryItem[]> {
    return await db.inventory.toArray();
}

export const StandardInventoryStrategy: ExportStrategy<InventoryItem> = {
    id: 'inventory-standard',
    name: 'Full Inventory Backup',
    description: 'Exports the entire inventory database.',
    supportedFormats: [
        { id: 'csv', label: 'CSV (Spreadsheet)', extension: 'csv' },
        { id: 'json', label: 'JSON (Full Data)', extension: 'json' }
    ],
    getData: () => fetchInventory(),

    transform: async (data, format) => {
        if (format === 'json') {
            return textToBlob(JSON.stringify(data, null, 2), 'application/json');
        }

        return textToBlob(jsonToCsv(data, [
            { key: 'name', label: 'Name' },
            { key: 'category', label: 'Category' },
            { key: 'quantity', label: 'Qty' },
            { key: 'location', label: 'Location' },
            { key: 'mpn', label: 'MPN' },
            { key: 'manufacturer', label: 'Manufacturer' },
            { key: 'description', label: 'Description' }
        ]), 'text/csv');
    }
};
