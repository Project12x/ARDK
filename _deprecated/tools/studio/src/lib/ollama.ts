export const OllamaService = {
    getUrl() {
        return localStorage.getItem('OLLAMA_URL') || 'http://localhost:11434';
    },

    async getTags(): Promise<string[]> {
        const url = this.getUrl();
        try {
            // Add timeout to avoid hanging
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2000);

            const res = await fetch(`${url}/api/tags`, { signal: controller.signal });
            clearTimeout(timeoutId);

            if (!res.ok) throw new Error("Failed to fetch tags");
            const data = await res.json();
            // data.models is array of { name: string, ... }
            return data.models?.map((m: any) => m.name) || [];
        } catch (e) {
            // Quiet failure is expected if Ollama isn't running
            return [];
        }
    },

    async chat(message: string, systemPrompt?: string, model = "llama3"): Promise<string> {
        const url = this.getUrl();
        try {
            const res = await fetch(`${url}/api/chat`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    model: model,
                    messages: [
                        { role: 'system', content: systemPrompt || "You are a helpful assistant." },
                        { role: 'user', content: message }
                    ],
                    stream: false
                })
            });
            if (!res.ok) throw new Error(`Ollama Error: ${res.statusText}`);
            const data = await res.json();
            return data.message.content;
        } catch (e) {
            console.error("Ollama Chat Failed", e);
            throw e;
        }
    }
};
