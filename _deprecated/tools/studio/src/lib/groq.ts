import Groq from 'groq-sdk';

export const getGroq = () => {
    const key = localStorage.getItem('GROQ_API_KEY');
    if (!key) throw new Error('Groq API Key not found');
    return new Groq({ apiKey: key, dangerouslyAllowBrowser: true });
};

export const GroqService = {
    async validateKey(apiKey: string): Promise<boolean> {
        try {
            const groq = new Groq({ apiKey, dangerouslyAllowBrowser: true });
            await groq.chat.completions.create({
                messages: [{ role: "user", content: "Test" }],
                model: "mixtral-8x7b-32768",
                max_tokens: 1
            });
            return true;
        } catch (e) {
            console.error("Groq Validation Failed", e);
            return false;
        }
    },

    async chat(message: string, systemPrompt?: string, model = "llama3-70b-8192"): Promise<string> {
        const groq = getGroq();
        const completion = await groq.chat.completions.create({
            messages: [
                { role: "system", content: systemPrompt || "You are a helpful assistant." },
                { role: "user", content: message }
            ],
            model: model,
            temperature: 0.5,
            max_tokens: 1024,
            top_p: 1,
            stream: false,
            stop: null,
            response_format: (systemPrompt?.includes('JSON') || message.includes('JSON')) ? { type: "json_object" } : undefined
        });

        return completion.choices[0]?.message?.content || "";
    },

    async jsonMode(prompt: string, modelStr = "llama3-70b-8192"): Promise<any> {
        const groq = getGroq();
        const completion = await groq.chat.completions.create({
            messages: [
                {
                    role: "system",
                    content: "You are a JSON-only API. You must return valid JSON. Do not return markdown blocks."
                },
                { role: "user", content: prompt }
            ],
            model: modelStr,
            response_format: { type: "json_object" }
        });

        const content = completion.choices[0]?.message?.content;
        if (!content) throw new Error("Empty response from Groq");
        return JSON.parse(content);
    },

    getAvailableModels(): string[] {
        return [
            "llama3-70b-8192",
            "llama3-8b-8192",
            "mixtral-8x7b-32768",
            "gemma-7b-it"
        ];
    }
};
