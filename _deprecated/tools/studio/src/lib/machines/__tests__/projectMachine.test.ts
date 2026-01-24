import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { projectStatusMachine } from '../projectMachine';

describe('projectStatusMachine', () => {
    it('should start in "planning"', () => {
        const actor = createActor(projectStatusMachine).start();
        expect(actor.getSnapshot().value).toBe('planning');
        expect(actor.getSnapshot().context.transitionCount).toBe(0);
    });

    it('should transition to "active" on START', () => {
        const actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });

        expect(actor.getSnapshot().value).toBe('active');
        expect(actor.getSnapshot().context.previousStatus).toBe('planning');
        expect(actor.getSnapshot().context.transitionCount).toBe(1);
    });

    it('should transition to "on_hold" on PAUSE from active', () => {
        const actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'PAUSE' });

        expect(actor.getSnapshot().value).toBe('on_hold');
        expect(actor.getSnapshot().context.previousStatus).toBe('active');
        expect(actor.getSnapshot().context.transitionCount).toBe(2);
    });

    it('should transition to "active" on RESUME from on_hold', () => {
        const actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'PAUSE' });
        actor.send({ type: 'RESUME' });

        expect(actor.getSnapshot().value).toBe('active');
        expect(actor.getSnapshot().context.previousStatus).toBe('on_hold');
    });

    it('should transition to "completed" on COMPLETE from active', () => {
        const actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'COMPLETE' });

        expect(actor.getSnapshot().value).toBe('completed');
        expect(actor.getSnapshot().context.previousStatus).toBe('active');
    });

    it('should transition to "active" on REOPEN from completed', () => {
        const actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'COMPLETE' });
        actor.send({ type: 'REOPEN' });

        expect(actor.getSnapshot().value).toBe('active');
    });

    it('should transition to "archived" on ARCHIVE from any state', () => {
        // Planning -> Archived
        let actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'ARCHIVE' });
        expect(actor.getSnapshot().value).toBe('archived');

        // Active -> Archived
        actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'ARCHIVE' });
        expect(actor.getSnapshot().value).toBe('archived');

        // Completed -> Archived
        actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'COMPLETE' });
        actor.send({ type: 'ARCHIVE' });
        expect(actor.getSnapshot().value).toBe('archived');
    });

    it('should transition to "planning" on RESTORE from archived', () => {
        const actor = createActor(projectStatusMachine).start();
        actor.send({ type: 'ARCHIVE' });
        actor.send({ type: 'RESTORE' });

        expect(actor.getSnapshot().value).toBe('planning');
        expect(actor.getSnapshot().context.previousStatus).toBe('archived');
    });
});
