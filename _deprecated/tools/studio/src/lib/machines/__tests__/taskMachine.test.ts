import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { taskStatusMachine } from '../taskMachine';

describe('taskStatusMachine', () => {
    it('should start in "todo" state', () => {
        const actor = createActor(taskStatusMachine);
        actor.start();
        expect(actor.getSnapshot().value).toBe('todo');
        expect(actor.getSnapshot().context.previousStatus).toBeUndefined();
    });

    it('should transition to "in_progress" on START', () => {
        const actor = createActor(taskStatusMachine);
        actor.start();
        actor.send({ type: 'START' });
        expect(actor.getSnapshot().value).toBe('in_progress');
        expect(actor.getSnapshot().context.previousStatus).toBe('todo');
    });

    it('should transition to "done" on COMPLETE from in_progress', () => {
        const actor = createActor(taskStatusMachine).start();
        actor.send({ type: 'START' }); // to in_progress
        actor.send({ type: 'COMPLETE' });
        expect(actor.getSnapshot().value).toBe('done');
        expect(actor.getSnapshot().context.previousStatus).toBe('in_progress');
    });

    it('should transition to "blocked" on BLOCK from in_progress', () => {
        const actor = createActor(taskStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'BLOCK', reason: 'Waiting on API' });

        const snapshot = actor.getSnapshot();
        expect(snapshot.value).toBe('blocked');
        expect(snapshot.context.previousStatus).toBe('in_progress');
        expect(snapshot.context.blockedReason).toBe('Waiting on API');
    });

    it('should transition back to "in_progress" on UNBLOCK', () => {
        const actor = createActor(taskStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'BLOCK', reason: 'blocker' });
        actor.send({ type: 'UNBLOCK' });

        expect(actor.getSnapshot().value).toBe('in_progress');
        expect(actor.getSnapshot().context.previousStatus).toBe('blocked');
        expect(actor.getSnapshot().context.blockedReason).toBeUndefined();
    });

    it('should allow COMPLETE from blocked state', () => {
        const actor = createActor(taskStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'BLOCK' });
        actor.send({ type: 'COMPLETE' });

        expect(actor.getSnapshot().value).toBe('done');
        expect(actor.getSnapshot().context.previousStatus).toBe('blocked');
    });

    it('should allow REOPEN from done state', () => {
        const actor = createActor(taskStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'COMPLETE' });
        actor.send({ type: 'REOPEN' });

        expect(actor.getSnapshot().value).toBe('todo');
        expect(actor.getSnapshot().context.previousStatus).toBe('done');
    });

    it('should allow RESET from in_progress state', () => {
        const actor = createActor(taskStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'RESET' });

        expect(actor.getSnapshot().value).toBe('todo');
        expect(actor.getSnapshot().context.previousStatus).toBe('in_progress');
    });
});
