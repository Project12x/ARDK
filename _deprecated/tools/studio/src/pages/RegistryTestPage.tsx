/**
 * Registry Test Page - Testing Gate T1 Validation
 * 
 * @module pages/RegistryTestPage
 * @description
 * Dedicated test page for validating the registry infrastructure.
 * Checks that all entities, actions, and events work correctly.
 * 
 * ## Testing Gate T1 Checklist:
 * - [ ] All 25+ entities defined in ENTITY_REGISTRY
 * - [ ] createUniversalEntity() works for all types
 * - [ ] Event bus delivers events correctly
 * - [ ] Actions execute without errors
 * - [ ] UniversalCard renders all entity types
 * - [ ] No console errors
 */

import React, { useState } from 'react';
import {
    getAllEntityTypes,
    getEntityDefinition,
    createUniversalEntity,
    eventBus,
    showToast,
    STATE_MACHINES,
    COMPUTED_FIELDS,
    canTransition,
    ACTION_REGISTRY,
} from '../lib/registry';
import { UniversalCard } from '../components/universal/UniversalCard';
import { Button } from '../components/ui/Button';
import { CheckCircle, XCircle, Play, RefreshCw, Box, GitBranch } from 'lucide-react';
import { db } from '../lib/db';
import { CreateEntityCommand } from '../lib/commands/EntityCommand';

// ============================================================================
// Test Result Types
// ============================================================================

interface TestResult {
    name: string;
    passed: boolean;
    message: string;
    details?: string;
}

interface TestSection {
    title: string;
    tests: TestResult[];
}

// ============================================================================
// Test Runners
// ============================================================================

/**
 * Test 1: Verify all entity types are defined
 */
function testEntityDefinitions(): TestResult[] {
    const results: TestResult[] = [];
    const entityTypes = getAllEntityTypes();

    // Check count
    results.push({
        name: 'Entity count >= 25',
        passed: entityTypes.length >= 25,
        message: `Found ${entityTypes.length} entity types`,
    });

    // Check each entity has required fields
    for (const type of entityTypes) {
        const def = getEntityDefinition(type);
        const hasRequired = def && def.table && def.primaryField && def.icon && def.color;

        results.push({
            name: `${type}: has required fields`,
            passed: !!hasRequired,
            message: hasRequired
                ? `✓ table=${def.table}, icon=${def.icon}`
                : `Missing: ${!def?.table ? 'table ' : ''}${!def?.primaryField ? 'primaryField ' : ''}${!def?.icon ? 'icon ' : ''}${!def?.color ? 'color' : ''}`,
        });
    }

    return results;
}

/**
 * Test 2: Verify createUniversalEntity works for all types
 */
function testCreateAdapter(): TestResult[] {
    const results: TestResult[] = [];
    const entityTypes = getAllEntityTypes();

    for (const type of entityTypes) {
        try {
            const def = getEntityDefinition(type);
            const mockData: Record<string, unknown> = {
                id: 999,
                status: 'active',
            };

            // Set the primary field
            if (def?.primaryField) {
                mockData[def.primaryField] = `Test ${type}`;
            }

            const entity = createUniversalEntity(type, mockData);

            const valid = entity && entity.type === type && entity.title;
            results.push({
                name: `createUniversalEntity('${type}')`,
                passed: !!valid,
                message: valid
                    ? `Created: "${entity.title}" (urn: ${entity.urn})`
                    : 'Failed to create valid entity',
            });
        } catch (err) {
            results.push({
                name: `createUniversalEntity('${type}')`,
                passed: false,
                message: `Error: ${(err as Error).message}`,
            });
        }
    }

    return results;
}

/**
 * Test 3: Verify event bus works
 */
function testEventBus(): TestResult[] {
    const results: TestResult[] = [];

    // Test event emission and reception
    let received = false;
    const handler = () => { received = true; };

    eventBus.on('toast:show', handler);
    showToast('Test message', 'info');
    eventBus.off('toast:show', handler);

    results.push({
        name: 'Event emission & reception',
        passed: received,
        message: received ? 'showToast() triggered toast:show event' : 'Event not received',
    });

    // Test entity events
    let entityEventReceived = false;
    const entityHandler = () => { entityEventReceived = true; };

    eventBus.on('entity:created', entityHandler);
    eventBus.emit('entity:created', {
        type: 'project',
        entity: { id: 1, type: 'project', title: 'Test', urn: 'project:1', data: {} } as any
    });
    eventBus.off('entity:created', entityHandler);

    results.push({
        name: 'Entity lifecycle events',
        passed: entityEventReceived,
        message: entityEventReceived ? 'entity:created event delivered' : 'Event not received',
    });

    return results;
}

