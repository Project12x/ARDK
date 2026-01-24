# Registry Module

> Single Source of Truth for Entity Configuration

This module centralizes all entity type definitions, actions, state machines, and computed fields.
The goal is **one edit = everywhere updated**.

## Architecture

```
src/lib/registry/
├── index.ts          # Central exports
├── entityRegistry.ts # All entity type definitions
├── actionRegistry.ts # Edit, delete, and custom actions
├── stateMachines.ts  # Status transitions (e.g., todo → done)
├── computedFields.ts # Derived values (progress, overdue, etc.)
├── validation.ts     # Zod schema validation & sanitization
├── eventBus.ts       # Global event system using mitt
└── createAdapter.ts  # Factory to create UniversalEntity from raw DB data
```

## Usage

```typescript
import { 
  ENTITY_REGISTRY, 
  createUniversalEntity, 
  eventBus,
  showToast 
} from '@/lib/registry';

// Get entity configuration
const projectDef = ENTITY_REGISTRY['project'];
console.log(projectDef.icon);  // 'FolderKanban'
console.log(projectDef.color); // '#3b82f6'

// Transform raw DB object to UniversalEntity
const universal = createUniversalEntity('project', rawProject, { tasks });

// Listen for events
eventBus.on('entity:created', ({ type, entity }) => {
  console.log(`New ${type} created:`, entity.title);
});

// Emit events
showToast('Project saved!', 'success');
```

## Adding a New Entity Type

1. **Add to EntityType union** in `src/lib/universal/types.ts`:

   ```typescript
   export type EntityType = 
     | 'project'
     | 'my_new_entity'  // ← Add here
     | ...;
   ```

2. **Add definition** to `ENTITY_REGISTRY` in `entityRegistry.ts`:

   ```typescript
   my_new_entity: {
     table: 'my_new_entities',      // DB table name
     primaryField: 'title',          // Main display field
     icon: 'Star',                   // Lucide icon name
     color: '#f59e0b',               // Accent color
     actions: ['edit', 'delete'],    // From ACTION_REGISTRY
     searchFields: ['title', 'tags'],
   },
   ```

3. **Optional: Add state machine** in `stateMachines.ts` if entity has status
4. **Optional: Add computed fields** in `computedFields.ts` for derived values
5. **Optional: Register custom actions** in `actionRegistry.ts`

## Entity Definition Properties

| Property | Required | Description |
|----------|----------|-------------|
| `table` | ✅ | Dexie table name |
| `primaryField` | ✅ | Field for main title |
| `icon` | ✅ | Lucide icon name (string) |
| `color` | ✅ | Hex color for accent |
| `actions` | ✅ | Array of action IDs |
| `searchFields` | ✅ | Fields to index for search |
| `subtitleField` | | Secondary display field |
| `badges` | | Fields to show as badges |
| `tags` | | Field containing tag array |
| `thumbnail` | | Field for image URL |
| `ratings` | | Numeric rating configs |
| `metaGrid` | | Key-value metadata display |
| `computedFields` | | Auto-calculated fields |
| `stateMachine` | | State machine ID for status |

## Event Types

```typescript
// Entity lifecycle
'entity:created' | 'entity:updated' | 'entity:deleted'

// Modal control
'modal:open' | 'modal:close' | 'modal:edit'

// UI feedback
'toast:show' | 'sidebar:toggle' | 'theme:changed'

// Actions
'action:started' | 'action:completed' | 'action:failed'
```

## Future: Plugin System (Phase 23)

Plugins will register custom entities:

```typescript
import { registerEntityType, registerAction } from '@/lib/registry';

registerEntityType('recipe', {
  table: 'recipes',
  primaryField: 'name',
  icon: 'ChefHat',
  color: '#f97316',
  actions: ['edit', 'delete', 'cook'],
  searchFields: ['name', 'ingredients'],
});

registerAction('cook', {
  icon: 'Flame',
  label: 'Start Cooking',
  handler: (entity) => startCooking(entity),
});
```

---

*Last updated: Phase 11B*
