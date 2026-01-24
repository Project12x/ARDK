import { db } from '../lib/db';

export interface PartSearchResult {
    mpn: string;
    manufacturer: string;
    description: string;
    image_url?: string;
    datasheet_url?: string;
    specs: Record<string, string>;
    market_data: {
        currency: string;
        price_breaks: Array<{ qty: number; price: number }>;
        availability: number; // Stock count
        supplier_link: string;
        last_updated: Date;
    };
    provider: string; // 'digikey', 'trustedparts', 'manual'
}

export interface IPartProvider {
    name: string;
    search(query: string): Promise<PartSearchResult[]>;
    getPricing(mpn: string): Promise<PartSearchResult | null>;
}

export class DigiKeyProvider implements IPartProvider {
    name = 'digikey';

    // TODO: Implement OAuth flow using Client ID
    // For now, this is a stub that could fetch from a local proxy or user-provided key

    async search(query: string): Promise<PartSearchResult[]> {

        // Mock data for development
        if (query.toLowerCase().includes('resistor')) {
            return [{
                mpn: "RC0603JR-0710KL",
                manufacturer: "Yageo",
                description: "RES SMD 10K OHM 5% 1/10W 0603",
                specs: { "Resistance": "10 kOhms", "Power": "0.1W", "Tolerance": "5%" },
                market_data: {
                    currency: "USD",
                    price_breaks: [{ qty: 1, price: 0.10 }, { qty: 100, price: 0.01 }],
                    availability: 50000,
                    supplier_link: "https://www.digikey.com/...",
                    last_updated: new Date()
                },
                provider: this.name
            }];
        }
        return [];
    }

    async getPricing(_mpn: string): Promise<PartSearchResult | null> {
        // Mock
        return null;
    }
}

export class TrustedPartsProvider implements IPartProvider {
    name = 'trustedparts';

    async search(_query: string): Promise<PartSearchResult[]> {
        // TrustedParts implementation logic would go here
        return [];
    }
    async getPricing(_mpn: string): Promise<PartSearchResult | null> {
        return null;
    }
}

export class PartSearchService {
    private providers: Record<string, IPartProvider> = {};
    private defaultProvider = 'digikey';

    constructor() {
        // Register Providers
        this.providers['digikey'] = new DigiKeyProvider();
        this.providers['trustedparts'] = new TrustedPartsProvider();
    }

    async search(query: string, providerName?: string): Promise<PartSearchResult[]> {
        const provider = this.providers[providerName || this.defaultProvider];
        if (!provider) throw new Error(`Provider ${providerName} not found`);

        // Check Cache? (Search results usually not cached as strictly as specific MPNs, but could be)
        // For search, we generally want fresh results or short TTL.
        // Let's rely on provider. 

        try {
            return await provider.search(query);
        } catch (e) {
            console.error("Search failed", e);
            return [];
        }
    }

    async getPartData(mpn: string, providerName?: string): Promise<PartSearchResult | null> {
        const pName = providerName || this.defaultProvider;

        // 1. Check Cache
        const cached = await db.part_cache.where({ provider: pName, proxied_id: mpn }).first();
        if (cached && cached.expires_at > new Date()) {

            return cached.data as PartSearchResult;
        }

        // 2. Fetch Live
        const provider = this.providers[pName];
        if (!provider) return null;

        const result = await provider.getPricing(mpn);

        if (result) {
            // 3. Update Cache (TTL 24 hours)
            const expires = new Date();
            expires.setHours(expires.getHours() + 24);

            await db.part_cache.put({
                provider: pName,
                proxied_id: mpn,
                data: result,
                expires_at: expires
            });
        }

        return result;
    }
}

export const partSearch = new PartSearchService();