/**
 * Test 4: Verify state machines
 */
function testStateMachines(): TestResult[] {
    const results: TestResult[] = [];
    const machineIds = Object.keys(STATE_MACHINES);

    results.push({
        name: 'State machines defined',
        passed: machineIds.length >= 2,
        message: `Found ${machineIds.length} state machines: ${machineIds.join(', ')}`,
    });

    // Test project status transitions
    const canStart = canTransition('projectStatus', 'planning', 'START');
    const cantInvalid = !canTransition('projectStatus', 'planning', 'INVALID_EVENT');

    results.push({
        name: 'Valid transitions allowed',
        passed: canStart,
        message: canStart ? 'planning -> START -> active works' : 'Transition failed',
    });

    results.push({
        name: 'Invalid transitions blocked',
        passed: cantInvalid,
        message: cantInvalid ? 'Invalid events correctly rejected' : 'Invalid event was accepted',
    });

    return results;
}

/**
 * Test 5: Verify computed fields
 */
function testComputedFields(): TestResult[] {
    const results: TestResult[] = [];
    const fieldIds = Object.keys(COMPUTED_FIELDS);

    results.push({
        name: 'Computed fields defined',
        passed: fieldIds.length >= 4,
        message: `Found ${fieldIds.length} computed fields: ${fieldIds.join(', ')}`,
    });

    // Test progress calculation
    const mockEntity = { id: 1 };
    const mockTasks = [
        { status: 'done' },
        { status: 'done' },
        { status: 'todo' },
        { status: 'todo' },
    ];

    const progress = COMPUTED_FIELDS.progress?.compute(mockEntity, { tasks: mockTasks });
    const expectedProgress = 50;

    results.push({
        name: 'Progress calculation',
        passed: progress === expectedProgress,
        message: `Progress: ${progress}% (expected ${expectedProgress}%)`,
    });

    return results;
}

/**
 * Test 6: Verify ACTION_REGISTRY
 */
function testActionRegistry(): TestResult[] {
    const results: TestResult[] = [];
    const actionIds = Object.keys(ACTION_REGISTRY);

    results.push({
        name: 'Action count >= 20',
        passed: actionIds.length >= 20,
        message: `Found ${actionIds.length} actions: ${actionIds.slice(0, 10).join(', ')}...`,
    });

    // Test that key actions exist
    const requiredActions = ['edit', 'delete', 'archive', 'complete', 'duplicate'];
    for (const actionId of requiredActions) {
        const action = ACTION_REGISTRY[actionId];
        results.push({
            name: `Action '${actionId}' defined`,
            passed: !!action && !!action.handler,
            message: action ? `icon=${action.icon}, label=${action.label}` : 'Not found',
        });
    }

    return results;
}

/**
 * Test 7: Verify Command Layer & Activity Log
 */
async function testCommandLayer(): Promise<TestResult[]> {
    const results: TestResult[] = [];

    try {
        // 1. Execute Create Command
        const testId = `cmd_test_${Date.now()}`;
        const command = new CreateEntityCommand(
            'project',
            { title: 'Command Layer Test', tags: [testId] },
            { actor: 'test_runner', timestamp: new Date() }
        );

        const result = await command.execute();

        results.push({
            name: 'Command execution',
            passed: result.success,
            message: result.success ? `Created urn:${result.urn}` : `Failed: ${result.error}`
        });

        if (result.success && result.entityId) {
            // 2. Verify Activity Log
            // Wait a moment for async DB write if needed, though dexie is usually fast
            const logs = await db.activity_log
                .where('entityId').equals(result.entityId)
                .toArray();

            const hasLog = logs.length > 0;
            const logEntry = logs[0];

            results.push({
                name: 'Activity Log entry created',
                passed: hasLog,
                message: hasLog
                    ? `Found log: ${logEntry.action} by ${logEntry.actor}`
                    : 'No activity log found for this entity'
            });

            // Cleanup
            if (result.entityId) {
                await db.projects.delete(result.entityId);
                if (hasLog) await db.activity_log.delete(logEntry.id!);
            }
        }

    } catch (err) {
        results.push({
            name: 'Command Layer Exception',
            passed: false,
            message: String(err)
        });
    }

    return results;
}

