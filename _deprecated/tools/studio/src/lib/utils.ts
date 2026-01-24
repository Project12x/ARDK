import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

// --- Resilience Helpers ---
export const safeDateStr = (d: any) => {
    if (!d) return '';
    const date = new Date(d);
    return isNaN(date.getTime()) ? '' : date.toISOString().split('T')[0];
};

export const safeDateDisplay = (d: any) => {
    if (!d) return 'N/A';
    const date = new Date(d);
    return isNaN(date.getTime()) ? 'N/A' : date.toLocaleDateString();
};

export const safeTs = (d: any) => {
    if (!d) return 0;
    const date = new Date(d);
    return isNaN(date.getTime()) ? 0 : date.getTime();
};

export const safeArr = (a: any) => {
    return Array.isArray(a) ? a : [];
};

export const safeStr = (s: any) => {
    if (s === null || s === undefined) return '';
    return String(s);
};

export const formatVersion = (v: string | null | undefined) => {
    if (!v) return 'v0.1.0';
    let s = String(v).trim();
    // Normalize "v" prefix
    if (s.toLowerCase().startsWith('v')) {
        s = s.substring(1);
    }

    // Check if it's purely numeric/dot based (e.g. "1.2", "0.5.1", not "Alpha")
    if (/^[\d.]+$/.test(s)) {
        const parts = s.split('.');
        while (parts.length < 3) {
            parts.push('0');
        }
        return `v${parts.join('.')}`;
    }

    // Fallback for non-numeric versions (e.g. "vAlpha") - just ensure 'v' prefix
    return `v${s}`;
};
