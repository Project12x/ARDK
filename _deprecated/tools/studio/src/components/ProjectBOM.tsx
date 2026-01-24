import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../lib/db';
import { Card } from './ui/Card';
import { Button } from './ui/Button';
import { Check, X, AlertTriangle, Zap, Import, Download } from 'lucide-react';
import clsx from 'clsx';
import { EnrichmentModal } from './bom/EnrichmentModal';
import { type PartSearchResult } from '../services/PartSearchService';
import { toast } from 'sonner';
import { type ProjectBOM as ProjectBOMItem } from '../lib/db';
import { findBestMatch } from '../lib/inventory-matcher';
import { useDroppable } from '@dnd-kit/core';
import { useExportFlow } from '../hooks/useExportFlow';
import { ExportDialog } from './ui/ExportComponents/ExportDialog';
import { StandardBOMStrategy, DigiKeyBOMStrategy, MouserBOMStrategy } from '../lib/strategies/bomStrategies';

interface ProjectBOMProps {
    projectId: number;
}

export function ProjectBOM({ projectId }: ProjectBOMProps) {
    const bomItems = useLiveQuery(() => db.project_bom.where({ project_id: projectId }).toArray());
    const inventory = useLiveQuery(() => db.inventory.toArray());

    const [enrichmentTarget, setEnrichmentTarget] = useState<{ id: number, name: string } | null>(null);
    const { isExportOpen, openExport, closeExport, exportContext } = useExportFlow();

    const { setNodeRef, isOver } = useDroppable({
        id: `bom-drop-zone-${projectId}`,
        data: { projectId, type: 'bom' }
    });

    // Simple matching logic (Enhanced to look for linked inventory_item_id)
    const getStockStatus = (item: ProjectBOMItem) => {
        if (item.inventory_item_id) {
            const invItem = inventory?.find(i => i.id === item.inventory_item_id);
            if (invItem) {
                return {
                    status: 'in-stock',
                    stock: invItem.quantity,
                    item: invItem
                };
            }
        }
        // Fallback to Fuzzy Matcher
        if (!inventory) return { status: 'unknown', stock: 0 };

        const matchResult = findBestMatch(item.part_name, inventory);

        if (matchResult && matchResult.score > 15) { // Confidence threshold
            return { status: 'in-stock', stock: matchResult.item.quantity, item: matchResult.item, isFuzzy: true };
        }

        return { status: 'missing', stock: 0 };
    };

    const handleEnrichSelect = async (part: PartSearchResult) => {
        if (!enrichmentTarget) return;

        try {
            // 1. Create or Find Inventory Item
            // Check if MPN exists? For now, always create new "Parts" entry or update if perfect match found?
            // Conservative: Create new entry if MPN doesn't exist
            let invId: number;
            const existingMpn = await db.inventory.where('mpn').equals(part.mpn).first();

            if (existingMpn) {
                invId = existingMpn.id!;
                // Optional: Update price/specs if older than X
                await db.inventory.update(invId, {
                    market_data: part.market_data,
                    last_api_fetch: new Date()
                });
            } else {
                invId = await db.inventory.add({
                    name: `${part.manufacturer} ${part.mpn}`,
                    category: 'Electronics', // Default
                    domain: 'Electronics',
                    description: part.description,
                    quantity: 0,
                    location: 'TBD',
                    min_stock: 0,
                    mpn: part.mpn,
                    manufacturer: part.manufacturer,
                    image_url: part.image_url,
                    specs: part.specs,
                    market_data: part.market_data,
                    last_api_fetch: new Date(),
                    supplier_api_source: part.provider as any,
                    type: 'part'
                });
            }

            // 2. Link BOM Item
            await db.project_bom.update(enrichmentTarget.id, {
                inventory_item_id: invId,
                part_name: `${part.manufacturer} ${part.mpn}`, // Rename to specific
                est_unit_cost: part.market_data.price_breaks[0]?.price || 0,
                manual_match_notes: `Matched via ${part.provider} on ${new Date().toLocaleDateString()}`
            });

            toast.success("Part Resolved & Linked!");
            setEnrichmentTarget(null);
        } catch (e) {
            console.error(e);
            toast.error("Failed to link part.");
        }
    };

    // Calculate Grand Total
    const grandTotal = bomItems?.reduce((acc, item) => acc + (item.quantity_required * (item.est_unit_cost || 0)), 0) || 0;

    return (
        <div className="space-y-6" ref={setNodeRef}>
            <Card
                title="Bill of Materials"
                className={clsx("transition-colors", isOver && "ring-2 ring-neon bg-neon/5")}
                action={
                    <Button variant="outline" size="sm" onClick={() => openExport({ projectId })}>
                        <Download size={14} className="mr-2 text-accent" />
                        Export
                    </Button>
                }
            >
                <div className="overflow-x-auto border border-border">
                    <table className="w-full text-left text-sm">
                        <thead className="bg-surface border-b border-border text-gray-400 uppercase tracking-wider font-bold">
                            <tr>
                                <th className="p-4">Component</th>
                                <th className="p-4 text-center">MPN / Spec</th>
                                <th className="p-4 text-right">Qty</th>
                                <th className="p-4 text-right">Unit Cost</th>
                                <th className="p-4 text-right">Total</th>
                                <th className="p-4">Status</th>
                                <th className="p-4 text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border">
                            {bomItems?.map((item) => {
                                const { stock, item: invItem } = getStockStatus(item);
                                const isStocked = stock >= item.quantity_required;
                                const lineTotal = item.quantity_required * (item.est_unit_cost || 0);

                                return (
                                    <tr key={item.id} className="hover:bg-white/5 transition-colors group">
                                        <td className="p-4">
                                            <div className="font-bold text-white flex items-center gap-2">
                                                {invItem?.image_url && (
                                                    <img src={invItem.image_url} className="w-6 h-6 object-contain bg-white rounded-sm" alt="" />
                                                )}
                                                {item.part_name}
                                            </div>
                                            {item.manual_match_notes && <div className="text-[10px] text-gray-500">{item.manual_match_notes}</div>}
                                        </td>
                                        <td className="p-4 text-center">
                                            {invItem?.mpn ? (
                                                <span className="font-mono text-xs text-accent bg-accent/10 px-1 rounded">
                                                    {invItem.mpn}
                                                </span>
                                            ) : (
                                                <span className="text-gray-600 italic text-xs">Generic</span>
                                            )}
                                        </td>
                                        <td className="p-4 text-right font-mono text-gray-400">{item.quantity_required}</td>
                                        <td className="p-4 text-right font-mono text-gray-400">
                                            <div className="flex items-center justify-end gap-1">
                                                <span className="text-gray-600">$</span>
                                                <input
                                                    type="number"
                                                    step="0.0001"
                                                    className="w-20 bg-transparent text-right border-b border-transparent focus:border-accent outline-none"
                                                    defaultValue={item.est_unit_cost || 0}
                                                    onBlur={(e) => db.project_bom.update(item.id!, { est_unit_cost: parseFloat(e.target.value) })}
                                                />
                                            </div>
                                        </td>
                                        <td className="p-4 text-right font-mono text-white">
                                            ${lineTotal.toFixed(2)}
                                        </td>
                                        <td className="p-4">
                                            {invItem ? (
                                                <div className={clsx("flex items-center gap-2 font-mono text-[10px] uppercase",
                                                    isStocked ? "text-green-500" : "text-red-500"
                                                )}>
                                                    {isStocked ? <Check size={12} /> : <AlertTriangle size={12} />}
                                                    {isStocked ? `IN STOCK (${stock})` : `MISSING (${item.quantity_required - stock} NEEDED)`}
                                                </div>
                                            ) : (
                                                <span className="text-gray-600 text-[10px] uppercase">UNRESOLVED</span>
                                            )}
                                        </td>
                                        <td className="p-4 text-right">
                                            <div className="flex justify-end gap-2">
                                                {!invItem && (
                                                    <Button
                                                        size="sm"
                                                        variant="outline"
                                                        className="h-7 text-[10px] border-accent/30 text-accent hover:bg-accent hover:text-black"
                                                        onClick={() => setEnrichmentTarget({ id: item.id!, name: item.part_name })}
                                                    >
                                                        <Zap size={10} className="mr-1" /> RESOLVE
                                                    </Button>
                                                )}
                                                <Button size="sm" variant="ghost" onClick={() => db.project_bom.delete(item.id!)} className="h-7 w-7 p-0">
                                                    <X size={14} />
                                                </Button>
                                            </div>
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                        {bomItems && bomItems.length > 0 && (
                            <tfoot className="bg-white/5 border-t border-border font-bold text-white">
                                <tr>
                                    <td colSpan={4} className="p-4 text-right uppercase tracking-wider text-gray-500">Total BOM Cost</td>
                                    <td className="p-4 text-right font-mono text-accent text-lg">${grandTotal.toFixed(2)}</td>
                                    <td colSpan={2}></td>
                                </tr>
                            </tfoot>
                        )}
                    </table>
                </div>
            </Card>

            <EnrichmentModal
                isOpen={!!enrichmentTarget}
                onClose={() => setEnrichmentTarget(null)}
                initialQuery={enrichmentTarget?.name || ''}
                onSelect={handleEnrichSelect}
            />

            <ExportDialog
                isOpen={isExportOpen}
                onClose={closeExport}
                strategies={[StandardBOMStrategy, DigiKeyBOMStrategy, MouserBOMStrategy]}
                context={exportContext}
            />
        </div>
    );
}

