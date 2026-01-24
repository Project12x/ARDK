export const TavilyService = {
    getApiKey() {
        return localStorage.getItem('TAVILY_API_KEY') || '';
    },

    async search(query: string, searchDepth: 'basic' | 'advanced' = 'basic'): Promise<{ url: string, content: string }[]> {
        const apiKey = this.getApiKey();
        if (!apiKey) throw new Error("Tavily API Key missing");

        try {
            const response = await fetch('https://api.tavily.com/search', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    api_key: apiKey,
                    query: query,
                    search_depth: searchDepth,
                    include_answer: true,
                    max_results: 5
                })
            });

            if (!response.ok) throw new Error("Tavily Search Failed");

            const data = await response.json();
            // Map to a clean simple format
            return data.results.map((r: any) => ({
                url: r.url,
                content: r.content
            }));
        } catch (e) {
            console.error("Tavily Error:", e);
            return [];
        }
    }
};
