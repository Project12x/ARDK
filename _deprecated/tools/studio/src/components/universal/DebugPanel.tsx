/**
 * DebugPanel - Comprehensive debug tools for Universal Test Page
 * 
 * Features:
 * - Entity Coverage Stats
 * - Entity Inspector (searchable)
 * - Validation Tests
 * - Performance Metrics
 * - DB Utilities
 * - Event Log
 */

import { useState, useEffect, useCallback } from 'react';
import {
    Database, Search, CheckCircle, XCircle, AlertTriangle, Clock,
    RefreshCw, Trash2, Download, Upload, Copy, Terminal, Zap,
    Eye, FileJson, Activity, Bug
} from 'lucide-react';
import clsx from 'clsx';
import { toast } from 'sonner';

import type { UniversalEntity } from '../../lib/universal/types';
import { db } from '../../lib/db';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';

// ============================================================================
// TYPES
// ============================================================================

interface DebugPanelProps {
    data: Record<string, UniversalEntity[]>;
    onResetDB?: () => Promise<void>;
    onSeedDB?: () => Promise<void>;
}

interface ValidationResult {
    name: string;
    status: 'pass' | 'fail' | 'warn';
    message: string;
    entity?: UniversalEntity;
}

interface EventLogEntry {
    id: string;
    timestamp: Date;
    type: 'info' | 'warn' | 'error' | 'success';
    message: string;
    data?: any;
}

// ============================================================================
// COMPONENT
// ============================================================================

