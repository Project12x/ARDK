import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Vendor } from '../../lib/db';
import { Button } from '../ui/Button';
import { Card } from '../ui/Card';
import { Trash2, Plus, Globe, Key } from 'lucide-react';
import { toast } from 'sonner';

export function VendorManager() {
    const vendors = useLiveQuery(() => db.vendors.toArray());
    const [isCreating, setIsCreating] = useState(false);

    const handleDelete = async (id: number) => {
        if (confirm('Delete this vendor? Purchase history may lose association.')) {
            await db.vendors.delete(id);
        }
    };

    return (
        <div className="space-y-6">
            <div className="flex justify-between items-center">
                <h3 className="font-bold text-white text-lg">Preferred Vendors</h3>
                <Button size="sm" onClick={() => setIsCreating(true)} className="bg-white/10 hover:bg-white/20">
                    <Plus size={16} className="mr-2" /> Add Vendor
                </Button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {vendors?.map(vendor => (
                    <Card key={vendor.id} className="p-4 bg-white/5 border-white/10 flex justify-between items-start">
                        <div>
                            <div className="font-bold text-white flex items-center gap-2">
                                {vendor.name}
                                {vendor.api_integration !== 'none' && vendor.api_integration && (
                                    <span className="text-[10px] bg-accent/20 text-accent px-1.5 py-0.5 rounded uppercase font-mono">
                                        {vendor.api_integration} API
                                    </span>
                                )}
                            </div>
                            {vendor.website && (
                                <a href={vendor.website} target="_blank" rel="noreferrer" className="text-xs text-gray-500 hover:text-accent flex items-center gap-1 mt-1">
                                    <Globe size={12} /> {new URL(vendor.website).hostname}
                                </a>
                            )}
                        </div>
                        <Button variant="ghost" size="sm" onClick={() => handleDelete(vendor.id!)} className="text-gray-600 hover:text-red-400">
                            <Trash2 size={14} />
                        </Button>
                    </Card>
                ))}

                {vendors?.length === 0 && (
                    <div className="col-span-2 text-center py-8 border border-dashed border-white/10 rounded-xl text-gray-500 text-sm">
                        No vendors configured. Add your frequent suppliers (e.g. Digikey, McMaster).
                    </div>
                )}
            </div>

            {isCreating && <CreateVendorModal onClose={() => setIsCreating(false)} />}
        </div>
    );
}

function CreateVendorModal({ onClose }: { onClose: () => void }) {
    const [name, setName] = useState('');
    const [website, setWebsite] = useState('');
    const [integration, setIntegration] = useState<Vendor['api_integration']>('none');

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        await db.vendors.add({
            name,
            website: website || undefined,
            api_integration: integration
        });
        toast.success("Vendor added");
        onClose();
    };

    return (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
            <div className="bg-neutral-900 border border-white/20 rounded-xl w-full max-w-md p-6">
                <h2 className="text-xl font-bold text-white mb-6">Add Vendor</h2>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <div>
                        <label className="text-xs uppercase font-bold text-gray-500">Name</label>
                        <input value={name} onChange={e => setName(e.target.value)} className="w-full bg-black border border-white/10 rounded p-2 text-white" autoFocus required />
                    </div>
                    <div>
                        <label className="text-xs uppercase font-bold text-gray-500">Website</label>
                        <input value={website} onChange={e => setWebsite(e.target.value)} className="w-full bg-black border border-white/10 rounded p-2 text-white" placeholder="https://..." />
                    </div>
                    <div>
                        <label className="text-xs uppercase font-bold text-gray-500">API Integration</label>
                        <select
                            value={integration}
                            onChange={(e) => setIntegration(e.target.value as any)}
                            className="w-full bg-black border border-white/10 rounded p-2 text-white"
                        >
                            <option value="none">None</option>
                            <option value="digikey">Digikey (Requires API Key)</option>
                            <option value="octopart">Octopart (Requires API Key)</option>
                        </select>
                        {integration !== 'none' && (
                            <p className="text-[10px] text-yellow-500 mt-1 flex items-center gap-1">
                                <Key size={10} /> API keys are managed in Settings.
                            </p>
                        )}
                    </div>
                    <div className="flex justify-end gap-3 mt-6">
                        <Button type="button" variant="ghost" onClick={onClose}>Cancel</Button>
                        <Button type="submit" disabled={!name}>Save Vendor</Button>
                    </div>
                </form>
            </div>
        </div>
    );
}
