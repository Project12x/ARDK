export const OpenAIService = {
    getApiKey() {
        return localStorage.getItem('OPENAI_API_KEY') || '';
    },

    async validateKey(apiKey: string): Promise<boolean> {
        try {
            const res = await fetch('https://api.openai.com/v1/models', {
                headers: { 'Authorization': `Bearer ${apiKey}` }
            });
            return res.ok;
        } catch {
            return false;
        }
    },

    async chat(message: string, systemPrompt?: string, model = "gpt-4o-mini"): Promise<string> {
        const apiKey = this.getApiKey();
        if (!apiKey) throw new Error("OpenAI Key Missing");

        try {
            const res = await fetch('https://api.openai.com/v1/chat/completions', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': `Bearer ${apiKey}`
                },
                body: JSON.stringify({
                    model: model,
                    messages: [
                        { role: "system", content: systemPrompt || "You are a helpful assistant." },
                        { role: "user", content: message }
                    ],
                    response_format: { type: "json_object" } // Force JSON Mode for consistency
                })
            });

            if (!res.ok) {
                const err = await res.json();
                throw new Error(err.error?.message || "OpenAI Error");
            }

            const data = await res.json();
            return data.choices[0].message.content;
        } catch (e) {
            console.error("OpenAI Chat Failed", e);
            throw e;
        }
    }
};