export function DebugPanel({ data, onResetDB, onSeedDB }: DebugPanelProps) {
    const [activeSection, setActiveSection] = useState<'coverage' | 'inspector' | 'validation' | 'db' | 'log'>('coverage');
    const [searchQuery, setSearchQuery] = useState('');
    const [selectedEntity, setSelectedEntity] = useState<UniversalEntity | null>(null);
    const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
    const [eventLog, setEventLog] = useState<EventLogEntry[]>([]);
    const [isRunningValidation, setIsRunningValidation] = useState(false);
    const [dbStats, setDbStats] = useState<Record<string, number>>({});
    const [confirmAction, setConfirmAction] = useState<{ message: string; action: () => Promise<void>; } | null>(null);

    // ========================================================================
    // PERSISTENT LOG STORAGE (survives crashes)
    // ========================================================================

    // Load persisted logs on mount
    useEffect(() => {
        async function loadPersistedLogs() {
            try {
                const logs = await (db as any).debug_logs?.orderBy('timestamp').reverse().limit(200).toArray() || [];
                if (logs.length > 0) {
                    setEventLog(logs.map((log: any) => ({
                        id: log.id?.toString() || Date.now().toString(),
                        timestamp: new Date(log.timestamp),
                        type: log.type,
                        message: log.message,
                        data: log.data
                    })));
                }
            } catch (err) {
                console.warn('[DebugPanel] Could not load persisted logs:', err);
            }
        }
        loadPersistedLogs();
    }, []);

    // Persist log to IndexedDB (survives crashes!)
    const persistLog = useCallback(async (type: EventLogEntry['type'], message: string, logData?: any) => {
        const entry: EventLogEntry = {
            id: Date.now().toString(),
            timestamp: new Date(),
            type,
            message,
            data: logData
        };

        // Update in-memory state
        setEventLog(prev => [entry, ...prev].slice(0, 200));

        // Persist to IndexedDB
        try {
            await (db as any).debug_logs?.add({
                timestamp: entry.timestamp.toISOString(),
                type: entry.type,
                message: entry.message,
                data: entry.data ? JSON.stringify(entry.data) : null
            });
        } catch (err) {
            console.warn('[DebugPanel] Could not persist log:', err);
        }
    }, []);

    // Clear all persisted logs
    const clearPersistedLogs = useCallback(async () => {
        setEventLog([]);
        try {
            await (db as any).debug_logs?.clear();
            toast.success('Logs cleared');
        } catch (err) {
            console.warn('[DebugPanel] Could not clear logs:', err);
        }
    }, []);

    // Export logs to file
    const exportLogs = useCallback(() => {
        const exportObj = {
            exportedAt: new Date().toISOString(),
            logCount: eventLog.length,
            logs: eventLog.map(e => ({
                timestamp: e.timestamp.toISOString(),
                type: e.type,
                message: e.message,
                data: e.data
            }))
        };
        const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `debug-logs-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        toast.success('Logs exported');
    }, [eventLog]);

    // Alias for backwards compatibility
    const log = persistLog;

    // Load DB table counts
    useEffect(() => {
        async function loadDbStats() {
            const stats: Record<string, number> = {};
            const tables = ['projects', 'inventory', 'project_tasks', 'assets', 'goals', 'songs', 'albums', 'recordings', 'inbox_items', 'routines', 'debug_logs'];

            for (const table of tables) {
                try {
                    stats[table] = await (db as any)[table]?.count() || 0;
                } catch {
                    stats[table] = -1; // Error
                }
            }
            setDbStats(stats);
        }
        loadDbStats();
    }, [data]);
    // Flatten all entities for search
    const allEntities = Object.values(data).flat();

    // Filter entities by search query
    const filteredEntities = searchQuery
        ? allEntities.filter(e =>
            e.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
            e.urn.toLowerCase().includes(searchQuery.toLowerCase()) ||
            e.type.toLowerCase().includes(searchQuery.toLowerCase())
        )
        : allEntities;

    // Run validation tests
    const runValidation = async () => {
        setIsRunningValidation(true);
        const results: ValidationResult[] = [];
        log('info', 'Starting validation tests...');

        // Test 1: All entities have URN
        for (const entity of allEntities) {
            if (!entity.urn) {
                results.push({ name: 'URN Check', status: 'fail', message: `Missing URN`, entity });
            }
        }
        if (!results.some(r => r.name === 'URN Check')) {
            results.push({ name: 'URN Check', status: 'pass', message: `All ${allEntities.length} entities have URN` });
        }

        // Test 2: All entities have title
        for (const entity of allEntities) {
            if (!entity.title || entity.title === 'Untitled') {
                results.push({ name: 'Title Check', status: 'warn', message: `Missing/default title: ${entity.urn}`, entity });
            }
        }
        if (!results.some(r => r.name === 'Title Check')) {
            results.push({ name: 'Title Check', status: 'pass', message: `All entities have titles` });
        }

        // Test 3: Check for duplicate URNs
        const urns = allEntities.map(e => e.urn);
        const duplicates = urns.filter((urn, i) => urns.indexOf(urn) !== i);
        if (duplicates.length > 0) {
            results.push({ name: 'Duplicate URN Check', status: 'fail', message: `Found ${duplicates.length} duplicate URNs: ${duplicates.join(', ')}` });
        } else {
            results.push({ name: 'Duplicate URN Check', status: 'pass', message: 'No duplicate URNs' });
        }

        // Test 4: All entities have valid type
        const validTypes = ['project', 'inventory', 'task', 'asset', 'goal', 'song', 'album', 'recording', 'inbox', 'routine'];
        for (const entity of allEntities) {
            if (!validTypes.includes(entity.type)) {
                results.push({ name: 'Type Check', status: 'warn', message: `Unknown type: ${entity.type}`, entity });
            }
        }
        if (!results.some(r => r.name === 'Type Check')) {
            results.push({ name: 'Type Check', status: 'pass', message: 'All entity types are valid' });
        }

        // Test 5: Data payload exists
        for (const entity of allEntities) {
            if (!entity.data || Object.keys(entity.data).length === 0) {
                results.push({ name: 'Data Payload Check', status: 'fail', message: `Empty data payload: ${entity.urn}`, entity });
            }
        }
        if (!results.some(r => r.name === 'Data Payload Check')) {
            results.push({ name: 'Data Payload Check', status: 'pass', message: 'All entities have data payloads' });
        }

        // Test 6: DB Connectivity
        try {
            await db.projects.count();
            results.push({ name: 'DB Connection', status: 'pass', message: 'Database is accessible' });
        } catch (err) {
            results.push({ name: 'DB Connection', status: 'fail', message: `DB Error: ${err}` });
        }

        setValidationResults(results);
        setIsRunningValidation(false);

        const passed = results.filter(r => r.status === 'pass').length;
        const failed = results.filter(r => r.status === 'fail').length;
        const warns = results.filter(r => r.status === 'warn').length;

        log('success', `Validation complete: ${passed} passed, ${failed} failed, ${warns} warnings`);
        toast.success(`Validation: ${passed} passed, ${failed} failed`);
    };

    // Export data as JSON
    const exportData = () => {
        const exportObj = {
            exportedAt: new Date().toISOString(),
            totalEntities: allEntities.length,
            entityCounts: Object.fromEntries(Object.entries(data).map(([k, v]) => [k, v.length])),
            entities: allEntities
        };
        const blob = new Blob([JSON.stringify(exportObj, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `universal-entities-${Date.now()}.json`;
        a.click();
        URL.revokeObjectURL(url);
        log('success', `Exported ${allEntities.length} entities`);
        toast.success('Data exported');
    };

    // Copy entity to clipboard
    const copyEntity = (entity: UniversalEntity) => {
        navigator.clipboard.writeText(JSON.stringify(entity, null, 2));
        toast.success('Copied to clipboard');
        log('info', `Copied entity: ${entity.urn}`);
    };

    // Confirm and execute action
    const handleConfirmAction = async () => {
        if (!confirmAction) return;

        try {
            await confirmAction.action();
            setConfirmAction(null);
            toast.success('Action completed');
            log('success', 'Database action completed successfully');
        } catch (err) {
            console.error(err);
            toast.error('Action failed');
            log('error', `Action failed: ${err}`);
        }
    };

    // ========================================================================
    // RENDER SECTIONS
    // ========================================================================

    const sections = [
        { id: 'coverage', label: 'Coverage', icon: Activity },
        { id: 'inspector', label: 'Inspector', icon: Search },
        { id: 'validation', label: 'Validation', icon: CheckCircle },
        { id: 'db', label: 'Database', icon: Database },
        { id: 'log', label: 'Event Log', icon: Terminal },
    ];

    return (
        <div className="space-y-4">
            {/* Section Tabs */}
            <div className="flex gap-2 flex-wrap">
                {sections.map(s => (
                    <button
                        key={s.id}
                        onClick={() => setActiveSection(s.id as any)}
                        className={clsx(
                            'flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                            activeSection === s.id
                                ? 'bg-accent text-black'
                                : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                        )}
                    >
                        <s.icon size={14} />
                        {s.label}
                    </button>
                ))}
            </div>

            {/* Confirmation Modal (Simple overlay) */}
            {confirmAction && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm">
                    <div className="bg-gray-900 border border-white/10 p-6 rounded-xl max-w-md w-full shadow-2xl">
                        <div className="flex items-center gap-3 text-red-500 mb-4">
                            <AlertTriangle size={24} />
                            <h3 className="text-xl font-bold">Confirm Action</h3>
                        </div>
                        <p className="text-gray-300 mb-6">{confirmAction.message}</p>
                        <div className="flex justify-end gap-3">
                            <Button variant="ghost" onClick={() => setConfirmAction(null)}>Cancel</Button>
                            <Button variant="danger" onClick={handleConfirmAction}>Confirm</Button>
                        </div>
                    </div>
                </div>
            )}

            {/* ================================================================ */}
            {/* COVERAGE SECTION */}
            {/* ================================================================ */}
            {activeSection === 'coverage' && (
                <div className="space-y-6">
                    <div className="bg-black/30 rounded-lg p-6 border border-white/10">
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="text-lg font-bold text-accent flex items-center gap-2">
                                <Activity size={18} /> Universal Entity Coverage
                            </h3>
                            <span className="text-2xl font-bold text-white">{allEntities.length} total</span>
                        </div>
                        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
                            {Object.entries(data).map(([key, entities]) => (
                                <div key={key} className="p-3 bg-white/5 rounded border border-white/10 hover:border-accent/50 transition-colors">
                                    <div className="text-xs text-gray-500 uppercase font-bold">{key}</div>
                                    <div className={clsx(
                                        'text-3xl font-bold',
                                        entities.length === 0 ? 'text-red-500' : 'text-accent'
                                    )}>{entities.length}</div>
                                    <div className="text-[10px] text-gray-600">entities loaded</div>
                                </div>
                            ))}
                        </div>
                    </div>

                    {/* Sample Payloads */}
                    <div className="bg-black/30 rounded-lg p-6 border border-white/10">
                        <h3 className="text-lg font-bold mb-4 text-accent flex items-center gap-2">
                            <FileJson size={18} /> Sample Entity Payloads
                        </h3>
                        <div className="grid gap-3">
                            {Object.entries(data).map(([key, entities]) => entities[0] && (
                                <details key={key} className="bg-black/20 rounded-lg overflow-hidden group">
                                    <summary className="p-3 cursor-pointer hover:bg-white/5 font-mono text-sm flex items-center gap-2">
                                        <Eye size={14} className="text-gray-500" />
                                        <span className="text-accent">{key}</span>
                                        <span className="text-gray-500">[0]</span>
                                        <span className="text-white">— {entities[0].title}</span>
                                        <button
                                            onClick={(e) => { e.preventDefault(); copyEntity(entities[0]); }}
                                            className="ml-auto p-1 rounded hover:bg-white/10 text-gray-500 hover:text-white"
                                        >
                                            <Copy size={12} />
                                        </button>
                                    </summary>
                                    <pre className="text-xs text-gray-400 overflow-auto max-h-64 p-4 bg-black/50 font-mono">
                                        {JSON.stringify(entities[0], null, 2)}
                                    </pre>
                                </details>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* ================================================================ */}
            {/* INSPECTOR SECTION */}
            {/* ================================================================ */}
            {activeSection === 'inspector' && (
                <div className="space-y-4">
                    <div className="bg-black/30 rounded-lg p-4 border border-white/10">
                        <div className="flex gap-4">
                            <div className="flex-1 relative">
                                <Search size={16} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
                                <input
                                    type="text"
                                    placeholder="Search by title, URN, or type..."
                                    value={searchQuery}
                                    onChange={e => setSearchQuery(e.target.value)}
                                    className="w-full bg-black/50 border border-white/10 rounded-lg pl-10 pr-4 py-2 text-sm text-white placeholder-gray-500 focus:outline-none focus:border-accent"
                                />
                            </div>
                            <span className="text-gray-500 text-sm self-center">
                                {filteredEntities.length} / {allEntities.length}
                            </span>
                        </div>
                    </div>

                    <div className="grid md:grid-cols-2 gap-4">
                        {/* Entity List */}
                        <div className="bg-black/30 rounded-lg border border-white/10 max-h-[60vh] overflow-auto">
                            {filteredEntities.slice(0, 50).map(entity => (
                                <button
                                    key={entity.urn}
                                    onClick={() => setSelectedEntity(entity)}
                                    className={clsx(
                                        'w-full p-3 text-left border-b border-white/5 hover:bg-white/5 transition-colors',
                                        selectedEntity?.urn === entity.urn && 'bg-accent/10 border-l-2 border-l-accent'
                                    )}
                                >
                                    <div className="font-medium text-white text-sm truncate">{entity.title}</div>
                                    <div className="flex items-center gap-2 mt-1">
                                        <span className="text-[10px] uppercase font-bold text-accent bg-accent/10 px-1.5 py-0.5 rounded">{entity.type}</span>
                                        <span className="text-[10px] text-gray-500 font-mono truncate">{entity.urn}</span>
                                    </div>
                                </button>
                            ))}
                            {filteredEntities.length > 50 && (
                                <div className="p-3 text-center text-gray-500 text-sm">
                                    + {filteredEntities.length - 50} more entities
                                </div>
                            )}
                        </div>

                        {/* Entity Detail */}
                        <div className="bg-black/30 rounded-lg border border-white/10 p-4">
                            {selectedEntity ? (
                                <div className="space-y-4">
                                    <div className="flex items-start justify-between">
                                        <div>
                                            <h4 className="font-bold text-white">{selectedEntity.title}</h4>
                                            <p className="text-xs text-gray-500 font-mono">{selectedEntity.urn}</p>
                                        </div>
                                        <button
                                            onClick={() => copyEntity(selectedEntity)}
                                            className="p-2 rounded hover:bg-white/10 text-gray-400 hover:text-white"
                                        >
                                            <Copy size={14} />
                                        </button>
                                    </div>

                                    <div className="grid grid-cols-2 gap-2 text-xs">
                                        <div className="bg-white/5 p-2 rounded">
                                            <span className="text-gray-500">Type:</span>
                                            <span className="ml-2 text-white">{selectedEntity.type}</span>
                                        </div>
                                        <div className="bg-white/5 p-2 rounded">
                                            <span className="text-gray-500">Status:</span>
                                            <span className="ml-2 text-white">{selectedEntity.status || 'N/A'}</span>
                                        </div>
                                        <div className="bg-white/5 p-2 rounded col-span-2">
                                            <span className="text-gray-500">Tags:</span>
                                            <span className="ml-2 text-white">{selectedEntity.tags?.join(', ') || 'None'}</span>
                                        </div>
                                    </div>

                                    <details className="bg-black/20 rounded overflow-hidden" open>
                                        <summary className="p-2 cursor-pointer text-xs font-bold text-gray-400 hover:bg-white/5">
                                            Full Payload
                                        </summary>
                                        <pre className="text-[10px] text-gray-400 overflow-auto max-h-64 p-3 font-mono">
                                            {JSON.stringify(selectedEntity, null, 2)}
                                        </pre>
                                    </details>
                                </div>
                            ) : (
                                <div className="text-center text-gray-500 py-12">
                                    <Bug size={32} className="mx-auto mb-2 opacity-50" />
                                    Select an entity to inspect
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* ================================================================ */}
            {/* VALIDATION SECTION */}
            {/* ================================================================ */}
            {activeSection === 'validation' && (
                <div className="space-y-4">
                    <div className="bg-black/30 rounded-lg p-4 border border-white/10 flex items-center gap-4">
                        <Button onClick={runValidation} disabled={isRunningValidation}>
                            {isRunningValidation ? (
                                <RefreshCw size={14} className="mr-2 animate-spin" />
                            ) : (
                                <Zap size={14} className="mr-2" />
                            )}
                            Run Validation Tests
                        </Button>
                        <span className="text-gray-500 text-sm">
                            Tests entity integrity, URN uniqueness, and DB connectivity
                        </span>
                    </div>

                    {validationResults.length > 0 && (
                        <div className="bg-black/30 rounded-lg border border-white/10">
                            <div className="p-4 border-b border-white/10">
                                <h4 className="font-bold text-white">Results</h4>
                            </div>
                            <div className="divide-y divide-white/5">
                                {validationResults.map((result, i) => (
                                    <div key={i} className="p-3 flex items-start gap-3">
                                        {result.status === 'pass' && <CheckCircle size={16} className="text-green-500 mt-0.5" />}
                                        {result.status === 'fail' && <XCircle size={16} className="text-red-500 mt-0.5" />}
                                        {result.status === 'warn' && <AlertTriangle size={16} className="text-amber-500 mt-0.5" />}
                                        <div className="flex-1">
                                            <div className="font-medium text-white text-sm">{result.name}</div>
                                            <div className="text-xs text-gray-500">{result.message}</div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}

            {/* ================================================================ */}
            {/* DATABASE SECTION */}
            {/* ================================================================ */}
            {activeSection === 'db' && (
                <div className="space-y-4">
                    <div className="bg-black/30 rounded-lg p-4 border border-white/10 flex items-center gap-4 flex-wrap">
                        <Button onClick={exportData} variant="secondary">
                            <Download size={14} className="mr-2" /> Export Entities
                        </Button>
                        <span className="text-gray-600">|</span>
                        <span className="text-gray-500 text-sm">Database: IndexedDB (Dexie v4)</span>
                    </div>

                    {/* Database Actions */}
                    <div className="bg-black/30 rounded-lg p-6 border border-white/10">
                        <h3 className="text-lg font-bold mb-4 text-accent flex items-center gap-2">
                            <Database size={18} /> Database Controls
                        </h3>
                        <div className="flex gap-4">
                            {onResetDB && (
                                <Button
                                    variant="danger"
                                    onClick={() => setConfirmAction({
                                        message: 'This will DELETE ALL DATA from the local database. This cannot be undone. Are you sure?',
                                        action: onResetDB
                                    })}
                                >
                                    <Trash2 size={14} className="mr-2" /> Reset Database
                                </Button>
                            )}
                            {onSeedDB && (
                                <Button
                                    variant="primary"
                                    onClick={() => setConfirmAction({
                                        message: 'This will generate and insert mock data into the database. Existing data will be preserved.',
                                        action: onSeedDB
                                    })}
                                >
                                    <Upload size={14} className="mr-2" /> Seed Mock Data
                                </Button>
                            )}
                        </div>
                    </div>

                    <div className="bg-black/30 rounded-lg p-6 border border-white/10">
                        <h3 className="text-lg font-bold mb-4 text-accent flex items-center gap-2">
                            <Database size={18} /> Raw Database Table Counts
                        </h3>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                            {Object.entries(dbStats).map(([table, count]) => (
                                <div key={table} className="p-3 bg-white/5 rounded border border-white/10">
                                    <div className="text-xs text-gray-500 font-mono">{table}</div>
                                    <div className={clsx(
                                        'text-2xl font-bold',
                                        count < 0 ? 'text-red-500' : count === 0 ? 'text-gray-500' : 'text-white'
                                    )}>
                                        {count < 0 ? 'ERR' : count}
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* ================================================================ */}
            {/* EVENT LOG SECTION */}
            {/* ================================================================ */}
            {activeSection === 'log' && (
                <div className="space-y-4">
                    {/* Persistent Log Notice */}
                    <div className="bg-green-500/10 border border-green-500/30 rounded-lg p-3 flex items-center gap-3 text-sm">
                        <Database size={16} className="text-green-500" />
                        <span className="text-green-400">Logs persist to IndexedDB — they survive page crashes!</span>
                        <div className="ml-auto flex gap-2">
                            <Button onClick={exportLogs} variant="secondary" size="sm">
                                <Download size={12} className="mr-1" /> Export
                            </Button>
                            <Button onClick={clearPersistedLogs} variant="ghost" size="sm">
                                <Trash2 size={12} className="mr-1" /> Clear All
                            </Button>
                        </div>
                    </div>

                    <div className="bg-black/30 rounded-lg border border-white/10">
                        <div className="p-4 border-b border-white/10 flex items-center justify-between">
                            <h4 className="font-bold text-white flex items-center gap-2">
                                <Terminal size={16} /> Event Log
                                <span className="text-xs text-gray-500 font-normal">({eventLog.length} entries)</span>
                            </h4>
                        </div>
                        <div className="max-h-[50vh] overflow-auto">
                            {eventLog.length === 0 ? (
                                <div className="p-8 text-center text-gray-500">
                                    No events yet. Run validation or interact with entities.
                                </div>
                            ) : (
                                <div className="divide-y divide-white/5">
                                    {eventLog.map(entry => (
                                        <div key={entry.id} className="p-3 flex items-start gap-3 text-xs font-mono">
                                            <span className="text-gray-600 whitespace-nowrap">
                                                {entry.timestamp.toLocaleTimeString()}
                                            </span>
                                            <span className={clsx(
                                                entry.type === 'error' && 'text-red-500',
                                                entry.type === 'warn' && 'text-amber-500',
                                                entry.type === 'success' && 'text-green-500',
                                                entry.type === 'info' && 'text-gray-400'
                                            )}>
                                                [{entry.type.toUpperCase()}]
                                            </span>
                                            <span className="text-white">{entry.message}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
