import { useState, useEffect } from 'react';
import { partSearch, type PartSearchResult } from '../../services/PartSearchService';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Search, Loader2, Check, AlertTriangle, ExternalLink, Package, X } from 'lucide-react';
import clsx from 'clsx';

interface EnrichmentModalProps {
    isOpen: boolean;
    onClose: () => void;
    initialQuery: string;
    onSelect: (part: PartSearchResult) => void;
}

export function EnrichmentModal({ isOpen, onClose, initialQuery, onSelect }: EnrichmentModalProps) {
    const [query, setQuery] = useState(initialQuery);
    const [results, setResults] = useState<PartSearchResult[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState('');
    const [provider, setProvider] = useState('digikey');

    useEffect(() => {
        if (isOpen && initialQuery) {
            setQuery(initialQuery);
            handleSearch(initialQuery);
        }
    }, [isOpen, initialQuery]);

    const handleSearch = async (q: string) => {
        if (!q.trim()) return;
        setLoading(true);
        setError('');
        try {
            const res = await partSearch.search(q, provider);
            setResults(res);
            if (res.length === 0) setError('No parts found. Try a different query or provider.');
        } catch (e) {
            console.error(e);
            setError('Search failed. Check API configuration.');
        } finally {
            setLoading(false);
        }
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[100] flex items-center justify-center p-4">
            <div className="absolute inset-0 bg-black/80 backdrop-blur-sm" onClick={onClose} />

            <div className="relative w-full max-w-4xl bg-neutral-900 border border-white/10 rounded-xl shadow-2xl flex flex-col max-h-[90vh] animate-in fade-in zoom-in-95">
                {/* Header */}
                <div className="p-4 border-b border-white/10 flex justify-between items-center bg-black/40 rounded-t-xl">
                    <h2 className="text-lg font-bold text-white flex items-center gap-2">
                        <Search size={18} className="text-accent" />
                        PART SEARCH & ENRICHMENT
                    </h2>
                    <div className="flex items-center gap-3">
                        <select
                            className="bg-black border border-white/20 text-xs rounded px-2 py-1 text-gray-400 focus:border-accent outline-none"
                            value={provider}
                            onChange={(e) => setProvider(e.target.value)}
                        >
                            <option value="digikey">DigiKey (Free Tier)</option>
                            <option value="trustedparts">TrustedParts (Free)</option>
                        </select>
                        <button onClick={onClose} className="text-gray-500 hover:text-white"><X size={20} /></button>
                    </div>
                </div>

                {/* Search Bar */}
                <div className="p-4 bg-white/5 border-b border-white/5 flex gap-2">
                    <div className="relative flex-1">
                        <Search size={16} className="absolute left-3 top-3 text-gray-500" />
                        <Input
                            value={query}
                            onChange={(e) => setQuery(e.target.value)}
                            onKeyDown={(e) => e.key === 'Enter' && handleSearch(query)}
                            className="pl-10"
                            placeholder="Search by MPN, Keyword, or Description..."
                            autoFocus
                        />
                    </div>
                    <Button onClick={() => handleSearch(query)} disabled={loading} className="w-24">
                        {loading ? <Loader2 size={16} className="animate-spin" /> : 'SEARCH'}
                    </Button>
                </div>

                {/* Results List */}
                <div className="flex-1 overflow-y-auto p-4 space-y-2 bg-neutral-900">
                    {error && (
                        <div className="p-4 text-center text-red-500 bg-red-900/10 border border-red-900/30 rounded">
                            {error}
                        </div>
                    )}

                    {results.map((part) => (
                        <div
                            key={part.mpn}
                            className="group flex items-start gap-4 p-4 bg-black/40 border border-white/5 rounded-lg hover:border-accent hover:bg-accent/5 transition-all cursor-default"
                        >
                            {/* Image / Thumbnail */}
                            <div className="w-16 h-16 bg-white rounded flex items-center justify-center overflow-hidden shrink-0">
                                {part.image_url ? (
                                    <img src={part.image_url} alt={part.mpn} className="w-full h-full object-contain" />
                                ) : (
                                    <Package size={24} className="text-gray-400" />
                                )}
                            </div>

                            {/* Details */}
                            <div className="flex-1 min-w-0">
                                <div className="flex justify-between items-start">
                                    <div>
                                        <h4 className="text-accent font-mono font-bold text-sm tracking-tight">{part.mpn}</h4>
                                        <p className="text-xs text-gray-400 font-bold uppercase mb-1">{part.manufacturer}</p>
                                    </div>
                                    <div className="text-right">
                                        {part.market_data.price_breaks[0] ? (
                                            <div className="text-lg font-mono text-green-400">
                                                ${part.market_data.price_breaks[0].price.toFixed(4)}
                                            </div>
                                        ) : (
                                            <span className="text-gray-600 text-xs italic">No Price</span>
                                        )}
                                    </div>
                                </div>

                                <p className="text-sm text-gray-300 line-clamp-2 mb-2 leading-relaxed">
                                    {part.description}
                                </p>

                                {/* Specs Grid */}
                                <div className="flex flex-wrap gap-2 mb-3">
                                    {Object.entries(part.specs).slice(0, 4).map(([k, v]) => (
                                        <span key={k} className="text-[10px] bg-white/5 border border-white/10 px-1.5 py-0.5 rounded text-gray-400">
                                            <strong className="text-gray-500 mr-1">{k}:</strong>{v}
                                        </span>
                                    ))}
                                </div>

                                <div className="flex justify-between items-center mt-2 pt-2 border-t border-white/5">
                                    <div className="flex items-center gap-3 text-xs font-mono">
                                        <span className={clsx(
                                            "flex items-center gap-1",
                                            part.market_data.availability > 0 ? "text-green-500" : "text-red-500"
                                        )}>
                                            {part.market_data.availability > 0 ? <Check size={12} /> : <AlertTriangle size={12} />}
                                            Stock: {part.market_data.availability.toLocaleString()}
                                        </span>
                                        {part.datasheet_url && (
                                            <a href={part.datasheet_url} target="_blank" rel="noreferrer" className="flex items-center gap-1 text-blue-400 hover:text-blue-300">
                                                <ExternalLink size={12} /> Datasheet
                                            </a>
                                        )}
                                    </div>

                                    <Button
                                        size="sm"
                                        className="bg-accent text-black hover:bg-white font-bold"
                                        onClick={() => onSelect(part)}
                                    >
                                        SELECT PART
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ))}

                    {results.length === 0 && !loading && !error && (
                        <div className="h-40 flex flex-col items-center justify-center text-gray-600 space-y-2">
                            <Search size={32} className="opacity-20" />
                            <p className="text-sm">Search via {provider === 'digikey' ? 'DigiKey' : 'TrustedParts'} to find matches.</p>
                        </div>
                    )}
                </div>

                <div className="p-4 border-t border-white/10 bg-black/40 flex justify-end">
                    <Button variant="ghost" onClick={onClose}>CANCEL</Button>
                </div>
            </div>
        </div>
    );
}
