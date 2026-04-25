# Mobile App — Technical Deep Dive

> React Native architecture, offline-first patterns, and mobile development

---

## Document Overview

**Series:** Mobile App Deep Dive
**Document:** 1 of 4
**Last Updated:** 2026-04-25
**Status:** ✅ Complete

**Related Documents:**
- [UX/UI Deep Dive](./MOBILE_APP_02_UX_UI_DEEP_DIVE.md) — Mobile design patterns
- [Sync Deep Dive](./MOBILE_APP_03_SYNC_DEEP_DIVE.md) — Data synchronization
- [Notifications Deep Dive](./MOBILE_APP_04_NOTIFICATIONS_DEEP_DIVE.md) — Push notifications

---

## Table of Contents

1. [Technology Stack Decision](#technology-stack-decision)
2. [App Architecture](#app-architecture)
3. [Offline-First Architecture](#offline-first-architecture)
4. [API Integration](#api-integration)
5. [Security](#security)
6. [Build & Deployment](#build--deployment)
7. [Performance Optimization](#performance-optimization)

---

## Technology Stack Decision

### React Native vs Native

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    MOBILE DEVELOPMENT APPROACH                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FACTORS TO CONSIDER                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Factor              │ React Native      │ Native (Swift/Kotlin)    │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  Development Speed   │ ★★★★★            │ ★★☆☆☆                    │   │
│  │  Code Reuse         │ ~95% shared       │ Separate codebases       │   │
│  │  Performance        │ Near-native       │ Native                   │   │
│  │  Team Skills        │ Web/JS devs       │ Mobile devs needed       │   │
│  │  Ecosystem          │ Large             │ Platform-specific        │   │
│  │  Time to Market     │ Faster            │ Slower                   │   │
│  │  Maintenance        │ Single codebase   │ Two codebases            │   │
│  │  Platform Features  │ May lag          │ First-party support      │   │
│  │  App Size           │ Slightly larger   │ Smaller                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  OUR CHOICE: REACT NATIVE                                                   │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Rationale:                                                         │   │
│  │  • Existing web team can develop mobile apps                       │   │
│  │  • Single codebase reduces maintenance burden                      │   │
│  │  • Performance is "good enough" for our use case                   │   │
│  │  • Hot reloading enables faster iteration                          │   │
│  │  • Large ecosystem with battle-tested libraries                    │   │
│  │  • OTA updates via Code Push for quick fixes                       │   │
│  │  • 95% code sharing between iOS and Android                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tech Stack Components

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MOBILE APP TECH STACK                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  FRAMEWORK & LANGUAGE                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  React Native 0.73+ (New Architecture enabled)                      │   │
│  │  TypeScript (strict mode)                                          │   │
│  │  Expo (for development tooling, managed workflow)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STATE MANAGEMENT                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Redux Toolkit (state)                                            │   │
│  │  RTK Query (server state)                                         │   │
│  │  Redux Persist (persistence)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NAVIGATION                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  React Navigation v6                                              │   │
│  │  • Stack Navigator (hierarchical)                                │   │
│  │  • Tab Navigator (bottom tabs)                                   │   │
│  │  • Modal Navigator (overlays)                                    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DATA & SYNCING                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Axios (HTTP client)                                               │   │
│  │  Redux Persist + IndexedDB (offline storage)                      │   │
│  │  React Query Background Sync                                       │   │
│  │  NetInfo (network awareness)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  UI COMPONENTS                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  React Native Paper (Material Design)                             │   │
│  │  React Native Elements (iOS components)                           │   │
│  │  NativeBase (cross-platform)                                      │   │
│  │  Custom component library (shared design tokens)                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NATIVE MODULES                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  React Native Maps (google maps integration)                       │   │
│  │  React Native Image Picker (photo upload)                         │   │
│  │  React Native Share (social sharing)                              │   │
│  │  React Native Haptic Feedback (vibrations)                        │   │
│  │  Custom modules for platform-specific features                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  DEVELOPMENT TOOLS                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Flipper (debugging)                                               │   │
│  │  Reactotron (Redux debugger)                                      │   │
│  │  CodePush (OTA updates)                                           │   │
│  │  Sentry (crash reporting)                                         │   │
│  │  Fastlane (build automation)                                      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## App Architecture

### Overall Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MOBILE APP ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         PRESENTATION LAYER                           │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌───────────┐  │    │
│  │  │  Screens    │  │ Components  │  │ Navigation  │  │ Themes   │  │    │
│  │  │             │  │             │  │             │  │           │  │    │
│  │  │ • Inbox     │  │ • TripCard  │  │ • Stack     │  │ • Light   │  │    │
│  │  │ • Trip      │  │ • Avatar    │  │ • Tab       │  │ • Dark    │  │    │
│  │  │ • Customer  │  │ • Status    │  │ • Modal     │  │           │  │    │
│  │  │ • Settings  │  │ • Timeline  │  │             │  │           │  │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └───────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         BUSINESS LOGIC LAYER                       │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │    │
│  │  │  Redux      │  │  Sagas      │  │  Selectors  │               │    │
│  │  │  Store      │  │             │  │             │               │    │
│  │  │             │  │ • API calls │  │ • Data     │               │    │
│  │  │ • Trips     │  │ • Sync      │  │   derived  │               │    │
│  │  │ • Customers │  │ • Push      │  │ • Filters  │               │    │
│  │  │ • User      │  │ • Nav       │  │             │               │    │
│  │  │ • Offline   │  │             │  │             │               │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                         DATA LAYER                                   │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │    │
│  │  │  API Client │  │  Storage    │  │  Sync       │               │    │
│  │  │             │  │             │  │  Engine     │               │    │
│  │  │ • Axios     │  │ • MMKV      │  │ • Conflict  │               │    │
│  │  │ • RTK Query │  │ • Async     │  │   resolution│               │    │
│  │  │ • Interceptors│   Storage   │  │ • Background│               │    │
│  │  │ • Retry     │  │ • Secure    │  │   sync      │               │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                  │                                          │
│                                  ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │                    PLATFORM & NATIVE LAYER                           │    │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐               │    │
│  │  │  iOS        │  │  Android    │  │  Shared     │               │    │
│  │  │  (Swift)    │  │  (Kotlin)   │  │  Modules    │               │    │
│  │  │             │  │             │  │             │               │    │
│  │  │ • Push      │  │ • Push      │  │ • Maps      │               │    │
│  │  │ • Biometrics│  │ • Biometrics│  │ • Camera    │               │    │
│  │  │ • Widgets   │  │ • Widgets   │  │ • File      │               │    │
│  │  └─────────────┘  └─────────────┘  └─────────────┘               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Directory Structure

```
src/
├── api/                    # API client and endpoints
│   ├── client.ts           # Axios instance with interceptors
│   ├── endpoints/          # API endpoint definitions
│   │   ├── trips.ts
│   │   ├── customers.ts
│   │   ├── messages.ts
│   │   └── auth.ts
│   └── middleware/         # Request/response middleware
│
├── components/             # Shared UI components
│   ├── common/            # Generic components
│   │   ├── Button.tsx
│   │   ├── Card.tsx
│   │   ├── Input.tsx
│   │   └── Avatar.tsx
│   ├── trip/              # Trip-specific components
│   │   ├── TripCard.tsx
│   │   ├── Timeline.tsx
│   │   └── StatusBadge.tsx
│   └── customer/          # Customer components
│       ├── CustomerCard.tsx
│       └── MessageList.tsx
│
├── navigation/             # Navigation configuration
│   ├── RootNavigator.tsx
│   ├── AuthNavigator.tsx
│   ├── MainNavigator.tsx
│   ├── linking.ts          # Deep linking config
│   └── types.ts           # Navigation types
│
├── redux/                 # State management
│   ├── store.ts           # Store configuration
│   ├── slices/            # Redux Toolkit slices
│   │   ├── tripsSlice.ts
│   │   ├── customersSlice.ts
│   │   ├── userSlice.ts
│   │   └── offlineSlice.ts
│   ├── sagas/             # Redux sagas
│   │   ├── tripsSaga.ts
│   │   ├── syncSaga.ts
│   │   └── pushSaga.ts
│   └── selectors/         # Memoized selectors
│
├── screens/               # Screen components
│   ├── auth/              # Authentication screens
│   │   ├── LoginScreen.tsx
│   │   └── OTPScreen.tsx
│   ├── inbox/             # Inbox screens
│   │   ├── InboxScreen.tsx
│   │   └── FiltersModal.tsx
│   ├── trips/             # Trip screens
│   │   ├── TripListScreen.tsx
│   │   ├── TripDetailScreen.tsx
│   │   └── TimelineScreen.tsx
│   ├── customers/         # Customer screens
│   │   ├── CustomerListScreen.tsx
│   │   └── CustomerDetailScreen.tsx
│   └── settings/          # Settings screens
│       ├── SettingsScreen.tsx
│       └── ProfileScreen.tsx
│
├── services/              # Business logic services
│   ├── sync/              # Sync service
│   │   ├── SyncEngine.ts
│   │   ├── ConflictResolver.ts
│   │   └── BackgroundSync.ts
│   ├── push/             # Push notification service
│   │   ├── PushNotification.ts
│   │   └── NotificationHandler.ts
│   ├── offline/          # Offline helpers
│   │   ├── OfflineQueue.ts
│   │   └── NetworkMonitor.ts
│   └── storage/          # Storage abstraction
│       ├── SecureStorage.ts
│       ├── KeyValueStorage.ts
│       └── ObjectStorage.ts
│
├── hooks/                 # Custom React hooks
│   ├── useAuth.ts
│   ├── useOffline.ts
│   ├── useSync.ts
│   └── usePush.ts
│
├── utils/                 # Utility functions
│   ├── date.ts
│   ├── formatting.ts
│   ├── validation.ts
│   └── constants.ts
│
├── types/                 # TypeScript types
│   ├── api.ts
│   ├── models.ts
│   └── navigation.ts
│
├── theme/                 # Theme configuration
│   ├── colors.ts
│   ├── typography.ts
│   ├── spacing.ts
│   └── index.ts
│
└── assets/                # Static assets
    ├── images/
    ├── fonts/
    └── icons/
```

### Redux Store Configuration

```typescript
/**
 * Redux store configuration with React Native
 */
import { configureStore, combineReducers } from '@reduxjs/toolkit';
import { setupListeners } from '@reduxjs/toolkit/query';
import { persistStore, persistReducer } from 'redux-persist';
import AsyncStorage from '@react-native-async-storage/async-storage';
import Flipper from 'rn-flipper-async-storage';

// Slices
import tripsReducer from './slices/tripsSlice';
import customersReducer from './slices/customersSlice';
import userReducer from './slices/userSlice';
import offlineReducer from './slices/offlineSlice';
import syncReducer from './slices/syncSlice';

// API
import { api } from './api/client';

// Root reducer
const rootReducer = combineReducers({
  [api.reducerPath]: api.reducer,
  trips: tripsReducer,
  customers: customersReducer,
  user: userReducer,
  offline: offlineReducer,
  sync: syncReducer
});

// Persist configuration
const persistConfig = {
  key: 'root',
  storage: AsyncStorage,
  whitelist: ['user', 'offline', 'sync'], // Only persist these
  blacklist: [api.reducerPath] // Don't persist API cache
};

const persistedReducer = persistReducer(persistConfig, rootReducer);

// Configure store
export const store = configureStore({
  reducer: persistedReducer,
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST', 'persist/REHYDRATE']
      },
      thunk: {
        extraArgument: { api }
      }
    }).concat(api.middleware),
  devTools: __DEV__
});

// Enable refetchOnFocus/refetchOnReconnect for RTK Query
setupListeners(store.dispatch);

// Persistor
export const persistor = persistStore(store);

// Infer types
export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;
```

---

## Offline-First Architecture

### Offline Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      OFFLINE-FIRST DATA FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  READ REQUEST                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Check local cache first (IndexedDB/MMKV)                       │   │
│  │  2. If data exists and fresh → Return immediately                   │   │
│  │  3. If missing/stale → Fetch from API in background                │   │
│  │  4. Update cache when API response arrives                          │   │
│  │  5. Re-render with fresh data                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  WRITE REQUEST                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. Check network status                                            │   │
│  │  2. If ONLINE → Send to API immediately                            │   │
│  │  3. If OFFLINE → Queue operation                                    │   │
│  │  4. Update local state optimistically                               │   │
│  │  5. When back online → Process queue in order                       │   │
│  │  6. Handle conflicts if server data changed                          │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SYNC STRATEGY                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Background Sync:                                                   │   │
│  │  • Every 5 minutes when on WiFi                                    │   │
│  │  • Every 15 minutes on cellular                                    │   │
│  │  • On app foreground                                               │   │
│  │  • Manual refresh trigger                                          │   │
│  │                                                                     │   │
│  │  Sync Priority:                                                     │   │
│  │  1. Pending writes (offline queue)                                 │   │
│  │  2. User-initiated refreshes                                       │   │
│  │  3. Background incremental sync                                     │   │
│  │  4. Full sync (rare, only if needed)                                │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Offline Queue Implementation

```typescript
/**
 * Offline operation queue
 */
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import NetInfo from '@react-native-community/netinfo';
import { offlineQueueApi } from '../api/client';

interface OfflineOperation {
  id: string;
  type: 'CREATE' | 'UPDATE' | 'DELETE';
  endpoint: string;
  payload: unknown;
  timestamp: number;
  retries: number;
  maxRetries: number;
}

interface OfflineQueueState {
  operations: OfflineOperation[];
  isOnline: boolean;
  isProcessing: boolean;
  lastSyncAt?: number;
}

const initialState: OfflineQueueState = {
  operations: [],
  isOnline: true,
  isProcessing: false
};

export const addToQueue = createAsyncThunk(
  'offlineQueue/add',
  async (operation: Omit<OfflineOperation, 'id' | 'timestamp' | 'retries'>) => {
    return {
      ...operation,
      id: `op_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
      timestamp: Date.now(),
      retries: 0
    };
  }
);

export const processQueue = createAsyncThunk(
  'offlineQueue/process',
  async (_, { getState, dispatch }) => {
    const state = getState() as { offlineQueue: OfflineQueueState };

    if (!state.offlineQueue.isOnline || state.offlineQueue.isProcessing) {
      return;
    }

    const operation = state.offlineQueue.operations[0];
    if (!operation) return;

    try {
      // Process the operation
      switch (operation.type) {
        case 'CREATE':
          await offlineQueueApi.create(operation.endpoint, operation.payload);
          break;
        case 'UPDATE':
          await offlineQueueApi.update(operation.endpoint, operation.payload);
          break;
        case 'DELETE':
          await offlineQueueApi.delete(operation.endpoint);
          break;
      }

      // Remove from queue on success
      dispatch(removeFromQueue(operation.id));

    } catch (error) {
      // Increment retry count
      dispatch(incrementRetry(operation.id));

      // Remove if max retries exceeded
      const updatedOp = { ...operation, retries: operation.retries + 1 };
      if (updatedOp.retries >= updatedOp.maxRetries) {
        dispatch(removeFromQueue(operation.id));
        dispatch(markAsFailed(operation.id, error));
      }
    }
  }
);

const offlineQueueSlice = createSlice({
  name: 'offlineQueue',
  initialState,
  reducers: {
    setOnlineStatus: (state, action) => {
      state.isOnline = action.payload;
    },
    removeFromQueue: (state, action) => {
      state.operations = state.operations.filter(op => op.id !== action.payload);
    },
    incrementRetry: (state, action) => {
      const op = state.operations.find(o => o.id === action.payload);
      if (op) op.retries++;
    },
    markAsFailed: (state, action) => {
      // Move to failed operations list
    }
  },
  extraReducers: (builder) => {
    builder
      .addCase(addToQueue.fulfilled, (state, action) => {
        state.operations.push(action.payload);
      })
      .addCase(processQueue.pending, (state) => {
        state.isProcessing = true;
      })
      .addCase(processQueue.fulfilled, (state) => {
        state.isProcessing = false;
        state.lastSyncAt = Date.now();
      });
  }
});

// Monitor network status
export const initNetworkMonitoring = () => (dispatch: AppDispatch) => {
  // Subscribe to network status changes
  const unsubscribe = NetInfo.addEventListener(state => {
    const isOnline = state.isConnected ?? false;
    dispatch(setOnlineStatus(isOnline));

    // Process queue when coming back online
    if (isOnline) {
      dispatch(processQueue());
    }
  });

  return unsubscribe;
};

export const { setOnlineStatus, removeFromQueue, incrementRetry, markAsFailed } = offlineQueueSlice.actions;
export default offlineQueueSlice.reducer;
```

### Conflict Resolution

```typescript
/**
 * Conflict resolution for offline sync
 */
enum ConflictStrategy {
  /**
   * Server wins - discard local changes
   */
  SERVER_WINS = 'SERVER_WINS',

  /**
   * Client wins - overwrite server
   */
  CLIENT_WINS = 'CLIENT_WINS',

  /**
   * Last write wins - compare timestamps
   */
  LAST_WRITE_WINS = 'LAST_WRITE_WINS',

  /**
   * Manual - require user to resolve
   */
  MANUAL = 'MANUAL'
}

interface Conflict<T> {
  local: T;
  remote: T;
  field: string;
  strategy?: ConflictStrategy;
}

/**
 * Resolve conflicts between local and server data
 */
class ConflictResolver {
  /**
   * Resolve conflict for a single entity
   */
  resolveEntity<T extends { updatedAt: string }>(
    local: T,
    remote: T,
    strategy: ConflictStrategy = ConflictStrategy.LAST_WRITE_WINS
  ): T {
    switch (strategy) {
      case ConflictStrategy.SERVER_WINS:
        return remote;

      case ConflictStrategy.CLIENT_WINS:
        return local;

      case ConflictStrategy.LAST_WRITE_WINS:
        return local.updatedAt > remote.updatedAt ? local : remote;

      case ConflictStrategy.MANUAL:
        // Should be handled by UI
        throw new Error('Manual conflict resolution required');

      default:
        return remote;
    }
  }

  /**
   * Merge entities with field-level conflicts
   */
  mergeWithConflicts<T extends { updatedAt: string }>(
    local: T,
    remote: T,
    conflicts: Conflict<T>[],
    strategies: Record<string, ConflictStrategy>
  ): T {
    const merged: T = { ...remote };

    for (const conflict of conflicts) {
      const strategy = strategies[conflict.field] || ConflictStrategy.LAST_WRITE_WINS;

      merged[conflict.field as keyof T] = this.resolveEntity(
        { ...remote, [conflict.field]: local[conflict.field as keyof T] },
        { ...remote, [conflict.field]: remote[conflict.field as keyof T] },
        strategy
      )[conflict.field as keyof T];
    }

    return merged;
  }

  /**
   * Detect conflicts between local and remote data
   */
  detectConflicts<T extends { id: string; updatedAt: string }>(
    local: T,
    remote: T,
    writableFields: (keyof T)[]
  ): Conflict<T>[] {
    const conflicts: Conflict<T>[] = [];

    for (const field of writableFields) {
      const localValue = local[field];
      const remoteValue = remote[field];

      if (JSON.stringify(localValue) !== JSON.stringify(remoteValue)) {
        conflicts.push({
          local: { [field]: localValue } as T,
          remote: { [field]: remoteValue } as T,
          field: field as string
        });
      }
    }

    return conflicts;
  }
}

export { ConflictResolver, ConflictStrategy };
```

---

## API Integration

### API Client Configuration

```typescript
/**
 * Axios client for React Native with interceptors
 */
import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { getBaseUrl, getApiKey } from '../config/env';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: getBaseUrl(),
  timeout: 15000, // 15 seconds for mobile
  headers: {
    'Content-Type': 'application/json',
    'X-Client-Platform': 'react-native',
    'X-Client-Version': __APP_VERSION__
  }
});

// Request interceptor - add auth token
apiClient.interceptors.request.use(
  async (config: InternalAxiosRequestConfig) => {
    const token = await AsyncStorage.getItem('auth_token');

    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Add request ID for tracking
    config.headers['X-Request-ID'] = generateRequestId();

    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Handle 401 - refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = await AsyncStorage.getItem('refresh_token');

        if (refreshToken) {
          const response = await axios.post(`${getBaseUrl()}/auth/refresh`, {
            refreshToken
          });

          const { token } = response.data;

          await AsyncStorage.setItem('auth_token', token);

          // Update authorization header
          originalRequest.headers.Authorization = `Bearer ${token}`;

          // Retry original request
          return apiClient(originalRequest);
        }
      } catch (refreshError) {
        // Refresh failed - logout user
        await AsyncStorage.multiRemove(['auth_token', 'refresh_token']);

        // Navigate to login
        // TODO: Navigate to login screen
      }
    }

    // Handle network errors
    if (!error.response) {
      // Network error - likely offline
      // Queue request if it's a mutation
      if (originalRequest.method?.toLowerCase() !== 'get') {
        // Add to offline queue
      }
    }

    return Promise.reject(error);
  }
);

