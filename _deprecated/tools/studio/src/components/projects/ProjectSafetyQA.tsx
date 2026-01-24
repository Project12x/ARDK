import { useState } from 'react';
import { useLiveQuery } from 'dexie-react-hooks';
import { db, type Project } from '../../lib/db';
import { SafetyGate } from '../safety/SafetyGate';
import { Button } from '../ui/Button';
import { Input } from '../ui/Input';
import { Trash2, Plus, CheckCircle2 } from 'lucide-react';
import clsx from 'clsx';

interface ProjectSafetyQAProps {
    project: Project;
    projectId: number;
}

export function ProjectSafetyQA({ project, projectId }: ProjectSafetyQAProps) {
    return (
        <div className="space-y-8 max-w-5xl mx-auto">

            {/* Safety Section */}
            <div>
                <SafetyGate project={project} />
            </div>

            {/* QA Test Plan Section */}
            <div>
                <div className="bg-black/30 border border-white/10 rounded-xl p-6">
                    <div className="flex items-center gap-2 mb-6">
                        <CheckCircle2 size={20} className="text-accent" />
                        <h3 className="font-bold text-white text-lg">QA Test Plan</h3>
                    </div>
                    <TestPlan projectId={projectId} />
                </div>
            </div>
        </div>
    );
}

function TestPlan({ projectId }: { projectId: number }) {
    const tests = useLiveQuery(() => db.project_tests.where('project_id').equals(projectId).toArray());
    const [newTest, setNewTest] = useState({ test_case: '', expected: '' });

    const addTest = async () => {
        if (!newTest.test_case) return;
        await db.project_tests.add({
            project_id: projectId,
            test_case: newTest.test_case,
            expected_value: newTest.expected,
            actual_value: '',
            status: 'pending',
            notes: ''
        });
        setNewTest({ test_case: '', expected: '' });
    };

    const updateStatus = (id: number, status: 'pass' | 'fail' | 'pending') => {
        db.project_tests.update(id, { status });
    };

    const deleteTest = (id: number) => db.project_tests.delete(id);

    return (
        <div className="space-y-6">
            <div className="flex gap-2 items-end bg-white/5 p-4 rounded-lg border border-white/5">
                <div className="flex-1">
                    <Input
                        label="Test Case"
                        placeholder="What to verify?"
                        value={newTest.test_case}
                        onChange={e => setNewTest({ ...newTest, test_case: e.target.value })}
                    />
                </div>
                <div className="w-1/3">
                    <Input
                        label="Expected Outcome"
                        placeholder="Range / Behavior"
                        value={newTest.expected}
                        onChange={e => setNewTest({ ...newTest, expected: e.target.value })}
                    />
                </div>
                <Button onClick={addTest} className="mb-0.5"><Plus size={16} className="mr-2" /> Add Case</Button>
            </div>

            <div className="space-y-3">
                {tests?.map(test => (
                    <div key={test.id} className="bg-black border border-white/10 p-4 rounded flex items-center gap-4 group hover:border-white/20 transition-colors">
                        <div className="flex-1">
                            <h4 className="font-bold text-gray-200">{test.test_case}</h4>
                            <div className="flex gap-4 mt-1 text-xs font-mono text-gray-500">
                                <span>EXPECTED: <span className="text-gray-400">{test.expected_value || 'N/A'}</span></span>
                            </div>
                        </div>

                        <div className="flex items-center gap-2">
                            <button
                                onClick={() => updateStatus(test.id!, 'pass')}
                                className={clsx("px-3 py-1 text-xs font-bold rounded border transition-all", test.status === 'pass' ? "bg-green-500 text-black border-green-500" : "border-white/10 text-gray-500 hover:text-green-500")}
                            >
                                PASS
                            </button>
                            <button
                                onClick={() => updateStatus(test.id!, 'fail')}
                                className={clsx("px-3 py-1 text-xs font-bold rounded border transition-all", test.status === 'fail' ? "bg-red-500 text-white border-red-500" : "border-white/10 text-gray-500 hover:text-red-500")}
                            >
                                FAIL
                            </button>
                        </div>

                        <button onClick={() => deleteTest(test.id!)} className="text-gray-700 hover:text-red-500 transition-colors ml-2">
                            <Trash2 size={14} />
                        </button>
                    </div>
                ))}

                {tests?.length === 0 && (
                    <div className="text-center py-10 text-gray-600 font-mono text-sm border-2 border-dashed border-white/5 rounded">
                        No active test plan.
                    </div>
                )}
            </div>
        </div>
    );
}
