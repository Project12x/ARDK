
export interface PrinterConfig {
    ip: string;
    apiKey: string;
}

export interface PrinterStatus {
    text: string;
    temp_bed?: number;
    temp_nozzle?: number;
    job_progress?: number;
    state?: string;
}

export const PrinterService = {
    async testConnection(ip: string, apiKey: string): Promise<boolean> {
        try {
            // Normalize IP (handle missing http/https)
            const proto = ip.startsWith('http') ? '' : 'http://';
            const url = `${proto}${ip}/api/version`;

            const res = await fetch(url, {
                headers: { 'X-Api-Key': apiKey },
            });

            return res.ok;
        } catch (e) {
            console.error("Printer connection test failed:", e);
            return false;
        }
    },

    async getStatus(config: PrinterConfig): Promise<PrinterStatus> {
        if (!config.ip || !config.apiKey) return { text: "Not Configured" };

        try {
            const proto = config.ip.startsWith('http') ? '' : 'http://';

            // 1. Get Connection State / Job State
            const jobRes = await fetch(`${proto}${config.ip}/api/job`, {
                headers: { 'X-Api-Key': config.apiKey },
            });
            const jobData = await jobRes.json();

            // 2. Get Printer State (Temps)
            const printerRes = await fetch(`${proto}${config.ip}/api/printer`, {
                headers: { 'X-Api-Key': config.apiKey },
            });

            if (!printerRes.ok) {
                // Printer might be offline or disconnected from serial
                return {
                    text: jobData.state || "Offline",
                    state: jobData.state
                };
            }

            const printerData = await printerRes.json();
            const tempBed = printerData.temperature?.bed?.actual;
            const tempTool = printerData.temperature?.tool0?.actual;

            let text = jobData.state;
            if (jobData.progress?.completion) {
                text = `${Math.round(jobData.progress.completion)}% - ${text}`;
            }

            return {
                text,
                state: jobData.state,
                temp_bed: tempBed,
                temp_nozzle: tempTool,
                job_progress: jobData.progress?.completion
            };

        } catch (e) {
            return { text: "Error connecting" };
        }
    }
};
