import { AlertTriangle } from 'lucide-react';
import type { HazardClass } from './db';

export const HAZARD_DEFS: Record<HazardClass, { label: string; icon: any; color: string; controls: string[] }> = {
    mains: {
        label: "Mains Voltage",
        icon: AlertTriangle,
        color: "text-red-500",
        controls: ["Isolation Transformer Verified", "Discharge Probe Ready", "One-Hand Rule Active"]
    },
    high_current: {
        label: "High Current / LiPo",
        icon: AlertTriangle,
        color: "text-orange-500",
        controls: ["Current Limiter Set", "Fire Bag/Extinguisher Nearby", "Wires Gauge Verified"]
    },
    chemicals: {
        label: "Chemicals / Solvents",
        icon: AlertTriangle,
        color: "text-yellow-500",
        controls: ["Ventilation/Fume Extractor On", "Gloves Donned", "Eyewear Donned"]
    },
    blades: {
        label: "Sharp Tools / Blades",
        icon: AlertTriangle,
        color: "text-red-400",
        controls: ["Workpiece Clamped", "Push Stick Ready", "Emergency Stop Test"]
    },
    fumes: {
        label: "Solder / Printer Fumes",
        icon: AlertTriangle,
        color: "text-gray-400",
        controls: ["Fume Extractor On", "Ventilation Open"]
    },
    lead: {
        label: "Lead Exposure",
        icon: AlertTriangle,
        color: "text-gray-500",
        controls: ["Gloves Donned", "Hand Wash Scheduled", "No Food/Drink"]
    },
    esd: {
        label: "ESD Sensitive",
        icon: AlertTriangle,
        color: "text-blue-400",
        controls: ["Wrist Strap Connected", "Mat Grounded"]
    }
};
