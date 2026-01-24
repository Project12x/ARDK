
// Abstract types for ANY AI service (Gemini, Groq, Ollama, OpenAI)
export interface WorkshopAI {
    chat(message: string, context: SystemContext, modelId?: string): Promise<AIResponse>;
    analyzeImage(image: File, prompt?: string): Promise<AIResponse>;
    generateJson(prompt: string, schema?: any): Promise<any>;
}

export interface AIResponse {
    text: string;
    // Standardized intent for actionable responses
    intent?: 'ADD_TASK' | 'UPDATE_STATUS' | 'INVENTORY_ADD' | 'CREATE_PROJECT' | 'LINKIFY_PROJECT' | 'NONE';
    data?: any;
}

export interface SystemContext {
    printerStatus?: any;
    recentLogs?: any[];
    activeProjects?: any[];
    inventoryMetrics?: { count: number };
    currentProject?: {
        id: number;
        title: string;
        status: string;
        tasks: any[];
        documents?: { title: string; type: string }[];
        productionItems?: { name: string; type: string; status: string }[];
        linkedAsset?: any;
    };
    pageContext?: string;
    ancillaryData?: Record<string, any[]>;
    songs?: { title: string; status: string; albumId?: number }[];
    albums?: { title: string; status: string }[];
}

// Unified Prompt Builder to ensure all models get the same instructions
export const PromptBuilder = {
    buildSystemPrompt(context: SystemContext): string {
        const { activeProjects, recentLogs, printerStatus, inventoryMetrics, currentProject, ancillaryData, songs, albums } = context;

        let prompt = `
        You are the 'Workshop Oracle', the central intelligence of this Workshop.OS.
        
        CURRENT WORKSHOP STATE:
        - Active Projects: ${activeProjects?.map(p => `"${p.title}"`).join(', ') || 'None'}
        - Inventory Stats: ${inventoryMetrics?.count || '?'} items.
        ${songs?.length ? `- Music Library: ${songs.length} Songs, ${albums?.length || 0} Albums` : ''}

        ${currentProject ? `
        FOCUS PROJECT:
        - Title: "${currentProject.title}" (ID: ${currentProject.id})
        - Status: ${currentProject.status}
        - Tasks: ${currentProject.tasks.map(t => `[${t.id}] ${t.title} (${t.status})`).join(', ')}
        ${currentProject.linkedAsset ? `
        - LINKED ASSET: ${currentProject.linkedAsset.name}
          Specs: ${JSON.stringify(currentProject.linkedAsset.specs_computer || {})}
        ` : ''}
        ` : ''}
        `;

        if (songs && songs.length > 0) {
            prompt += `\nMUSIC LIBRARY CONTEXT:\n${songs.slice(0, 20).map(s => `- ${s.title} (${s.status})`).join('\n')}\n(Total: ${songs.length} songs)\n`;
        }

        if (ancillaryData) {
            prompt += `\n\nGLOBAL CONTEXT:`;
            for (const [key, items] of Object.entries(ancillaryData)) {
                if (items && items.length > 0) {
                    prompt += `\n\n${key.toUpperCase()}:\n`;
                    items.slice(0, 10).forEach(item => {
                        const label = item.title || item.name || item.content || JSON.stringify(item);
                        const status = item.status || item.frequency || '';
                        prompt += `- ${label} ${status ? `(${status})` : ''}\n`;
                    });
                }
            }
        }

        prompt += `
        INSTRUCTIONS:
        - Answer as a helpful, slightly sci-fi workshop assistant.
        - If the user wants to perform an action, return a JSON object with an 'intent'.
        
        ALLOWED INTENTS & SCHEMAS:
        1. INVENTORY_ADD: { "intent": "INVENTORY_ADD", "data": [ ...items... ] }
        2. ADD_TASK: { "intent": "ADD_TASK", "payload": { "project_id": 123, "title": "...", "priority": 1-5 } }
        3. UPDATE_TASK: { "intent": "UPDATE_TASK", "payload": { "id": 123, "status": "..." } }
        4. CREATE_PROJECT: { "intent": "CREATE_PROJECT", "payload": { "title": "...", "category": "...", "description": "Premise/Goal...", "plot": "...", "characters": "..." } } (For creative projects, include premise, plot, etc.)
        5. LINKIFY_PROJECT: { "intent": "LINKIFY_PROJECT", "payload": { "projectId": 123 } } (Use current project ID if active). Scan logic for text.

        If NO action is needed, return standard JSON: { "message": "Your response here." }
        `;

        return prompt;
    }
};
