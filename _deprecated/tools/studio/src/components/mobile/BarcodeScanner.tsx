import { useEffect, useRef } from 'react';
import { Html5QrcodeScanner } from 'html5-qrcode';
import { X } from 'lucide-react';

interface BarcodeScannerProps {
    onScan: (decodedText: string) => void;
    onClose: () => void;
}

export function BarcodeScanner({ onScan, onClose }: BarcodeScannerProps) {
    const scannerRef = useRef<Html5QrcodeScanner | null>(null);

    useEffect(() => {
        // Initialize scanner
        // ID must match the div ID below
        const scanner = new Html5QrcodeScanner(
            "reader",
            { fps: 10, qrbox: { width: 250, height: 250 } },
            /* verbose= */ false
        );

        scanner.render(
            (decodedText) => {
                onScan(decodedText);
                // Optional: Close on first scan? Or keep open?
                // Let's keep specific behavior to parent, but usually we want to stop.
                scanner.clear();
                onClose();
            },
            (errorMessage) => {
                // ignore errors during scanning
            }
        );

        scannerRef.current = scanner;

        // Cleanup
        return () => {
            if (scannerRef.current) {
                scannerRef.current.clear().catch(err => console.error("Failed to clear scanner", err));
            }
        };
    }, [onScan, onClose]);

    return (
        <div className="fixed inset-0 z-[100] bg-black/90 flex flex-col items-center justify-center p-4">
            <div className="w-full max-w-md bg-neutral-900 rounded-xl overflow-hidden relative shadow-2xl border border-white/10">
                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 z-50 text-white bg-black/50 p-2 rounded-full hover:bg-red-500/50 transition-colors"
                >
                    <X size={24} />
                </button>
                <div className="p-4 text-center border-b border-white/10">
                    <h3 className="font-bold text-white">Scan Barcode / UPC</h3>
                    <p className="text-xs text-gray-400">Point camera at code</p>
                </div>
                <div id="reader" className="w-full h-[400px] bg-black overflow-hidden relative" />
                <style>{`
                    #reader__scan_region img { display: none; } /* Hide the example img */
                `}</style>
            </div>
        </div>
    );
}
