# Mobile App — Notifications Deep Dive

> Push notifications, in-app messaging, and engagement strategies

---

## Document Overview

**Series:** Mobile App | **Document:** 4 of 4 | **Focus:** Notifications

**Related Documents:**
- [01: Technical Deep Dive](./MOBILE_APP_01_TECHNICAL_DEEP_DIVE.md) — Architecture overview
- [02: UX/UI Deep Dive](./MOBILE_APP_02_UX_UI_DEEP_DIVE.md) — Mobile design patterns
- [03: Sync Deep Dive](./MOBILE_APP_03_SYNC_DEEP_DIVE.md) — Data synchronization

---

## Table of Contents

1. [Push Notification Architecture](#1-push-notification-architecture)
2. [Notification Types & Payloads](#2-notification-types--payloads)
3. [In-App Notification Center](#3-in-app-notification-center)
4. [Notification Preferences](#4-notification-preferences)
5. [Deep Linking](#5-deep-linking)
6. [Analytics & Engagement](#6-analytics--engagement)
7. [Implementation Patterns](#7-implementation-patterns)
8. [Testing & Compliance](#8-testing--compliance)

---

## 1. Push Notification Architecture

### 1.1 Platform Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    PUSH NOTIFICATION FLOW                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐             │
│  │   SERVER    │      │   FCM/APNs  │      │   DEVICE    │             │
│  │             │      │   SERVICE   │      │             │             │
│  │  ┌───────┐  │      │  ┌───────┐  │      │  ┌───────┐  │             │
│  │  │  API  │──┼──────┼──│ TOKEN │──┼──────┼──│  OS   │  │             │
│  │  │       │  │      │  │ REG   │  │      │  │       │  │             │
│  │  └───────┘  │      │  └───────┘  │      │  └───────┘  │             │
│  │      │      │      │      │      │      │      │      │             │
│  │  ┌───▼────┐  │      │  ┌───▼────┐  │      │  ┌───▼────┐             │
│  │  │  PUSH  │  │      │  │ ROUTE  │  │      │  │  APP   │             │
│  │  │ MGR   │──┼──────┼──│ & DEL. │──┼──────┼──│       │             │
│  │  └───────┘  │      │  └───────┘  │      │  └───────┘             │
│  └─────────────┘      └─────────────┘      └─────────────────────────│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  FCM (Firebase Cloud Messaging) — Android & Cross-Platform            │
│  APNs (Apple Push Notification Service) — iOS                          │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 1.2 Token Registration

```typescript
import { getMessaging, getToken } from '@react-native-firebase/messaging';
import PushNotificationIOS from '@react-native-community/push-notification-ios';

// FCM Token Registration (Android)
async function registerFCMToken(): Promise<string | null> {
  try {
    const messaging = getMessaging();
    const authStatus = await messaging.requestPermission();

    const enabled =
      authStatus === messaging.AuthorizationStatus.AUTHORIZED ||
      authStatus === messaging.AuthorizationStatus.PROVISIONAL;

    if (!enabled) {
      console.log('FCM permission not granted');
      return null;
    }

    const token = await getToken(messaging);
    if (token) {
      // Send token to backend
      await api.post('/devices/register', {
        token,
        platform: Platform.OS,
        appVersion: APP_VERSION,
      });
      return token;
    }
  } catch (error) {
    console.error('FCM token registration failed:', error);
  }
  return null;
}

// APNs Token Registration (iOS)
function registerAPNSToken(): void {
  PushNotificationIOS.addEventListener('register', token => {
    // Send token to backend
    api.post('/devices/register', {
      token,
      platform: 'ios',
      appVersion: APP_VERSION,
    });
  });

  PushNotificationIOS.requestPermissions();
}

// Token refresh handler
useEffect(() => {
  const unsubscribe = getMessaging().onTokenRefresh(async (newToken) => {
    await api.post('/devices/refresh-token', {
      oldToken: await getStoredToken(),
      newToken,
    });
  });

  return unsubscribe;
}, []);
```

### 1.3 Permission Handling

```typescript
// Permission request strategy
enum PermissionStatus {
  GRANTED = 'granted',
  DENIED = 'denied',
  NOT_DETERMINED = 'not_determined',
  PROVISIONAL = 'provisional', // iOS only
}

class NotificationPermissionManager {
  async requestPermission(showRationale?: boolean): Promise<PermissionStatus> {
    const currentStatus = await this.checkPermission();

    if (currentStatus === PermissionStatus.GRANTED) {
      return PermissionStatus.GRANTED;
    }

    if (currentStatus === PermissionStatus.DENIED) {
      if (showRationale) {
        // Show in-app explanation with settings deep link
        this.showRationaleDialog();
      }
      return PermissionStatus.DENIED;
    }

    // Request permission
    if (Platform.OS === 'ios') {
      return this.requestIOSPermission();
    }
    return this.requestAndroidPermission();
  }

  private async requestIOSPermission(): Promise<PermissionStatus> {
    // iOS: Try provisional first (non-interrupting notifications)
    const provisional = await PushNotificationIOS.requestPermissions({
      alert: true,
      badge: true,
      sound: false, // Provisional: no sound initially
    });

    if (provisional === 'provisional') {
      // Schedule prompt for full permission later
      this.scheduleFullPermissionPrompt();
      return PermissionStatus.PROVISIONAL;
    }

    return provisional === 'authorized'
      ? PermissionStatus.GRANTED
      : PermissionStatus.DENIED;
  }

  private async requestAndroidPermission(): Promise<PermissionStatus> {
    const granted = await PermissionsAndroid.request(
      PermissionsAndroid.PERMISSIONS.POST_NOTIFICATIONS
    );
    return granted === PermissionsAndroid.RESULTS.GRANTED
      ? PermissionStatus.GRANTED
      : PermissionStatus.DENIED;
  }

  private showRationaleDialog(): void {
    Alert.alert(
      'Enable Notifications',
      'Stay updated on trip changes and customer messages. Open Settings to enable notifications.',
      [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Open Settings', onPress: () => Linking.openSettings() },
      ]
    );
  }
}
```

---

## 2. Notification Types & Payloads

### 2.1 Notification Taxonomy

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    NOTIFICATION TYPE TAXONOMY                           │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  CRITICAL (Immediate delivery, sound, badge)                            │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ • Payment received/failure                                       │   │
│  │ • Booking confirmation                                           │   │
│  │ • Urgent customer message (within SLA)                           │   │
│  │ • Trip cancellation                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  IMPORTANT (Standard delivery, sound)                                   │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ • New trip assignment                                            │   │
│  │ • Customer reply                                                 │   │
│  │ • Quote request                                                  │   │
│  │ • Document uploaded                                              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  INFORMATIONAL (Quiet delivery, no sound)                               │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ • Trip status update                                             │   │
│  │ • Price drop alert                                               │   │
│  │ • Daily summary                                                  │   │
│  │ • Agency announcement                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
│  BACKGROUND (Silent, data-only)                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │ • Sync trigger                                                   │   │
│  │ • Configuration update                                           │   │
│  │ • Analytics data sync                                            │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 Payload Structure

```typescript
// Standard notification payload
interface NotificationPayload {
  // Standard fields
  title: string;
  body: string;
  sound?: 'default' | 'critical' | 'custom';
  badge?: number;

  // Custom data (passed to app on tap)
  data: NotificationData;

  // iOS-specific
  aps?: {
    alert?: {
      title: string;
      body: string;
      'launch-image'?: string;
    };
    badge?: number;
    sound?: string;
    category?: string;
    'mutable-content'?: number;
    'content-available'?: number;
  };

  // Android-specific
  android?: {
    notification?: {
      channelId: string;
      color?: string;
      icon?: string;
      visibility?: 'public' | 'secret' | 'private';
    };
    priority?: 'min' | 'low' | 'default' | 'high' | 'max';
    ttl?: number;
  };
}

// Notification data payload
interface NotificationData {
  type: NotificationType;
  entityType: 'trip' | 'message' | 'customer' | 'payment' | 'document';
  entityId: string;
  agencyId: string;
  timestamp: number;
  deepLink?: string;
  action?: NotificationAction;
}

enum NotificationType {
  TRIP_ASSIGNED = 'trip_assigned',
  TRIP_UPDATED = 'trip_updated',
  TRIP_CANCELLED = 'trip_cancelled',
  MESSAGE_RECEIVED = 'message_received',
  PAYMENT_RECEIVED = 'payment_received',
  PAYMENT_FAILED = 'payment_failed',
  DOCUMENT_UPLOADED = 'document_uploaded',
  QUOTE_REQUESTED = 'quote_requested',
  BOOKING_CONFIRMED = 'booking_confirmed',
  PRICE_ALERT = 'price_alert',
}

enum NotificationAction {
  VIEW_TRIP = 'view_trip',
  REPLY_MESSAGE = 'reply_message',
  VIEW_PAYMENT = 'view_payment',
  CALL_CUSTOMER = 'call_customer',
  ARCHIVE = 'archive',
}
```

### 2.3 Rich Notifications (iOS)

```typescript
// iOS Notification Service Extension for rich media
interface RichNotificationAttachment {
  identifier: string;
  url: string;
  type: 'image' | 'video' | 'audio';
}

// Notification with image
interface ImageNotificationPayload extends NotificationPayload {
  data: NotificationData & {
    imageUrl: string;
  };
}

// Notification Service Extension (iOS native)
// Notifies.swift
import UserNotifications

class NotificationService: UNNotificationServiceExtension {
  func didReceive(_ request: UNNotificationRequest,
                  withContentHandler contentHandler: @escaping (UNNotificationContent) -> Void) {
    self.contentHandler = contentHandler
    bestAttemptContent = (request.content.mutableCopy() as? UNMutableNotificationContent)

    if let imageUrl = request.content.userInfo["imageUrl"] as? String {
      downloadImage(from: imageUrl) { image in
        if let image = image {
          let attachment = try? UNNotificationAttachment(
            identifier: "image",
            url: image,
            options: nil
          )
          self.bestAttemptContent?.attachments = [attachment]
        }
        contentHandler(self.bestAttemptContent ?? request.content)
      }
    }
  }
}
```

### 2.4 Notification Categories & Actions

```typescript
// Define notification categories with actions
interface NotificationCategory {
  identifier: string;
  actions: NotificationActionConfig[];
  intentIdentifiers?: string[];
  options?: CategoryOptions;
}

interface NotificationActionConfig {
  identifier: string;
  title: string;
  options: ActionOptions;
  authenticationRequired?: boolean;
  destructive?: boolean;
  foreground?: boolean;
}

// iOS Categories
const iOSCategories: NotificationCategory[] = [
  {
    identifier: 'TRIP_ASSIGNED',
    actions: [
      { identifier: 'VIEW', title: 'View', options: { foreground: true } },
      { identifier: 'ARCHIVE', title: 'Archive', options: { foreground: false } },
    ],
  },
  {
    identifier: 'MESSAGE_RECEIVED',
    actions: [
      { identifier: 'REPLY', title: 'Reply', options: { foreground: true } },
      { identifier: 'MARK_READ', title: 'Mark Read', options: { foreground: false } },
      { identifier: 'CALL', title: 'Call', options: { foreground: false } },
    ],
  },
  {
    identifier: 'PAYMENT_RECEIVED',
    actions: [
      { identifier: 'VIEW', title: 'View', options: { foreground: true } },
      { identifier: 'SHARE', title: 'Share', options: { foreground: false } },
    ],
  },
];

// Register categories
function registerNotificationCategories(): void {
  if (Platform.OS === 'ios') {
    PushNotificationIOS.setNotificationCategories(
      iOSCategories.map(category => ({
        identifier: category.identifier,
        actions: category.actions.map(action => ({
          identifier: action.identifier,
          title: action.title,
          options: {
            foreground: action.options.foreground || false,
            destructive: action.destructive || false,
            authenticationRequired: action.authenticationRequired || false,
          },
        })),
      }))
    );
  }
}
```

---

## 3. In-App Notification Center

### 3.1 Notification Storage

```typescript
// Local notification store
interface StoredNotification {
  id: string;
  type: NotificationType;
  title: string;
  body: string;
  data: NotificationData;
  readAt: number | null;
  receivedAt: number;
  expiresAt: number | null;
}

class NotificationStore {
  private storage: PersistentCache;
  private maxNotifications = 500;
  private retentionDays = 90;

  async add(notification: StoredNotification): Promise<void> {
    const key = `notification:${notification.id}`;
    await this.storage.set(key, notification, this.retentionDays * 24 * 60 * 60 * 1000);

    // Prune old notifications
    await this.prune();
  }

  async getUnread(limit: number = 50): Promise<StoredNotification[]> {
    const all = await this.getAll();
    return all
      .filter(n => !n.readAt)
      .sort((a, b) => b.receivedAt - a.receivedAt)
      .slice(0, limit);
  }

  async markRead(id: string): Promise<void> {
    const notification = await this.get(id);
    if (notification && !notification.readAt) {
      notification.readAt = Date.now();
      await this.add(notification);

      // Sync to server
      api.post('/notifications/read', { notificationIds: [id] }).catch(() => {});
    }
  }

  async markAllRead(): Promise<void> {
    const unread = await this.getUnread(1000);
    const ids = unread.map(n => n.id);

    await Promise.all(ids.map(id => this.markRead(id)));
  }

  private async prune(): Promise<void> {
    const all = await this.getAll();
    const cutoff = Date.now() - (this.retentionDays * 24 * 60 * 60 * 1000);

    const expired = all.filter(n => n.receivedAt < cutoff);
    for (const notification of expired) {
      await this.storage.delete(`notification:${notification.id}`);
    }

    // Enforce max count
    if (all.length > this.maxNotifications) {
      const excess = all
        .sort((a, b) => a.receivedAt - b.receivedAt)
        .slice(0, all.length - this.maxNotifications);

      for (const notification of excess) {
        await this.storage.delete(`notification:${notification.id}`);
      }
    }
  }
}
```

### 3.2 Notification List UI

```typescript
interface NotificationListProps {
  onNotificationPress: (notification: StoredNotification) => void;
}

export const NotificationList: React.FC<NotificationListProps> = ({
  onNotificationPress
}) => {
  const [notifications, setNotifications] = useState<StoredNotification[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread'>('unread');

  useEffect(() => {
    loadNotifications();
  }, [filter]);

  const loadNotifications = async () => {
    setLoading(true);
    const store = NotificationStore.getInstance();
    const list = filter === 'unread'
      ? await store.getUnread()
      : await store.getAll(50);
    setNotifications(list);
    setLoading(false);
  };

  const handleDismiss = async (id: string) => {
    const store = NotificationStore.getInstance();
    await store.markRead(id);
    setNotifications(prev => prev.filter(n => n.id !== id));
  };

  const handleDismissAll = async () => {
    const store = NotificationStore.getInstance();
    await store.markAllRead();
    setNotifications([]);
  };

  return (
    <View style={styles.container}>
      <View style={styles.header}>
        <Text style={styles.title}>Notifications</Text>
        <View style={styles.filters}>
          <Chip
            selected={filter === 'unread'}
            onPress={() => setFilter('unread')}
          >
            Unread
          </Chip>
          <Chip
            selected={filter === 'all'}
            onPress={() => setFilter('all')}
          >
            All
          </Chip>
        </View>
      </View>

      {notifications.length > 0 && (
        <Button onPress={handleDismissAll}>
          Dismiss All
        </Button>
      )}

      <FlatList
        data={notifications}
        keyExtractor={(item) => item.id}
        renderItem={({ item }) => (
          <NotificationCard
            notification={item}
            onPress={() => onNotificationPress(item)}
            onDismiss={() => handleDismiss(item.id)}
          />
        )}
        refreshing={loading}
        onRefresh={loadNotifications}
        ListEmptyComponent={
          <EmptyState
            icon="notifications-none"
            message={filter === 'unread' ? 'No unread notifications' : 'No notifications'}
          />
        }
      />
    </View>
  );
};
```

### 3.3 Grouped Notifications

```typescript
// Group notifications by type/entity
interface NotificationGroup {
  id: string;
  type: NotificationType;
  entityId: string;
  title: string;
  notifications: StoredNotification[];
  count: number;
  latestAt: number;
}

function groupNotifications(notifications: StoredNotification[]): NotificationGroup[] {
  const groups = new Map<string, NotificationGroup>();

  for (const notification of notifications) {
    const key = `${notification.type}:${notification.data.entityId}`;

    if (!groups.has(key)) {
      groups.set(key, {
        id: key,
        type: notification.type,
        entityId: notification.data.entityId,
        title: getGroupTitle(notification),
        notifications: [],
        count: 0,
        latestAt: notification.receivedAt,
      });
    }

    const group = groups.get(key)!;
    group.notifications.push(notification);
    group.count++;
    group.latestAt = Math.max(group.latestAt, notification.receivedAt);
  }

  return Array.from(groups.values()).sort((a, b) => b.latestAt - a.latestAt);
}

function getGroupTitle(notification: StoredNotification): string {
  switch (notification.type) {
    case NotificationType.MESSAGE_RECEIVED:
      return 'New messages';
    case NotificationType.TRIP_UPDATED:
      return 'Trip updates';
    case NotificationType.PAYMENT_RECEIVED:
      return 'Payments received';
    default:
      return notification.title;
  }
}
```

---

## 4. Notification Preferences

### 4.1 Preference Model

```typescript
interface NotificationPreferences {
  // Global settings
  enabled: boolean;
  quietHoursEnabled: boolean;
  quietHoursStart: string; // HH:mm
  quietHoursEnd: string;   // HH:mm

  // Per-type settings
  tripAssigned: NotificationSetting;
  tripUpdated: NotificationSetting;
  messageReceived: NotificationSetting;
  paymentReceived: NotificationSetting;
  paymentFailed: NotificationSetting;
  documentUploaded: NotificationSetting;
  quoteRequested: NotificationSetting;
  priceAlert: NotificationSetting;

  // Channel settings
  pushEnabled: boolean;
  inAppEnabled: boolean;
  emailEnabled: boolean;
}

enum NotificationSetting {
  ALL = 'all',           // All notifications
  MENTION_ONLY = 'mention_only',  // Only when mentioned/assigned
  NONE = 'none',         // Disabled
}

// Default preferences
const defaultPreferences: NotificationPreferences = {
  enabled: true,
  quietHoursEnabled: false,
  quietHoursStart: '22:00',
  quietHoursEnd: '08:00',
  tripAssigned: NotificationSetting.ALL,
  tripUpdated: NotificationSetting.ALL,
  messageReceived: NotificationSetting.ALL,
  paymentReceived: NotificationSetting.ALL,
  paymentFailed: NotificationSetting.ALL,
  documentUploaded: NotificationSetting.MENTION_ONLY,
  quoteRequested: NotificationSetting.ALL,
  priceAlert: NotificationSetting.MENTION_ONLY,
  pushEnabled: true,
  inAppEnabled: true,
  emailEnabled: false,
};
```

### 4.2 Preference Manager

```typescript
class PreferenceManager {
  private store: PersistentCache;
  private preferences: NotificationPreferences;
  private listeners: Set<(prefs: NotificationPreferences) => void> = new Set();

  async load(): Promise<NotificationPreferences> {
    const stored = await this.store.get<NotificationPreferences>('notification_preferences');
    this.preferences = stored || { ...defaultPreferences };
    return this.preferences;
  }

  async save(preferences: Partial<NotificationPreferences>): Promise<void> {
    this.preferences = { ...this.preferences, ...preferences };
    await this.store.set('notification_preferences', this.preferences, -1);
    await this.syncToServer();
    this.notifyListeners();
  }

  async updateTypeSetting(
    type: keyof NotificationPreferences,
    setting: NotificationSetting
  ): Promise<void> {
    await this.save({ [type]: setting } as Partial<NotificationPreferences>);
  }

  shouldDeliver(type: NotificationType, timestamp: number = Date.now()): boolean {
    if (!this.preferences.enabled) return false;

    // Check quiet hours
    if (this.preferences.quietHoursEnabled && this.isInQuietHours(timestamp)) {
      return false;
    }

    // Check per-type setting
    const setting = this.getTypeSetting(type);
    if (setting === NotificationSetting.NONE) {
      return false;
    }

    return true;
  }

  private isInQuietHours(timestamp: number): boolean {
    const hour = new Date(timestamp).getHours();
    const start = parseInt(this.preferences.quietHoursStart.split(':')[0]);
    const end = parseInt(this.preferences.quietHoursEnd.split(':')[0]);

    if (start < end) {
      return hour >= start && hour < end;
    } else {
      // Spans midnight
      return hour >= start || hour < end;
    }
  }

  private getTypeSetting(type: NotificationType): NotificationSetting {
    const key = typeToPreferenceKey(type);
    return this.preferences[key] || NotificationSetting.ALL;
  }

  subscribe(listener: (prefs: NotificationPreferences) => void): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(): void {
    this.listeners.forEach(listener => listener(this.preferences));
  }

  private async syncToServer(): Promise<void> {
    await api.put('/notifications/preferences', this.preferences);
  }
}

function typeToPreferenceKey(type: NotificationType): keyof NotificationPreferences {
  switch (type) {
    case NotificationType.TRIP_ASSIGNED:
      return 'tripAssigned';
    case NotificationType.TRIP_UPDATED:
      return 'tripUpdated';
    case NotificationType.MESSAGE_RECEIVED:
      return 'messageReceived';
    case NotificationType.PAYMENT_RECEIVED:
      return 'paymentReceived';
    case NotificationType.PAYMENT_FAILED:
      return 'paymentFailed';
    case NotificationType.DOCUMENT_UPLOADED:
      return 'documentUploaded';
    case NotificationType.QUOTE_REQUESTED:
      return 'quoteRequested';
    case NotificationType.PRICE_ALERT:
      return 'priceAlert';
    default:
      return 'tripAssigned';
  }
}
```

### 4.3 Settings UI

```typescript
export const NotificationSettingsScreen: React.FC = () => {
  const [preferences, setPreferences] = useState<NotificationPreferences>(defaultPreferences);
  const manager = PreferenceManager.getInstance();

  useEffect(() => {
    manager.load().then(setPreferences);
    const unsubscribe = manager.subscribe(setPreferences);
    return unsubscribe;
  }, []);

  const updateSetting = async (key: keyof NotificationPreferences, value: any) => {
    setPreferences(prev => ({ ...prev, [key]: value }));
    await manager.save({ [key]: value });
  };

  return (
    <ScrollView style={styles.container}>
      <Section>
        <SectionHeader title="General" />
        <SwitchRow
          label="Enable Notifications"
          value={preferences.enabled}
          onChange={(value) => updateSetting('enabled', value)}
        />
        <SwitchRow
          label="Quiet Hours"
          value={preferences.quietHoursEnabled}
          onChange={(value) => updateSetting('quietHoursEnabled', value)}
        />
        {preferences.quietHoursEnabled && (
          <TimeRangeRow
            start={preferences.quietHoursStart}
            end={preferences.quietHoursEnd}
            onStartChange={(value) => updateSetting('quietHoursStart', value)}
            onEndChange={(value) => updateSetting('quietHoursEnd', value)}
          />
        )}
      </Section>

      <Section>
        <SectionHeader title="Trip Notifications" />
        <EnumRow
          label="New Trip Assignments"
          value={preferences.tripAssigned}
          options={[
            { label: 'All', value: NotificationSetting.ALL },
            { label: 'Assigned Only', value: NotificationSetting.MENTION_ONLY },
            { label: 'None', value: NotificationSetting.NONE },
          ]}
          onChange={(value) => updateSetting('tripAssigned', value)}
        />
        <EnumRow
          label="Trip Updates"
          value={preferences.tripUpdated}
          options={[
            { label: 'All', value: NotificationSetting.ALL },
            { label: 'Assigned Only', value: NotificationSetting.MENTION_ONLY },
            { label: 'None', value: NotificationSetting.NONE },
          ]}
          onChange={(value) => updateSetting('tripUpdated', value)}
        />
      </Section>

      <Section>
        <SectionHeader title="Customer Notifications" />
        <EnumRow
          label="Messages"
          value={preferences.messageReceived}
          options={[
            { label: 'All', value: NotificationSetting.ALL },
            { label: 'Assigned Only', value: NotificationSetting.MENTION_ONLY },
            { label: 'None', value: NotificationSetting.NONE },
          ]}
          onChange={(value) => updateSetting('messageReceived', value)}
        />
        <EnumRow
          label="Quote Requests"
          value={preferences.quoteRequested}
          options={[
            { label: 'All', value: NotificationSetting.ALL },
            { label: 'Assigned Only', value: NotificationSetting.MENTION_ONLY },
            { label: 'None', value: NotificationSetting.NONE },
          ]}
          onChange={(value) => updateSetting('quoteRequested', value)}
        />
      </Section>

      <Section>
        <SectionHeader title="Payment Notifications" />
        <EnumRow
          label="Payments Received"
          value={preferences.paymentReceived}
          options={[
            { label: 'All', value: NotificationSetting.ALL },
            { label: 'None', value: NotificationSetting.NONE },
          ]}
          onChange={(value) => updateSetting('paymentReceived', value)}
        />
        <EnumRow
          label="Payment Failures"
          value={preferences.paymentFailed}
          options={[
            { label: 'All', value: NotificationSetting.ALL },
            { label: 'None', value: NotificationSetting.NONE },
          ]}
          onChange={(value) => updateSetting('paymentFailed', value)}
        />
      </Section>
    </ScrollView>
  );
};
```

---

## 5. Deep Linking

### 5.1 URL Scheme & Universal Links

```typescript
// App URL configuration
const DEEP_LINK_CONFIG = {
  // Custom URL scheme
  urlScheme: 'travelagent',

  // Universal Links (iOS) / App Links (Android)
  universalLinkDomain: 'app.travelagent.com',

  // Path mappings
  pathMappings: {
    '/trips/:id': 'TripDetail',
    '/messages/:conversationId': 'ConversationDetail',
    '/customers/:id': 'CustomerDetail',
    '/payments/:id': 'PaymentDetail',
    '/inbox': 'Inbox',
    '/settings/notifications': 'NotificationSettings',
  },
};

// Linking configuration
const linking = {
  prefixes: [
    'travelagent://',
    'https://app.travelagent.com',
  ],
  config: {
    screens: {
      TripDetail: {
        path: 'trips/:id',
        parse: { id: (id: string) => id },
      },
      ConversationDetail: {
        path: 'messages/:conversationId',
        parse: { conversationId: (conversationId: string) => conversationId },
      },
      CustomerDetail: {
        path: 'customers/:id',
        parse: { id: (id: string) => id },
      },
      PaymentDetail: {
        path: 'payments/:id',
        parse: { id: (id: string) => id },
      },
      Inbox: 'inbox',
      NotificationSettings: 'settings/notifications',
    },
  },
};
```

### 5.2 Notification Tap Handler

```typescript
// Handle notification tap to deep link
import { NavigationContainer, useNavigation } from '@react-navigation/native';

function App(): React.ReactElement {
  const navigationRef = useNavigation();
  const linkingRef = useRef<NavigationContainer>(null);
  const notificationHandled = useRef(false);

  useEffect(() => {
    // Handle notification tap when app is opened from background
    const subscription = getMessaging().onNotificationOpenedApp(remoteMessage => {
      handleNotificationTap(remoteMessage.data);
    });

    // Handle notification tap when app is closed
    getMessaging().getInitialNotification().then(remoteMessage => {
      if (remoteMessage && !notificationHandled.current) {
        notificationHandled.current = true;
        handleNotificationTap(remoteMessage.data);
      }
    });

    return () => subscription();
  }, []);

  const handleNotificationTap = (data: any) => {
    const deepLink = data?.deepLink;
    const entityType = data?.entityType;
    const entityId = data?.entityId;

    if (deepLink) {
      // Use explicit deep link
      navigationRef.current?.navigate(deepLink);
    } else if (entityType && entityId) {
      // Construct deep link from data
      const screen = getScreenForEntityType(entityType);
      if (screen) {
        navigationRef.current?.navigate(screen, { id: entityId });
      }
    }
  };

  return (
    <NavigationContainer ref={linkingRef} linking={linking}>
      {/* ... */}
    </NavigationContainer>
  );
}

function getScreenForEntityType(entityType: string): string | null {
  switch (entityType) {
    case 'trip':
      return 'TripDetail';
    case 'conversation':
      return 'ConversationDetail';
    case 'customer':
      return 'CustomerDetail';
    case 'payment':
      return 'PaymentDetail';
    default:
      return null;
  }
}
```

### 5.3 Universal Links Setup

```bash
# iOS: apple-app-site-association file
# https://app.travelagent.com/.well-known/apple-app-site-association

{
  "applinks": {
    "apps": [],
    "details": [
      {
        "appIDs": ["TEAMID.com.travelagent.app"],
        "components": [
          {
            "/": "/trips/*",
            "comment": "Trip detail pages"
          },
          {
            "/": "/messages/*",
            "comment": "Conversation pages"
          },
          {
            "/": "/customers/*",
            "comment": "Customer pages"
          },
          {
            "/": "/payments/*",
            "comment": "Payment pages"
          },
          {
            "/": "/inbox",
            "comment": "Inbox"
          }
        ]
      }
    ]
  }
}

# Android: assetlinks.json file
# https://app.travelagent.com/.well-known/assetlinks.json

[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.travelagent.app",
    "sha256_cert_fingerprints": [
      "AA:BB:CC:DD:EE:FF:..."
    ]
  }
}]
```

---

## 6. Analytics & Engagement

### 6.1 Notification Metrics

```typescript
interface NotificationMetrics {
  // Delivery metrics
  sent: number;
  delivered: number;
  failed: number;

  // Engagement metrics
  opened: number;
  converted: number;
  dismissed: number;

  // Timing metrics
  avgTimeToOpen: number; // milliseconds
  openRate: number; // percentage

  // Breakdown by type
  byType: Record<NotificationType, TypeMetrics>;
}

interface TypeMetrics extends NotificationMetrics {
  type: NotificationType;
}

// Analytics tracking
class NotificationAnalytics {
  trackSent(type: NotificationType, notificationId: string): void {
    this.logEvent('notification_sent', {
      notification_id: notificationId,
      type,
      timestamp: Date.now(),
    });
  }

  trackDelivered(type: NotificationType, notificationId: string): void {
    this.logEvent('notification_delivered', {
      notification_id: notificationId,
      type,
      timestamp: Date.now(),
    });
  }

  trackOpened(type: NotificationType, notificationId: string, timeToOpen: number): void {
    this.logEvent('notification_opened', {
      notification_id: notificationId,
      type,
      time_to_open: timeToOpen,
      timestamp: Date.now(),
    });
  }

  trackConverted(type: NotificationType, notificationId: string, action: string): void {
    this.logEvent('notification_converted', {
      notification_id: notificationId,
      type,
      action,
      timestamp: Date.now(),
    });
  }

  trackDismissed(type: NotificationType, notificationId: string): void {
    this.logEvent('notification_dismissed', {
      notification_id: notificationId,
      type,
      timestamp: Date.now(),
    });
  }

  private logEvent(name: string, properties: Record<string, any>): void {
    // Send to analytics service (e.g., Mixpanel, Amplitude)
    Analytics.track(name, properties);
  }
}
```

### 6.2 Engagement Optimization

```typescript
// Smart delivery time optimization
interface DeliverySchedule {
  timeZone: string;
  optimalSendTimes: number[]; // Hours (0-23)
  avoidTimes: number[]; // Hours to avoid
}

class DeliveryOptimizer {
  private schedule: DeliverySchedule;
  private analytics: NotificationAnalytics;

  async getOptimalSendTime(
    recipientId: string,
    type: NotificationType
  ): Promise<Date> {
    const userSchedule = await this.getUserSchedule(recipientId);
    const now = new Date();

    // Find next optimal time
    for (let i = 0; i < 24; i++) {
      const candidate = new Date(now.getTime() + i * 60 * 60 * 1000);
      const hour = this.getHoursInTimeZone(candidate, userSchedule.timeZone);

      if (userSchedule.optimalSendTimes.includes(hour) &&
          !userSchedule.avoidTimes.includes(hour)) {
        return candidate;
      }
    }

    // Fallback to now
    return now;
  }

  private async getUserSchedule(recipientId: string): Promise<DeliverySchedule> {
    // Fetch from user preferences or derive from activity patterns
    const activity = await this.getUserActivityPatterns(recipientId);

    return {
      timeZone: activity.timeZone,
      optimalSendTimes: activity.peakHours,
      avoidTimes: activity.quietHours,
    };
  }

  private getHoursInTimeZone(date: Date, timeZone: string): number {
    return parseInt(
      new Date(date.toLocaleString('en-US', { timeZone }))
        .toLocaleTimeString('en-US', { hour12: false })
        .split(':')[0],
      10
    );
  }
}

// A/B testing for notification content
interface NotificationVariant {
  id: string;
  title: string;
  body: string;
  groupId: string;
}

class NotificationExperiment {
  async getVariant(experimentId: string): Promise<NotificationVariant | null> {
    // Fetch active experiment
    const experiment = await this.fetchExperiment(experimentId);
    if (!experiment || !experiment.isActive) return null;

    // Assign variant based on user hash
    const userId = await this.getCurrentUserId();
    const variantIndex = this.hashUserId(userId, experiment.variants.length);
    return experiment.variants[variantIndex];
  }

  private hashUserId(userId: string, numVariants: number): number {
    let hash = 0;
    for (let i = 0; i < userId.length; i++) {
      hash = ((hash << 5) - hash) + userId.charCodeAt(i);
      hash = hash & hash;
    }
    return Math.abs(hash) % numVariants;
  }
}
```

### 6.3 Dashboard Metrics

```typescript
// Notification performance dashboard
interface NotificationDashboard {
  summary: {
    totalSent: number;
    deliveryRate: number;
    openRate: number;
    conversionRate: number;
  };
  trends: {
    daily: TimeSeriesData[];
    byType: Record<NotificationType, TimeSeriesData[]>;
  };
  topPerformers: {
    byOpenRate: NotificationType[];
    byConversionRate: NotificationType[];
  };
}

async function getNotificationDashboard(
  startDate: Date,
  endDate: Date
): Promise<NotificationDashboard> {
  const metrics = await api.get('/analytics/notifications', {
    start_date: startDate.toISOString(),
    end_date: endDate.toISOString(),
  });

  return {
    summary: {
      totalSent: metrics.sent,
      deliveryRate: (metrics.delivered / metrics.sent) * 100,
      openRate: (metrics.opened / metrics.delivered) * 100,
      conversionRate: (metrics.converted / metrics.opened) * 100,
    },
    trends: {
      daily: groupByDay(metrics.timeline),
      byType: groupByType(metrics.timeline),
    },
    topPerformers: {
      byOpenRate: sortBy(metrics.byType, 'openRate'),
      byConversionRate: sortBy(metrics.byType, 'conversionRate'),
    },
  };
}
```

---

## 7. Implementation Patterns

### 7.1 Notification Hook

```typescript
// useNotifications hook
interface UseNotificationsReturn {
  notifications: StoredNotification[];
  unreadCount: number;
  loading: boolean;
  refresh: () => Promise<void>;
  markRead: (id: string) => Promise<void>;
  markAllRead: () => Promise<void>;
  requestPermission: () => Promise<boolean>;
}

export function useNotifications(): UseNotificationsReturn {
  const [notifications, setNotifications] = useState<StoredNotification[]>([]);
  const [loading, setLoading] = useState(false);
  const store = NotificationStore.getInstance();
  const preferenceManager = PreferenceManager.getInstance();

  const refresh = useCallback(async () => {
    setLoading(true);
    const list = await store.getAll(50);
    setNotifications(list);
    setLoading(false);
  }, []);

  const markRead = useCallback(async (id: string) => {
    await store.markRead(id);
    setNotifications(prev =>
      prev.map(n => n.id === id ? { ...n, readAt: Date.now() } : n)
    );
  }, []);

  const markAllRead = useCallback(async () => {
    await store.markAllRead();
    setNotifications(prev =>
      prev.map(n => ({ ...n, readAt: Date.now() }))
    );
  }, []);

  const requestPermission = useCallback(async () => {
    const manager = new NotificationPermissionManager();
    const status = await manager.requestPermission(true);
    return status === PermissionStatus.GRANTED;
  }, []);

  // Listen for new notifications
  useEffect(() => {
    const unsubscribe = messaging().onMessage(async (remoteMessage) => {
      const notification = parseRemoteMessage(remoteMessage);
      await store.add(notification);
      await refresh();
    });

    return unsubscribe;
  }, [refresh]);

  return {
    notifications,
    unreadCount: notifications.filter(n => !n.readAt).length,
    loading,
    refresh,
    markRead,
    markAllRead,
    requestPermission,
  };
}
```

### 7.2 Notification Provider

```typescript
// Notification context provider
interface NotificationContextValue {
  preferences: NotificationPreferences;
  updatePreferences: (prefs: Partial<NotificationPreferences>) => Promise<void>;
}

const NotificationContext = createContext<NotificationContextValue | null>(null);

export const NotificationProvider: React.FC<{ children: React.ReactNode }> = ({
  children
}) => {
  const preferenceManager = PreferenceManager.getInstance();
  const [preferences, setPreferences] = useState<NotificationPreferences>(defaultPreferences);

  useEffect(() => {
    preferenceManager.load().then(setPreferences);
    const unsubscribe = preferenceManager.subscribe(setPreferences);
    return unsubscribe;
  }, []);

  const updatePreferences = useCallback(async (prefs: Partial<NotificationPreferences>) => {
    await preferenceManager.save(prefs);
  }, []);

  return (
    <NotificationContext.Provider value={{ preferences, updatePreferences }}>
      {children}
    </NotificationContext.Provider>
  );
};

export const useNotificationPreferences = (): NotificationContextValue => {
  const context = useContext(NotificationContext);
  if (!context) {
    throw new Error('useNotificationPreferences must be used within NotificationProvider');
  }
  return context;
};
```

---

## 8. Testing & Compliance

### 8.1 Permission Testing

```typescript
describe('Notification Permissions', () => {
  it('should request permission on first notification', async () => {
    const manager = new NotificationPermissionManager();
    const status = await manager.requestPermission();
    expect([PermissionStatus.GRANTED, PermissionStatus.DENIED, PermissionStatus.PROVISIONAL])
      .toContain(status);
  });

  it('should show rationale for denied permission', async () => {
    const manager = new NotificationPermissionManager();
    jest.spyOn(manager, 'checkPermission').mockResolvedValue(PermissionStatus.DENIED);

    const rationaleSpy = jest.spyOn(manager as any, 'showRationaleDialog');
    await manager.requestPermission(true);

    expect(rationaleSpy).toHaveBeenCalled();
  });
});
```

### 8.2 Quiet Hours Testing

```typescript
describe('Quiet Hours', () => {
  it('should not deliver notifications during quiet hours', () => {
    const manager = PreferenceManager.getInstance();
    manager.save({
      quietHoursEnabled: true,
      quietHoursStart: '22:00',
      quietHoursEnd: '08:00',
    });

    // 11 PM - during quiet hours
    const nightTime = new Date('2026-04-25T23:00:00');
    expect(manager.shouldDeliver(NotificationType.TRIP_ASSIGNED, nightTime.getTime()))
      .toBe(false);

    // 10 AM - outside quiet hours
    const dayTime = new Date('2026-04-25T10:00:00');
    expect(manager.shouldDeliver(NotificationType.TRIP_ASSIGNED, dayTime.getTime()))
      .toBe(true);
  });

  it('should handle quiet hours spanning midnight', () => {
    const manager = PreferenceManager.getInstance();
    manager.save({
      quietHoursEnabled: true,
      quietHoursStart: '22:00',
      quietHoursEnd: '06:00',
    });

    // 3 AM - should be quiet
    const lateNight = new Date('2026-04-25T03:00:00');
    expect(manager.shouldDeliver(NotificationType.TRIP_ASSIGNED, lateNight.getTime()))
      .toBe(false);
  });
});
```

### 8.3 GDPR & Privacy Compliance

```typescript
// Consent tracking
interface NotificationConsent {
  granted: boolean;
  timestamp: number;
  version: string;
  categories: string[];
}

class ConsentManager {
  private consentKey = 'notification_consent';

  async hasConsent(): Promise<boolean> {
    const consent = await this.getConsent();
    return consent?.granted || false;
  }

  async grantConsent(categories: string[] = []): Promise<void> {
    const consent: NotificationConsent = {
      granted: true,
      timestamp: Date.now(),
      version: APP_VERSION,
      categories,
    };
    await AsyncStorage.setItem(this.consentKey, JSON.stringify(consent));
    await this.syncConsent(consent);
  }

  async revokeConsent(): Promise<void> {
    const consent: NotificationConsent = {
      granted: false,
      timestamp: Date.now(),
      version: APP_VERSION,
      categories: [],
    };
    await AsyncStorage.setItem(this.consentKey, JSON.stringify(consent));
    await this.syncConsent(consent);

    // Unregister device
    await api.post('/devices/unregister');
  }

  private async getConsent(): Promise<NotificationConsent | null> {
    const data = await AsyncStorage.getItem(this.consentKey);
    return data ? JSON.parse(data) : null;
  }

  private async syncConsent(consent: NotificationConsent): Promise<void> {
    await api.post('/notifications/consent', consent);
  }
}
```

---

## Summary

The notification system enables real-time engagement with travel agents:

| Component | Purpose |
|-----------|---------|
| **Push Notifications** | FCM/APNs for immediate alerts |
| **Notification Types** | Critical, Important, Informational, Background |
| **Rich Notifications** | Images, videos, action buttons |
| **In-App Center** | Full notification history, grouped views |
| **Preferences** | Granular control per type, quiet hours |
| **Deep Linking** | Universal links, URL schemes |
| **Analytics** | Delivery, open, conversion metrics |

**Key Takeaways:**
- Handle permission gracefully with rationale
- Respect quiet hours and user preferences
- Use notification categories for quick actions
- Track metrics to optimize engagement
- Support deep linking from notification taps
- Comply with GDPR consent requirements

---

**Mobile App Series Complete!** All 4 documents now available.
