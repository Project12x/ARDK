import React from 'react';
import { Link } from 'react-router-dom';
import { eventBus } from '../lib/registry/eventBus';
import { Edit, Eye, FolderKanban, CheckSquare, Package, ArrowRight, LayoutTemplate } from 'lucide-react';

export function UniversalPageTest() {

    const testEntities = [
        { type: 'project', id: '1', label: 'Test Project (ID: 1)', desc: 'Should open Tabbed Modal' },
        { type: 'task', id: '101', label: 'Test Task (ID: 101)', desc: 'Should open Generic AutoForm' },
        { type: 'inventory', id: '5', label: 'Inventory Item (ID: 5)', desc: 'Should open Generic AutoForm' },
        { type: 'asset', id: '2', label: 'Asset (ID: 2)', desc: 'Should open Generic AutoForm' },
    ];

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8">
            <div className="space-y-2">
                <h1 className="text-3xl font-bold flex items-center gap-3">
                    <LayoutTemplate className="text-accent" />
                    Universal Page System Test
                </h1>
                <p className="text-gray-400">
                    Verify the <b>UniversalDetailPage</b> routing and the <b>UniversalEditModal</b> hybrid behavior.
                </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {testEntities.map((item) => (
                    <div key={item.type} className="bg-white/5 border border-white/10 rounded-xl p-6 space-y-4">
                        <div className="flex items-center justify-between">
                            <h3 className="font-bold text-lg">{item.type.toUpperCase()}</h3>
                            <span className="text-xs font-mono bg-black/50 px-2 py-1 rounded text-gray-500">ID: {item.id}</span>
                        </div>
                        <p className="text-sm text-gray-400">{item.desc}</p>

                        <div className="flex gap-3 pt-2">
                            {/* Test Modal */}
                            <button
                                onClick={() => eventBus.emit('modal:edit', {
                                    modalId: 'edit',
                                    entityType: item.type,
                                    entityId: item.id
                                })}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-accent/10 hover:bg-accent/20 text-accent rounded transition-colors"
                            >
                                <Edit size={16} />
                                Test Modal
                            </button>

                            {/* Test Page Route */}
                            <Link
                                to={`/entity/${item.type}/${item.id}`}
                                className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-white/5 hover:bg-white/10 text-white rounded transition-colors"
                            >
                                <Eye size={16} />
                                View Page
                            </Link>
                        </div>
                    </div>
                ))}
            </div>

            <div className="bg-blue-500/10 border border-blue-500/20 rounded-xl p-6">
                <h3 className="text-blue-400 font-bold mb-2">Instructions</h3>
                <ul className="list-disc list-inside text-sm text-gray-300 space-y-1">
                    <li>Click <b>Test Modal</b> on Project to verify the <b>High-Fidelity Tabbed Form</b> loads.</li>
                    <li>Click <b>Test Modal</b> on Task/Inventory to verify the <b>Generic Auto-Form</b> loads.</li>
                    <li>Click <b>View Page</b> to verify the <b>Universal Detail Page</b> loads correctly.</li>
                    <li>Ensure <b>History Panel</b> appears on the Detail Page.</li>
                </ul>
            </div>
        </div>
    );
}
