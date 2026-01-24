import { Maximize, Minimize } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Button } from './Button';
import clsx from 'clsx';

interface FullscreenToggleProps {
    targetRef: React.RefObject<HTMLElement>;
    className?: string;
}

export function FullscreenToggleButton({ targetRef, className }: FullscreenToggleProps) {
    const [isFullscreen, setIsFullscreen] = useState(false);

    useEffect(() => {
        const handleChange = () => {
            const isFull = document.fullscreenElement === targetRef.current;
            setIsFullscreen(isFull);
        };

        document.addEventListener('fullscreenchange', handleChange);
        return () => document.removeEventListener('fullscreenchange', handleChange);
    }, [targetRef]);

    const toggleFullscreen = async () => {
        if (!targetRef.current) return;

        try {
            if (!document.fullscreenElement) {
                await targetRef.current.requestFullscreen();
            } else {
                if (document.exitFullscreen) {
                    await document.exitFullscreen();
                }
            }
        } catch (err) {
            console.error("Fullscreen toggle failed:", err);
        }
    };

    return (
        <Button
            variant="outline"
            size="sm"
            onClick={toggleFullscreen}
            className={clsx("backdrop-blur-md bg-black/50 hover:bg-white/10", className, isFullscreen && "bg-accent/20 border-accent text-accent")}
            title={isFullscreen ? "Exit Fullscreen (Esc)" : "Enter Fullscreen"}
        >
            {isFullscreen ? <Minimize size={16} /> : <Maximize size={16} />}
        </Button>
    );
}
