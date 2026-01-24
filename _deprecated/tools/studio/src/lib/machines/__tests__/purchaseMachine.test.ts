import { describe, it, expect } from 'vitest';
import { createActor } from 'xstate';
import { purchaseStatusMachine } from '../purchaseMachine';

describe('purchaseStatusMachine', () => {
    it('should start in wishlist', () => {
        const actor = createActor(purchaseStatusMachine).start();
        expect(actor.getSnapshot().value).toBe('wishlist');
    });

    it('should follow the happy path: wishlist -> considering -> approved -> ordered -> received', () => {
        const actor = createActor(purchaseStatusMachine).start();

        actor.send({ type: 'CONSIDER' });
        expect(actor.getSnapshot().value).toBe('considering');

        actor.send({ type: 'APPROVE' });
        expect(actor.getSnapshot().value).toBe('approved');

        actor.send({ type: 'ORDER' });
        expect(actor.getSnapshot().value).toBe('ordered');
        expect(actor.getSnapshot().context.orderedAt).toBeDefined();

        actor.send({ type: 'RECEIVE' });
        expect(actor.getSnapshot().value).toBe('received');
        expect(actor.getSnapshot().context.receivedAt).toBeDefined();
    });

    it('should handle returns and reorders', () => {
        const actor = createActor(purchaseStatusMachine).start();
        // Fast forward to received
        actor.send({ type: 'APPROVE' });
        actor.send({ type: 'ORDER' });
        actor.send({ type: 'RECEIVE' });

        actor.send({ type: 'RETURN' });
        expect(actor.getSnapshot().value).toBe('returned');

        actor.send({ type: 'REORDER' });
        expect(actor.getSnapshot().value).toBe('ordered');
        expect(actor.getSnapshot().context.receivedAt).toBeUndefined(); // Should be cleared
    });

    it('should handle removal and restoration', () => {
        const actor = createActor(purchaseStatusMachine).start();
        actor.send({ type: 'REMOVE' });
        expect(actor.getSnapshot().value).toBe('removed');

        actor.send({ type: 'RESTORE' });
        expect(actor.getSnapshot().value).toBe('wishlist');
    });
});