// ============================================================================
// Component
// ============================================================================

// ============================================================================
// State Machine Visualizer
// ============================================================================

function StateMachineVisualizer({ entityType }: { entityType: string }) {
    const [currentState, setCurrentState] = useState<string>('initial');
    const [history, setHistory] = useState<string[]>([]);

    // Get machine ID for entity type
    const machineMap: Record<string, string> = {
        project: 'projectStatus',
        task: 'taskStatus',
        goal: 'goalStatus',
        purchase: 'purchaseStatus',
        routine: 'routineStatus',
        song: 'songStatus',
        recording: 'songStatus',
        inbox: 'inboxStatus',
    };
    const machineId = machineMap[entityType];

    if (!machineId) return <div className="text-gray-500 italic">No state machine defined for {entityType}</div>;

    const allStates = Object.keys(STATE_MACHINES[machineId]?.states || {});
    // Reset if type changes
    React.useEffect(() => {
        const initial = STATE_MACHINES[machineId]?.initial || 'initial';
        setCurrentState(initial);
        setHistory([initial]);
    }, [machineId]);

    const validEvents = canTransition ? Object.keys(STATE_MACHINES[machineId]?.states[currentState]?.on || {}) : [];

    const handleTransition = async (event: string) => {
        // Create mock entity
        const mockEntity = createUniversalEntity(entityType, {
            id: 999,
            title: 'Transition Test',
            status: currentState
        });

        // Use the new executeTransition (if available in exports, otherwise simulate)
        // Since we are in the test page, we can assume we might need to mock or import it.
        // For visualizer purposes, we'll just check valid transitions locally if needed,
        // but better to use the real registry function.

        // Simulating transition for visualizer since executeTransition might need DB
        const next = STATE_MACHINES[machineId].states[currentState].on[event];
        if (next) {
            setCurrentState(next);
            setHistory(prev => [...prev, next]);
        }
    };

    return (
        <div className="bg-black/30 p-4 rounded-lg border border-white/10 space-y-4">
            <h3 className="font-bold text-accent flex items-center gap-2">
                <RefreshCw size={14} /> State Machine: {machineId}
            </h3>

            <div className="flex gap-8">
                {/* States Visualization */}
                <div className="flex-1 space-y-2">
                    <div className="text-xs uppercase text-gray-500 font-bold mb-2">States</div>
                    <div className="flex flex-wrap gap-2">
                        {allStates.map(state => (
                            <div
                                key={state}
                                className={`px-3 py-1 rounded-full text-xs border ${currentState === state
                                    ? 'bg-accent text-black border-accent font-bold ring-2 ring-white/20'
                                    : 'bg-white/5 text-gray-400 border-white/10'
                                    }`}
                            >
                                {state}
                            </div>
                        ))}
                    </div>
                </div>

                {/* Available Transitions */}
                <div className="flex-1 space-y-2 border-l border-white/10 pl-6">
                    <div className="text-xs uppercase text-gray-500 font-bold mb-2">Available Events</div>
                    <div className="flex flex-col gap-2">
                        {validEvents.map(event => (
                            <Button
                                key={event}
                                size="sm"
                                variant="outline"
                                onClick={() => handleTransition(event)}
                                className="justify-between group"
                            >
                                <span>{event}</span>
                                <span className="text-gray-500 group-hover:text-accent">
                                    → {STATE_MACHINES[machineId].states[currentState].on[event]}
                                </span>
                            </Button>
                        ))}
                        {validEvents.length === 0 && (
                            <div className="text-gray-600 italic text-sm">Terminal State</div>
                        )}
                    </div>
                </div>
            </div>

            {/* Path History */}
            <div className="text-xs font-mono text-gray-500 flex items-center gap-2 mt-4 pt-4 border-t border-white/5">
                Path: {history.join(' → ')}
            </div>
        </div>
    );
}

// ============================================================================
// Action Registry Debugger
// ============================================================================

