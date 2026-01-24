/**
 * Universal Adapters Index
 * Central export for all entity adapters
 */

// Core Entity Adapters
export { toUniversalProject, type ProjectRelatedData } from './projectAdapter';
export { toUniversalInventory, toUniversalInventoryBatch, type InventoryRelatedData } from './inventoryAdapter';
export { toUniversalTask, toUniversalTaskBatch, type TaskRelatedData } from './taskAdapter';
export { toUniversalAsset, toUniversalAssetBatch, type AssetRelatedData } from './assetAdapter';
export { toUniversalGoal, toUniversalGoalBatch, type GoalRelatedData } from './goalAdapter';

// Media Entity Adapters
export { toUniversalSong, toUniversalSongBatch, type SongRelatedData } from './songAdapter';
export { toUniversalAlbum, toUniversalAlbumBatch } from './albumAdapter';
export { toUniversalRecording, toUniversalRecordingBatch } from './recordingAdapter';
export { toUniversalLibrary, toUniversalLibraryBatch } from './libraryAdapter';

// Workflow Entity Adapters
export { toUniversalInbox, toUniversalInboxBatch } from './inboxAdapter';
export { toUniversalRoutine, toUniversalRoutineBatch } from './routineAdapter';
export { toUniversalPurchase, toUniversalPurchaseBatch } from './purchaseAdapter';
export { toUniversalVendor, toUniversalVendorBatch } from './vendorAdapter';
export * from './specialAdapter';
export { toUniversalReminder, toUniversalReminderBatch } from './reminderAdapter';

// Knowledge & History Adapters
export { toUniversalGlobalNote, toUniversalGlobalNoteBatch } from './globalNoteAdapter';
export { toUniversalLog, toUniversalLogBatch } from './logAdapter';

// Relationship Adapters
export { toUniversalEntityLink, toUniversalEntityLinkBatch } from './entityLinkAdapter';

// Phase 8: NEW Universal Types
export { toUniversalActivity, toUniversalActivityBatch, type ActivityEntry, ACTIVITY_ACTION_CONFIG } from './activityAdapter';
export { toUniversalComment, toUniversalCommentBatch, type CommentEntry } from './commentAdapter';
export { toUniversalMetric, toUniversalMetricBatch, type MetricEntry } from './metricAdapter';
export { toUniversalRelationship, toUniversalRelationshipBatch, type RelationshipEntry, RELATIONSHIP_CONFIG } from './relationshipAdapter';
export { toUniversalProcess, toUniversalProcessBatch, type ProcessEntry, type ProcessStep } from './processAdapter';
export { toUniversalTemplate, toUniversalTemplateBatch, type TemplateEntry } from './templateAdapter';
export { toUniversalCollection, toUniversalCollectionBatch, type CollectionEntry, type CollectionMember } from './collectionAdapter';
