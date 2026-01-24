import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { goalStatusMachine } from '../goalMachine';

describe('goalStatusMachine', () => {
    it('should start in not_started', () => {
        const actor = createActor(goalStatusMachine).start();
        expect(actor.getSnapshot().value).toBe('not_started');
    });

    it('should transition to working on START', () => {
        const actor = createActor(goalStatusMachine).start();
        actor.send({ type: 'START' });
        expect(actor.getSnapshot().value).toBe('working');
    });

    it('should transition to achieved on ACHIEVE', () => {
        const actor = createActor(goalStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'ACHIEVE' });

        expect(actor.getSnapshot().value).toBe('achieved');
        expect(actor.getSnapshot().context.achievedAt).toBeDefined();
    });

    it('should transition to abandoned on ABANDON', () => {
        const actor = createActor(goalStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'ABANDON' });

        expect(actor.getSnapshot().value).toBe('abandoned');
    });

    it('should handle pause and resume', () => {
        const actor = createActor(goalStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'PAUSE' });
        expect(actor.getSnapshot().value).toBe('paused');

        actor.send({ type: 'RESUME' });
        expect(actor.getSnapshot().value).toBe('working');
    });

    it('should allow REOPEN from achieved', () => {
        const actor = createActor(goalStatusMachine).start();
        actor.send({ type: 'START' });
        actor.send({ type: 'ACHIEVE' });
        actor.send({ type: 'REOPEN' });

        expect(actor.getSnapshot().value).toBe('working');
        expect(actor.getSnapshot().context.achievedAt).toBeUndefined();
    });
});
