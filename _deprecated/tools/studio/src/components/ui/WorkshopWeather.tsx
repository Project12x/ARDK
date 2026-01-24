import { useEffect, useState } from 'react';
import { Cloud, CloudRain, Droplets, AlertTriangle, Sun } from 'lucide-react';

interface WeatherData {
    current: {
        temperature_2m: number;
        relative_humidity_2m: number;
        weather_code: number;
    };
    current_units: {
        temperature_2m: string;
        relative_humidity_2m: string;
    };
}

export function WorkshopWeather() {
    const [weather, setWeather] = useState<WeatherData | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        if (!navigator.geolocation) {
            setError("Geolocation not supported");
            setLoading(false);
            return;
        }

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                try {
                    const { latitude, longitude } = position.coords;
                    const res = await fetch(
                        `https://api.open-meteo.com/v1/forecast?latitude=${latitude}&longitude=${longitude}&current=temperature_2m,relative_humidity_2m,weather_code,wind_speed_10m&temperature_unit=fahrenheit&wind_speed_unit=mph`
                    );

                    if (!res.ok) throw new Error("Weather fetch failed");

                    const data = await res.json();
                    setWeather(data);
                } catch (err) {
                    setError("Failed to load weather data");
                    console.error(err);
                } finally {
                    setLoading(false);
                }
            },
            () => {
                setError("Location access denied");
                setLoading(false);
            }
        );
    }, []);

    // Conditions Logic
    const getAdvice = (temp: number, humidity: number) => {
        const warnings = [];
        const goods = [];

        if (humidity > 60) warnings.push("Poor for Spray Painting / Resin (High Humidity)");
        else goods.push("Good for Painting");

        if (humidity < 30) warnings.push("Static Electricity Risk (Low Humidity)");

        if (temp < 50) warnings.push("Too Cold for Glue Curing");
        if (temp > 85) warnings.push("Fast Pot Life for Resins");

        return { warnings, goods };
    };

    const getWeatherIcon = (code: number) => {
        // WMO Weather interpretation codes (http://www.nodc.noaa.gov/archive/arc0021/0002199/1.1/data/0-data/HTML/WMO-CODE/WMO4677.HTM)
        if (code <= 1) return <Sun className="text-yellow-400" size={24} />;
        if (code <= 3) return <Cloud className="text-gray-400" size={24} />;
        if (code <= 67) return <CloudRain className="text-blue-400" size={24} />;
        if (code <= 77) return <CloudRain className="text-white" size={24} />; // Snow-ish
        return <Cloud className="text-gray-500" size={24} />;
    };

    const [time, setTime] = useState(new Date());

    useEffect(() => {
        const timer = setInterval(() => setTime(new Date()), 1000);
        return () => clearInterval(timer);
    }, []);

    if (loading) return <div className="animate-pulse h-24 bg-white/5 rounded-xl" />;
    if (error || !weather) return (
        <div className="bg-red-900/10 border border-red-900/30 p-4 rounded-xl flex items-center gap-3">
            <AlertTriangle className="text-red-500" />
            <span className="text-xs text-red-400">Weather Unavailable</span>
        </div>
    );

    const { temperature_2m, relative_humidity_2m, weather_code } = weather.current;
    const { warnings, goods } = getAdvice(temperature_2m, relative_humidity_2m);

    return (
        <div className="bg-black/40 border border-white/10 rounded-xl p-4 flex flex-col justify-between relative overflow-hidden group hover:border-accent/50 transition-colors h-full min-h-[140px]">
            {/* Background Gradient */}
            <div className="absolute top-0 right-0 w-32 h-32 bg-accent/5 rounded-full blur-3xl -translate-y-1/2 translate-x-1/2 pointer-events-none" />

            <div className="flex items-start justify-between relative z-10">
                <div>
                    <div className="flex flex-col">
                        <div className="flex items-baseline gap-1">
                            <span className="text-2xl font-semibold text-white tracking-tight">
                                {time.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                            </span>
                            <span className="text-xs font-medium text-gray-400">
                                {time.getHours() >= 12 ? 'PM' : 'AM'}
                            </span>
                        </div>
                        <span className="text-xs font-mono text-gray-500 uppercase tracking-widest">
                            {time.toLocaleDateString([], { weekday: 'short', month: 'short', day: 'numeric' })}
                        </span>
                    </div>
                </div>

                <div className="text-right flex flex-col items-end">
                    <div className="flex items-center gap-2">
                        {getWeatherIcon(weather_code)}
                        <span className="text-xl font-medium text-white">{Math.round(temperature_2m)}°F</span>
                    </div>

                    <div className="flex items-center gap-1 text-blue-400 mt-1">
                        <Droplets size={12} />
                        <span className="font-mono text-sm font-medium">{relative_humidity_2m}%</span>
                    </div>
                </div>
            </div>

            <div className="mt-4 space-y-1 relative z-10">
                {warnings.slice(0, 2).map((w, i) => (
                    <div key={i} className="flex items-center gap-2 text-red-400 text-xs bg-red-900/10 px-2 py-1 rounded border border-red-900/20">
                        <AlertTriangle size={10} />
                        {w}
                    </div>
                ))}
                {warnings.length === 0 && goods.map((g, i) => (
                    <div key={i} className="flex items-center gap-2 text-green-400 text-xs bg-green-900/10 px-2 py-1 rounded border border-green-900/20">
                        <Sun size={10} />
                        {g}
                    </div>
                ))}
            </div>
        </div>
    );
}
