import {
    Keyboard,
    Sparkles,
    Inbox,
    HelpCircle,
    Command,
    Settings,
    Database,
    Bot,

    Workflow,
    Target,
    Palette
} from 'lucide-react';
import { Card } from '../components/ui/Card';

export function HelpPage() {
    return (
        <div className="p-8 max-w-5xl mx-auto space-y-10 pb-20">
            {/* Header */}
            <div className="flex items-center gap-4 border-b border-white/10 pb-6">
                <div className="p-3 bg-accent/10 rounded-xl">
                    <HelpCircle size={28} className="text-accent" />
                </div>
                <div>
                    <h1 className="text-3xl font-black text-white uppercase tracking-tight">Help & Documentation</h1>
                    <p className="text-gray-400 text-sm font-mono">
                        Master the WorkshopOS: Commands, AI Oracle, and Workflow
                    </p>
                </div>
            </div>

            {/* Quick Start / Core Loop */}
            <Section title="The Core Loop" icon={<Workflow className="text-accent" />}>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="bg-black/30 p-4 rounded-lg border border-white/10">
                        <div className="text-accent font-black text-4xl mb-2 opacity-50">01</div>
                        <h3 className="font-bold text-white mb-2">Capture</h3>
                        <p className="text-sm text-gray-400">
                            Use <kbd className="bg-white/10 px-1 rounded mx-1">Ctrl+Shift+Space</kbd> anywhere to dump ideas. Don't think, just capture. Everything goes to the Inbox.
                        </p>
                    </div>
                    <div className="bg-black/30 p-4 rounded-lg border border-white/10">
                        <div className="text-accent font-black text-4xl mb-2 opacity-50">02</div>
                        <h3 className="font-bold text-white mb-2">Triage</h3>
                        <p className="text-sm text-gray-400">
                            Process your Inbox. Turn items into <strong>Projects</strong>, <strong>Tasks</strong>, or <strong>Reference</strong> notes. Use the AI Oracle to auto-suggest categories.
                        </p>
                    </div>
                    <div className="bg-black/30 p-4 rounded-lg border border-white/10">
                        <div className="text-accent font-black text-4xl mb-2 opacity-50">03</div>
                        <h3 className="font-bold text-white mb-2">Execute</h3>
                        <p className="text-sm text-gray-400">
                            Work from the <strong>Dashboard</strong>. Track progress, check off tasks, and update project phases.
                        </p>
                    </div>
                </div>
            </Section>

            {/* Global Command Bar */}
            <Section title="Global Command Bar" icon={<Command className="text-accent" />}>
                <div className="prose prose-invert max-w-none text-gray-300 space-y-4">
                    <p>
                        Access the Command Bar anytime with <kbd className="bg-white/10 px-1.5 py-0.5 rounded">Ctrl+K</kbd>. It's the fastest way to navigate and perform actions.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                        <CommandRow command="/p or /projects" description="Go to Projects list" />
                        <CommandRow command="/goals" description="Open Goals & Strategy" />
                        <CommandRow command="/new" description="Create a new Project" />
                        <CommandRow command="/inv or /inventory" description="Go to Inventory" />
                        <CommandRow command="/settings" description="Open Settings" />
                        <CommandRow command="/help" description="Open this Help page" />
                        <CommandRow command="/theme [name]" description="Switch theme (e.g., /theme midnight)" />
                        <CommandRow command="> [search]" description="Search all projects and tasks" />
                    </div>
                </div>
            </Section>

            {/* Oracle / AI */}
            <Section title="Workshop Oracle" icon={<Bot className="text-accent" />}>
                <div className="space-y-4">
                    <p className="text-gray-300">
                        The Oracle is a context-aware AI assistant integrated into your workshop data. It knows about your projects, inventory, and goals.
                    </p>
                    <div className="bg-white/5 border border-white/10 rounded-lg p-4">
                        <h4 className="text-sm font-bold text-gray-300 mb-3 uppercase tracking-wider">Example Prompts</h4>
                        <ul className="space-y-3">
                            <li className="flex gap-3 text-sm">
                                <span className="text-accent">●</span>
                                <span className="text-gray-400">"I need to build a workbench. Create a project for it with a list of standard materials."</span>
                            </li>
                            <li className="flex gap-3 text-sm">
                                <span className="text-accent">●</span>
                                <span className="text-gray-400">"Create a yearly goal: 'Master CNC Machining' with motivation 'To build custom guitar bodies'."</span>
                            </li>
                            <li className="flex gap-3 text-sm">
                                <span className="text-accent">●</span>
                                <span className="text-gray-400">"Check if I have enough M5 screws for the 3D printer upgrade project."</span>
                            </li>
                            <li className="flex gap-3 text-sm">
                                <span className="text-accent">●</span>
                                <span className="text-gray-400">"What are the high priority tasks for today?"</span>
                            </li>
                        </ul>
                    </div>

                    <div className="bg-accent/10 border border-accent/20 rounded-lg p-4">
                        <h4 className="text-sm font-bold text-accent mb-2 uppercase tracking-wider flex items-center gap-2">
                            <Sparkles size={14} /> New: AI Diagnostics
                        </h4>
                        <p className="text-sm text-gray-300 mb-2">
                            Unsure if your API keys are working?
                        </p>
                        <ul className="list-disc pl-5 text-sm text-gray-400 space-y-1">
                            <li>Type <code className="text-white bg-black/30 px-1 rounded">/test-models</code> in the chat to run a full connectivity test for all providers.</li>
                            <li>Hover over the status lights in <strong>Settings</strong> to see which specific models (e.g., GPT-4o, Gemini 1.5 Pro) are available.</li>
                        </ul>
                    </div>

                    <p className="text-xs text-gray-500 italic">
                        Note: Requires a valid Gemini API Key set in Settings &gt; API Keys.
                    </p>
                </div>
            </Section>

            {/* Asset Management */}
            <Section title="Asset Management" icon={<Database className="text-accent" />}>
                <div className="space-y-4">
                    <p className="text-gray-300">
                        Track your physical equipment, tools, software licenses, and high-value items in the <strong>Asset Registry</strong>.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="space-y-2">
                            <h4 className="font-bold text-white text-sm uppercase">Actions</h4>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li className="flex items-center gap-2">
                                    <span className="bg-white/10 p-1 rounded"><Sparkles size={12} /></span>
                                    <strong>Register:</strong> Click "Register Asset" to add new items.
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="bg-white/10 p-1 rounded"><Bot size={12} /></span>
                                    <strong>Edit:</strong> Click the Pencil icon on any asset card to modify details like Value, Location, or Serial Number.
                                </li>
                                <li className="flex items-center gap-2">
                                    <span className="bg-white/10 p-1 rounded"><Command size={12} /></span>
                                    <strong>Delete:</strong> Click the Trash icon to remove an asset (requires confirmation).
                                </li>
                            </ul>
                        </div>
                        <div className="bg-black/30 p-4 rounded-lg border border-white/10">
                            <h4 className="font-bold text-white text-sm uppercase mb-2">Tracking Fields</h4>
                            <p className="text-xs text-gray-400 mb-2">
                                Detailed records help with insurance and organization.
                            </p>
                            <div className="flex flex-wrap gap-2">
                                {['Value ($)', 'Purchase Date', 'Location', 'Serial Number', 'Make/Model', 'Category'].map(tag => (
                                    <span key={tag} className="text-xs bg-white/5 border border-white/10 px-2 py-1 rounded text-gray-300">
                                        {tag}
                                    </span>
                                ))}
                            </div>
                        </div>
                    </div>
                </div>
            </Section>

            {/* Goals & Strategy */}
            <Section title="Goals & Strategy" icon={<Target className="text-accent" />}>
                <div className="space-y-4">
                    <p className="text-gray-300">
                        Define high-level objectives. The new Goal system tracks <strong>Motivation</strong> and <strong>Success Criteria</strong> to help the AI align with your long-term vision.
                    </p>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                        <div className="bg-black/30 p-4 rounded-lg border border-white/10">
                            <h4 className="font-bold text-white text-sm uppercase mb-2">New Fields</h4>
                            <ul className="space-y-2 text-sm text-gray-400">
                                <li><strong>Motivation:</strong> Why do you want this? (e.g., "To become self-sufficient.")</li>
                                <li><strong>Success Criteria:</strong> Specific milestones defining completion.</li>
                                <li><strong>Review Cadence:</strong> Weekly, Monthly, Quarterly, or Yearly reviews.</li>
                            </ul>
                        </div>
                        <div className="bg-black/30 p-4 rounded-lg border border-white/10">
                            <h4 className="font-bold text-white text-sm uppercase mb-2">AI Integration</h4>
                            <p className="text-sm text-gray-400">
                                Use the Oracle to create complex goals in one shot:<br />
                                <span className="italic text-gray-500">"Create a yearly goal 'Build a Cabin' with motivation 'Escape the city'..."</span>
                            </p>
                        </div>
                    </div>
                </div>
            </Section>

            {/* Themes & Appearance */}
            <Section title="Themes & Appearance" icon={<Palette className="text-accent" />}>
                <div className="space-y-4">
                    <p className="text-gray-300">
                        Customize your workspace with the new <strong>Dual-Theme System</strong>.
                    </p>
                    <ul className="list-disc pl-5 text-sm text-gray-400 space-y-2">
                        <li><strong>Independent Themes:</strong> Set different themes for the Main App (Analytical) and the Music Section (Creative).</li>
                        <li><strong>Context Awareness:</strong> The interface automatically switches styles as you navigate between work and creative modes.</li>
                        <li><strong>Configuration:</strong> Go to <strong>Settings &gt; Appearance</strong> or use the dropdown in the Music Page header.</li>
                    </ul>
                    <div className="bg-black/30 p-4 rounded-lg border border-white/10 mt-4">
                        <h4 className="font-bold text-white text-sm uppercase mb-2">Available Themes</h4>
                        <div className="flex flex-wrap gap-2 text-xs font-mono text-gray-300">
                            {['Default', 'Music', 'Synthwave', 'Midnight', 'Forest', 'Light'].map(t => (
                                <span key={t} className="bg-white/5 border border-white/10 px-2 py-1 rounded capitalize">{t}</span>
                            ))}
                        </div>
                    </div>
                </div>
            </Section>

            {/* Setup & Integration */}
            <Section title="Setup & Integration" icon={<Settings className="text-accent" />}>
                <div className="space-y-6">
                    <div>
                        <h4 className="font-bold text-white mb-2 flex items-center gap-2">
                            <Database size={16} className="text-gray-400" />
                            Database & Backup
                        </h4>
                        <p className="text-sm text-gray-400 mb-2">
                            All data is stored locally in your browser (IndexedDB).
                        </p>
                        <ul className="list-disc pl-5 text-sm text-gray-400 space-y-1">
                            <li><strong>Backup:</strong> Go to Settings and click "Export Backup" to download a .zip of your data.</li>
                            <li><strong>Restore:</strong> Drag and drop a backup .zip into the Import zone in Settings.</li>
                        </ul>
                    </div>

                    <div className="h-px bg-white/10" />

                    <div>
                        <h4 className="font-bold text-white mb-2 flex items-center gap-2">
                            <Sparkles size={16} className="text-gray-400" />
                            API Keys
                        </h4>
                        <p className="text-sm text-gray-400 mb-2">
                            To enable the Oracle and auto-triage features:
                        </p>
                        <ol className="list-decimal pl-5 text-sm text-gray-400 space-y-1">
                            <li>Get a Google Gemini API Key from AI Studio.</li>
                            <li>Go to <strong>Settings</strong> via the gear icon <Settings size={12} className="inline text-gray-500" /> in the sidebar footer.</li>
                            <li>Paste your key into the "Gemini API Key" field.</li>
                        </ol>
                    </div>
                </div>
            </Section>

            {/* Shortcuts Reference */}
            <Section title="Keyboard Shortcuts Reference" icon={<Keyboard className="text-accent" />}>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-x-8 gap-y-4">
                    <ShortcutRow keys={['Ctrl', 'Shift', 'Space']} description="Quick Capture (Global)" />
                    <ShortcutRow keys={['Ctrl', 'K']} description="Toggle Command Bar" />
                    <ShortcutRow keys={['Alt', '1-5']} description="Navigate Sidebar Tabs" />
                    <ShortcutRow keys={['Escape']} description="Close Modals / Clear Selection" />

                    <div className="col-span-1 md:col-span-2 mt-2 mb-1 border-b border-white/10 pb-1 text-xs font-mono text-gray-500 uppercase">
                        Triage Mode
                    </div>
                    <ShortcutRow keys={['P']} description="Convert to Project" />
                    <ShortcutRow keys={['T']} description="Convert to Task" />
                    <ShortcutRow keys={['R']} description="Convert to Reference" />
                    <ShortcutRow keys={['S']} description="Move to Someday" />
                    <ShortcutRow keys={['Y']} description="Accept Oracle Suggestion" />
                    <ShortcutRow keys={['D']} description="Delete Item" />
                    <ShortcutRow keys={['↓', 'J']} description="Next Item" />
                    <ShortcutRow keys={['↑', 'K']} description="Previous Item" />
                </div>
            </Section>
        </div>
    );
}

