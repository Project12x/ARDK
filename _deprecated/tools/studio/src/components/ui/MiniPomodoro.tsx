import { Play, Pause, RotateCcw, Brain, Coffee, X } from 'lucide-react';
import { useUIStore } from '../../store/useStore';
import { useEffect } from 'react';
import { toast } from 'sonner';
import clsx from 'clsx';

export function MiniPomodoro() {
    const { pomodoro, togglePomodoro, resetPomodoro, setPomodoroMode, hidePomodoro, nextPomodoroSession } = useUIStore();
    const { timeLeft, isRunning, mode, isVisible, isFinished } = pomodoro;

    // Audio Ref
    const audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();

    const playBeep = () => {
        const oscillator = audioContext.createOscillator();
        const gainNode = audioContext.createGain();
        oscillator.connect(gainNode);
        gainNode.connect(audioContext.destination);
        oscillator.type = 'sine';
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
        oscillator.frequency.exponentialRampToValueAtTime(400, audioContext.currentTime + 0.5);
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5);
        oscillator.start();
        oscillator.stop(audioContext.currentTime + 0.5);
    };

    // Trigger sound on finish
    useEffect(() => {
        if (isFinished) {
            playBeep();
            toast.success("Timer Finished!", { description: "Take a break or start next session." });
        }
    }, [isFinished]);

    // Only render if visible
    if (!isVisible) {
        return null;
    }

    const formatTime = (seconds: number) => {
        const mins = Math.floor(seconds / 60);
        const secs = seconds % 60;
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    };

    return (
        <div className={clsx(
            "flex items-center gap-3 px-4 py-1.5 bg-black/40 rounded-full border border-white/5 animate-in fade-in slide-in-from-top-2 group",
            isFinished && "animate-pulse border-accent/50 bg-accent/10"
        )}>
            {/* Mode Indicator */}
            <button
                onClick={() => isFinished ? nextPomodoroSession() : setPomodoroMode(mode === 'work' ? 'break' : 'work')}
                className={clsx(
                    "flex items-center gap-2 transition-colors",
                    mode === 'work' ? "text-red-400" : "text-green-400"
                )}
                title={isFinished ? "Start Next Session" : (mode === 'work' ? "Switch to Break" : "Switch to Work")}
            >
                {mode === 'work' ? <Brain size={14} /> : <Coffee size={14} />}
                <span className="text-xs font-mono font-bold tracking-tighter w-12 text-center">
                    {isFinished ? "DONE" : formatTime(timeLeft)}
                </span>
            </button>

            <div className="w-px h-4 bg-white/10" />

            {/* Controls */}
            <div className="flex items-center gap-1.5">
                {isFinished ? (
                    <button
                        onClick={nextPomodoroSession}
                        className="p-1 rounded-full text-white hover:bg-white/10 transition-colors text-xs font-bold uppercase px-3"
                    >
                        Next
                    </button>
                ) : (
                    <>
                        <button
                            onClick={togglePomodoro}
                            className={clsx(
                                "p-1.5 rounded-full transition-all",
                                isRunning
                                    ? "text-white hover:bg-white/10"
                                    : (mode === 'work' ? "text-red-400 hover:bg-red-500/10" : "text-green-400 hover:bg-green-500/10")
                            )}
                        >
                            {isRunning ? <Pause size={14} /> : <Play size={14} className="ml-0.5" />}
                        </button>
                        <button
                            onClick={resetPomodoro}
                            className="p-1.5 text-gray-600 hover:text-white transition-colors"
                        >
                            <RotateCcw size={12} />
                        </button>
                    </>
                )}
            </div>

            {/* Divider for Close Button */}
            <div className="w-px h-4 bg-white/10 ml-1 opacity-0 group-hover:opacity-100 transition-opacity" />

            {/* Close Button (Hover only) */}
            <button
                onClick={hidePomodoro}
                className="p-1 text-gray-600 hover:text-red-400 transition-colors opacity-0 group-hover:opacity-100"
                title="Hide Timer"
            >
                <X size={12} />
            </button>
        </div>
    );
}
