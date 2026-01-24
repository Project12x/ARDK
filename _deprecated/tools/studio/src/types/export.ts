export type ExportFormat = 'csv' | 'pdf' | 'markdown' | 'json' | 'docx' | 'digikey-csv' | 'mouser-csv' | 'png' | 'svg' | 'zip';

export interface ExportOption {
    id: ExportFormat;
    label: string;
    extension: string;
    isVendorSpecific?: boolean;
}

export interface ExportValidationResult<T> {
    isValid: boolean;
    missingFields: string[];
    invalidItems: T[];
}

export interface ExportStrategy<T> {
    id: string;
    name: string;
    description: string;
    supportedFormats: ExportOption[];

    // 1. Fetch Data
    getData: (context?: any) => Promise<T[]>;

    // 1b. AI-Enrichment (Optional)
    enrichData?: (data: T[]) => Promise<T[]>;

    // 2. Validate Data (Pre-flight check)
    validate?: (data: T[]) => ExportValidationResult<T>;

    // 3. Resolve Issues 
    resolveIssues?: (invalidItems: T[]) => Promise<T[]>;

    // 4. Transform
    transform: (data: T[], format: ExportFormat) => Promise<Blob | string>;
}
