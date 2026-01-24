
export type DomainType = 'workshop' | 'kitchen' | 'garden';

interface DomainConfigSchema {
    activeDomain: DomainType;
    systemName: string; // e.g. "WorkshopOS" or "SousChef"

    // UI Aliases: Rename standard concepts
    aliases: {
        project: string; // e.g. "Recipe" or "Plant"
        task: string;    // e.g. "Step" or "Care"
        inventory: string; // e.g. "Pantry" or "Supplies"
        asset: string;   // e.g. "Tool" or "Sensor"
    };

    // LLM Persona Injection
    oraclePersona: string;

    // Dynamic Collections (Tables to show in sidebar)
    collections: Array<{
        tableName: string;
        label: string;
        icon?: string;
    }>;
}

/**
 * WORKSHOP.OS DOMAIN CONFIGURATION
 * Change 'activeDomain' to switch the entire application context.
 */
export const DOMAIN_CONFIG: DomainConfigSchema = {
    // CHANGE THIS TO SWITCH MODES: 'workshop' | 'kitchen' | 'garden'
    activeDomain: 'workshop',

    systemName: 'WorkshopOS',

    aliases: {
        project: 'Project',
        task: 'Task',
        inventory: 'Inventory',
        asset: 'Asset'
    },

    oraclePersona: "You are the Workshop Oracle, a senior engineer and systems architect.",

    collections: [
        // Add custom tables here to make them appear in the "Systems" menu
        // { tableName: 'recipes', label: 'Cookbook' },
        // { tableName: 'seeds', label: 'Seed Bank' }
    ]
};

// PRESET: KITCHEN MODE (Example)
/*
export const KITCHEN_CONFIG: DomainConfigSchema = {
    activeDomain: 'kitchen',
    systemName: 'SousChef.OS',
    aliases: {
        project: 'Recipe',
        task: 'Method Step',
        inventory: 'Pantry',
        asset: 'Appliance'
    },
    oraclePersona: "You are a Michelin-star Head Chef and Food Scientist.",
    collections: [
        { tableName: 'menus', label: 'Menu Plans' },
        { tableName: 'dietary_restrictions', label: 'Allergies' }
    ]
};
*/

// PRESET: GARDEN MODE (Example)
/*
export const GARDEN_CONFIG: DomainConfigSchema = {
    activeDomain: 'garden',
    systemName: 'Gaia.OS',
    aliases: {
        project: 'Plant Bed',
        task: 'Care Cycle',
        inventory: 'Nutrients',
        asset: 'Sensor'
    },
    oraclePersona: "You are a Master Gardener and Botanist.",
    collections: [
        { tableName: 'weather_logs', label: 'Weather' },
        { tableName: 'plant_database', label: 'Plant DB' }
    ]
};
*/
