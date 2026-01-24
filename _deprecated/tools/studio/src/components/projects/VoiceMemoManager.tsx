import { useState, useRef, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { toast } from 'sonner';
import { db } from '../../lib/db';
import { Mic, Square, Play, Pause, Trash2, Upload, Music, Volume2 } from 'lucide-react';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';
import { useSpeechToText } from '../../hooks/useSpeechToText';

interface VoiceMemoManagerProps {
    projectId: number;
}

export function VoiceMemoManager({ projectId }: VoiceMemoManagerProps) {
    const [isRecording, setIsRecording] = useState(false);
    const [recordingTime, setRecordingTime] = useState(0);
    const mediaRecorderRef = useRef<MediaRecorder | null>(null);
    const chunksRef = useRef<Blob[]>([]);
    const timerRef = useRef<NodeJS.Timeout | null>(null);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const transcriptRef = useRef<string>(''); // Accumulate transcript

    const { toggleListening: toggleSpeech, isListening: isSpeechListening } = useSpeechToText({
        onTranscript: (text) => {
            transcriptRef.current += " " + text;
        },
        continuous: true // Keep listening
    });

    // Query audio files for this project
    const audioFiles = useLiveQuery(
        () => db.project_files
            .where('project_id').equals(projectId)
            .and(f => f.type.startsWith('audio/'))
            .reverse()
            .sortBy('created_at')
    );

    const startRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
            const mediaRecorder = new MediaRecorder(stream);
            mediaRecorderRef.current = mediaRecorder;
            chunksRef.current = [];
            transcriptRef.current = ''; // Reset transcript

            // Start Speech Recognition if available
            toggleSpeech();

            mediaRecorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    chunksRef.current.push(e.data);
                }
            };

            mediaRecorder.onstop = async () => {
                // Stop Speech
                if (isSpeechListening) toggleSpeech();

                const blob = new Blob(chunksRef.current, { type: 'audio/webm' });
                await db.project_files.add({
                    project_id: projectId,
                    name: `Voice Memo ${new Date().toLocaleString()}`,
                    type: 'audio/webm',
                    content: blob,
                    created_at: new Date(),
                    extracted_metadata: { transcript: transcriptRef.current.trim() }
                });
                setRecordingTime(0);

                // Stop all tracks to release mic
                stream.getTracks().forEach(track => track.stop());
            };

            mediaRecorder.start();
            setIsRecording(true);

            // Timer
            const startTime = Date.now();
            timerRef.current = setInterval(() => {
                setRecordingTime(Math.floor((Date.now() - startTime) / 1000));
            }, 1000);

        } catch (err) {
            console.error("Error accessing microphone:", err);
            toast.error("Could not access microphone. Check permissions.");
        }
    };

    const stopRecording = () => {
        if (mediaRecorderRef.current && isRecording) {
            mediaRecorderRef.current.stop();
            // Speech stop handled in onstop above
            setIsRecording(false);
            if (timerRef.current) clearInterval(timerRef.current);
        }
    };

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const files = e.target.files;
        if (!files) return;

        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (file.type.startsWith('audio/')) {
                await db.project_files.add({
                    project_id: projectId,
                    name: file.name,
                    type: file.type,
                    content: file,
                    created_at: new Date()
                });
            } else {
                toast.warning(`${file.name} is not an audio file.`);
            }
        }

        if (fileInputRef.current) fileInputRef.current.value = '';
    };

    const deleteAudio = async (id: number) => {
        if (confirm("Delete this recording?")) {
            await db.project_files.delete(id);
        }
    };

    return (
        <div className="bg-neutral-900 border border-white/10 rounded-xl p-6 relative overflow-hidden group">
            <div className="flex justify-between items-start mb-6">
                <div>
                    <h3 className="text-xl font-black text-white uppercase tracking-tighter flex items-center gap-2">
                        <Mic className="text-accent" size={20} />
                        Sonic Logs
                    </h3>
                    <p className="text-xs text-gray-500 font-mono mt-1">VOICE MEMOS & AUDIO SAMPLES</p>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => fileInputRef.current?.click()}
                        className="bg-white/5 hover:bg-white/10 text-gray-300 p-2 rounded-full transition-colors"
                        title="Upload Audio File"
                    >
                        <Upload size={18} />
                    </button>
                    <input
                        type="file"
                        ref={fileInputRef}
                        onChange={handleFileUpload}
                        className="hidden"
                        accept="audio/*"
                        multiple
                    />
                </div>
            </div>

            {/* Recorder Interface */}
            <div className="flex items-center justify-center mb-8 py-4 bg-black/40 rounded-lg border border-white/5 relative">
                <AnimatePresence mode="wait">
                    {isRecording ? (
                        <motion.button
                            key="stop"
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.8, opacity: 0 }}
                            onClick={stopRecording}
                            className="w-16 h-16 rounded-full bg-red-500 flex items-center justify-center hover:bg-red-600 transition-colors shadow-[0_0_20px_rgba(239,68,68,0.5)] animate-pulse"
                        >
                            <Square fill="white" className="text-white" size={24} />
                        </motion.button>
                    ) : (
                        <motion.button
                            key="record"
                            initial={{ scale: 0.8, opacity: 0 }}
                            animate={{ scale: 1, opacity: 1 }}
                            exit={{ scale: 0.8, opacity: 0 }}
                            onClick={startRecording}
                            className="w-16 h-16 rounded-full bg-accent/10 border-2 border-accent text-accent flex items-center justify-center hover:bg-accent hover:text-black transition-all"
                        >
                            <Mic size={28} />
                        </motion.button>
                    )}
                </AnimatePresence>

                {isRecording && (
                    <div className="absolute -bottom-8 font-mono text-xs text-red-500 font-bold animate-pulse">
                        RECORDING {new Date(recordingTime * 1000).toISOString().substr(14, 5)}
                    </div>
                )}
            </div>

            {/* List */}
            <div className="space-y-3 max-h-60 overflow-y-auto custom-scrollbar pr-2">
                {audioFiles?.map(file => (
                    <AudioItem key={file.id} file={file} onDelete={() => deleteAudio(file.id!)} />
                ))}
                {audioFiles?.length === 0 && (
                    <div className="text-center text-gray-600 text-xs uppercase p-4 border border-dashed border-white/5 rounded">
                        No Audio Logs Recorded
                    </div>
                )}
            </div>
        </div>
    );
}

