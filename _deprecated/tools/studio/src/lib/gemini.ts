import { GoogleGenerativeAI } from '@google/generative-ai';

// Initialize with the key from localStorage
const getGenAI = () => {
    const key = localStorage.getItem('GEMINI_API_KEY');
    if (!key) throw new Error('Gemini API Key not found');
    return new GoogleGenerativeAI(key);
};

export interface ExtractedProjectData {
    title?: string;
    version?: string;
    description?: string;
    category?: string;
    role?: string;
    intrusiveness?: number;
    io_spec?: string[];
    target_completion_date?: string;
    taxonomy_path?: string;
    initial_notebook_entry?: {
        title: string;
        content: string;
        tags?: string[];
    };
    design_philosophy?: string;
    golden_voltages?: string;
    changelog_history?: Array<{
        version: string;
        date: string;
        summary: string;
    }>;
    tasks?: Array<{ title: string; phase?: string; priority?: number; estimated_time?: string }>;
    bom?: Array<{ name?: string; quantity: number | string; notes?: string; est_unit_cost?: number }>;
    // v16
    project_code?: string;
    design_status?: string; // e.g. 'idea', 'draft', 'planted' ...
    build_status?: string; // e.g. 'unbuilt', 'wip', 'harvesting' ...
    exp_cv_usage?: string;
    // v17
    time_estimate_active?: number;
    time_estimate_passive?: number;
    financial_budget?: number;
    rationale?: string;
    risk_level?: 'low' | 'medium' | 'high';
    summary?: string;
    tags?: string[];
    label_color?: string;
    // v19 - Universal Support
    domains?: string[];
    hazards?: string[];
    specs_technical?: Record<string, any>;
    specs_performance?: Record<string, any>;
    market_context?: Record<string, any>;
    signal_chain?: Record<string, any>;
    specs_environment?: Record<string, any>;
    // v20 - MDBD Dictionary
    universal_map?: Record<string, any>;
    // v37 - Energy & Safety
    safety_data?: {
        hazards: string[];
        controls: Array<{ description: string; is_checked: boolean }>;
    };
}

import { PromptBuilder } from './ai-types';
import type { SystemContext } from './ai-types';

