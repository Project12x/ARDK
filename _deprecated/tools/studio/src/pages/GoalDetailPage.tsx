import React, { useState, useEffect } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { useParams, useNavigate } from 'react-router-dom';
import { db, type Goal } from '../lib/db';
import { VaultService } from '../services/VaultService';
import { Button } from '../components/ui/Button';
import { useUIStore } from '../store/useStore';
import { Card } from '../components/ui/Card';
import {
    ArrowLeft, Save, Target, Calendar, BarChart3,
    CheckCircle2, PauseCircle, XCircle, Circle,
    BrainCircuit, FileText, ChevronRight, Share2
} from 'lucide-react';
import { toast } from 'sonner';
import clsx from 'clsx';
import { TipTapEditor } from '../components/ui/TipTapEditor';

const LEVEL_CONFIG = {
    vision: { label: 'Vision', color: 'text-purple-400' },
    year: { label: 'Yearly Goal', color: 'text-blue-400' },
    quarter: { label: 'Quarterly', color: 'text-green-400' },
    objective: { label: 'Objective', color: 'text-amber-400' }
};

export default function GoalDetailPage() {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const goalId = parseInt(id || '0');

    // Fetch Goal
    const goal = useLiveQuery(() => db.goals.get(goalId), [goalId]);
    const parent = useLiveQuery(() => goal?.parent_id ? db.goals.get(goal.parent_id) : undefined, [goal?.parent_id]);
    const children = useLiveQuery(() => db.goals.where('parent_id').equals(goalId).toArray(), [goalId]);
    const activeTasks = useLiveQuery(() => db.project_tasks.where('goal_id').equals(goalId).toArray(), [goalId]);

    const [activeTab, setActiveTab] = useState<'overview' | 'strategy' | 'notes'>('overview');
    const [formData, setFormData] = useState<Partial<Goal>>({});
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        if (goal) {
            setFormData({
                title: goal.title,
                status: goal.status,
                progress: goal.progress,
                priority: goal.priority,
                description: goal.description,
                target_date: goal.target_date,
                notes: goal.notes,
                motivation: goal.motivation,
                success_criteria: goal.success_criteria,
                review_cadence: goal.review_cadence
            });
        }
    }, [goal]);

    if (!goal) return <div className="p-10 text-center text-gray-500">Loading goal...</div>;

    const handleChange = (field: keyof Goal, value: any) => {
        setFormData(prev => ({ ...prev, [field]: value }));
    };

    const handleSave = async () => {
        if (!goalId) return;
        setIsSaving(true);
        try {
            await db.goals.update(goalId, {
                ...formData,
                updated_at: new Date()
            });
            // Attempt generic sync if possible, but don't block
            try {
                // @ts-ignore
                const handle = await window.showDirectoryPicker().catch(() => null);
                if (handle) {
                    await VaultService.syncTable('goals', handle);
                }
            } catch (ignore) { /* user might cancel or not supported */ }

            toast.success("Goal updated");
        } catch (e) {
            console.error(e);
            toast.error("Failed to save");
        } finally {
            setIsSaving(false);
        }
    };

    const activeConfig = LEVEL_CONFIG[goal.level] || { label: 'Goal', color: 'text-gray-400' };

    return (
        <div className="flex flex-col h-full bg-black text-white">
            {/* Header */}
            <header className="h-16 border-b border-white/10 flex items-center justify-between px-6 bg-white/5">
                <div className="flex items-center gap-4 flex-1">
                    <button onClick={() => navigate('/goals')} className="text-gray-500 hover:text-white transition-colors">
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex-1 max-w-2xl">
                        <div className="flex items-center gap-2 text-xs text-gray-500 mb-1">
                            {parent && (
                                <>
                                    <span className="hover:text-accent cursor-pointer" onClick={() => navigate(`/goals/${parent.id}`)}>
                                        {parent.title}
                                    </span>
                                    <ChevronRight size={10} />
                                </>
                            )}
                            <span className={activeConfig.color}>{activeConfig.label}</span>
                        </div>
                        <input
                            className="bg-transparent text-xl font-bold text-white w-full border-b border-transparent hover:border-white/20 focus:border-accent outline-none transition-colors placeholder:text-gray-700"
                            value={formData.title || ''}
                            onChange={e => handleChange('title', e.target.value)}
                            placeholder="Goal Title"
                        />
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <div className="flex bg-white/5 rounded p-1 border border-white/5 mr-4">
                        {[
                            { id: 'overview', icon: Target, label: 'Overview' },
                            { id: 'strategy', icon: BrainCircuit, label: 'Strategy' },
                            { id: 'notes', icon: FileText, label: 'Notes' },
                        ].map(tab => (
                            <button
                                key={tab.id}
                                onClick={() => setActiveTab(tab.id as any)}
                                className={clsx(
                                    "px-3 py-1.5 rounded flex items-center gap-2 text-sm font-medium transition-all",
                                    activeTab === tab.id ? "bg-accent/20 text-accent shadow-sm" : "text-gray-400 hover:bg-white/5"
                                )}
                            >
                                <tab.icon size={14} />
                                <span>{tab.label}</span>
                            </button>
                        ))}
                    </div>
                    <Button onClick={handleSave} disabled={isSaving}>
                        <Save size={16} className="mr-2" />
                        {isSaving ? 'Saving...' : 'Save Changes'}
                    </Button>
                </div>
            </header>

            {/* Content */}
            <div className="flex-1 overflow-y-auto p-8">
                <div className="max-w-6xl mx-auto">

                    {activeTab === 'overview' && (
                        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                            {/* Left Column: Metadata */}
                            <div className="space-y-6">
                                <Card className="p-6 space-y-4 bg-white/5 border-white/10">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest">Metadata</h3>

                                    {/* Status */}
                                    <div>
                                        <label className="text-xs text-gray-500 mb-1 block">Status</label>
                                        <div className="grid grid-cols-2 gap-2">
                                            {['active', 'achieved', 'paused', 'abandoned'].map(s => (
                                                <button
                                                    key={s}
                                                    onClick={() => handleChange('status', s)}
                                                    className={clsx(
                                                        "py-2 rounded text-xs font-bold uppercase border transition-all",
                                                        formData.status === s
                                                            ? "bg-accent/20 border-accent text-accent"
                                                            : "bg-black/20 border-white/10 text-gray-500 hover:bg-white/5"
                                                    )}
                                                >
                                                    {s}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Progress */}
                                    <div>
                                        <label className="text-xs text-gray-500 mb-1 flex justify-between">
                                            Progress <span className="text-accent">{formData.progress}%</span>
                                        </label>
                                        <input
                                            type="range"
                                            min="0"
                                            max="100"
                                            className="w-full accent-accent h-2 bg-white/10 rounded-lg appearance-none cursor-pointer"
                                            value={formData.progress || 0}
                                            onChange={e => handleChange('progress', parseInt(e.target.value))}
                                        />
                                    </div>

                                    {/* Priority */}
                                    <div>
                                        <label className="text-xs text-gray-500 mb-1 block">Priority (1-5)</label>
                                        <div className="flex gap-1">
                                            {[1, 2, 3, 4, 5].map(p => (
                                                <button
                                                    key={p}
                                                    onClick={() => handleChange('priority', p)}
                                                    className={clsx(
                                                        "flex-1 py-1 rounded text-xs font-bold border transition-all",
                                                        formData.priority === p
                                                            ? "bg-amber-500/20 border-amber-500 text-amber-500"
                                                            : "bg-black/20 border-white/10 text-gray-500"
                                                    )}
                                                >
                                                    {p}
                                                </button>
                                            ))}
                                        </div>
                                    </div>

                                    {/* Review Cadence */}
                                    <div>
                                        <label className="text-xs text-gray-500 mb-1 block">Review Cadence</label>
                                        <select
                                            className="w-full bg-black/50 border border-white/10 rounded p-2 text-white text-sm"
                                            value={formData.review_cadence || 'weekly'}
                                            onChange={e => handleChange('review_cadence', e.target.value)}
                                        >
                                            <option value="weekly">Weekly</option>
                                            <option value="monthly">Monthly</option>
                                            <option value="quarterly">Quarterly</option>
                                            <option value="yearly">Yearly</option>
                                        </select>
                                    </div>

                                    {/* Target Date */}
                                    <div>
                                        <label className="text-xs text-gray-500 mb-1 block">Target Date</label>
                                        <input
                                            type="date"
                                            className="w-full bg-black/50 border border-white/10 rounded p-2 text-white text-sm"
                                            value={formData.target_date ? new Date(formData.target_date).toISOString().split('T')[0] : ''}
                                            onChange={e => handleChange('target_date', new Date(e.target.value))}
                                        />
                                    </div>
                                </Card>

                                <Card className="p-6 bg-white/5 border-white/10">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Hierarchy</h3>

                                    {parent && (
                                        <div className="mb-4">
                                            <div className="text-xs text-gray-600 mb-1">Parent Goal</div>
                                            <div
                                                className="p-2 bg-white/5 rounded border border-white/10 text-sm hover:border-accent cursor-pointer truncate"
                                                onClick={() => navigate(`/goals/${parent.id}`)}
                                            >
                                                {parent.title}
                                            </div>
                                        </div>
                                    )}

                                    {children && children.length > 0 && (
                                        <div>
                                            <div className="text-xs text-gray-600 mb-1">Sub-Goals</div>
                                            <div className="space-y-1">
                                                {children.map(c => (
                                                    <div
                                                        key={c.id}
                                                        className="p-2 bg-white/5 rounded border border-white/10 text-sm hover:border-accent cursor-pointer truncate flex justify-between"
                                                        onClick={() => navigate(`/goals/${c.id}`)}
                                                    >
                                                        <span>{c.title}</span>
                                                        <span className={clsx("text-xs", c.status === 'achieved' ? "text-green-500" : "text-gray-500")}>
                                                            {c.progress}%
                                                        </span>
                                                    </div>
                                                ))}
                                            </div>
                                        </div>
                                    )}
                                </Card>
                            </div>

                            {/* Center/Right: Description & Tasks */}
                            <div className="lg:col-span-2 space-y-6">


                                <Card className="p-6 min-h-[200px] bg-white/5 border-white/10">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Description / Vision</h3>
                                    <textarea
                                        className="w-full h-48 bg-transparent border-none outline-none text-gray-300 resize-none font-sans leading-relaxed"
                                        placeholder="Detailed description of the goal..."
                                        value={formData.description || ''}
                                        onChange={e => handleChange('description', e.target.value)}
                                    />
                                </Card>

                                <Card className="p-6 bg-white/5 border-white/10">
                                    <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Active Tasks</h3>
                                    <div className="space-y-2">
                                        {activeTasks?.map(task => (
                                            <div key={task.id} className="flex items-center gap-3 p-3 bg-black/20 rounded border border-white/5">
                                                <div className={clsx("w-2 h-2 rounded-full", task.status === 'completed' ? 'bg-green-500' : 'bg-gray-500')} />
                                                <span className="flex-1 text-sm font-medium">{task.title}</span>
                                                <span className="text-xs text-gray-600 uppercase">{task.status}</span>
                                            </div>
                                        ))}
                                        {(!activeTasks || activeTasks.length === 0) && (
                                            <div className="text-center text-gray-600 py-4 italic">No active tasks linked directly to this goal.</div>
                                        )}
                                    </div>
                                </Card>
                            </div>
                        </div>
                    )}

                    {activeTab === 'strategy' && (
                        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 h-full">
                            {/* Strategic Context Inputs */}
                            <Card className="p-6 bg-white/5 border-white/10 h-full">
                                <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Strategic Context</h3>

                                <div className="space-y-6">
                                    <div>
                                        <label className="text-xs text-gray-500 uppercase mb-1 block font-bold">Motivation ("Why")</label>
                                        <textarea
                                            className="w-full h-32 bg-black/20 border border-white/5 rounded-lg p-3 text-sm text-gray-300 resize-none focus:border-accent/50 outline-none transition-colors"
                                            placeholder="Why is this goal important? What is the driving force?"
                                            value={formData.motivation || ''}
                                            onChange={e => handleChange('motivation', e.target.value)}
                                        />
                                    </div>

                                    <div>
                                        <label className="text-xs text-gray-500 uppercase mb-1 block font-bold">Success Criteria (KPIs)</label>
                                        <div className="space-y-2">
                                            {(formData.success_criteria || []).map((kpi, idx) => (
                                                <div key={idx} className="flex gap-2">
                                                    <div className="flex-1 bg-black/20 border border-white/5 rounded px-3 py-2 text-sm text-gray-300">{kpi}</div>
                                                    <button
                                                        onClick={() => {
                                                            const newKpis = [...(formData.success_criteria || [])];
                                                            newKpis.splice(idx, 1);
                                                            handleChange('success_criteria', newKpis);
                                                        }}
                                                        className="text-gray-500 hover:text-red-500"
                                                    >
                                                        <XCircle size={16} />
                                                    </button>
                                                </div>
                                            ))}
                                            <div className="flex gap-2">
                                                <input
                                                    id="new-kpi-strategy"
                                                    className="flex-1 bg-black/20 border border-white/10 rounded px-3 py-2 text-sm text-white focus:border-accent/50 outline-none"
                                                    placeholder="Add new success criteria..."
                                                    onKeyDown={e => {
                                                        if (e.key === 'Enter') {
                                                            const val = (e.currentTarget as HTMLInputElement).value;
                                                            if (val.trim()) {
                                                                handleChange('success_criteria', [...(formData.success_criteria || []), val.trim()]);
                                                                (e.currentTarget as HTMLInputElement).value = '';
                                                            }
                                                        }
                                                    }}
                                                />
                                                <Button onClick={() => {
                                                    const el = document.getElementById('new-kpi-strategy') as HTMLInputElement;
                                                    if (el && el.value.trim()) {
                                                        handleChange('success_criteria', [...(formData.success_criteria || []), el.value.trim()]);
                                                        el.value = '';
                                                    }
                                                }}>Add</Button>
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            </Card>

                            {/* AI Start Button */}
                            <Card className="p-8 text-center bg-white/5 border-white/10 h-full flex flex-col items-center justify-center">
                                <BrainCircuit size={48} className="text-purple-500 mb-4 opacity-50" />
                                <h3 className="text-xl font-bold mb-2">AI Strategist</h3>
                                <p className="text-gray-500 max-w-md mb-6">
                                    Chat with the Oracle to break down this goal into actionable steps, identify potential blockers, and refine your approach.
                                </p>
                                <Button variant="outline" size="sm" onClick={() => {
                                    console.log("Starting Strategy Session for Goal:", goalId);
                                    const { setActiveGoalId, setOracleChatOpen, setOraclePendingMessage } = useUIStore.getState();
                                    setActiveGoalId(goalId);
                                    setOraclePendingMessage(`I want to work on the goal: "${goal.title}". Help me refine the strategy.`);
                                    setOracleChatOpen(true);
                                }}>
                                    Start Strategy Session
                                </Button>
                            </Card>
                        </div>
                    )}

                    {activeTab === 'notes' && (
                        <Card className="p-6 min-h-[500px] bg-white/5 border-white/10 flex flex-col">
                            <h3 className="text-xs font-bold text-gray-500 uppercase tracking-widest mb-4">Goal Journal</h3>
                            <textarea
                                className="flex-1 bg-transparent border-none outline-none text-gray-300 resize-none font-mono text-sm leading-relaxed p-4 bg-black/20 rounded-lg"
                                placeholder="- Log your progress, thoughts, and reflections here..."
                                value={formData.notes || ''}
                                onChange={e => handleChange('notes', e.target.value)}
                            />
                        </Card>
                    )}

                </div>
            </div>
        </div>
    );
}
