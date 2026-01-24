
import { addDays, addWeeks, addMonths, addYears } from 'date-fns';
import type { Routine } from '../lib/db';

export class RoutineService {
    static calculateNextDue(frequency: Routine['frequency'], fromDate: Date = new Date()): Date {
        // Reset time to start of day for cleaner dates, or keep time?
        // Usually maintenance tasks are date-based, not time-based.
        const base = new Date(fromDate);
        base.setHours(0, 0, 0, 0);

        switch (frequency) {
            case 'daily':
                return addDays(base, 1);
            case 'weekly':
                return addWeeks(base, 1);
            case 'monthly':
                return addMonths(base, 1);
            case 'quarterly':
                return addMonths(base, 3);
            case 'yearly':
                return addYears(base, 1);
            case 'seasonal':
                // Seasonal is tricky. Let's assume 3 months from now for simple recurrence,
                // or we could implement specific season logic (e.g. "Next Spring").
                // For now, let's treat generic seasonal as ~90 days.
                return addMonths(base, 3);
            default:
                return addWeeks(base, 1);
        }
    }

    static getSeason(): 'spring' | 'summer' | 'fall' | 'winter' {
        const month = new Date().getMonth(); // 0-11
        if (month >= 2 && month <= 4) return 'spring';
        if (month >= 5 && month <= 7) return 'summer';
        if (month >= 8 && month <= 10) return 'fall';
        return 'winter';
    }
}
