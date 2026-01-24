// Stub service for searching parts via Digikey/Octopart
// In a real implementation, this would call actual APIs or a backend proxy

export interface PartSearchResult {
    title: string;
    mpn: string; // Internal Part Number
    manufacturer: string;
    description: string;
    price: number;
    availability: number;
    datasheet_url?: string;
    image_url?: string;
    supplier: 'digikey' | 'octopart';
    supplier_url: string;
}

export const PartSearchService = {
    async search(_query: string): Promise<PartSearchResult[]> {
        console.log("Searching for:", _query);
        // Simulate API delay
        await new Promise(resolve => setTimeout(resolve, 500));

        // Mock data
        return [
            {
                title: "Resistor 10k Ohm 1/4W",
                mpn: "RC0603FR-0710KL",
                manufacturer: "Yageo",
                description: "RES SMD 10K OHM 1% 1/10W 0603",
                price: 0.01,
                availability: 5000,
                supplier: 'digikey',
                supplier_url: 'https://www.digikey.com',
                image_url: 'https://media.digikey.com/Renders/Yageo%20Renders/RC0603.jpg'
            },
            {
                title: "Arduino Uno R3",
                mpn: "A000066",
                manufacturer: "Arduino",
                description: "BOARD ATMEGA328P UNO R3",
                price: 23.00,
                availability: 124,
                supplier: 'digikey',
                supplier_url: 'https://www.digikey.com',
                image_url: 'https://media.digikey.com/Photos/Arduino%20Photos/A000066_sml.jpg'
            }
        ];
    }
};
