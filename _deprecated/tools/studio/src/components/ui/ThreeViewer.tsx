import { Suspense, useState, useEffect, Component, type ReactNode } from 'react';
import { Box } from 'lucide-react';

interface ThreeViewerProps {
    url: string;
    fileName: string;
    className?: string;
}

// Error boundary to catch Three.js initialization errors
class ThreeErrorBoundary extends Component<{ children: ReactNode, fallback: ReactNode }, { hasError: boolean }> {
    constructor(props: { children: ReactNode, fallback: ReactNode }) {
        super(props);
        this.state = { hasError: false };
    }

    static getDerivedStateFromError() {
        return { hasError: true };
    }

    componentDidCatch(error: Error) {
        console.warn('ThreeViewer error:', error.message);
    }

    render() {
        if (this.state.hasError) {
            return this.props.fallback;
        }
        return this.props.children;
    }
}

// Lazy loaded Three.js components to avoid module initialization errors
const ThreeCanvas = ({ url, fileName }: { url: string, fileName: string }) => {
    const [ThreeComponents, setThreeComponents] = useState<{
        Canvas: typeof import('@react-three/fiber').Canvas;
        useLoader: typeof import('@react-three/fiber').useLoader;
        OrbitControls: typeof import('@react-three/drei').OrbitControls;
        Stage: typeof import('@react-three/drei').Stage;
        Center: typeof import('@react-three/drei').Center;
        STLLoader: any;
        OBJLoader: any;
        GCodeLoader: any;
    } | null>(null);
    const [error, setError] = useState(false);

    useEffect(() => {
        let mounted = true;

        const loadThree = async () => {
            try {
                const [fiber, drei, stl, obj, gcode] = await Promise.all([
                    import('@react-three/fiber'),
                    import('@react-three/drei'),
                    import('three/examples/jsm/loaders/STLLoader'),
                    import('three/examples/jsm/loaders/OBJLoader'),
                    import('three/examples/jsm/loaders/GCodeLoader'),
                ]);

                if (mounted) {
                    setThreeComponents({
                        Canvas: fiber.Canvas,
                        useLoader: fiber.useLoader,
                        OrbitControls: drei.OrbitControls,
                        Stage: drei.Stage,
                        Center: drei.Center,
                        STLLoader: stl.STLLoader,
                        OBJLoader: obj.OBJLoader,
                        GCodeLoader: gcode.GCodeLoader,
                    });
                }
            } catch (e) {
                console.warn('Failed to load Three.js:', e);
                if (mounted) setError(true);
            }
        };

        loadThree();
        return () => { mounted = false; };
    }, []);

    if (error) {
        return (
            <div className="flex items-center justify-center h-full text-gray-500 text-xs">
                <span>3D Preview unavailable</span>
            </div>
        );
    }

    if (!ThreeComponents) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-accent"></div>
            </div>
        );
    }

    const { Canvas, useLoader, OrbitControls, Stage, Center, STLLoader, OBJLoader, GCodeLoader } = ThreeComponents;
    const extension = fileName.split('.').pop()?.toLowerCase();

    // Model components defined inline to use dynamic imports
    const STLModel = () => {
        const geometry = useLoader(STLLoader, url);
        return (
            <mesh geometry={geometry} castShadow receiveShadow>
                <meshStandardMaterial color="#3b82f6" roughness={0.5} metalness={0.1} />
            </mesh>
        );
    };

    const OBJModel = () => {
        const object = useLoader(OBJLoader, url);
        return <primitive object={object} />;
    };

    const GCodeModel = () => {
        const object = useLoader(GCodeLoader, url);
        return <primitive object={object} />;
    };

    const ModelComponent = () => {
        if (extension === 'stl') return <STLModel />;
        if (extension === 'obj') return <OBJModel />;
        if (extension === 'gcode') return <GCodeModel />;
        return null;
    };

    return (
        <Canvas shadows dpr={[1, 2]} camera={{ position: [0, 0, 150], fov: 50 }}>
            <Suspense fallback={null}>
                <Stage environment="city" intensity={0.5} shadows={{ type: 'contact', opacity: 0.5, blur: 2 }}>
                    <Center>
                        <ModelComponent />
                    </Center>
                </Stage>
            </Suspense>
            <OrbitControls autoRotate autoRotateSpeed={0.5} makeDefault />
        </Canvas>
    );
};

export function ThreeViewer({ url, fileName, className }: ThreeViewerProps) {
    return (
        <div className={`relative bg-neutral-950 border border-white/10 rounded-lg overflow-hidden ${className}`}>
            <div className="absolute top-2 left-2 z-10 flex items-center gap-2 text-xs font-mono text-gray-400 bg-black/50 px-2 py-1 rounded">
                <Box size={12} className="text-accent" />
                <span>{fileName}</span>
            </div>

            <ThreeErrorBoundary fallback={
                <div className="flex items-center justify-center h-full text-gray-500 text-xs">
                    <span>3D Preview failed to load</span>
                </div>
            }>
                <ThreeCanvas url={url} fileName={fileName} />
            </ThreeErrorBoundary>

            <div className="absolute bottom-2 right-2 text-[10px] text-gray-600 font-mono pointer-events-none">
                LMB: Rotate | RMB: Pan | Scr: Zoom
            </div>
        </div>
    );
}
