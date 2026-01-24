import type { InventoryItem } from './db';

/**
 * Normalizes a string for matching:
 * - Lowercase
 * - Removes special characters except common electronics chars (., / mostly)
 * - Standardizes spacing
 */
function normalize(str: string): string {
    return str.toLowerCase()
        .replace(/[^a-z0-9./\s-]/g, ' ') // Keep dots, slashes, hyphens
        .replace(/\s+/g, ' ')
        .trim();
}

/**
 * Extracts "Critical" tokens (usually values like 10k, 3.3v, M3)
 * Rule: Contains Digit AND (Letter OR Symbol)
 */
function extractCriticals(tokens: string[]): string[] {
    // Regex for: Starts with digit, contains letter (e.g. 10k, 10uF)
    // OR Starts with letter, contains digit (e.g. M3, ESP32)
    return tokens.filter(t =>
        (/\d/.test(t) && /[a-z]/i.test(t)) || // 10k, M3
        (/^[0-9]+(\.[0-9]+)?$/.test(t)) // Pure numbers (e.g. 100, 4.7)
    );
}

export function findBestMatch(queryName: string, inventory: InventoryItem[]): { item: InventoryItem, score: number } | null {
    if (!queryName || !inventory || inventory.length === 0) return null;

    const normQuery = normalize(queryName);
    const queryTokens = normQuery.split(' ').filter(t => t.length > 0);
    const queryCriticals = extractCriticals(queryTokens);

    let bestMatch: InventoryItem | null = null;
    let bestScore = -Infinity;

    for (const item of inventory) {
        const normItem = normalize(item.name);
        const itemTokens = normItem.split(' ');

        let score = 0;

        // 1. Critical Token Matching (High Weight)
        // Everything in queryCriticals SHOULD appear in itemTokens for a high score.
        let criticalsHit = 0;
        for (const crit of queryCriticals) {
            // Check for exact substring match within tokens to handle "10k" vs "10k,"
            // But we already split by space and regex replace.
            // Let's do exact token match first, then substring.
            if (itemTokens.includes(crit)) {
                score += 20;
                criticalsHit++;
            } else if (normItem.includes(crit)) {
                // "10k" is inside "10k-resistor" (if logic failed to split)
                score += 15;
                criticalsHit++;
            } else {
                // Penalty for missing a SPECIFIC value
                // If BOM is "10k" and Item has no "10k", it's likely wrong match
                score -= 10;
            }
        }

        // 2. Standard Token Matching (Medium Weight)
        // e.g. "Resistor", "Silicon"
        const nonCriticals = queryTokens.filter(t => !queryCriticals.includes(t));
        for (const token of nonCriticals) {
            // Skip common stopwords if needed, but for now exact match
            if (token.length < 2) continue; // Skip single chars?

            if (itemTokens.includes(token)) {
                score += 5;
            } else if (normItem.includes(token)) {
                score += 3;
            }
        }

        // 3. Contextual Bonus
        // If categories match (requires inferring category from BOM name, which is hard without AI)
        // Skip for now.

        // 4. Quantity Handling (Heuristic)
        // If BOM starts with "2", but item name doesn't have "2", user might have pasted quantity.
        // We generally ignore the first token if it looks like a quantity integer?
        // No, "2N2222" starts with 2.
        // Let's rely on Critical Scores.

        // Thresholding
        // We need at least ONE critical match or significant word match
        if (score > bestScore) {
            bestScore = score;
            bestMatch = item;
        }
    }

    // Heuristic Threshold
    // If score is too low, return null.
    // e.g. "Silicon Resistor" vs "Capacitor" -> Score might be 0.
    // "10k Resistor" vs "10k Capacitor" -> Score 20 (10k) - ? (Resistor missing).
    // Let's set a minimal threshold.
    if (bestScore > 10) {
        return { item: bestMatch!, score: bestScore };
    }

    return null;
}
