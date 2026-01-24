import { useLiveQuery } from 'dexie-react-hooks';
import { db } from '../../lib/db';
import { Card } from '../ui/Card';
import { Target, ChevronRight, Star } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import clsx from 'clsx';
import { useUIStore } from '../../store/useStore';

export function DashboardGoalsWidget() {
    const navigate = useNavigate();
    const { addToStash } = useUIStore();

    // Fetch active high-priority goals (Priority >= 4)
    const activeGoals = useLiveQuery(() =>
        db.goals
            .where('status').equals('active')
            .filter(g => (g.priority || 0) >= 4)
            .sortBy('priority')
    );

    // Reverse to get highest priority first
    const sortedGoals = activeGoals?.reverse().slice(0, 5);

    if (!sortedGoals || sortedGoals.length === 0) {
        return (
            <Card className="h-full flex flex-col items-center justify-center p-4 bg-purple-500/5 border-purple-500/10 opacity-70">
                <Target size={24} className="text-purple-500/30 mb-2" />
                <span className="text-xs text-purple-300/50 font-medium uppercase tracking-wide text-center">No Active Visions</span>
                <button
                    onClick={() => navigate('/goals')}
                    className="mt-2 text-[10px] text-purple-400 hover:text-purple-300 underline decoration-dotted"
                >
                    Create Goal
                </button>
            </Card>
        );
    }

    return (
        <Card className="h-full flex flex-col p-4 bg-purple-500/5 border-purple-500/20">
            <div className="flex justify-between items-center mb-4">
                <h3 className="text-sm font-medium tracking-wide text-purple-400 flex items-center gap-2">
                    <Target size={16} />
                    Vision Targets
                </h3>
                <button
                    onClick={() => navigate('/goals')}
                    className="text-xs text-gray-400 hover:text-white flex items-center gap-1 font-medium"
                >
                    View All <ChevronRight size={12} />
                </button>
            </div>

            <div className="space-y-3 flex-1 overflow-auto">
                {sortedGoals.map(goal => (
                    <div
                        key={goal.id}
                        className="group flex flex-col gap-1 p-2 rounded hover:bg-white/5 cursor-pointer border border-transparent hover:border-white/10 transition-all"
                        onClick={() => navigate('/goals')}
                    >
                        <div className="flex justify-between items-start">
                            <span className="font-medium text-sm text-white group-hover:text-purple-300 transition-colors">
                                {goal.title}
                            </span>
                            {goal.level === 'vision' && <Star size={12} className="text-purple-500 fill-purple-500" />}
                        </div>

                        <div className="w-full h-1.5 bg-white/10 rounded-full overflow-hidden mt-1">
                            <div
                                className="h-full bg-gradient-to-r from-purple-500 to-purple-400 rounded-full transition-all duration-1000"
                                style={{ width: `${goal.progress || 0}%` }}
                            />
                        </div>
                    </div>
                ))}
            </div>
        </Card>
    );
}
