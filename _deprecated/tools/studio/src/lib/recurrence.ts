
import * as chrono from 'chrono-node';

/**
 * Parses a natural language recurrence pattern and returns the next occurrence date.
 * @param text The text description (e.g. "every Monday", "tomorrow", "in 3 days")
 * @param referenceDate The date to start calculating from (default: now)
 * @returns The next Date or null if invalid
 */
export function parseRecurrence(text: string, referenceDate: Date = new Date()): Date | null {
    if (!text || !text.trim()) return null;

    // Use strict forward date parsing to avoid past dates
    const parsedDate = chrono.parseDate(text, referenceDate, { forwardDate: true });

    // If parsed date is valid and different from reference (or we accept today if it's later in day?)
    // Actually, simpler to just return what chrono finds.
    return parsedDate;
}

/**
 * Validates if the text string is a comprehensible recurrence pattern
 */
export function validateRecurrence(text: string): boolean {
    return !!parseRecurrence(text);
}
