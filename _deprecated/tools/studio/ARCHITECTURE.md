# WalrusPM Architecture Guide

> **Living Documentation** — Updated as architecture evolves  
> **Last Updated:** January 10, 2026  
> **Version:** 2.0 (Universal Architecture)

---

## Quick Navigation

- [Project Overview](#project-overview)
- [Technology Stack](#technology-stack)
- [Directory Structure](#directory-structure)
- [Core Systems](#core-systems)
- [Data Flow](#data-flow)
- [Key Patterns](#key-patterns)
- [Entity Registry](#entity-registry)
- [AI Integration](#ai-integration)
- [State Management](#state-management)

---

## Project Overview

WalrusPM is a **personal project management application** built with React and Vite. It manages multiple entity types (Projects, Tasks, Goals, Assets, etc.) through a unified system.

### Key Concepts

| Concept | Description |
|---------|-------------|
| **Universal Architecture** | All entities handled through centralized registry |
| **Command Layer** | All mutations via Command pattern, never direct DB calls |
| **Parity Strategy** | Legacy code kept until new implementation matches features |
| **Registry-Driven** | Entity metadata, views, forms defined in `ENTITY_REGISTRY` |

---

## Technology Stack

### Core

| Technology | Purpose |
|------------|---------|
| **React 18** | UI framework |
| **Vite** | Build tool / dev server |
| **TypeScript** | Type safety |
| **Dexie (IndexedDB)** | Local-first database |
| **TailwindCSS** | Styling |

### State & Data

| Library | Purpose |
|---------|---------|
| **Zustand** | Global state management |
| **React Query** | Server state / caching |
| **XState** | State machines for status flows |
| **Immer** | Immutable state updates |
| **Zod** | Schema validation |

### AI Integration

| Library | Purpose |
|---------|---------|
| **Vercel AI SDK (`ai`)** | Unified LLM interface |
| **@ai-sdk/google** | Gemini provider |
| **@ai-sdk/openai** | OpenAI provider |
| **@ai-sdk/anthropic** | Claude provider |
| **@ai-sdk/groq** | Groq (fast inference) |
| **ollama-ai-provider** | Local LLM via Ollama |

### UI Components

| Library | Purpose |
|---------|---------|
| **Radix UI** | Accessible primitives (Dialog, Tooltip, etc.) |
| **HeadlessUI** | Transitions, Menu components |
| **Lucide React** | Icons |
| **Framer Motion** | Animations |
| **react-hook-form** | Form management |
| **cmdk** | Command palette |

---

## Directory Structure

```
src/
├── components/           # React components
│   ├── universal/        # NEW: Universal card/form system
│   ├── cards/            # LEGACY: Entity-specific cards
│   ├── primitives/       # Radix UI wrappers
│   └── ui/               # Shared UI components
│
├── lib/                  # Core logic
│   ├── ai/               # NEW: Vercel AI SDK integration
│   │   ├── providers.ts  # Provider configurations
│   │   ├── useLLM.ts     # Unified LLM hook
│   │   ├── useChat.ts    # Conversational hook
│   │   └── AIProvider.tsx # React context
│   │
│   ├── commands/         # Command layer (mutations)
│   ├── db/               # Dexie database
│   ├── machines/         # XState state machines
│   ├── registry/         # ENTITY_REGISTRY definition
│   ├── universal/        # Universal adapter system
│   └── *.ts              # Various services
│
├── pages/                # Route components
├── hooks/                # Custom React hooks
├── stores/               # Zustand stores
├── test/                 # Test setup & fixtures
└── mocks/                # MSW mock handlers
```

---

## Core Systems

### 1. Entity Registry

The **`ENTITY_REGISTRY`** (`src/lib/registry/ENTITY_REGISTRY.ts`) is the single source of truth for all entity metadata:

```typescript
ENTITY_REGISTRY.project = {
  tableName: 'projects',
  displayName: 'Project',
  icon: FolderKanban,
  schema: projectSchema,
  stateMachine: 'projectStatus',
  cardVariants: ['compact', 'moderate', 'detailed'],
  tabs: ['overview', 'tasks', 'goals', ...],
  // ...
};
```

**What it controls:**

- Database table mapping
- Display names and icons
- Forms and validation schemas
- Card variants
- Detail page tabs
- State machine bindings

### 2. Command Layer

All data mutations go through **Commands** (`src/lib/commands/`):

```typescript
// Instead of:
db.projects.update(id, data); // ❌ NEVER

// Always use:
new UpdateEntityCommand('project', id, data).execute(); // ✅
```

**Benefits:**

- Undo/redo capability
- Audit logging
- Validation layer
- EventBus integration

### 3. Universal Card System

The **Universal Card** (`src/components/universal/`) renders any entity:

```typescript
<UniversalCard 
  entity={project} 
  entityType="project" 
  variant="moderate" 
/>
```

**Variants:**

- `compact` — List item (1 line)
- `moderate` — Card (3-4 lines)
- `detailed` — Full card with actions

---

## Data Flow

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   UI Layer  │───▶│  Commands   │───▶│   Dexie DB  │
│ (React)     │    │ (Mutations) │    │ (IndexedDB) │
└─────────────┘    └─────────────┘    └─────────────┘
       ▲                  │                  │
       │                  ▼                  ▼
       │           ┌─────────────┐    ┌─────────────┐
       └───────────│  EventBus   │◀───│ React Query │
                   │ (mitt)      │    │ (Cache)     │
                   └─────────────┘    └─────────────┘
```

### Flow Explanation

1. **User Action** → Component calls Command
2. **Command** → Validates, mutates DB, emits event
3. **EventBus** → Notifies subscribers (XState, other components)
4. **React Query** → Invalidates cache, refetches
5. **UI** → Re-renders with new data

---

## Key Patterns

### Pattern: Registry Lookup

```typescript
import { ENTITY_REGISTRY } from '@/lib/registry';

const config = ENTITY_REGISTRY[entityType];
const Icon = config.icon;
const schema = config.schema;
```

### Pattern: Feature Flags

```typescript
import { isFeatureEnabled, FEATURE_FLAGS } from '@/lib/featureFlags';

if (isFeatureEnabled(FEATURE_FLAGS.USE_NEW_AI_SERVICE)) {
  // Use new Vercel AI SDK
} else {
  // Use legacy AIService
}
```

### Pattern: State Machines

```typescript
import { useMachineWithEventBus } from '@/lib/machines';
import { projectStatusMachine } from '@/lib/machines';

const { state, send } = useMachineWithEventBus(projectStatusMachine, {
  entityType: 'project',
  entityId: project.id,
});

// Transition
send({ type: 'START' }); // planning → active
```

### Pattern: AI Usage

```typescript
import { useLLM } from '@/lib/ai';

const { generate, isLoading } = useLLM();

const response = await generate({
  prompt: 'Suggest a project name...',
  model: 'gemini:gemini-2.5-flash',
});
```

---

## Entity Registry

### Supported Entities

| Entity | Table | Status Machine |
|--------|-------|----------------|
| `project` | `projects` | `projectStatus` |
| `task` | `project_tasks` | `taskStatus` |
| `goal` | `goals` | `goalStatus` |
| `asset` | `assets` | — |
| `purchase` | `purchases` | `purchaseStatus` |
| `song` | `songs` | `songStatus` |
| `routine` | `routines` | `routineStatus` |
| `inbox` | `inbox_items` | `inboxStatus` |
| `note` | `notes` | — |
| `session` | `work_sessions` | — |

---

## AI Integration

### Provider Hierarchy

```
User selects model
       │
       ▼
┌──────────────────┐
│ getModel(id)     │  ← providers.ts
└────────┬─────────┘
         │
    ┌────┴────┬────────┬────────┬────────┐
    ▼         ▼        ▼        ▼        ▼
 Gemini   OpenAI   Anthropic  Groq    Ollama
 (cloud)  (cloud)   (cloud)  (cloud) (local)
```

### API Key Storage

Keys stored in `localStorage`:

- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `ANTHROPIC_API_KEY`
- `GROQ_API_KEY`

---

## State Management

### Zustand Stores

| Store | Purpose |
|-------|---------|
| `useAppStore` | UI state (sidebar, modals) |
| `useSettingsStore` | User preferences |
| `useSearchStore` | Search state |

### React Query

- **Entity queries:** `useEntity(type, id)`
- **List queries:** `useEntities(type, filters)`
- **Invalidation:** Via Command layer

### XState Machines

Located in `src/lib/machines/`:

- `projectStatusMachine` — planning → active → completed
- `taskStatusMachine` — todo → in_progress → done
- `goalStatusMachine` — not_started → working → achieved
- `purchaseStatusMachine` — wishlist → ordered → received
- `syncStatusMachine` — idle → syncing → synced

---

## Development Commands

```bash
# Start dev server
npm run dev

# Run tests
npm run test:run

# Lint
npm run lint

# Type check
npx tsc --noEmit

# Dead code check
npx knip

# Bundle analysis
npx vite-bundle-visualizer
```

---

## Hygiene Checkpoints

After each major phase, run:

1. ✅ `npm run lint` — 0 errors
2. ✅ `npm run test:run` — 100% pass
3. ✅ `npx tsc --noEmit` — No type errors
4. ✅ `npx knip` — Document dead code
5. ✅ Review TODO/FIXME comments

---

## See Also

- [Implementation Plan](/.gemini/antigravity/brain/.../implementation_plan.md)
- [V10 Master Plan](/.gemini/antigravity/brain/.../universal_architecture_master_plan_v10.md)