function ActionDebugger() {
    const actions = Object.values(ACTION_REGISTRY);
    const [filter, setFilter] = useState('');

    const filtered = actions.filter(a =>
        a.id.toLowerCase().includes(filter.toLowerCase()) ||
        a.label.toLowerCase().includes(filter.toLowerCase())
    );

    return (
        <div className="space-y-4">
            <input
                type="text"
                placeholder="Filter actions..."
                className="w-full bg-white/5 border border-white/10 rounded px-3 py-2 text-sm"
                value={filter}
                onChange={e => setFilter(e.target.value)}
            />

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-2 max-h-96 overflow-y-auto pr-2">
                {filtered.map(action => (
                    <div key={action.id} className="p-3 bg-white/5 rounded border border-white/5 hover:border-accent/50 transition-colors">
                        <div className="flex items-center justify-between mb-1">
                            <span className="font-bold text-sm text-white">{action.label}</span>
                            <span className="text-[10px] font-mono text-gray-500">{action.id}</span>
                        </div>
                        <div className="flex gap-2 text-[10px] text-gray-400">
                            {action.destructive && <span className="text-red-400">Destructive</span>}
                            {action.batch && <span className="text-blue-400">Batch</span>}
                            {action.shortcut && <span className="text-yellow-400">Key: {action.shortcut}</span>}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ============================================================================
// Component
// ============================================================================

export default function RegistryTestPage() {
    const [testSections, setTestSections] = useState<TestSection[]>([]);
    const [isRunning, setIsRunning] = useState(false);
    const [selectedEntity, setSelectedEntity] = useState<string>('project'); // Default to project

    // Run all tests
    const runTests = async () => {
        setIsRunning(true);

        const sections: TestSection[] = [
            { title: '1. Entity Definitions', tests: testEntityDefinitions() },
            { title: '2. Create Adapter', tests: testCreateAdapter() },
            { title: '3. Event Bus', tests: testEventBus() },
            { title: '4. State Machines', tests: testStateMachines() },
            { title: '5. Computed Fields', tests: testComputedFields() },
            { title: '6. Action Registry', tests: testActionRegistry() },
        ];

        // Run async tests
        try {
            const commandTests = await testCommandLayer();
            sections.push({ title: '7. Command Layer', tests: commandTests });
        } catch (e) {
            console.error(e);
            sections.push({ title: '7. Command Layer', tests: [{ name: 'Test Runner Error', passed: false, message: 'Exception running async tests' }] });
        }

        setTestSections(sections);
        setIsRunning(false);
    };

    // Calculate summary
    const totalTests = testSections.reduce((sum, s) => sum + s.tests.length, 0);
    const passedTests = testSections.reduce(
        (sum, s) => sum + s.tests.filter(t => t.passed).length,
        0
    );
    const failedTests = totalTests - passedTests;

    // Get sample entity for card preview
    const sampleEntity = createUniversalEntity(selectedEntity, {
        id: 1,
        [getEntityDefinition(selectedEntity)?.primaryField || 'title']: `Sample ${selectedEntity}`,
        status: 'active',
        tags: ['demo', 'registry'],
    });

    return (
        <div className="p-6 max-w-7xl mx-auto space-y-8 pb-20">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-black tracking-tight mb-2">🧪 Testing Gate T1</h1>
                    <p className="text-muted-foreground w-full max-w-2xl">
                        Comprehensive validation suite for the Entity Registry infrastructure.
                        Verifies definitions, actions, state machines, and lifecycle events.
                    </p>
                </div>

                <div className="flex gap-3">
                    <Button onClick={() => window.location.reload()} variant="ghost">
                        Reload
                    </Button>
                    <Button onClick={runTests} disabled={isRunning} className="w-40">
                        {isRunning ? (
                            <><RefreshCw className="w-4 h-4 mr-2 animate-spin" /> Running...</>
                        ) : (
                            <><Play className="w-4 h-4 mr-2" /> Run Suite</>
                        )}
                    </Button>
                </div>
            </div>

            {/* Results Grid */}
            {testSections.length > 0 && (
                <div className="space-y-4 animate-in fade-in slide-in-from-top-4">
                    <div className={`p-4 rounded-xl border flex items-center justify-between ${failedTests === 0
                        ? 'bg-green-500/10 border-green-500/30'
                        : 'bg-red-500/10 border-red-500/30'
                        }`}>
                        <div className="flex items-center gap-3">
                            {failedTests === 0 ? (
                                <CheckCircle className="w-6 h-6 text-green-500" />
                            ) : (
                                <XCircle className="w-6 h-6 text-red-500" />
                            )}
                            <div>
                                <div className="font-bold text-lg">
                                    {failedTests === 0 ? 'All Systems Operational' : 'Validation Failed'}
                                </div>
                                <div className="text-sm opacity-80">
                                    {passedTests}/{totalTests} tests passed • {failedTests} failed
                                </div>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-6">
                        {testSections.map((section) => (
                            <div key={section.title} className="border border-white/10 bg-white/5 rounded-xl p-4">
                                <h2 className="font-bold mb-4 flex items-center gap-2 text-sm uppercase tracking-wider text-gray-400">
                                    {section.title}
                                </h2>
                                <div className="space-y-2 max-h-60 overflow-y-auto pr-2 custom-scrollbar">
                                    {section.tests.map((test, i) => (
                                        <div
                                            key={i}
                                            className={`flex items-start gap-3 p-2.5 rounded-lg text-sm border ${test.passed
                                                ? 'bg-green-500/5 border-green-500/10'
                                                : 'bg-red-500/5 border-red-500/10'
                                                }`}
                                        >
                                            {test.passed ? (
                                                <CheckCircle className="w-4 h-4 text-green-500 shrink-0 mt-0.5" />
                                            ) : (
                                                <XCircle className="w-4 h-4 text-red-500 shrink-0 mt-0.5" />
                                            )}
                                            <div>
                                                <div className="font-medium text-white">{test.name}</div>
                                                <div className="text-gray-500 text-xs mt-0.5">{test.message}</div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <div className="grid grid-cols-1 xl:grid-cols-3 gap-8">
                {/* Left Column: Explorer */}
                <div className="xl:col-span-2 space-y-8">

                    {/* Entity Explorer */}
                    <section className="border border-white/10 bg-black/20 rounded-xl p-6">
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                            <Box className="text-accent" /> Entity Explorer
                        </h2>

                        <div className="flex flex-wrap gap-2 mb-8">
                            {getAllEntityTypes().map((type) => (
                                <button
                                    key={type}
                                    onClick={() => setSelectedEntity(type)}
                                    className={`px-3 py-1.5 rounded-md text-xs font-medium transition-all ${selectedEntity === type
                                        ? 'bg-accent text-black shadow-[0_0_15px_rgba(255,255,255,0.3)]'
                                        : 'bg-white/5 text-gray-400 hover:bg-white/10 hover:text-white'
                                        }`}
                                >
                                    {type}
                                </button>
                            ))}
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-gray-500 uppercase">Card Preview</h3>
                                <div className="p-4 border border-white/5 rounded-2xl bg-black/40 min-h-[200px] flex items-center justify-center">
                                    <div className="w-full max-w-sm">
                                        <UniversalCard
                                            entity={sampleEntity}
                                            showActions={true}
                                            showStatus={true}
                                            onEdit={async () => console.log('Edit')}
                                            onDelete={async () => console.log('Delete')}
                                        />
                                    </div>
                                </div>
                            </div>

                            <div className="space-y-4">
                                <h3 className="text-sm font-bold text-gray-500 uppercase">JSON Definition</h3>
                                <pre className="text-[10px] font-mono bg-black rounded-lg p-4 h-[250px] overflow-auto border border-white/10 text-green-400">
                                    {JSON.stringify(getEntityDefinition(selectedEntity), null, 2)}
                                </pre>
                            </div>
                        </div>
                    </section>

                    {/* State Machine Visualizer */}
                    <section className="border border-white/10 bg-black/20 rounded-xl p-6">
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                            <GitBranch className="text-accent" /> State Machine Visualizer
                        </h2>
                        <StateMachineVisualizer entityType={selectedEntity} />
                    </section>
                </div>

                {/* Right Column: Action Registry */}
                <div className="xl:col-span-1">
                    <section className="border border-white/10 bg-black/20 rounded-xl p-6 h-full">
                        <h2 className="text-xl font-bold mb-6 flex items-center gap-2">
                            <Play className="text-accent" /> Action Registry
                        </h2>
                        <ActionDebugger />
                    </section>
                </div>
            </div>
        </div>
    );
}
