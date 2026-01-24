import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { syncStatusMachine } from '../syncMachine';

describe('syncStatusMachine', () => {
    it('should start in idle', () => {
        const actor = createActor(syncStatusMachine).start();
        expect(actor.getSnapshot().value).toBe('idle');
        expect(actor.getSnapshot().context.pendingChanges).toBe(0);
    });

    it('should transition to syncing on SYNC', () => {
        const actor = createActor(syncStatusMachine).start();
        actor.send({ type: 'SYNC' });
        expect(actor.getSnapshot().value).toBe('syncing');
    });

    it('should transition to synced on SYNC_SUCCESS', () => {
        const actor = createActor(syncStatusMachine).start();
        actor.send({ type: 'SYNC' });

        const timestamp = new Date();
        actor.send({ type: 'SYNC_SUCCESS', timestamp });

        expect(actor.getSnapshot().value).toBe('synced');
        expect(actor.getSnapshot().context.lastSyncAt).toBe(timestamp);
        expect(actor.getSnapshot().context.retryCount).toBe(0);
    });

    it('should transition to error on SYNC_ERROR', () => {
        const actor = createActor(syncStatusMachine).start();
        actor.send({ type: 'SYNC' });

        actor.send({ type: 'SYNC_ERROR', error: 'Network fail' });

        expect(actor.getSnapshot().value).toBe('error');
        expect(actor.getSnapshot().context.lastError).toBe('Network fail');
        expect(actor.getSnapshot().context.retryCount).toBe(1);
    });

    it('should retry from error state', () => {
        const actor = createActor(syncStatusMachine).start();
        actor.send({ type: 'SYNC' });
        actor.send({ type: 'SYNC_ERROR', error: 'fail' });

        actor.send({ type: 'RETRY' });
        expect(actor.getSnapshot().value).toBe('syncing');
    });

    it('should reset from error state to idle', () => {
        const actor = createActor(syncStatusMachine).start();
        actor.send({ type: 'SYNC' });
        actor.send({ type: 'SYNC_ERROR', error: 'fail' });

        actor.send({ type: 'RESET' });
        expect(actor.getSnapshot().value).toBe('idle');
        expect(actor.getSnapshot().context.lastError).toBeUndefined();
        expect(actor.getSnapshot().context.retryCount).toBe(0);
    });

    it('should track pending changes', () => {
        const actor = createActor(syncStatusMachine).start();
        actor.send({ type: 'QUEUE_CHANGE' });
        actor.send({ type: 'QUEUE_CHANGE' });

        expect(actor.getSnapshot().context.pendingChanges).toBe(2);
    });
});
