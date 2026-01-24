import { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type InventoryItem } from '../lib/db';
import { Card } from '../components/ui/Card';
import { Button } from '../components/ui/Button';
import { Input } from '../components/ui/Input';
import { Plus, Folder, Package, Layers, Box, LayoutGrid, List, Globe, ShoppingCart, Wrench, Sparkles } from 'lucide-react';
import clsx from 'clsx';
import { InventoryIngestModal } from '../components/InventoryIngestModal';
import { FilamentBunker } from '../components/inventory/FilamentBunker';
import { CategorizedInventoryView } from '../components/inventory/CategorizedInventoryView';
import { InventoryItemCard } from '../components/inventory/InventoryItemCard';
import { PurchaseQueuePage } from './PurchaseQueuePage';
import { LabelGeneratorModal } from '../components/printing/LabelGenerator'; // Import Modal
import { useExportFlow } from '../hooks/useExportFlow';
import { ExportDialog } from '../components/ui/ExportComponents/ExportDialog';
import { StandardInventoryStrategy } from '../lib/strategies/inventoryStrategies';
import { Download } from 'lucide-react';
import { ResponsiveTabs } from '../components/ui/ResponsiveTabs';

export function InventoryPage() {
    const [searchParams, setSearchParams] = useSearchParams();
    const initialTab = (searchParams.get('tab') as 'part' | 'tool' | 'consumable' | 'filament' | 'global' | 'purchasing') || 'global';
    const [activeTab, setActiveTab] = useState<'part' | 'tool' | 'consumable' | 'filament' | 'global' | 'purchasing'>(initialTab);
    const [viewMode, setViewMode] = useState<'grid' | 'table'>('grid');
    const [printQueue, setPrintQueue] = useState<InventoryItem[]>([]); // Print Queue State

    useEffect(() => {
        setSearchParams(prev => {
            prev.set('tab', activeTab);
            return prev;
        });
    }, [activeTab, setSearchParams]);
    useEffect(() => {
        setSearchParams(prev => {
            prev.set('tab', activeTab);
            return prev;
        });
    }, [activeTab, setSearchParams]);

    const inventory = useLiveQuery(() => {
        // Optimization: Don't fetch global inventory if we are in a mode that handles its own data fetching
        if (activeTab === 'purchasing' || activeTab === 'filament') return [];
        return db.inventory.toArray();
    }, [activeTab]);

    const [isAdding, setIsAdding] = useState(false);
    const [isIngesting, setIsIngesting] = useState(false);
    const { isExportOpen, openExport, closeExport, exportContext } = useExportFlow();

    // Add Form State
    const [newItem, setNewItem] = useState({
        name: '',
        quantity: '',
        units: '',
        category: '',
        domain: '',
        location: '',
        cost: ''
    });

    const currentInventory = inventory?.filter(i => {
        if (activeTab === 'global') return true;

        if (activeTab === 'purchasing') return false; // Handled separately

        return (i.type || 'part') === activeTab;
    }) || [];

    // Grouping Logic: Kingdom(Domain) -> Phylum(Category) -> Items
    const inventoryByKingdom = currentInventory.reduce((acc, item) => {
        const kingdom = item.domain || 'Unsorted';
        const phylum = item.category || 'Misc';

        if (!acc[kingdom]) acc[kingdom] = {};
        if (!acc[kingdom][phylum]) acc[kingdom][phylum] = [];

        acc[kingdom][phylum].push(item);
        return acc;
    }, {} as Record<string, Record<string, InventoryItem[]>>);

    const handleAdd = async () => {
        if (!newItem.name) return;
        await db.inventory.add({
            name: newItem.name,
            quantity: newItem.quantity === '' ? 0 : Number(newItem.quantity),
            units: newItem.units,
            category: newItem.category || 'Misc',
            domain: newItem.domain || 'Unsorted',
            location: newItem.location,
            unit_cost: newItem.cost ? Number(newItem.cost) : undefined,
            type: (activeTab === 'global' || activeTab === 'purchasing') ? 'part' : activeTab === 'filament' ? 'consumable' : activeTab,
            min_stock: 0
        });
        setNewItem({ name: '', quantity: '1', units: '', category: '', domain: '', location: '', cost: '' });
        setIsAdding(false);
    };

    // Collapsible State: formatted as "Kingdom" or "Kingdom:Phylum"
    const [collapsedSections, setCollapsedSections] = useState<Record<string, boolean>>({});

    const toggleSection = (key: string) => {
        setCollapsedSections(prev => ({ ...prev, [key]: !prev[key] }));
    };

    return (
        <div className="space-y-8 pb-20">
            {/* Header with Tabs */}
            {/* Header with Tabs */}
            <div className="flex flex-col xl:flex-row justify-between items-start xl:items-center gap-6 border-b border-white/10 pb-6">
                <div>
                    <h2 className="text-3xl font-black text-white uppercase tracking-tighter flex items-center gap-3">
                        {activeTab === 'part' ? <Package className="text-accent" /> :
                            activeTab === 'tool' ? <Wrench className="text-accent" /> :
                                activeTab === 'global' ? <Globe className="text-accent" /> :
                                    <Layers className="text-accent" />}
                        {activeTab === 'global' ? 'Global Inventory' : 'Categorized Inventory'}
                    </h2>
                    <p className="text-gray-500 font-mono text-sm mt-1">
                        {activeTab === 'part' ? 'COMPONENTS & HARDWARE' :
                            activeTab === 'tool' ? 'TOOLS & EQUIPMENT' :
                                activeTab === 'global' ? 'MASTER LIST VIEW' :
                                    activeTab === 'purchasing' ? 'PROCUREMENT & VENDORS' :
                                        'CONSUMABLES & CHEMICALS'}
                    </p>
                </div>

                <div className="flex flex-wrap gap-4 items-center">
                    <ResponsiveTabs
                        activeId={activeTab}
                        onChange={(id) => setActiveTab(id as any)}
                        items={[
                            { id: 'global', label: 'Global', icon: Globe },
                            { id: 'part', label: 'Parts', icon: Package },
                            { id: 'consumable', label: 'Consumables', icon: Layers },
                            { id: 'tool', label: 'Tools', icon: Wrench },
                            { id: 'filament', label: 'Filament', icon: Box },
                            { id: 'purchasing', label: 'Purchasing', icon: ShoppingCart },
                        ]}
                    />

                    <div className="h-6 w-px bg-white/10 mx-1 hidden xl:block" />

                    {/* View Toggles */}
                    <div className="flex bg-black p-0.5 rounded border border-white/10">
                        <button onClick={() => setViewMode('grid')} className={clsx("p-1.5 rounded transition-colors", viewMode === 'grid' ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300")}>
                            <LayoutGrid size={16} />
                        </button>
                        <button onClick={() => setViewMode('table')} className={clsx("p-1.5 rounded transition-colors", viewMode === 'table' ? "bg-white/10 text-white shadow-sm" : "text-gray-500 hover:text-gray-300")}>
                            <List size={16} />
                        </button>
                    </div>

                    <div className="h-6 w-px bg-white/10 mx-1 hidden xl:block" />

                    <div className="flex gap-2">
                        <Button onClick={() => setIsAdding(!isAdding)} size="sm">
                            <Plus size={16} className="mr-2" />
                            Manual
                        </Button>
                        <Button onClick={() => setIsIngesting(true)} size="sm" className="bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 border-none text-white">
                            <Sparkles size={16} className="mr-2" />
                            AI Ingest
                        </Button>
                        <Button onClick={() => openExport({})} size="sm" className="bg-white/5 text-white border-white/10 hover:bg-white/10">
                            <Download size={16} className="mr-2" />
                            Export
                        </Button>
                    </div>
                </div>
            </div>

            <InventoryIngestModal isOpen={isIngesting} onClose={() => setIsIngesting(false)} />

            {isAdding && (
                <Card title={`New ${activeTab === 'part' ? 'Part' : 'Tool'}`} className="animate-in fade-in slide-in-from-top-4 duration-300 border-accent/20">
                    <div className="grid grid-cols-1 md:grid-cols-6 gap-4 items-end">
                        <div className="md:col-span-2">
                            <Input label="Name" value={newItem.name} onChange={e => setNewItem({ ...newItem, name: e.target.value })} autoFocus />
                        </div>
                        <Input label="Kingdom" placeholder={activeTab === 'part' ? "Electronics" : "Woodshop"} value={newItem.domain} onChange={e => setNewItem({ ...newItem, domain: e.target.value })} />
                        <Input label="Phylum" placeholder={activeTab === 'part' ? "Resistors" : "Saws"} value={newItem.category} onChange={e => setNewItem({ ...newItem, category: e.target.value })} />

                        <div className="flex gap-2">
                            <div className="flex-1">
                                <Input label="Qty" type="number" value={newItem.quantity} onChange={e => setNewItem({ ...newItem, quantity: e.target.value })} />
                            </div>
                            <div className="flex-1">
                                <Input label="Units" placeholder="pcs" value={newItem.units} onChange={e => setNewItem({ ...newItem, units: e.target.value })} />
                            </div>
                        </div>

                        <div className="md:col-span-1">
                            <Input label="Location" value={newItem.location} onChange={e => setNewItem({ ...newItem, location: e.target.value })} />
                        </div>
                        <div className="md:col-span-6 flex justify-end gap-2 mt-2 pt-4 border-t border-white/5">
                            <Button variant="ghost" onClick={() => setIsAdding(false)}>Cancel</Button>
                            <Button onClick={handleAdd} variant="primary">Init Item</Button>
                        </div>
                    </div>
                </Card>
            )}

            {/* Standard Inventory List */}
            {activeTab === 'purchasing' ? (
                <PurchaseQueuePage />
            ) : activeTab === 'filament' ? (
                <FilamentBunker viewMode={viewMode} />
            ) : viewMode === 'table' ? (
                <CategorizedInventoryView inventory={currentInventory} />
            ) : (
                <div className="space-y-8">
                    {Object.keys(inventoryByKingdom).length === 0 && (
                        <div className="text-center py-20 border-2 border-dashed border-white/5 rounded flex flex-col items-center gap-4 text-gray-500">
                            {activeTab === 'part' ? <Package size={48} className="opacity-20" /> : <Wrench size={48} className="opacity-20" />}
                            <p className="font-mono uppercase tracking-widest">No {activeTab}s Found</p>
                        </div>
                    )}

                    {Object.entries(inventoryByKingdom).map(([kingdom, phyla]) => (
                        <div key={kingdom} className="space-y-6">
                            {/* Kingdom Header - Collapsible */}
                            <div
                                className="flex items-center gap-3 border-b-2 border-white/10 pb-2 cursor-pointer hover:text-accent transition-colors"
                                onClick={() => toggleSection(kingdom)}
                            >
                                <span className={clsx("transition-transform", collapsedSections[kingdom] ? "-rotate-90" : "rotate-0")}>
                                    <Layers size={24} className={clsx(collapsedSections[kingdom] ? "text-gray-600" : "text-accent")} />
                                </span>
                                <h3 className={clsx("text-2xl font-black uppercase tracking-tighter", collapsedSections[kingdom] ? "text-gray-600" : "text-white")}>{kingdom}</h3>
                                <span className="text-xs font-mono text-gray-500 bg-white/5 px-2 py-0.5 rounded ml-2">KINGDOM</span>
                                <span className="ml-auto text-xs font-mono text-gray-600">{Object.values(phyla).flat().length} items</span>
                            </div>

                            {/* Kingdom Content */}
                            {!collapsedSections[kingdom] && (
                                <div className="pl-6 grid gap-6 animate-in slide-in-from-top-2 duration-200">
                                    {Object.entries(phyla).map(([phylum, items]) => (
                                        <div key={phylum} className="relative">
                                            {/* Phylum Header - Collapsible */}
                                            <div
                                                className="flex items-center gap-2 mb-4 text-gray-400 p-2 rounded transition-colors cursor-pointer hover:bg-white/5"
                                                onClick={(e) => { e.stopPropagation(); toggleSection(`${kingdom}:${phylum}`); }}
                                                onDragOver={(e) => {
                                                    e.preventDefault();
                                                    e.currentTarget.classList.add('bg-accent/10');
                                                    e.currentTarget.classList.add('text-accent');
                                                }}
                                                onDragLeave={(e) => {
                                                    e.currentTarget.classList.remove('bg-accent/10');
                                                    e.currentTarget.classList.remove('text-accent');
                                                }}
                                                onDrop={async (e) => {
                                                    e.preventDefault();
                                                    e.currentTarget.classList.remove('bg-accent/10');
                                                    e.currentTarget.classList.remove('text-accent');
                                                    const idStr = e.dataTransfer.getData('application/inventory-id');
                                                    if (idStr) {
                                                        await db.inventory.update(Number(idStr), {
                                                            domain: kingdom,
                                                            category: phylum
                                                        });
                                                    }
                                                }}
                                            >
                                                <Folder size={16} className={clsx(collapsedSections[`${kingdom}:${phylum}`] && "text-gray-600")} />
                                                <h4 className={clsx("text-sm font-bold uppercase tracking-widest", collapsedSections[`${kingdom}:${phylum}`] ? "text-gray-600" : "text-accent/80")}>{phylum}</h4>
                                                <div className="h-px bg-white/10 flex-1" />
                                                <span className="text-[10px] font-mono text-gray-600 bg-black px-1 border border-white/5 rounded">{items.length}</span>
                                            </div>

                                            {/* Items Grid */}
                                            {!collapsedSections[`${kingdom}:${phylum}`] && (
                                                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4 animate-in fade-in duration-300">
                                                    {items.map(item => (
                                                        <InventoryItemCard
                                                            key={item.id}
                                                            item={item}
                                                            onPrint={(i) => setPrintQueue([i])}
                                                        />
                                                    ))}
                                                </div>
                                            )}
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}

            {printQueue.length > 0 && (
                <LabelGeneratorModal
                    items={printQueue}
                    onClose={() => setPrintQueue([])}
                />
            )}

            <ExportDialog
                isOpen={isExportOpen}
                onClose={closeExport}
                strategies={[StandardInventoryStrategy]}
                context={exportContext}
            />
        </div>
    );
}


// InventoryItemCard moved to src/components/inventory/InventoryItemCard.tsx
