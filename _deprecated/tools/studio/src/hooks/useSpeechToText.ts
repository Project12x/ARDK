import { useState, useEffect, useCallback, useRef } from 'react';

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start: () => void;
    stop: () => void;
    onresult: (event: SpeechRecognitionEvent) => void;
    onend: () => void;
    onerror: (event: SpeechRecognitionErrorEvent) => void;
}

interface SpeechRecognitionEvent {
    resultIndex: number;
    results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
    length: number;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
    isFinal: boolean;
    [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionAlternative {
    transcript: string;
}

interface SpeechRecognitionErrorEvent extends Event {
    error: string;
}

export interface UseSpeechToTextProps {
    onTranscript: (text: string) => void;
    continuous?: boolean;
    interimResults?: boolean;
}

export function useSpeechToText({ onTranscript, continuous = false, interimResults = true }: UseSpeechToTextProps) {
    const [isListening, setIsListening] = useState(false);
    const [isSupported] = useState(() =>
        typeof window !== 'undefined' && ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window)
    );
    const recognitionRef = useRef<SpeechRecognition | null>(null);

    useEffect(() => {
        if (isSupported && !recognitionRef.current) {
            // @ts-ignore: Web Speech API types not standard in all envs
            const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
            recognitionRef.current = new SpeechRecognition();
            if (recognitionRef.current) {
                recognitionRef.current.continuous = continuous;
                recognitionRef.current.interimResults = interimResults;
                recognitionRef.current.lang = 'en-US';

                recognitionRef.current.onresult = (event: SpeechRecognitionEvent) => {
                    let finalTranscript = '';
                    for (let i = event.resultIndex; i < event.results.length; ++i) {
                        if (event.results[i].isFinal) {
                            finalTranscript += event.results[i][0].transcript;
                        }
                    }
                    if (finalTranscript) {
                        onTranscript(finalTranscript);
                    }
                };

                recognitionRef.current.onend = () => {
                    setIsListening(false);
                };

                recognitionRef.current.onerror = (event: SpeechRecognitionErrorEvent) => {
                    console.error("Speech recognition error", event.error);
                    setIsListening(false);
                };
            }
        }
    }, [isSupported, onTranscript, continuous, interimResults]);

    const toggleListening = useCallback(() => {
        if (!recognitionRef.current) {
            return;
        }

        if (isListening) {
            recognitionRef.current.stop();
            setIsListening(false); // Optimistic update
        } else {
            try {
                recognitionRef.current.start();
                setIsListening(true);
            } catch (err) {
                console.error("Failed to start speech recognition", err);
                setIsListening(false);
            }
        }
    }, [isListening]);

    return { isListening, toggleListening, isSupported };
}
