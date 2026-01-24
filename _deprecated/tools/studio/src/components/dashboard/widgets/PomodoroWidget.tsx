import { Play, Pause, RotateCcw, Coffee, Brain } from 'lucide-react';
import clsx from 'clsx';
import { useUIStore } from '../../../store/useStore';

export function PomodoroWidget() {
    const { pomodoro, togglePomodoro, resetPomodoro, setPomodoroMode } = useUIStore();
    const { timeLeft, isRunning, mode, sessions } = pomodoro;

    const WORK_DURATION = 25 * 60;
    const BREAK_DURATION = 5 * 60;
    const duration = mode === 'work' ? WORK_DURATION : BREAK_DURATION;
    const progress = ((duration - timeLeft) / duration) * 100;

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className="h-full flex flex-col p-4 bg-black/40">
            {/* Header */}
            <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                    {mode === 'work' ? (
                        <Brain size={14} className="text-red-400" />
                    ) : (
                        <Coffee size={14} className="text-green-400" />
                    )}
                    <span className="text-[10px] font-mono uppercase font-bold text-gray-400">
                        {mode === 'work' ? 'Focus Time' : 'Break Time'}
                    </span>
                </div>
                <span className="text-[9px] font-mono text-gray-600">
                    {sessions} sessions
                </span>
            </div>

            {/* Timer Display */}
            <div className="flex-1 flex flex-col items-center justify-center">
                {/* Progress Ring */}
                <div className="relative w-24 h-24 mb-3">
                    <svg className="w-full h-full transform -rotate-90">
                        <circle
                            cx="48"
                            cy="48"
                            r="44"
                            fill="none"
                            stroke="rgba(255,255,255,0.1)"
                            strokeWidth="4"
                        />
                        <circle
                            cx="48"
                            cy="48"
                            r="44"
                            fill="none"
                            stroke={mode === 'work' ? '#ef4444' : '#22c55e'}
                            strokeWidth="4"
                            strokeLinecap="round"
                            strokeDasharray={`${2 * Math.PI * 44}`}
                            strokeDashoffset={`${2 * Math.PI * 44 * (1 - progress / 100)}`}
                            className="transition-all duration-1000"
                        />
                    </svg>
                    <div className="absolute inset-0 flex items-center justify-center">
                        <span className={clsx(
                            "text-2xl font-mono font-bold",
                            mode === 'work' ? 'text-red-400' : 'text-green-400'
                        )}>
                            {formatTime(timeLeft)}
                        </span>
                    </div>
                </div>

                {/* Controls */}
                <div className="flex items-center gap-2">
                    <button
                        onClick={resetPomodoro}
                        className="p-2 text-gray-500 hover:text-white transition-colors rounded-lg hover:bg-white/5"
                    >
                        <RotateCcw size={16} />
                    </button>
                    <button
                        onClick={togglePomodoro}
                        className={clsx(
                            "p-3 rounded-full transition-all",
                            mode === 'work'
                                ? 'bg-red-500/20 text-red-400 hover:bg-red-500/30'
                                : 'bg-green-500/20 text-green-400 hover:bg-green-500/30'
                        )}
                    >
                        {isRunning ? <Pause size={18} /> : <Play size={18} className="ml-0.5" />}
                    </button>
                    <button
                        onClick={() => setPomodoroMode(mode === 'work' ? 'break' : 'work')}
                        className="p-2 text-gray-500 hover:text-white transition-colors rounded-lg hover:bg-white/5"
                        title={mode === 'work' ? 'Switch to Break' : 'Switch to Work'}
                    >
                        {mode === 'work' ? <Coffee size={16} /> : <Brain size={16} />}
                    </button>
                </div>
            </div>
        </div>
    );
}
