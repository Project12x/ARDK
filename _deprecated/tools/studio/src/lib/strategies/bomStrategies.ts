
import type { ExportStrategy, ExportValidationResult } from '../../types/export';
import { db, type ProjectBOM, type InventoryItem } from '../db';
import { jsonToCsv, textToBlob } from '../../utils/exportTransformers';

// Helper type for joined data
export interface BOMExportItem {
    part_name: string;
    quantity: number;
    status: string;
    mpn?: string;
    manufacturer?: string;
    description?: string;
    inventory_id?: number;
    notes?: string;
}

async function fetchBOMData(projectId: number): Promise<BOMExportItem[]> {
    const bomItems = await db.project_bom.where('project_id').equals(projectId).toArray();
    const inventoryIds = bomItems.map(b => b.inventory_item_id).filter(Boolean) as number[];
    const inventoryItems = await db.inventory.bulkGet(inventoryIds);

    // Map ID to Item
    const invMap = new Map<number, InventoryItem>();
    inventoryItems.forEach(i => {
        if (i) invMap.set(i.id!, i);
    });

    return bomItems.map(b => {
        const inv = b.inventory_item_id ? invMap.get(b.inventory_item_id) : undefined;
        return {
            part_name: b.part_name,
            quantity: b.quantity_required,
            status: b.status,
            mpn: inv?.mpn || '',
            manufacturer: inv?.manufacturer || '',
            description: inv?.description || '',
            inventory_id: b.inventory_item_id,
            notes: b.manual_match_notes || ''
        };
    });
}

// --- Strategy 1: Standard BOM ---
export const StandardBOMStrategy: ExportStrategy<BOMExportItem> = {
    id: 'bom-standard',
    name: 'Standard BOM',
    description: 'Generic CSV list of all parts.',
    supportedFormats: [
        { id: 'csv', label: 'CSV (Excel)', extension: 'csv' },
        { id: 'json', label: 'JSON', extension: 'json' }
    ],
    getData: (context: { projectId: number }) => fetchBOMData(context.projectId),
    transform: async (data, format) => {
        if (format === 'json') {
            return textToBlob(JSON.stringify(data, null, 2), 'application/json');
        }
        return textToBlob(jsonToCsv(data, [
            { key: 'part_name', label: 'Part Name' },
            { key: 'quantity', label: 'Qty' },
            { key: 'status', label: 'Status' },
            { key: 'mpn', label: 'MPN' },
            { key: 'manufacturer', label: 'Manufacturer' },
            { key: 'notes', label: 'Notes' }
        ]), 'text/csv');
    }
};

// --- Strategy 2: DigiKey BOM ---
export const DigiKeyBOMStrategy: ExportStrategy<BOMExportItem> = {
    id: 'bom-digikey',
    name: 'DigiKey Cart Import',
    description: 'Strict format for DigiKey Bulk Upload.',
    supportedFormats: [
        { id: 'digikey-csv', label: 'DigiKey CSV', extension: 'csv', isVendorSpecific: true }
    ],
    getData: (context: { projectId: number }) => fetchBOMData(context.projectId),

    validate: (data) => {
        const invalidItems = data.filter(item => !item.mpn || item.mpn.trim() === '');
        return {
            isValid: invalidItems.length === 0,
            missingFields: ['Manufacturer Part Number (MPN)'],
            invalidItems
        };
    },

    transform: async (data, format) => {
        // DigiKey Format: "Quantity, manufacturer Part Number, Customer Reference"
        // Note: Headers might vary, checking standard bulk upload format.
        // Usually: Quantity, Part Number, Customer Reference

        const csv = jsonToCsv(data, [
            { key: 'quantity', label: 'Quantity' },
            { key: 'mpn', label: 'Manufacturer Part Number' },
            { key: 'part_name', label: 'Customer Reference' }
        ]);
        return textToBlob(csv, 'text/csv');
    }
};

// --- Strategy 3: Mouser BOM ---
export const MouserBOMStrategy: ExportStrategy<BOMExportItem> = {
    id: 'bom-mouser',
    name: 'Mouser Cart Import',
    description: 'Strict format for Mouser BOM Tool.',
    supportedFormats: [
        { id: 'mouser-csv', label: 'Mouser CSV', extension: 'csv', isVendorSpecific: true }
    ],
    getData: (context: { projectId: number }) => fetchBOMData(context.projectId),

    validate: (data) => {
        const invalidItems = data.filter(item => !item.mpn || item.mpn.trim() === '');
        return {
            isValid: invalidItems.length === 0,
            missingFields: ['Mouser/Man Part Number'],
            invalidItems
        };
    },

    transform: async (data, format) => {
        // Mouser Format: "Mouser Part Number|Manufacturer Part Number|Quantity|..."
        // We will prioritize MPN as we don't store Mouser PNs typically.

        const csv = jsonToCsv(data, [
            { key: 'mpn', label: 'Manufacturer Part Number' },
            { key: 'quantity', label: 'Quantity 1' }, // Mouser sometimes likes 'Quantity 1' header
            { key: 'part_name', label: 'Customer Part No' }
        ]);
        return textToBlob(csv, 'text/csv');
    }
};