// Retry interceptor for failed requests
apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as InternalAxiosRequestConfig & { _retry?: number; _retryCount?: number };

    // Retry on 5xx errors or network errors
    const shouldRetry =
      !error.response ||
      (error.response.status >= 500 && error.response.status < 600);

    if (shouldRetry && (!config._retryCount || config._retryCount < 3)) {
      config._retryCount = config._retryCount || 0;
      config._retryCount++;

      // Exponential backoff
      const delay = Math.pow(2, config._retryCount) * 1000;

      await new Promise(resolve => setTimeout(resolve, delay));

      return apiClient(config);
    }

    return Promise.reject(error);
  }
);

function generateRequestId(): string {
  return `${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

export default apiClient;
```

### RTK Query Setup

```typescript
/**
 * RTK Query API configuration for React Native
 */
import { createApi, fetchBaseQuery } from '@reduxjs/toolkit/query/react';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Base query with offline support
const baseQuery = fetchBaseQuery({
  baseUrl: getBaseUrl(),
  prepareHeaders: async (headers) => {
    const token = await AsyncStorage.getItem('auth_token');

    if (token) {
      headers.set('authorization', `Bearer ${token}`);
    }

    return headers;
  },
});

// Create API slice
export const api = createApi({
  reducerPath: 'api',
  baseQuery,
  tagTypes: ['Trip', 'Customer', 'Message', 'User'],
  endpoints: (builder) => ({
    // Trips
    getTrips: builder.query<Trip[], TripFilters>({
      query: (filters) => ({
        url: '/trips',
        params: filters
      }),
      providesTags: (result) =>
        result
          ? [...result.map(({ id }) => ({ type: 'Trip' as const, id })), 'Trip']
          : ['Trip']
    }),
    getTrip: builder.query<Trip, string>({
      query: (id) => `/trips/${id}`,
      providesTags: (result, error, id) => [{ type: 'Trip', id }]
    }),
    updateTrip: builder.mutation<Trip, Partial<Trip> & { id: string }>({
      query: ({ id, ...patch }) => ({
        url: `/trips/${id}`,
        method: 'PATCH',
        body: patch
      }),
      invalidatesTags: (result, error, { id }) => [{ type: 'Trip', id }]
    }),

    // Customers
    getCustomers: builder.query<Customer[], void>({
      query: () => '/customers',
      providesTags: ['Customer']
    }),

    // Messages
    getMessages: builder.query<Message[], string>({
      query: (tripId) => `/trips/${tripId}/messages`,
      providesTags: (result, error, tripId) => [
        { type: 'Message', id: tripId },
        'Message'
      ]
    }),
    sendMessage: builder.mutation<Message, Omit<Message, 'id'>>({
      query: (message) => ({
        url: '/messages',
        method: 'POST',
        body: message
      }),
      invalidatesTags: (result, error, { tripId }) => [
        { type: 'Message', id: tripId }
      ],
      async onQueryStarted({ tripId }, { dispatch, queryFulfilled }) {
        // Optimistic update
        const patchResult = dispatch(
          api.util.updateQueryData('getMessages', tripId, (draft) => {
            draft.push({ ...tripId, tempId: true } as Message);
          })
        );

        try {
          await queryFulfilled;
        } catch {
          patchResult.undo();
        }
      }
    })
  })
});

export const {
  useGetTripsQuery,
  useGetTripQuery,
  useUpdateTripMutation,
  useGetCustomersQuery,
  useGetMessagesQuery,
  useSendMessageMutation
} = api;
```

---

## Security

### Code Signing & Proguard

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MOBILE APP SECURITY                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  IOS CODE SIGNING                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Development:                                                       │   │
│  │  • Apple Developer account required                                 │   │
│  │  • Development certificate + Provisioning profile                   │   │
│  │  • Team ID for app identification                                    │   │
│  │                                                                     │   │
│  │  Distribution:                                                      │   │
│  │  • Distribution certificate                                         │   │
│  │  • App Store provisioning profile                                   │   │
│  │  • Bundle ID (com.agency.app)                                       │   │
│  │                                                                     │   │
│  │  Build Process:                                                     │   │
│  │  • Xcode: Archive → Export → Upload to App Store                   │   │
│  │  • EAS (Expo Application Services) for managed workflow             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ANDROID CODE SIGNING & OBFUSCATION                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Debug:                                                              │   │
│  │  • Debug certificate (auto-generated)                               │   │
│  │  • Debug build type                                                 │   │
│  │                                                                     │   │
│  │  Release:                                                           │   │
│  │  • Keystore file (.jks) with passwords                              │   │
│  │  • Release signing config                                          │   │
│  │  • ProGuard/R8 obfuscation enabled                                  │   │
│  │                                                                     │   │
│  │  ProGuard Rules:                                                    │   │
│  │  • Keep React Native classes                                       │   │
│  │  • Keep our API models                                              │   │
│  │  • Keep第三方库 classes                                      │   │
│  │  • Obfuscate business logic                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  RUNTIME SECURITY                                                           │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  • SSL Pinning (prevent MITM)                                      │   │
│  │  • Root/jailbreak detection                                        │   │
│  │  • Screen capture prevention (for sensitive data)                   │   │
│  │  • Certificate pinning for API calls                                │   │
│  │  • Secure storage (Keychain/Keystore)                               │   │
│  │  • Biometric authentication (Face ID, Touch ID, Fingerprint)         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Secure Storage

```typescript
/**
 * Secure storage wrapper for React Native
 */
import { Platform } from 'react-native';
import Keychain from 'react-native-keychain';
import EncryptedStorage from 'react-native-encrypted-storage';

/**
 * Securely store sensitive data
 */
class SecureStorage {
  private static instance: SecureStorage;

  private constructor() {}

  static getInstance(): SecureStorage {
    if (!SecureStorage.instance) {
      SecureStorage.instance = new SecureStorage();
    }
    return SecureStorage.instance;
  }

  /**
   * Store auth tokens securely
   */
  async setAuthTokens(tokens: { accessToken: string; refreshToken: string }): Promise<void> {
    if (Platform.OS === 'ios') {
      // Use Keychain on iOS
      await Keychain.setGenericPassword(
        'auth_tokens',
        JSON.stringify(tokens),
        {
          service: 'com.agency.app.auth',
          accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_CURRENT_SET
        }
      );
    } else {
      // Use EncryptedStorage on Android
      await EncryptedStorage.setItem('auth_tokens', JSON.stringify(tokens));
    }
  }

  /**
   * Get auth tokens
   */
  async getAuthTokens(): Promise<{ accessToken: string; refreshToken: string } | null> {
    try {
      let data: string;

      if (Platform.OS === 'ios') {
        const credentials = await Keychain.getGenericPassword('com.agency.app.auth');
        data = credentials.password;
      } else {
        data = await EncryptedStorage.getItem('auth_tokens');
      }

      return data ? JSON.parse(data) : null;
    } catch {
      return null;
    }
  }

  /**
   * Clear auth tokens (logout)
   */
  async clearAuthTokens(): Promise<void> {
    if (Platform.OS === 'ios') {
      await Keychain.resetGenericPassword({ service: 'com.agency.app.auth' });
    } else {
      await EncryptedStorage.removeItem('auth_tokens');
    }
  }

  /**
   * Store user credentials (for biometric login)
   */
  async setUserCredentials(username: string, password: string): Promise<void> {
    await Keychain.setInternetCredentials(
      'com.agency.app',
      username,
      password,
      {
        accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_CURRENT_SET
      }
    );
  }

  /**
   * Get user credentials
   */
  async getUserCredentials(): Promise<{ username: string; password: string } | null> {
    try {
      const credentials = await Keychain.getInternetCredentials('com.agency.app');
      if (credentials.username && credentials.password) {
        return {
          username: credentials.username,
          password: credentials.password
        };
      }
      return null;
    } catch {
      return null;
    }
  }

  /**
   * Clear user credentials
   */
  async clearUserCredentials(): Promise<void> {
    await Keychain.resetInternetCredentials('com.agency.app');
  }
}

export default SecureStorage;
```

### Biometric Authentication

```typescript
/**
 * Biometric authentication service
 */
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';

class BiometricAuthService {
  private rnBiometrics = ReactNativeBiometrics;

  /**
   * Check if biometric authentication is available
   */
  async isAvailable(): Promise<boolean> {
    try {
      const { available } = await this.rnBiometrics.isSensorAvailable();
      return available;
    } catch {
      return false;
    }
  }

  /**
   * Get biometry type (Face ID, Touch ID, Fingerprint)
   */
  async getBiometryType(): Promise<string | null> {
    try {
      const { available, biometryType } = await this.rnBiometrics.isSensorAvailable();

      if (!available) return null;

      switch (biometryType) {
        case BiometryTypes.TOUCH_ID:
          return 'Touch ID';
        case BiometryTypes.FACE_ID:
          return 'Face ID';
        case BiometryTypes.BIOMETRICS:
          return 'Fingerprint';
        default:
          return 'Biometric';
      }
    } catch {
      return null;
    }
  }

  /**
   * Prompt user for biometric authentication
   */
  async authenticate(promptMessage?: string): Promise<boolean> {
    try {
      const { success } = await this.rnBiometrics.prompt({
        promptMessage: promptMessage || 'Authenticate to continue',
        cancelButtonText: 'Cancel'
      });

      return success;
    } catch (error) {
      // User cancelled or error
      return false;
    }
  }

  /**
   * Create biometric keys for secure operations
   */
  async createKeys(): Promise<void> {
    await this.rnBiometrics.createKeys('com.agency.app.biometric');
  }

  /**
   * Delete biometric keys
   */
  async deleteKeys(): Promise<void> {
    await this.rnBiometrics.deleteKeys('com.agency.app.biometric');
  }

  /**
   * Sign data with biometric key
   */
  async biometricKeysExist(): Promise<boolean> {
    const { keysExist } = await this.rnBiometrics.biometricKeysExist();
    return keysExist;
  }
}

export default BiometricAuthService;
```

---

## Build & Deployment

### Build Configuration

```typescript
/**
 * React Native build configuration
 */
{
  "name": "AgencyApp",
  "version": "1.0.0",

  // React Native configuration
  "react-native": {
    "android": {
      "package": "com.agency.app",
      "permissions": [
        "INTERNET",
        "ACCESS_NETWORK_STATE",
        "VIBRATE",
        "RECEIVE_BOOT_COMPLETED",
        "CAMERA",
        "READ_EXTERNAL_STORAGE",
        "WRITE_EXTERNAL_STORAGE"
      ]
    },
    "ios": {
      "bundleIdentifier": "com.agency.app",
      "supportsTablet": false,
      "usesAppleSignIn": true
    }
  },

  // Build variants
  "builds": {
    "android": {
      "debug": {
        "bundleId": "com.agency.app.debug",
        "applicationId": "com.agency.app.debug",
        "signingConfig": "debug"
      },
      "release": {
        "bundleId": "com.agency.app",
        "applicationId": "com.agency.app",
        "signingConfig": "release",
        "minifyEnabled": true,
        "shrinkResources": true,
        "proguardEnabled": true
      }
    },
    "ios": {
      "debug": {
        "bundleId": "com.agency.app.debug",
        "provisioningStyle": "automatic"
      },
      "release": {
        "bundleId": "com.agency.app",
        "provisioningStyle": "manual",
        "bitcode": false
      }
    }
  }
}
```

### Fastlane Configuration

```ruby
# Fastfile for automated builds

default_platform(:android)

platform :android do
  desc "Build debug APK"
  lane :debug do
    gradle(
      task: "assemble",
      build_type: "Debug",
      properties: {
        "android.injected.signing.store.file" => ENV["ANDROID_KEYSTORE_PATH"],
        "android.injected.signing.store.password" => ENV["ANDROID_KEYSTORE_PASSWORD"],
        "android.injected.signing.key.alias" => ENV["ANDROID_KEY_ALIAS"],
        "android.injected.signing.key.password" => ENV["ANDROID_KEY_PASSWORD"]
      }
    )
  end

  desc "Build release APK"
  lane :release do
    gradle(
      task: "assemble",
      build_type: "Release",
      properties: {
        "android.injected.signing.store.file" => ENV["ANDROID_KEYSTORE_PATH"],
        "android.injected.signing.store.password" => ENV["ANDROID_KEYSTORE_PASSWORD"],
        "android.injected.signing.key.alias" => ENV["ANDROID_KEY_ALIAS"],
        "android.injected.signing.key.password" => ENV["ANDROID_KEY_PASSWORD"]
      }
    )
  end

  desc "Deploy to Play Store (internal track)"
  lane :deploy_internal do
    upload_to_play_store(
      track: "internal",
      aab: "../app/build/outputs/bundle/release/app-release.aab",
      skip_upload_screenshots: true,
      skip_upload_images: true
    )
  end

  desc "Deploy to Play Store (production)"
  lane :deploy_production do
    upload_to_play_store(
      track: "production",
      aab: "../app/build/outputs/bundle/release/app-release.aab",
      skip_upload_screenshots: true,
      skip_upload_images: true,
      release_status: "completed"
    )
  end
end

platform :ios do
  desc "Build debug IPA"
  lane :debug do
    build_app(
      workspace: "AgencyApp.xcworkspace",
      scheme: "AgencyApp",
      configuration: "Debug",
      export_method: "development"
    )
  end

  desc "Build release IPA"
  lane :release do
    build_app(
      workspace: "AgencyApp.xcworkspace",
      scheme: "AgencyApp",
      configuration: "Release",
      export_method: "app-store",
      export_options: {
        provisioningProfiles: {
          "com.agency.app" => ENV["APP_STORE_PROVISIONING_PROFILE"]
        }
      }
    )
  end

  desc "Deploy to TestFlight"
  lane :beta do
    build_app(
      workspace: "AgencyApp.xcworkspace",
      scheme: "AgencyApp",
      export_method: "app-store"
    )

    upload_to_testflight(
      skip_waiting_for_build_processing: true
    )
  end

  desc "Deploy to App Store"
  lane :deploy_production do
    build_app(
      workspace: "AgencyApp.xcworkspace",
      scheme: "AgencyApp",
      export_method: "app-store"
    )

    upload_to_app_store(
      skip_metadata: true,
      skip_screenshots: true,
      submit_for_review: false
    )
  end
end
```

---

## Performance Optimization

### Performance Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      PERFORMANCE OPTIMIZATION CHECKLIST                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  RENDER PERFORMANCE                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Use React.memo for expensive components                         │   │
│  │  ☐ Use useMemo for expensive computations                            │   │
│  │  ☐ Use useCallback for stable function references                    │   │
│  │  ☐ FlatList/SectionList instead of ScrollView for long lists        │   │
│  │  �3 Remove console.logs in production                                │   │
│  │  ☐ Optimize images (webp, proper sizing)                            │   │
│  │  ☐ Use lazy loading for images and components                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  BUNDLE SIZE                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Tree shaking for unused code                                     │   │
│  │  ☐ Code splitting (lazy loading routes)                             │   │
│  │  �3 Hermes for bundle analysis                                       │   │
│  │  ☐ Remove unused translations                                      │   │
│  │  ☐ Optimize native modules                                          │   │
│  │  ☐ Use ProGuard/R8 (Android)                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NETWORK PERFORMANCE                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Request batching                                                │   │
│  │  ☐ Response caching                                                 │   │
│  │  ☐ Image optimization and caching                                   │   │
│  │  ☐ Compression (gzip/brotli)                                       │   │
│  │  ☐ Pagination for large lists                                       │   │
│  │  ☐ Offline mode support                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STARTUP PERFORMANCE                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Lazy load routes and components                                  │   │
│  │  ☐ Async initialization for non-critical services                   │   │
│  │  ☐ Defer expensive operations                                      │   │
│  │  ☐ Use RAM bundles for instant start                               │   │
│  │  ☐ Optimize JavaScript execution                                    │   │
│  │  ☐ Reduce native module initialization time                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Performance Monitoring Hook

```typescript
/**
 * Performance monitoring hook
 */
import { useEffect, useRef } from 'react';
import { Performance } from 'react-native-performance';

interface PerformanceMetrics {
  renderTime: number;
  componentMountTime: number;
  fps: number;
  memory: number;
}

export function usePerformanceMonitoring(componentName: string) {
  const mountTime = useRef(Date.now());
  const renderStartTime = useRef(Date.now());

  useEffect(() => {
    const renderTime = Date.now() - renderStartTime.current;
    const mountTimeTotal = Date.now - mountTime.current;

    // Log performance metrics
    if (__DEV__) {
      console.log(`[Performance] ${componentName}:`, {
        renderTime: `${renderTime}ms`,
        mountTime: `${mountTimeTotal}ms`
      });
    }

    // Send to analytics in production
    if (!__DEV__) {
      Performance.mark(`${componentName}_mount`, {
        value: mountTimeTotal
      });
    }

    // Monitor FPS
    const fpsSubscription = Performance.observe('fps', (metrics) => {
      if (metrics.fps < 30) {
        // Log low FPS
        console.warn(`[Performance] ${componentName} low FPS:`, metrics.fps);
      }
    });

    return () => {
      fpsSubscription.unsubscribe();
    };
  }, [componentName]);

  return {
    markRenderStart: () => {
      renderStartTime.current = Date.now();
    },
    getRenderTime: () => Date.now() - renderStartTime.current
  };
}
```

---

## Summary

This document covers the technical architecture of the mobile app:

1. **Technology Stack Decision** — React Native vs native, tech stack components
2. **App Architecture** — Layered architecture, directory structure, Redux setup
3. **Offline-First Architecture** — Data flow, offline queue, conflict resolution
4. **API Integration** — Axios client, RTK Query, network handling
5. **Security** — Code signing, secure storage, biometric auth
6. **Build & Deployment** — Build configuration, Fastlane automation
7. **Performance Optimization** — Checklist, monitoring hook

**Key Takeaways:**

- React Native enables 95% code sharing between iOS and Android
- Offline-first architecture is essential for travel agents on the go
- Redux Toolkit + RTK Query provides robust state management
- Secure storage (Keychain/EncryptedStorage) for sensitive data
- Fastlane automates build and deployment
- Performance monitoring ensures smooth UX

**Related Documents:**
- [UX/UI Deep Dive](./MOBILE_APP_02_UX_UI_DEEP_DIVE.md) — Mobile design patterns
- [Sync Deep Dive](./MOBILE_APP_03_SYNC_DEEP_DIVE.md) — Data synchronization
