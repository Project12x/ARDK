import { db, type EntityLink } from '../lib/db';
import type { EntityType, LinkType } from '../lib/universal';

export class LinkService {
    /**
     * Create a link between two entities
     */
    static async link(
        sourceType: EntityType,
        sourceId: number,
        targetType: EntityType,
        targetId: number,
        relationship: LinkType
    ) {
        // Prevent duplicates
        const existing = await db.links
            .where({
                source_type: sourceType,
                source_id: sourceId,
                target_type: targetType,
                target_id: targetId,
                relationship
            })
            .first();

        if (existing) return existing.id;

        return await db.links.add({
            source_type: sourceType,
            source_id: sourceId,
            target_type: targetType,
            target_id: targetId,
            relationship,
            created_at: new Date()
        });
    }

    /**
     * Remove a link
     */
    static async unlink(
        sourceType: EntityType,
        sourceId: number,
        targetType: EntityType,
        targetId: number
    ) {
        return await db.links
            .where({
                source_type: sourceType,
                source_id: sourceId,
                target_type: targetType,
                target_id: targetId
            })
            .delete();
    }

    /**
     * Get all entities linked TO this entity (Incoming)
     */
    static async getIncomingLinks(type: EntityType, id: number) {
        return await db.links
            .where('[target_type+target_id]')
            .equals([type, id])
            .toArray();
    }

    /**
     * Get all entities this entity links TO (Outgoing)
     */
    static async getOutgoingLinks(type: EntityType, id: number) {
        return await db.links
            .where('[source_type+source_id]')
            .equals([type, id])
            .toArray();
    }

    /**
     * Get all connections (both ways)
     */
    static async getAllConnections(type: EntityType, id: number) {
        const [incoming, outgoing] = await Promise.all([
            this.getIncomingLinks(type, id),
            this.getOutgoingLinks(type, id)
        ]);
        return [...incoming, ...outgoing];
    }
}
