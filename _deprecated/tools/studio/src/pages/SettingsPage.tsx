import { useState } from 'react';
import { GeneralSettings } from '../components/settings/GeneralSettings';
import { IntegrationSettings } from '../components/settings/IntegrationSettings';
import { VendorManager } from '../components/purchasing/VendorManager';
import { Network, HardDrive, Sliders, ShoppingCart, Palette, Monitor, Music as MusicIcon } from 'lucide-react';
import { clsx } from 'clsx';
import { useUIStore } from '../store/useStore';

function AppearanceSettings() {
    const { mainTheme, setMainTheme, musicTheme, setMusicTheme } = useUIStore();
    const themes = ['default', 'music', 'synthwave', 'light', 'midnight', 'forest'];

    return (
        <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
            <div>
                <h3 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                    <Palette className="text-accent" size={20} /> Appearance & Themes
                </h3>
                <p className="text-gray-500 font-mono text-sm mb-6">Customize the visual identity of the workspace.</p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    {/* Main Theme */}
                    <div className="bg-white/5 border border-white/5 rounded-xl p-6 hover:border-white/10 transition-colors">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 bg-blue-500/20 text-blue-400 rounded-lg">
                                <Monitor size={20} />
                            </div>
                            <div>
                                <h4 className="font-bold text-white">Main Application Theme</h4>
                                <p className="text-xs text-gray-500 font-mono">Dashboard, Projects, Inventory</p>
                            </div>
                        </div>
                        <div className="space-y-2">
                            {themes.map(t => (
                                <button
                                    key={`main-${t}`}
                                    onClick={() => setMainTheme(t)}
                                    className={clsx(
                                        "w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-all text-sm font-medium",
                                        mainTheme === t
                                            ? "bg-accent/20 border-accent text-white shadow-[0_0_10px_rgba(var(--accent-rgb),0.2)]"
                                            : "bg-black/20 border-white/5 text-gray-400 hover:bg-white/5 hover:text-white"
                                    )}
                                >
                                    <span className="capitalize">{t}</span>
                                    {mainTheme === t && <div className="w-2 h-2 rounded-full bg-accent animate-pulse" />}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Music Theme */}
                    <div className="bg-white/5 border border-white/5 rounded-xl p-6 hover:border-white/10 transition-colors">
                        <div className="flex items-center gap-3 mb-4">
                            <div className="p-2 bg-purple-500/20 text-purple-400 rounded-lg">
                                <MusicIcon size={20} />
                            </div>
                            <div>
                                <h4 className="font-bold text-white">Music Section Theme</h4>
                                <p className="text-xs text-gray-500 font-mono">Songs, Albums, Creative Flow</p>
                            </div>
                        </div>
                        <div className="space-y-2">
                            {themes.map(t => (
                                <button
                                    key={`music-${t}`}
                                    onClick={() => setMusicTheme(t)}
                                    className={clsx(
                                        "w-full flex items-center justify-between px-4 py-3 rounded-lg border transition-all text-sm font-medium",
                                        musicTheme === t
                                            ? "bg-purple-500/20 border-purple-500 text-white shadow-[0_0_10px_rgba(168,85,247,0.2)]"
                                            : "bg-black/20 border-white/5 text-gray-400 hover:bg-white/5 hover:text-white"
                                    )}
                                >
                                    <span className="capitalize">{t}</span>
                                    {musicTheme === t && <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

export function SettingsPage() {
    const [activeTab, setActiveTab] = useState<'general' | 'integrations' | 'purchasing' | 'appearance'>('appearance');

    const tabs = [
        { id: 'purchasing', label: 'Purchasing & Vendors', icon: ShoppingCart },
        { id: 'integrations', label: 'Integration Hub', icon: Network },
        { id: 'general', label: 'System & Data', icon: HardDrive },
        { id: 'appearance', label: 'Appearance', icon: Palette },
    ];

    return (
        <div className="max-w-4xl mx-auto h-full flex flex-col">
            <div className="mb-8">
                <h2 className="text-3xl font-black text-white uppercase tracking-tighter mb-2 flex items-center gap-3">
                    <Sliders className="text-accent" /> System Configuration
                </h2>
                <p className="text-gray-500 font-mono text-sm">Manage connections, data, and system preferences.</p>
            </div>

            <div className="flex flex-col md:flex-row gap-8 h-full min-h-0">
                {/* Sidebar Navigation */}
                <div className="w-full md:w-64 flex-shrink-0 space-y-2">
                    {tabs.map(tab => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as typeof activeTab)}
                                className={clsx(
                                    "w-full flex items-center gap-3 px-4 py-3 rounded-lg transition-all text-sm font-bold uppercase tracking-wide",
                                    isActive
                                        ? "bg-accent text-black shadow-lg shadow-accent/20 translate-x-1"
                                        : "hover:bg-white/5 text-gray-500 hover:text-white"
                                )}
                            >
                                <Icon size={18} />
                                {tab.label}
                            </button>
                        );
                    })}
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto pb-20">
                    {activeTab === 'general' && <GeneralSettings />}
                    {activeTab === 'integrations' && <IntegrationSettings />}
                    {activeTab === 'purchasing' && <VendorManager />}
                    {activeTab === 'appearance' && <AppearanceSettings />}
                </div>
            </div>
        </div>
    );
}