function Section({ title, icon, children }: { title: string; icon: React.ReactNode; children: React.ReactNode }) {
    return (
        <Card className="p-6">
            <div className="flex items-center gap-3 mb-6 border-b border-white/5 pb-4">
                {icon}
                <h2 className="text-xl font-bold text-white uppercase tracking-tight">{title}</h2>
            </div>
            {children}
        </Card>
    );
}

function ShortcutRow({ keys, description }: { keys: string[]; description: string }) {
    return (
        <div className="flex items-center justify-between group">
            <span className="text-sm text-gray-400 group-hover:text-gray-200 transition-colors">{description}</span>
            <div className="flex items-center gap-1">
                {keys.map((key, i) => (
                    <span key={i}>
                        <kbd className="bg-white/5 border border-white/10 px-2 py-1 rounded text-[10px] font-mono text-gray-300 min-w-[24px] text-center inline-block shadow-sm">
                            {key}
                        </kbd>
                        {i < keys.length - 1 && <span className="text-gray-700 mx-1">+</span>}
                    </span>
                ))}
            </div>
        </div>
    );
}

function CommandRow({ command, description }: { command: string; description: string }) {
    return (
        <div className="flex items-center justify-between bg-white/5 px-3 py-2 rounded border border-white/5">
            <code className="text-accent font-mono text-sm">{command}</code>
            <span className="text-xs text-gray-400">{description}</span>
        </div>
    );
}