export const GeminiService = {

    async chatWithSystem(message: string, context: SystemContext, image?: File): Promise<string> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({
            model: "gemini-2.5-flash",
            generationConfig: { responseMimeType: "application/json" }
        }, { apiVersion: 'v1beta' });

        // If image is provided, add a vision-specific instruction
        const imageContext = image ? `\n\n[USER HAS ATTACHED AN IMAGE. Analyze it in context of their query.]` : '';

        const systemPrompt = PromptBuilder.buildSystemPrompt(context) +
            `\n\nUSER QUERY: "${message}"\n` +
            imageContext;


        // Build content array for multimodal
        const contentParts: Array<string | { inlineData: { data: string; mimeType: string } }> = [systemPrompt];
        if (image) {
            const imagePart = await fileToGenerativePart(image);
            contentParts.push(imagePart);
        }

        const result = await model.generateContent(contentParts);
        const text = result.response.text();
        // JSON Mode is enabled, but we still sanitize just in case
        // JSON Mode is enabled, but we still sanitize just in case
        try {
            const clean = text.replace(/```json/g, '').replace(/```/g, '').trim();
            if (clean.startsWith('{')) return clean;
            return JSON.stringify({ message: text });
        } catch {
            return JSON.stringify({ message: text });
        }
    },
    async analyzeFile(file: File): Promise<any> {
        const genAI = getGenAI();
        const { KNOWN_MODELS } = await import('./IntegrationService');
        // List of models to try in order of preference/speed
        const modelsToTry = KNOWN_MODELS.gemini.map(m => m.id);

        let lastError;

        for (const modelName of modelsToTry) {
            try {
                // Add a small delay between attempts to avoid rapid-fire limits
                if (modelName !== modelsToTry[0]) {
                    await new Promise(r => setTimeout(r, 1000));
                }

                const model = genAI.getGenerativeModel({ model: modelName }, { apiVersion: 'v1beta' });

                let prompt = `
            You are a universal project analyzer. Analyze this document/image to extract project information.
            
            STEP 1: DETECT OR INVENT THE DOMAIN
            Identify the primary domain. You may use one of these standard domains OR INVENT A NEW ONE if the project doesn't fit (e.g. "Falconry", "Quantum Baking", "Genealogy").
            Standard Domains:
            - Technical: Electronics, Software, Mechanical, Fabrication, 3D Printing, CNC
            - Creative: Art, Music, Writing, Photography, Video, Design, Crafts
            - Knowledge: Research, Education, Science, Engineering
            - Life: Home, Personal, Health, Fitness, Travel, Cooking
            - Business: Finance, Marketing, Event Planning, Consulting
            - Maintenance: Repair, Automotive, Motorcycle
            
            STEP 2: EXTRACT UNIVERSAL FIELDS (ALL PROJECTS)
            - title: The project name
            - version: Version number if mentioned (e.g., "v1.0", "Draft 2")
            - description: Brief summary of what this project is
            - domains: Array of applicable domains (Standard or Custom)
            - category: Primary category (e.g., "Writing", "Electronics", "Falconry")
            - tags: Keywords for searching
            - risk_level: "low", "medium", or "high"
            - rationale: Why this project matters
            - specs_custom: Key-Value object for ANY important project data that doesn't fit standard fields. (e.g. { "Oven Temp": "350F", "Tuning": "Drop D", "Soil pH": "6.5" })

            STEP 3: DEEP PARSING (TASKS & RESOURCES)
            - tasks: Array of objects
              - title: Task name
              - phase: Map to (Ideation, Research, Planning, Preparation, Execution, Review, Delivery, Maintenance)
              - priority: Infer 1-5 (5=Critical)
              - estimated_time: e.g. "2h", "30m" (Infer if possible)
              - sensory_load: "low", "medium", "high" (Infer based on noise/mess/focus needed)
            
            - bom: Array of objects (Materials/Ingredients/Parts)
              - name: Clean name
              - quantity: Number or string
              - status: "have", "need", "ordered" (Infer from context)
              - est_unit_cost: Number (Estimate if unknown)
              - url: Purchase link if present
            
            STEP 4: SPECIALIZED STRUCTURAL DATA
            
            IF MANUSCRIPT / WRITING:
            - documents: Array of { title, type (chapter/scene/note), content (summary or text snippet), status }
            
            IF PRODUCTION / MEDIA:
            - productionItems: Array of { name, type (song/shot/clip), status, metadata (KV object) }

            STEP 5: EXTRACT DOMAIN-SPECIFIC FIELDS (Standard Schemas)
            (Populate these if they apply, otherwise use specs_custom)
            - specs_technical: (Mainly Electronics/Mech) { voltages, dimensions, materials }
            - specs_performance: { targets, benchmarks }
            - creative_specs: { theme, style, mood, references }
            - event_specs: { date, venue, budget }
            
            CRITICAL OUTPUT INSTRUCTIONS:
            1. Output strictly valid JSON.
            2. Do NOT use Markdown code blocks.
            3. Populate ALL applicable fields. If data is missing, INFER reasonable estimates.
            4. Be creative with "specs_custom" - capture the unique essence of the project.
            
            "json_structure_example": {
              "title": "Project Name",
              "domains": ["CustomDomain"],
              "specs_custom": { "WeirdParam": "Value" },
              "tasks": [ { "title": "Task", "priority": 5, "estimated_time": "1h" } ],
              "documents": [],
              "productionItems": []
            }
          `;

                let result;
                const generate = async () => {
                    const isPdf = file.type === 'application/pdf';
                    if (file.type.startsWith('image/') || isPdf) {
                        const base64Data = await fileToGenerativePart(file);
                        return await model.generateContent([prompt, base64Data]);
                    } else {
                        const text = await file.text();
                        prompt += `\n\nDOCUMENT CONTENT:\n${text.substring(0, 30000)}`;
                        return await model.generateContent(prompt);
                    }
                };

                try {
                    result = await generate();
                } catch (err: unknown) {
                    // Critical Fix: If 429 (Rate Limit), wait and retry ONCE for this specific model
                    // since we know this model exists (unlike the 404s).
                    const errorMessage = err instanceof Error ? err.message : String(err);
                    if (errorMessage.includes('429')) {
                        console.warn(`Rate limit hit for ${modelName}. Waiting 15s to retry...`);
                        await new Promise(resolve => setTimeout(resolve, 15000));
                        result = await generate(); // Retry once
                    } else {
                        throw err; // Re-throw other errors to fallback
                    }
                }

                const response = await result.response;
                const responseText = response.text();

                // Clean up markdown code blocks if present - improved regex
                const jsonMatch = responseText.match(/\{[\s\S]*\}/);
                if (!jsonMatch) throw new Error("No JSON found in response");

                return JSON.parse(jsonMatch[0]);

            } catch (error: unknown) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                console.warn(`Failed with model ${modelName}:`, errorMessage);
                lastError = error;
                // Continue to next model
            }
        }

        console.error("All Gemini models failed. Last error:", lastError);
        return { summary: "Automatic analysis failed. Please verify API key and Region availability." };
    },

    async chatWithProject(message: string, projectContext: Record<string, any>, image?: File): Promise<string> {
        const genAI = getGenAI();
        const chatModels = ["gemini-2.5-flash", "gemini-3.0-pro", "gemini-2.0-flash-exp", "gemini-1.5-pro", "gemini-1.5-flash"];

        // If image is provided, add a vision-specific instruction
        const imageContext = image ? `\n\n[USER HAS ATTACHED AN IMAGE. Analyze it in context of their query.]` : '';

        const systemPrompt = `
        You are the 'Workshop Oracle', an AI assistant integrated into a DIY Project Manager.
        ${imageContext}
        
        CONTEXT:
        ${Object.entries(projectContext)
                .filter(([key]) => !['title', 'status', 'status_description', 'documents', 'productionItems', 'linkedAsset', 'id', 'project_id'].includes(key)) // Filter known/handled fields
                .map(([key, value]) => {
                    // Formatting helper
                    let displayVal = value;
                    if (Array.isArray(value)) displayVal = `${value.length} items`;
                    else if (typeof value === 'object' && value !== null) displayVal = JSON.stringify(value);

                    return `${key.replace(/_/g, ' ').toUpperCase()}: ${displayVal}`;
                }).join('\n        ')}

        Project Title: ${projectContext.title}
        Status: ${projectContext.status}
        Description: ${projectContext.status_description}

        ${projectContext.documents?.length ? `
        DOCUMENTS (Manuscript):
        ${projectContext.documents.map((d: any) => `- [${d.type}] ${d.title}`).join('\n')}
        ` : ''}

        ${projectContext.productionItems?.length ? `
        PRODUCTION ITEMS:
        ${projectContext.productionItems.map((p: any) => `- [${p.type}] ${p.name} (${p.status})`).join('\n')}
        ` : ''}

        ${projectContext.linkedAsset ? `
        LINKED ASSET:
        ${JSON.stringify(projectContext.linkedAsset, null, 2)}
        ` : ''}
        
        USER QUERY: ${message}
        
        INSTRUCTIONS:
        - Answer as a helpful senior engineer / maker.
        - Be concise and actionable.
        - Use terminology appropriate for the project's specific domain.

        CRITICAL: If the user explicitly asks to perform an action (add task, add bom item, update status), you MUST return a valid JSON object.
        
        FORMAT:
        {
          "message": "Start with a conversational confirmation...",
          "proposed_action": {
            "type": "ADD_TASK" | "ADD_BOM_ITEM" | "UPDATE_STATUS",
            "payload": { ... }
          }
        }

        Payload Schemas:
        - ADD_TASK: { "title": "...", "priority": 1-5, "energy_level": "low"|"medium"|"high", "sensory_load": [] }
        - ADD_BOM_ITEM: { "name": "...", "quantity": 1, "status": "missing" }
        - UPDATE_STATUS: { "status": "active" | "on-hold" | "completed" | "archived" }

        Examples:
        User: "Remind me to buy screws" -> { "message": "Sure, I'll add that.", "proposed_action": { "type": "ADD_TASK", "payload": { "title": "Buy screws", "priority": 3 } } }
        User: "Mark this done" -> { "message": "Congrats! Marking as completed.", "proposed_action": { "type": "UPDATE_STATUS", "payload": { "status": "completed" } } }
        
        If NO action is needed, just return the plain text response (or the same JSON with no proposed_action).
        `;

        for (const modelName of chatModels) {

            try {
                const model = genAI.getGenerativeModel({ model: modelName }, { apiVersion: 'v1beta' });

                let result;
                if (image) {
                    const imagePart = await fileToGenerativePart(image);
                    result = await model.generateContent([systemPrompt, imagePart]);
                } else {
                    result = await model.generateContent(systemPrompt);
                }

                const text = result.response.text();

                // Parse JSON if present, otherwise wrap text
                try {
                    const cleanJson = text.replace(/```json/g, '').replace(/```/g, '').trim();
                    const parsed = JSON.parse(cleanJson);
                    return JSON.stringify(parsed); // Return stringified JSON for consistent handling
                } catch {
                    // If not JSON, return as standard message structure
                    return JSON.stringify({ message: text });
                }
            } catch (error: unknown) {
                const errorMessage = error instanceof Error ? error.message : String(error);
                console.warn(`Chat model ${modelName} failed:`, errorMessage);
                if (modelName === chatModels[chatModels.length - 1]) {
                    console.error("All chat models failed", error);
                    return "Connection to the Oracle severed. Please check your API usage or network.";
                }
            }
        }
        return "Oracle is silent.";
    },

    async validateAvailableModels(): Promise<Record<string, boolean>> {
        const genAI = getGenAI();
        const { KNOWN_MODELS } = await import('./IntegrationService');
        const modelsToTest = KNOWN_MODELS.gemini.map(m => m.id);

        const results: Record<string, boolean> = {};

        for (const modelName of modelsToTest) {
            try {
                const model = genAI.getGenerativeModel({ model: modelName }, { apiVersion: 'v1beta' });
                // rapid check
                await model.generateContent("Test");
                results[modelName] = true;
            } catch (e: unknown) {
                const errorMessage = e instanceof Error ? e.message : String(e);
                console.warn(`Model ${modelName} is UNAVAILABLE:`, errorMessage);
                results[modelName] = false;
            }
        }
        return results;
    },

    async analyzeInventory(input: string | File): Promise<any[]> {
        const genAI = getGenAI();
        const models = ["gemini-2.5-flash", "gemini-1.5-pro"];
        let prompt = `
        Identify if the item is a **Discrete Component/Tool** or a **Raw Material**.
        
        Extract a JSON ARRAY of objects with these fields:
        - name: CLEAN Name. 
            * **Rule for Discrete/Tools**: MUST be precise (e.g. "M3x10mm CSS Screw", "10k Resistor 1/4W"). NO quantities or "approx" in the name.
            * **Rule for Materials**: Natural language allowed if specific part unknown (e.g. "Pine board scrap", "Loose wires").
        - category: Phylum (e.g. Resistors, Filament, Wood, Adhesives)
        - domain: Kingdom (e.g. Electronics, Woodworking)
        - quantity: Number. (For bulk materials, estimate).
        - units: (e.g. pcs, g, m)
        - mpn: Manufacturer Part Number (if visible/known)
        - manufacturer: Brand/Make
        - barcode: UPC/EAN if visible
        - unit_cost: Estimated USD
        - location: Suggested location
        - type: "part" | "tool" | "consumable" | "equipment"
        
        // v36 Enhanced Fields
        - description: Short descriptive text (e.g. "Red PLA, 1kg spool", "1/4W 5% Carbon Film")
        - specs: JSON Object of technical details (e.g. { "Resistance": "10k", "Tolerance": "5%" })
        - image_url: (Leave empty, will be filled by search)
        
        CRITICAL CLASSIFICATION:
        1. Filament -> type: 'consumable', category: 'Filament'.
        2. Tools/Equipment -> type: 'tool'.
        3. Components -> type: 'part'.
        
        If input is a table/cart, extract ALL rows.
        `;

        let result;
        for (const modelName of models) {
            try {
                const model = genAI.getGenerativeModel({ model: modelName }, { apiVersion: 'v1beta' });
                if (typeof input === 'string') {
                    prompt += `\n\nINPUT TEXT:\n${input.substring(0, 30000)}`;
                    result = await model.generateContent(prompt);
                } else {
                    const base64Data = await fileToGenerativePart(input);
                    result = await model.generateContent([prompt, base64Data]);
                }

                const text = result.response.text();
                const jsonMatch = text.match(/\[[\s\S]*\]/); // Look for Array
                if (jsonMatch) return JSON.parse(jsonMatch[0]);
            } catch (e) {
                console.warn(`Inventory Analysis failed with ${modelName}`, e);
            }
        }
        throw new Error("Failed to extract inventory data.");
    },



    /**
     * Parses a "Master Index" text file or PDF/Image to extract multiple projects.
     */
    async parsePortfolio(input: string | File): Promise<Record<string, any>[]> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: "gemini-2.5-flash" }, { apiVersion: 'v1beta' });

        let prompt = `
        Analyze this "Master Index" portfolio document.
        Extract ALL projects listed.
        Important: This document may contain Technical, Creative, or Hybrid projects. Adapt your understanding of "Role", "Specs", and "Status" to the specific domain of each entry (e.g. "Draft" for writing vs "Breadboard" for electronics).

        For each project, look for:
        - ID (e.g. "PE-MK4") -> map to 'project_code'
        - Name -> map to 'title'
        - Project Status (ACTIVE, LEGACY, RND, DROPPED) -> map to 'status' (lowercase)
        - Category Tags -> map to 'tags' (array)
        - Role / Niche / Genre -> map to 'role'
        - Design Status (e.g. "Idea", "Draft", "Sketch", "Planted", "Composing") -> map to 'design_status' (lowercase)
        - Build Status (e.g. "Unbuilt", "WIP", "Fruiting", "Framed", "Recording") -> map to 'build_status' (lowercase)
        - Notes / Description -> map to 'status_description'
        - EXP / CV usage -> map to 'exp_cv_usage'

        - Tasks: Extract explicit, numbered, or bulleted task lists. ALSO detect implicit tasks in narrative descriptions. If none found, auto-generate 3-5 high-level tasks. Map to 'tasks' (array of strings).
        - BOM/Resources: Extract explicit BOM/Ingredients/Materials. ALSO detect implicit parts. Map to 'bom' (array of strings).

        - 'domains' (array of strings) - e.g. ['Electronics', 'Woodworking', 'Gardening', 'Music', 'Cooking']
        - 'hazards' (array of strings) - e.g. ['Fumes', 'High Voltage', 'Sharp Tools', 'Allergens']
        - 'specs_technical' (JSON object) - e.g. { "Power": "9V", "Materials": "Oak", "Soil": "Loam" }
        - 'specs_performance' (JSON object) - e.g. { "Noise": "-90dB", "Yield": "5lbs" }
        - 'market_context' (JSON object) - e.g. { "Target": "Pro" }
        - 'signal_chain' (JSON object) - e.g. { "In": "Jack", "Out": "XLR" }
        - 'specs_environment' (JSON object) - e.g. { "Temp": "65F" }

        Output a JSON array of project objects.
        
        INPUT CONTENT:
        `;

        try {
            let result;
            if (typeof input === 'string') {
                prompt += input.substring(0, 30000);
                result = await model.generateContent(prompt);
            } else {
                const isPdf = input.type === 'application/pdf';
                if (input.type.startsWith('image/') || isPdf) {
                    const base64Data = await fileToGenerativePart(input);
                    result = await model.generateContent([prompt, base64Data]);
                } else {
                    const text = await input.text();
                    prompt += text.substring(0, 30000);
                    result = await model.generateContent(prompt);
                }
            }

            const responseText = result.response.text();
            const jsonString = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
            // Handle array or wrapped
            const parsed = JSON.parse(jsonString);
            return Array.isArray(parsed) ? parsed : (parsed.projects || [parsed]);
        } catch (e) {
            console.error("Portfolio Parsing Failed", e);
            throw e;
        }
    },

    /**
     * Parse inbox item and suggest action
     */
    async parseInboxItem(content: string): Promise<{
        suggested_action: 'create_project' | 'add_task' | 'reference' | 'someday';
        suggested_project_id?: number;
        suggested_project_title?: string;
        extracted_title: string;
        confidence: number;
    }> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: 'gemini-1.5-flash' });

        // Get existing projects for matching
        const { db } = await import('./db');
        const projects = await db.projects.filter(p => !p.deleted_at && p.status !== 'archived').toArray();
        const projectList = projects.map(p => ({ id: p.id, title: p.title }));

        const prompt = `You are a GTD (Getting Things Done) inbox parser. Analyze this captured input and suggest how to process it.

INPUT: "${content}"

EXISTING PROJECTS:
${JSON.stringify(projectList, null, 2)}

RULES:
1. If this looks like a standalone project idea (building something, creating something new), suggest "create_project"
2. If this looks like a task for an existing project, suggest "add_task" and include the matching project
3. If this is informational (a link, reference, note to remember), suggest "reference"
4. If this is a "maybe someday" idea with no urgency, suggest "someday"
5. Extract a clean title from the content
6. Provide confidence 0.0-1.0 based on how sure you are

RESPOND WITH ONLY JSON:
{
  "suggested_action": "create_project" | "add_task" | "reference" | "someday",
  "suggested_project_id": number | null,
  "suggested_project_title": string | null,
  "extracted_title": "Clean title extracted from input",
  "confidence": 0.0-1.0
}`;

        try {
            const result = await model.generateContent(prompt);
            const responseText = result.response.text();
            const jsonString = responseText.replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(jsonString);
        } catch (e) {
            console.error("Inbox parsing failed", e);
            // Fallback to default
            return {
                suggested_action: 'reference',
                extracted_title: content.substring(0, 50),
                confidence: 0.0
            };
        }
    },

    /**
     * Generates a professional project report content (Summary, Risks, Recommendations).
     */
    async generateProjectReport(context: any): Promise<{
        executive_summary: string;
        risk_analysis: string;
        strategic_recommendations: string[];
    }> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' }, { apiVersion: 'v1beta' });

        const prompt = `
        You are a Senior Project Manager generating a status report (Dossier).
        
        PROJECT DATA:
        Title: ${context.project.title}
        Status: ${context.project.status}
        Description: ${context.project.status_description}
        Priority: ${context.project.priority}/5
        
        TASKS (${context.tasks.length}):
        ${context.tasks.slice(0, 20).map((t: any) => `- [${t.status}] ${t.title}`).join('\n')}
        
        BOM (${context.bom.length}):
        ${context.bom.slice(0, 10).map((b: any) => `- ${b.name} (${b.quantity}) [${b.status}]`).join('\n')}
        
        Reflect on the state of the project.
        
        OUTPUT JSON ONLY:
        {
          "executive_summary": "2-3 sentences summarizing progress and current state.",
          "risk_analysis": "Identify 1-2 key risks based on blocked tasks or missing items.",
          "strategic_recommendations": ["Actionable advice 1", "Actionable advice 2", "Actionable advice 3"]
        }
        `;

        try {
            const result = await model.generateContent(prompt);
            const text = result.response.text();
            const clean = text.replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(clean);
        } catch (e) {
            console.error("Report Generation Failed", e);
            return {
                executive_summary: "AI Generation unavailable.",
                risk_analysis: "N/A",
                strategic_recommendations: []
            };
        }
    },

    /**
     * UNIVERSAL CLASSIFIER
     * Determines what a file is to route it to the correct Ingestion Pipeline.
     */
    async classifyUpload(file: File): Promise<{
        type: 'project' | 'inventory' | 'song' | 'asset' | 'goal' | 'unknown';
        confidence: number;
        reasoning: string;
    }> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' }, { apiVersion: 'v1beta' });

        const prompt = `
        Classify this uploaded file into one of the WorkshopOS domains.
        
        OPTIONS:
        - 'project': Technical documents, PDF manuals, Project notes, Circuit schematics, Code files.
        - 'inventory': Receipts, Lists of parts, Invoices, Photos of multiple items on a table.
        - 'song': Audio files, Lyrics sheets, Music demos, Chord charts.
        - 'asset': Photos of single tools/equipment (Drills, Multimeters), Manuals for a specific tool.
        - 'goal': Strategic documents, Life plans, Year resolutions.
        
        INPUT METADATA:
        Name: ${file.name}
        Type: ${file.type}
        Size: ${file.size} bytes
        
        Analyze the content/image to determine the BEST match.
        
        OUTPUT JSON:
        {
          "type": "project" | "inventory" | "song" | "asset" | "goal" | "unknown",
          "confidence": 0.0-1.0,
          "reasoning": "Short explanation"
        }
        `;

        try {
            const runner = async () => {
                const isImage = file.type.startsWith('image/');
                const isPdf = file.type === 'application/pdf';

                if (isImage || isPdf) {
                    const base64 = await fileToGenerativePart(file);
                    return await model.generateContent([prompt, base64]);
                } else if (file.type.startsWith('audio/')) {
                    // Gemini 1.5/2.0 supports audio files directly via inlineData!
                    const base64 = await fileToGenerativePart(file);
                    // Update prompt for audio context
                    const audioPrompt = prompt + "\n\n(This is an AUDIO file. Listen to it. Is it a song? A voice memo? A field recording?)";
                    return await model.generateContent([audioPrompt, base64]);
                } else {
                    const text = await file.text();
                    return await model.generateContent(prompt + `\n\nTEXT CONTENT START:\n${text.substring(0, 5000)}`);
                }
            };

            const result = await runner();
            const jsonStr = result.response.text().replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(jsonStr);

        } catch (e) {
            console.error("Classification Failed", e);
            return { type: 'unknown', confidence: 0, reasoning: 'AI Error' };
        }
    },

    /**
     * MUSIC ANALYZER
     * Extracts Song Data from Audio or Lyrics Text.
     */
    async analyzeMusicData(file: File): Promise<{
        title: string;
        bpm?: number;
        key?: string;
        mood?: string;
        tags: string[];
        lyrics_snippet?: string;
        is_instrumental: boolean;
        instruments_detected: string[];
    }> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' }, { apiVersion: 'v1beta' });

        let prompt = `
        Analyze this music file (or lyrics text).
        Extract metadata for the Song Database.
        
        OUTPUT JSON:
        {
            "title": "Song Title (Infer from filename or content)",
            "bpm": Number (Estimate tempo),
            "key": "Musical Key (e.g. Cmin, F#Maj)",
            "mood": "Atmospheric, Aggressive, Upbeat, etc.",
            "tags": ["Tag1", "Tag2"],
            "lyrics_snippet": "First few lines if vocals present...",
            "is_instrumental": true/false,
            "instruments_detected": ["Guitar", "Synth", "Drums"]
        }
        `;

        try {
            let result;
            if (file.type.startsWith('audio/')) {
                const base64 = await fileToGenerativePart(file);
                result = await model.generateContent([prompt, base64]);
            } else {
                // Assume text lyrics
                const text = await file.text();
                prompt += `\n\nCONTENT:\n${text.substring(0, 10000)}`;
                result = await model.generateContent(prompt);
            }

            const jsonStr = result.response.text().replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(jsonStr);

        } catch (e) {
            console.error("Music Analysis Failed", e);
            return {
                title: file.name.replace(/\.[^/.]+$/, ""),
                tags: [],
                is_instrumental: false,
                instruments_detected: []
            };
        }
    },

    /**
     * ASSET ANALYZER
     * Extracts Tool/Equipment data from photos.
     */
    async analyzeAssetImage(file: File): Promise<{
        name: string;
        make?: string;
        model?: string;
        category: string;
        description: string;
        estimated_value?: number;
        serial_number?: string;
        condition: string;
    }> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' }, { apiVersion: 'v1beta' });

        const prompt = `
        Analyze this photo of a tool or equipment.
        Extract registry data.
        
        OUTPUT JSON:
        {
            "name": "Common Name (e.g. Cordless Drill)",
            "make": "Brand (e.g. DeWalt)",
            "model": "Model Number if visible",
            "category": "Power Tools, Test Equipment, Furniture, Computing...",
            "description": "Visual description including color and features",
            "estimated_value": Number (USD Estimate based on market),
            "serial_number": "String if visible",
            "condition": "New, Used, Worn, Damaged"
        }
        `;

        try {
            const base64 = await fileToGenerativePart(file);
            const result = await model.generateContent([prompt, base64]);
            const jsonStr = result.response.text().replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(jsonStr);
        } catch (e) {
            console.error("Asset Analysis Failed", e);
            throw new Error("Could not analyze asset image.");
        }
    },

    /**
     * DOCUMENT ANALYZER (Library -> Asset)
     * Creates an Asset entry from a technical document or manual.
     */
    async analyzeDocumentForAsset(input: string, title?: string): Promise<{
        name: string;
        category: string;
        description: string;
        make?: string;
        model?: string;
        specs_technical?: Record<string, any>;
        tags: string[];
    }> {
        const genAI = getGenAI();
        const model = genAI.getGenerativeModel({ model: 'gemini-2.5-flash' }, { apiVersion: 'v1beta' });

        const prompt = `
        Analyze this technical document/manual content.
        Create an Asset Registry entry for the primary item described.

        Document Title: ${title || 'Unknown'}

        EXTRACT:
        - name: The primary product name (e.g. "Saleae Logic Pro 16", "Arduino Uno R3", "Datasheet X")
        - category: The closest category (e.g. "Test Equipment", "Microcontrollers", "Power Tools")
        - make: Manufacturer
        - model: Specific model number
        - description: A brief technical summary of what it is.
        - tags: Key features or keywords.
        - specs_technical: A JSON object of KEY technical specs found (e.g. { "Voltage": "5V", "Channels": 16, "Bandwidth": "100MHz" })

        OUTPUT JSON ONLY.
        `;

        try {
            let result;
            if (input.startsWith('data:')) {
                // Handle Base64 (Image or PDF)
                const mimeType = input.split(';')[0].split(':')[1];
                const base64Data = input.split(',')[1];

                result = await model.generateContent([
                    prompt,
                    { inlineData: { data: base64Data, mimeType } }
                ]);
            } else {
                // Text
                result = await model.generateContent(prompt + `\n\nCONTENT:\n${input.substring(0, 30000)}`);
            }

            const jsonStr = result.response.text().replace(/```json/g, '').replace(/```/g, '').trim();
            return JSON.parse(jsonStr);
        } catch (e) {
            console.error("Document Asset Analysis Failed", e);
            throw new Error("Could not analyze document.");
        }
    }
};

async function fileToGenerativePart(file: File): Promise<{ inlineData: { data: string; mimeType: string; } }> {
    const base64EncodedDataPromise = new Promise<string>((resolve) => {
        const reader = new FileReader();
        reader.onloadend = () => resolve((reader.result as string).split(',')[1]);
        reader.readAsDataURL(file);
    });

    return {
        inlineData: {
            data: await base64EncodedDataPromise,
            mimeType: file.type,
        },
    };
}