function AudioItem({ file, onDelete }: { file: any, onDelete: () => void }) {
    const [isPlaying, setIsPlaying] = useState(false);
    const audioRef = useRef<HTMLAudioElement>(null);
    const [url, setUrl] = useState<string>('');

    useEffect(() => {
        const objectUrl = URL.createObjectURL(file.content);
        setUrl(objectUrl);
        return () => URL.revokeObjectURL(objectUrl);
    }, [file]);

    const togglePlay = () => {
        if (!audioRef.current) return;
        if (isPlaying) {
            audioRef.current.pause();
        } else {
            audioRef.current.play();
        }
        setIsPlaying(!isPlaying);
    };

    return (
        <div className="group">
            <div className="bg-white/5 border border-white/5 rounded p-3 flex items-center gap-3 hover:border-white/20 transition-colors">
                <button
                    onClick={togglePlay}
                    className={clsx(
                        "w-8 h-8 rounded-full flex items-center justify-center shrink-0 transition-colors",
                        isPlaying ? "bg-accent text-black" : "bg-black text-white group-hover:bg-accent group-hover:text-black"
                    )}
                >
                    {isPlaying ? <Pause size={14} fill="currentColor" /> : <Play size={14} fill="currentColor" className="ml-0.5" />}
                </button>

                <div className="flex-1 min-w-0">
                    <div className="text-sm font-bold text-gray-200 truncate">{file.name}</div>
                    <div className="text-[10px] text-gray-500 font-mono flex items-center gap-2">
                        {new Date(file.created_at).toLocaleDateString()}
                        <span className="opacity-50">•</span>
                        {(file.content.size / 1024 / 1024).toFixed(2)} MB
                    </div>
                </div>

                <button
                    onClick={onDelete}
                    className="text-gray-600 hover:text-red-500 transition-colors p-2"
                >
                    <Trash2 size={14} />
                </button>

                <audio
                    ref={audioRef}
                    src={url}
                    onEnded={() => setIsPlaying(false)}
                    className="hidden"
                />
            </div>

            {/* Transcript Display */}
            {file.extracted_metadata?.transcript && (
                <div className="mt-1 ml-11 text-xs text-gray-400 italic bg-black/20 p-2 rounded border-l-2 border-accent/20">
                    "{file.extracted_metadata.transcript}"
                </div>
            )}
        </div>
    );
}
