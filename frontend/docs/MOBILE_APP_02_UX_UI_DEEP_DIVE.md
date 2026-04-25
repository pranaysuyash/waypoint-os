# Mobile App — UX/UI Deep Dive

> Mobile-first design principles, touch interactions, and platform conventions

---

## Document Overview

**Series:** Mobile App Deep Dive
**Document:** 2 of 4
**Last Updated:** 2026-04-25
**Status:** ✅ Complete

**Related Documents:**
- [Technical Deep Dive](./MOBILE_APP_01_TECHNICAL_DEEP_DIVE.md) — Architecture, React Native
- [Sync Deep Dive](./MOBILE_APP_03_SYNC_DEEP_DIVE.md) — Data synchronization
- [Notifications Deep Dive](./MOBILE_APP_04_NOTIFICATIONS_DEEP_DIVE.md) — Push notifications

---

## Table of Contents

1. [Mobile-First Design Principles](#mobile-first-design-principles)
2. [Touch Interactions & Gestures](#touch-interactions--gestures)
3. [Navigation Patterns](#navigation-patterns)
4. [Screen Layouts](#screen-layouts)
5. [Platform Conventions](#platform-conventions)
6. [Accessibility](#accessibility)
7. [Component Library](#component-library)

---

## Mobile-First Design Principles

### Design Philosophy

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      MOBILE-FIRST DESIGN PHILOSOPHY                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  CORE PRINCIPLES                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  1. THUMB-FRIENDLY                                                    │   │
│  │     Primary actions within easy thumb reach                          │   │
│  │     Bottom 1/3 of screen is "prime real estate"                       │   │
│  │                                                                     │   │
│  │  2. TOUCH-OPTIMIZED                                                   │   │
│  │     Minimum touch target: 44x44pt (iOS), 48x48dp (Android)          │   │
│  │     Generous spacing between interactive elements                    │   │
│  │                                                                     │   │
│  │  3. CONTENT-FIRST                                                     │   │
│  │     Focus on essential information                                   │   │
│  │     Progressive disclosure for complex data                          │   │
│  │                                                                     │   │
│  │  4. CONTEXT-AWARE                                                     │   │
│  │     Adapt to user's current situation                                 │   │
│  │     On-the-go vs stationary use cases                                 │   │
│  │                                                                     │   │
│  │  5. PERFORMANCE-FOCUSED                                               │   │
│  │     Instant feedback for all interactions                            │   │
│  │     Smooth animations and transitions                                │   │
│  │                                                                     │   │
│  │  6. OFFLINE-CONSCIOUS                                                 │   │
│  │     Clear indication of online/offline status                        │   │
│  │     Graceful handling of network issues                              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Screen Real Estate Zones

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SCREEN ZONES FOR INTERACTION                           │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  HARD TO REACH (Top)  ───────────────────────────────────────────   │    │
│  │  • Status indicators                                                │    │
│  │  • Rare actions                                                     │    │
│  │  • Information display (read-only)                                  │    │
│  │                                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  STRETCH ZONE  ───────────────────────────────────────────────────   │    │
│  │  • Requires two-handed use                                          │    │
│  │  • Secondary actions                                                │    │
│  │  • Navigation items (tabs, headers)                                 │    │
│  │                                                                     │    │
│  ├─────────────────────────────────────────────────────────────────────┤    │
│  │  NATURAL ZONE (Bottom)  ─────────────────────────────────────────   │    │
│  │  • Primary actions (CTAs)                                            │    │
│  │  • Bottom navigation                                                │    │
│  │  • Frequently used controls                                         │    │
│  │  • Thumb-friendly zone                                              │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  Thumb Zone Map (Right-Handed User)                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────┐  ┌─────┐  ┌─────┐  ┌─────┐                             │    │
│  │  │ RED │  │ORANG│  │ YELL│  │GREEN│                             │    │
│  │  │     │  │     │  │     │  │     │                             │    │
│  │  │Hard │  │Stret│  │Easy │  │Natural│                           │    │
│  │  │     │  │     │  │     │  │     │                             │    │
│  │  └─────┘  └─────┘  └─────┘  └─────┘                             │    │
│  │                                                                     │    │
│  │  Place critical CTAs in GREEN zone                                   │    │
│  │  Place secondary actions in YELLOW zone                             │    │
│  │  Avoid placing touch targets in RED zone                            │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Touch Interactions & Gestures

### Touch Target Guidelines

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      TOUCH TARGET GUIDELINES                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  MINIMUM SIZES                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Platform    │ Minimum Size  │ Recommended Size  │ Spacing          │   │
│  │  ─────────────────────────────────────────────────────────────────  │   │
│  │  iOS         │ 44x44pt       │ 48x48pt+          │ 8pt between      │   │
│  │  Android     │ 48x48dp       │ 56x56dp+          │ 8dp between      │   │
│  │  Web         │ 44x44px       │ 48x48px+          │ 8px between      │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TOUCH TARGET EXAMPLES                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐   ┌──────┐           │   │
│  │  │ ICON │   │ ICON │   │ TEXT │   │ ICON │   │ TEXT │           │   │
│  │  │ 44x44│   │ 48x48│   │BTN  │   │ 32x32│   │LINK │           │   │
│  │  │     │   │     │   │44x44 │   │ + pad│   │ + pad│           │   │
│  │  └──────┘   └──────┘   └──────┘   └──────┘   └──────┘           │   │
│  │  Minimum   Preferred  Minimum    Too small   Expand tap            │   │
│  │                                                                     │   │
│  │  ┌─────────────────────────────────────────────────────────────┐   │   │
│  │  │  TOUCH TARGETS SHOULD BE:                                   │   │   │
│  │  │  • Large enough for accurate tapping                         │   │   │
│  │  │  • Surrounded by adequate spacing                             │   │   │
│  │  │  • Visually distinct from surrounding content                 │   │   │
│  │  │  • Provide immediate feedback on tap                          │   │   │
│  │  └─────────────────────────────────────────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Supported Gestures

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      SUPPORTED GESTURES                                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  TAP                                                                        │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Usage: Select, activate, confirm                                   │   │
│  │  Feedback: Visual highlight, haptic feedback                        │   │
│  │  Examples: Tap trip card, tap call button, tap checkbox             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  LONG PRESS                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Usage: Context menu, multi-select, reveal options                 │   │
│  │  Duration: 500ms before triggering                                  │   │
│  │  Feedback: Vibration, visual indicator (progress)                   │   │
│  │  Examples: Long press trip to archive, long press message to delete│   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SWIPE (HORIZONTAL)                                                          │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Left Swipe: Actions (archive, delete, etc.)                       │   │
│  │  Right Swipe: Quick actions (mark read, reply, etc.)                │   │
│  │  Feedback: Action buttons revealed, background color change        │   │
│  │  Examples: Swipe trip to archive, swipe message to reply           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  SWIPE (VERTICAL)                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Pull to Refresh: Reload current list                               │   │
│  │  Pull to Load More: Load additional items                          │   │
│  │  Dismiss: Swipe down to close modal/sheet                           │   │
│  │  Examples: Pull inbox to refresh, swipe down to close new message  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PINCH                                                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Usage: Zoom in/out (images, maps, documents)                      │   │
│  │  Feedback: Content scales smoothly                                  │   │
│  │  Examples: Zoom itinerary map, zoom PDF document                   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  PAN                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Usage: Move around content (maps, large images, timelines)         │   │
│  │  Feedback: Content follows finger movement                         │   │
│  │  Examples: Pan map to explore destination, pan timeline            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Gesture Implementation

```typescript
/**
 * Gesture handler components
 */
import React from 'react';
import { GestureDetector, GestureHandlerRootView, Directions } from 'react-native-gesture-handler';
import Animated, { runOnJS } from 'react-native-reanimated';

/**
 * Swipeable trip card component
 */
interface SwipeableTripCardProps {
  children: React.ReactNode;
  onArchive?: () => void;
  onDelete?: () => void;
  onReply?: () => void;
}

export const SwipeableTripCard: React.FC<SwipeableTripCardProps> = ({
  children,
  onArchive,
  onDelete,
  onReply
}) => {
  const translateX = new Animated.Value(0);
  const swipeRef = React.useRef(null);

  const gestureHandler = GestureDetector.NativeGestureHandler.extend()
    .onUpdate((event) => {
      translateX.setValue(event.translationX);
    })
    .onEnd((event) => {
      if (Math.abs(event.translationX) < 80) {
        // Not enough swipe - reset position
        runOnJS(() => translateX.setValue(0));
      } else {
        // Determine action based on direction
        if (event.translationX > 0 && onReply) {
          // Right swipe - reply
          runOnJS(() => {
            translateX.setValue(0);
            onReply();
          });
        } else if (event.translationX < 0 && onArchive) {
          // Left swipe - archive
          runOnJS(() => {
            translateX.setValue(-500);
            setTimeout(() => {
              translateX.setValue(0);
              onArchive();
            }, 250);
          });
        }
      }
    });

  return (
    <GestureDetector gesture={gestureHandler}>
      <Animated.View style={[styles.card, { transform: [{ translateX }] }]}>
        {children}
      </Animated.View>
    </GestureDetector>
  );
};

/**
 * Pull to refresh component
 */
import { RefreshControl } from 'react-native';

interface PullToRefreshProps {
  onRefresh: () => Promise<void>;
  refreshing: boolean;
  children: React.ReactNode;
}

export const PullToRefresh: React.FC<PullToRefreshProps> = ({
  onRefresh,
  refreshing,
  children
}) => {
  return (
    <ScrollView
      refreshControl={
        <RefreshControl
          refreshing={refreshing}
          onRefresh={onRefresh}
          tintColor="#007AFF"
          title="Pull to refresh"
          titleColor="#999"
        />
      }
    >
      {children}
    </ScrollView>
  );
};

/**
 * Long press handler hook
 */
import { useSharedValue } from 'react-native-reanimated';

export function useLongPress(
  callback: () => void,
  duration: number = 500
) {
  const isActive = useSharedValue(false);

  const gesture = GestureDetector.NativeGestureHandler.extend()
    .onStart(() => {
      'worklet';
      isActive.value = true;
      setTimeout(() => {
        if (isActive.value) {
          runOnJS(callback);
        }
      }, duration);
    })
    .onEnd(() => {
      'worklet';
      isActive.value = false;
    });

  return gesture;
}

const styles = StyleSheet.create({
  card: {
    backgroundColor: 'white',
    borderRadius: 8,
    padding: 16,
    marginVertical: 8,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2
  }
});
```

---

## Navigation Patterns

### Navigation Structure

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      NAVIGATION STRUCTURE                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AUTH FLOW                                                                  │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Login Screen ──► OTP Screen ──► (Optional) Onboarding ──► Main App   │   │
│  │     │              │              │                │                  │   │
│  │     │              │              │                │                  │   │
│  │     └──────────────┴──────────────┴────────────────────────┘       │   │
│  │                      │                                             │   │
│  │                      ▼                                             │   │
│  │               Skip if authenticated                               │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MAIN NAVIGATION (Bottom Tabs)                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                                                                     │   │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐ │   │
│  │  │  Inbox  │  │ Trips   │  │Customers│  │Messages│  │Settings │ │   │
│  │  │         │  │         │  │         │  │         │  │         │ │   │
│  │  │   ✓    3│  │   📋   12│  │   👥   48│  │   💬   5│  │   ⚙️    │ │   │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘ │   │
│  │      Badge                                               Badge       │   │
│  │                                                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  STACK NAVIGATION                                                            │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Inbox List ──► Trip Detail ──► Timeline ──► Customer Profile      │   │
│  │      │             │             │              │                   │   │
│  │      │             │             │              ▼                   │   │
│  │      │             │             │         Actions Modal            │   │
│  │      │             │             │              │                   │   │
│  │      │             │             │         ┌─────────────┐         │   │
│  │      │             │             │         │ Call        │         │   │
│  │      │             │             │         │ Message     │         │   │
│  │      │             │             │         │ Email       │         │   │
│  │      │             │             │         └─────────────┘         │   │
│  │      │             │             │                                  │   │
│  │      └─────────────┴─────────────┴──────────────────────────┘       │   │
│  │                      │                                             │   │
│  │                      ▼                                             │   │
│  │              Back to list (swipe or button)                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Tab Navigation Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      BOTTOM TAB NAVIGATION                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Content Area                                                         │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │                                                                 │  │    │
│  │  │  Trip cards, customer lists, messages, etc.                     │  │    │
│  │  │                                                                 │  │    │
│  │  │                                                                 │  │    │
│  │  │                                                                 │  │    │
│  │  │                                                                 │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                       │    │
│  │  ══════════════════════════════════════════════════════════════════   │    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐      │    │
│  │  │  📬     │  │  📋     │  │  👥     │  │  💬     │  │  ⚙️     │      │    │
│  │  │         │  │         │  │         │  │         │  │         │      │    │
│  │  │ Inbox   │  │ Trips   │  │Customers│  │Messages │  │Settings │      │    │
│  │  │    3    │  │   12    │  │   48    │  │    5    │  │         │      │    │
│  │  │  ───────│  │  ───────│  │  ───────│  │  ───────│  │  ───────│      │    │
│  │  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘      │    │
│  │      Active tab highlighted with brand color                          │    │
│  │                                                                       │    │
│  └───────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  DESIGN SPECIFICATIONS                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  Height: 56pt (iOS) / 64dp (Android)                                 │   │
│  │  Background: Surface color (light: #F5F5F5, dark: #1C1C1E)            │   │
│  │  Active color: Brand primary (#007AFF)                                │   │
│  │  Inactive color: Gray secondary (#8E8E93)                             │   │
│  │  Border top: 1px solid (#C6C6C8)                                     │   │
│  │  Safe area bottom: Account for iPhone home indicator                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Navigation Component

```typescript
/**
 * Main tab navigator configuration
 */
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

/**
 * Bottom tab navigator with badge support
 */
function MainTabs() {
  return (
    <Tab.Navigator
      screenOptions={({ route }) => ({
        tabBarIcon: ({ focused, color, size }) => {
          let iconName: string;

          switch (route.name) {
            case 'Inbox':
              iconName = focused ? 'mail' : 'mail-outline';
              break;
            case 'Trips':
              iconName = focused ? 'list' : 'list-outline';
              break;
            case 'Customers':
              iconName = focused ? 'people' : 'people-outline';
              break;
            case 'Messages':
              iconName = focused ? 'chatbubbles' : 'chatbubbles-outline';
              break;
            case 'Settings':
              iconName = focused ? 'settings' : 'settings-outline';
              break;
          }

          return <Ionicons name={iconName} size={size} color={color} />;
        },
        tabBarActiveTintColor: '#007AFF',
        tabBarInactiveTintColor: '#8E8E93',
        tabBarStyle: {
          borderTopColor: '#C6C6C8',
          borderTopWidth: 1,
          height: 56,
          paddingBottom: 8,
          paddingTop: 8
        },
        tabBarLabelStyle: {
          fontSize: 12,
          fontWeight: '500'
        },
        headerShown: false
      })}
    >
      <Tab.Screen
        name="Inbox"
        component={InboxStack}
        options={{
          tabBarBadge: getUnreadCount() > 0 ? getUnreadCount() : undefined
        }}
      />
      <Tab.Screen name="Trips" component={TripsStack} />
      <Tab.Screen name="Customers" component={CustomersStack} />
      <Tab.Screen
        name="Messages"
        component={MessagesStack}
        options={{
          tabBarBadge: getUnreadMessageCount() > 0 ? getUnreadMessageCount() : undefined
        }}
      />
      <Tab.Screen name="Settings" component={SettingsStack} />
    </Tab.Navigator>
  );
}

/**
 * Stack navigator for each tab
 */
function TripsStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: {
          backgroundColor: '#007AFF'
        },
        headerTintColor: '#fff',
        headerTitleStyle: {
          fontWeight: '600'
        },
        cardStyle: {
          backgroundColor: '#F2F2F7'
        }
      }}
    >
      <Stack.Screen
        name="TripList"
        component={TripListScreen}
        options={{ title: 'Trips' }}
      />
      <Stack.Screen
        name="TripDetail"
        component={TripDetailScreen}
        options={({ route }) => ({
          title: route.params?.customerName || 'Trip Details',
          headerRight: () => <HeaderActions tripId={route.params?.tripId} />
        })}
      />
      <Stack.Screen
        name="Timeline"
        component={TimelineScreen}
        options={{ title: 'Timeline' }}
      />
    </Stack.Navigator>
  );
}

function getUnreadCount(): number {
  // Get from Redux store
  return 3;
}

function getUnreadMessageCount(): number {
  // Get from Redux store
  return 5;
}
```

---

## Screen Layouts

### Inbox Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          INBOX SCREEN                                     │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Trips                              ────────────────  Filter       │    │
│  │  ═══════════════════════════════════════════════════════════════   │    │
│  │  Search trips...                                         🔍           │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  Status Filter: [All] [Pending] [Confirmed] [Completed]             │    │
│  │  Sort by: [Recent ▼]                                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐   │  │    │
│  │  │  │ Goa Weekend Trip                          Mar 15-18    │   │  │    │
│  │  │  │ ─────────────────────────────────────────────────────── │   │  │    │
│  │  │  │  👤 John & Jane Doe                           🟢 Confirmed│   │  │    │
│  │  │  │  📅 3 Nights • 2 Adults                       ₹45,000    │   │  │    │
│  │  │  │  💬 Last: "Thanks for the quick response!"   2h ago    │   │  │    │
│  │  │  │                                                          │   │  │    │
│  │  │  │  [Timeline] [Messages] [Documents]                    │   │  │    │
│  │  │  └─────────────────────────────────────────────────────────┘   │  │    │
│  │  │                                                          │   │  │    │
│  │  │  ← Swipe left to archive, right to reply                 │   │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │  ┌─────────────────────────────────────────────────────────┐   │  │    │
│  │  │  │ Kerala Family Trip                         Mar 20-27    │   │  │    │
│  │  │  │ ─────────────────────────────────────────────────────── │   │  │    │
│  │  │  │  👤 Sharma Family                           🟡 Pending  │   │  │    │
│  │  │  │  📅 7 Nights • 4 Adults                       ₹1,25,000  │   │  │    │
│  │  │  │  💬 Last: "Is the itinerary finalized?"          1d ago    │   │  │    │
│  │  │  │                                                          │   │  │    │
│  │  │  │  [Timeline] [Messages] [Documents]                    │   │  │    │
│  │  │  └─────────────────────────────────────────────────────────┘   │  │    │
│  │  │                                                          │   │  │    │
│  │  │  ← Swipe left to archive, right to reply                 │   │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  🔄 Offline: Last synced 5 min ago                                │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ═══════════════════════════════════════════════════════════════════════   │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐       │
│  │  📬     │  │  📋     │  │  👥     │  │  💬     │  │  ⚙️     │       │
│  │  Inbox   │  │ Trips   │  │Customers│  │Messages │  │Settings │       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Trip Detail Screen

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TRIP DETAIL SCREEN                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ← Goa Weekend Trip                  ⋯ More            ✎ Edit     │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │  Status: 🟢 Confirmed                                          │  │    │
│  │  │  ─────────────────────────────────────────────────────────────  │  │    │
│  │  │  📅 March 15-18, 2024 (3 Nights)                              │  │    │
│  │  │  👤 2 Adults • 1 Child                                         │  │    │
│  │  │  💰 Budget: ₹50,000 • Spent: ₹45,000                           │  │    │
│  │  │  💬 Last message: "Thanks for the quick response!"              │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  │                                                                     │    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │  BOOKING SUMMARY                                                │  │    │
│  │  │  ┌────────────────────────────────────────────────────────────┐ │  │    │
│  │  │  │ Hotel: Taj Resort Goa                     3 Nights   ₹24K│ │  │    │
│  │  │  │ 🏨  ✓ Booked                                        │ │  │    │
│  │  │  ├────────────────────────────────────────────────────────────┤ │  │    │
│  │  │  │ Flight: Indigo 6E-234                       Round trip  ₹12K│ │  │    │
│  │  │  │ ✈️  ✓ Booked                                        │ │  │    │
│  │  │  ├────────────────────────────────────────────────────────────┤ │  │    │
│  │  │  │ Activities: Dudhsagar Waterfall, Old Goa Tour     1 Day   │ │  │    │
│  │  │  │ 🎯  Pending                                         │ │  │    │
│  │  │  └────────────────────────────────────────────────────────────┘ │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  TIMELINE              BOOKINGS              MESSAGES                 │    │
│  ═══════════════════════════════════════════════════════════════════════   │    │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────────────────────────────────────────────────────────────┐  │    │
│  │  │ Mar 10  ──────────────────────────────────────────────────     │  │    │
│  │  │  👤 Inquiry: "Planning a Goa trip for 2..."             🟢     │  │    │
│  │  │  ✉️ Auto-response: "Thanks! We'll get back..."          🟢     │  │    │
│  │  │                                                          │  │    │
│  │  │  Mar 11  ──────────────────────────────────────────────────     │  │    │
│  │  │  👤 Quote sent: "Here's a great itinerary..."        🟢     │  │    │
│  │  │  👤 Customer: "Looks good! Can we add..."              🟢     │  │    │
│  │  │                                                          │  │    │
│  │  │  Mar 12  ──────────────────────────────────────────────────     │  │    │
│  │  │  💰 Payment received: ₹45,000                        🟢     │  │    │
│  │  │  ✅ Booking confirmed                                  🟢     │  │    │
│  │  │                                                          │  │    │
│  │  └─────────────────────────────────────────────────────────────────┘  │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐    │
│  │  ┌─────────┐  ┌─────────┐  ┌─────────┐                               │    │
│  │  │   📞    │  │   💬    │  │   ✉️    │  Quick Actions                │    │
│  │  │  Call    │  │ Message │  │  Email   │                               │    │
│  │  └─────────┘  └─────────┘  └─────────┘                               │    │
│  └─────────────────────────────────────────────────────────────────────┘    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Platform Conventions

### iOS vs Android Design

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    iOS VS ANDROID DESIGN CONVENTIONS                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  NAVIGATION                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  iOS                          Android                              │   │
│  │  ───────────────────────────────────────────────────────────────   │   │
│  │  • Back button in nav bar     • Back button in action bar        │   │
│  │    (left)                      (left) or system back              │   │
│  │  • Swipe back gesture        • System back button + gesture     │   │
│  │  • Bottom tab navigation     • Bottom navigation + top/bottom   │   │
│  │  • Modal sheets (bottom)     • Bottom sheets / dialogs         │   │
│  │  • Page control dots         • Viewpager/Indicator            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  ACTIONS                                                                    │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  iOS                          Android                              │   │
│  │  ───────────────────────────────────────────────────────────────   │   │
│  │  • Action button (top right)  • FAB (bottom right)               │   │
│  │  • Edit button (top right)   • Overflow menu (top right)       │   │
│  │  • Context menu (long press)  • Context menu (long press)       │   │
│  │  • Swipe actions              • Swipe actions                    │   │
│  │  • Pull to refresh            • Pull to refresh + swipe down     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  COMPONENTS                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  iOS                          Android                              │   │
│  │  ───────────────────────────────────────────────────────────────   │   │
│  │  • Segmented Control         • Tabs / Material Tabs           │   │
│  │  • Switch                    • Switch                           │   │
│  │  • Picker (wheel)             • Dropdown / Spinner              │   │
│  │  • Action Sheet              • Bottom Sheet                     │   │
│  │  • Alert Dialog              • AlertDialog                     │   │
│  │  • Navigation Bar            • Top App Bar + Toolbar           │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  TYPOGRAPHY                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  iOS                          Android                              │   │
│  │  ───────────────────────────────────────────────────────────────   │   │
│  │  • San Francisco              • Roboto                          │   │
│  │  • SF Pro Display            • System font (San Francisco on     │   │
│  │  • Dynamic Type               •  some Androids)                  │   │
│  │  • Text styles (Title, Body     • Text styles (H1-H6, Body,     │   │
│  │    etc.)                      •  Caption, Overline)            │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Platform-Specific Components

```typescript
/**
 * Platform-specific component wrapper
 */
import { Platform } from 'react-native';

/**
 * Platform-aware button component
 */
export const PlatformButton: React.FC<ButtonProps> = (props) => {
  if (Platform.OS === 'ios') {
    return <IOSButton {...props} />;
  }
  return <AndroidButton {...props} />;
};

/**
 * iOS-style button
 */
const IOSButton: React.FC<ButtonProps> = ({ title, onPress, variant = 'primary' }) => {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.iosButton,
        variant === 'primary' ? styles.iosButtonPrimary : styles.iosButtonSecondary
      ]}
      activeOpacity={0.7}
    >
      <Text style={[
        styles.iosButtonText,
        variant === 'primary' ? styles.iosButtonTextPrimary : styles.iosButtonTextSecondary
      ]}>
        {title}
      </Text>
    </TouchableOpacity>
  );
};

/**
 * Android-style button (Material Design)
 */
const AndroidButton: React.FC<ButtonProps> = ({ title, onPress, variant = 'primary' }) => {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={[
        styles.androidButton,
        variant === 'primary' ? styles.androidButtonPrimary : styles.androidButtonSecondary
      ]}
    >
      <Text
        style={[
          styles.androidButtonText,
          variant === 'primary' ? styles.androidButtonTextPrimary : styles.androidButtonTextSecondary
        ]}
        uppercase={false}
      >
        {title}
      </Text>
    </TouchableOpacity>
  );
};

/**
 * Platform-aware segmented control
 */
export const PlatformSegmentedControl: React.FC<SegmentedControlProps> = ({
  segments,
  selectedSegment,
  onSegmentChange
}) => {
  if (Platform.OS === 'ios') {
    return (
      <SegmentedControl
        values={segments.map(s => s.label)}
        selectedIndex={selectedSegment}
        onChange={(event) => {
          onSegmentChange(event.nativeEvent.selectedSegmentIndex);
        }}
        style={styles.iosSegmentedControl}
        tintColor="#007AFF"
      />
    );
  }

  return (
    <View style={styles.androidSegmentedControl}>
      {segments.map((segment, index) => (
        <TouchableOpacity
          key={index}
          style={[
            styles.androidSegment,
            selectedSegment === index && styles.androidSegmentSelected
          ]}
          onPress={() => onSegmentChange(index)}
        >
          <Text
            style={[
              styles.androidSegmentText,
              selectedSegment === index && styles.androidSegmentTextSelected
            ]}
          >
            {segment.label}
          </Text>
        </TouchableOpacity>
      ))}
    </View>
  );
};

const styles = StyleSheet.create({
  // iOS Button Styles
  iosButton: {
    height: 44,
    borderRadius: 8,
    justifyContent: 'center',
    alignItems: 'center'
  },
  iosButtonPrimary: {
    backgroundColor: '#007AFF'
  },
  iosButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#007AFF'
  },
  iosButtonText: {
    fontSize: 17,
    fontWeight: '600'
  },
  iosButtonTextPrimary: {
    color: '#fff'
  },
  iosButtonTextSecondary: {
    color: '#007AFF'
  },

  // Android Button Styles
  androidButton: {
    height: 48,
    borderRadius: 4,
    justifyContent: 'center',
    alignItems: 'center',
    elevation: 2
  },
  androidButtonPrimary: {
    backgroundColor: '#6200EE'
  },
  androidButtonSecondary: {
    backgroundColor: 'transparent',
    borderWidth: 1,
    borderColor: '#6200EE'
  },
  androidButtonText: {
    fontSize: 14,
    fontWeight: '500',
    letterSpacing: 0.75
  },
  androidButtonTextPrimary: {
    color: '#fff'
  },
  androidButtonTextSecondary: {
    color: '#6200EE'
  },

  // iOS Segmented Control
  iosSegmentedControl: {
    height: 32
  },

  // Android Segmented Control
  androidSegmentedControl: {
    flexDirection: 'row',
    borderRadius: 4,
    backgroundColor: '#E0E0E0',
    overflow: 'hidden'
  },
  androidSegment: {
    flex: 1,
    paddingVertical: 12,
    paddingHorizontal: 16,
    justifyContent: 'center',
    alignItems: 'center'
  },
  androidSegmentSelected: {
    backgroundColor: '#6200EE'
  },
  androidSegmentText: {
    fontSize: 14,
    fontWeight: '500',
    color: '#666'
  },
  androidSegmentTextSelected: {
    color: '#fff'
  }
});
```

---

## Accessibility

### Accessibility Checklist

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      ACCESSIBILITY CHECKLIST                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  VISUAL                                                                     │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Minimum touch target size (44x44pt iOS, 48x48dp Android)         │   │
│  │  ☐ Color contrast ratio 4.5:1 for normal text                      │   │
│  │  ☐ Color contrast ratio 3:1 for large text (18pt+)                  │   │
│  │  ☐ Don't rely on color alone to convey information                  │   │
│  │  ☐ Support Dynamic Type (text scaling)                             │   │
│  │  ☐ Support dark mode                                              │   │
│  │  ☐ Avoid flashing content (>3 flashes/second)                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  NAVIGATION                                                                 │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ All elements accessible via screen reader                       │   │
│  │  ☐ Logical tab order                                              │   │
│  │  ☐ Focus indicators visible                                        │   │
│  │  ☐ Skip navigation links (for multiple items)                     │   │
│  │  ☐ Heading hierarchy (h1, h2, h3...)                               │   │
│  │  ☐ Landmarks for main regions                                     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  INTERACTIONS                                                               │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Touch targets have 8pt+ spacing                                 │   │
│  │  ☐ Minimum 44x44pt touch target size                               │   │
│  │  ☐ Actionable elements have accessible labels                      │   │
│  │  ☐ Button roles clearly defined                                    │   │
│  │  ☐ State announcements (toggle switches, etc.)                      │   │
│  │  ☐ Error messages accessible to screen reader                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
│  MEDIA                                                                      │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ☐ Images have alt text                                             │   │
│  │  ☐ Video content has captions                                       │   │
│  │  ☐ Audio content has transcripts                                    │   │
│  │  ☐ Video doesn't auto-play                                         │   │
│  │  ☐ Animation can be disabled (prefers-reduced-motion)              │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Accessible Components

```typescript
/**
 * Accessible components
 */
import { AccessibilityInfo, Platform } from 'react-native';

/**
 * Accessible button with proper accessibility props
 */
interface AccessibleButtonProps {
  title: string;
  onPress: () => void;
  variant?: 'primary' | 'secondary' | 'text';
  disabled?: boolean;
  accessibilityLabel?: string;
  accessibilityHint?: string;
  icon?: string;
}

export const AccessibleButton: React.FC<AccessibleButtonProps> = ({
  title,
  onPress,
  variant = 'primary',
  disabled = false,
  accessibilityLabel,
  accessibilityHint,
  icon
}) => {
  const [isScreenReaderEnabled, setIsScreenReaderEnabled] = React.useState(false);

  React.useEffect(() => {
    AccessibilityInfo.isScreenReaderEnabled().then(setIsScreenReaderEnabled);
  }, []);

  return (
    <TouchableOpacity
      onPress={onPress}
      disabled={disabled}
      accessibilityRole="button"
      accessibilityLabel={accessibilityLabel || title}
      accessibilityHint={accessibilityHint}
      accessibilityState={{ disabled: disabled ? ['disabled'] : [] }}
      style={[styles.button, styles[variant], disabled && styles.disabled]}
    >
      {icon && <Text style={styles.icon}>{icon}</Text>}
      <Text
        style={[styles.text, styles[`${variant}Text`]]}
        accessibilityElementsHidden={isScreenReaderEnabled && !!accessibilityLabel}
      >
        {title}
      </Text>
    </TouchableOpacity>
  );
};

/**
 * Accessible trip card
 */
interface AccessibleTripCardProps {
  trip: Trip;
  onPress: () => void;
  onLongPress?: () => void;
}

export const AccessibleTripCard: React.FC<AccessibleTripCardProps> = ({
  trip,
  onPress,
  onLongPress
}) => {
  const statusText = trip.status === 'confirmed'
    ? 'Confirmed'
    : trip.status === 'pending'
    ? 'Pending'
    : 'Completed';

  return (
    <TouchableOpacity
      onPress={onPress}
      onLongPress={onLongPress}
      accessible={true}
      accessibilityRole="button"
      accessibilityLabel={`${trip.destination} trip from ${trip.startDate} to ${trip.endDate}. Status: ${statusText}. Amount: ${trip.amount}. Double tap to view details.`}
      accessibilityHint="Double tap to open trip details"
      style={styles.card}
    >
      <View style={styles.cardContent}>
        <View accessibilityRole="text" style={styles.header}>
          <Text style={styles.destination}>{trip.destination}</Text>
          <View
            style={styles.status}
            accessibilityLabel={`Status: ${statusText}`}
          >
            <Text style={styles.statusText}>{statusText}</Text>
          </View>
        </View>

        <View style={styles.details} accessibilityRole="text">
          <Text style={styles.dates}>
            {formatDate(trip.startDate)} - {formatDate(trip.endDate)}
          </Text>
          <Text style={styles.amount}>{formatCurrency(trip.amount)}</Text>
        </View>

        {trip.lastMessage && (
          <View style={styles.message} accessibilityRole="text">
            <Text style={styles.messageText} numberOfLines={1}>
              💬 {trip.lastMessage.text}
            </Text>
            <Text style={styles.messageTime}>
              {formatRelativeTime(trip.lastMessage.timestamp)}
            </Text>
          </View>
        )}
      </View>
    </TouchableOpacity>
  );
};

/**
 * Accessibility utilities
 */
export const AccessibilityUtils = {
  /**
   * Announce message to screen reader
   */
  announce(message: string): void {
    if (Platform.OS === 'ios') {
      AccessibilityInfo.announceForAccessibility(message);
    } else {
      // Android uses different approach
      AccessibilityInfo.announceForAccessibility(message);
    }
  },

  /**
   * Check if reduce motion is preferred
   */
  isReduceMotionEnabled(): Promise<boolean> {
    return AccessibilityInfo.isReduceMotionEnabled();
  },

  /**
   * Check if screen reader is enabled
   */
  isScreenReaderEnabled(): Promise<boolean> {
    return AccessibilityInfo.isScreenReaderEnabled();
  },

  /**
   * Focus an element programmatically
   */
  focus(elementRef: React.RefObject<any>): void {
    // Focus the element for screen reader
  }
};
```

---

## Component Library

### Design Tokens

```typescript
/**
 * Design tokens for mobile app
 */
export const Colors = {
  // Primary brand colors
  primary: '#007AFF',
  primaryDark: '#0051D5',
  primaryLight: '#3395FF',

  // Semantic colors
  success: '#34C759',
  warning: '#FF9500',
  error: '#FF3B30',
  info: '#5AC8FA',

  // Neutral colors
  text: {
    primary: '#000000',
    secondary: '#666666',
    tertiary: '#999999',
    inverse: '#FFFFFF'
  },

  // Background colors
  background: {
    primary: '#FFFFFF',
    secondary: '#F2F2F7',
    tertiary: '#E5E5EA',
    elevated: '#FFFFFF'
  },

  // Status colors
  status: {
    pending: '#FF9500',
    confirmed: '#34C759',
    completed: '#5AC8FA',
    cancelled: '#8E8E93',
    failed: '#FF3B30'
  }
};

export const Spacing = {
  xs: 4,
  sm: 8,
  md: 16,
  lg: 24,
  xl: 32,
  xxl: 48
};

export const Typography = {
  // Large title (iOS)
  largeTitle: {
    fontSize: 34,
    fontWeight: '700' as const,
    lineHeight: 41
  },

  // Title 1 (iOS)
  title1: {
    fontSize: 28,
    fontWeight: '700' as const,
    lineHeight: 34
  },

  // Title 2 (iOS)
  title2: {
    fontSize: 22,
    fontWeight: '700' as const,
    lineHeight: 28
  },

  // Title 3 (iOS)
  title3: {
    fontSize: 20,
    fontWeight: '600' as const,
    lineHeight: 25
  },

  // Headline
  headline: {
    fontSize: 17,
    fontWeight: '600' as const,
    lineHeight: 22
  },

  // Body
  body: {
    fontSize: 17,
    fontWeight: '400' as const,
    lineHeight: 22
  },

  // Callout
  callout: {
    fontSize: 16,
    fontWeight: '400' as const,
    lineHeight: 21
  },

  // Subhead
  subhead: {
    fontSize: 15,
    fontWeight: '400' as const,
    lineHeight: 20
  },

  // Footnote
  footnote: {
    fontSize: 13,
    fontWeight: '400' as const,
    lineHeight: 18
  },

  // Caption 1
  caption1: {
    fontSize: 12,
    fontWeight: '400' as const,
    lineHeight: 16
  },

  // Caption 2
  caption2: {
    fontSize: 11,
    fontWeight: '400' as const,
    lineHeight: 13
  }
};

export const BorderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999
};

export const Shadows = {
  sm: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1
  },
  md: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 2
  },
  lg: {
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15,
    shadowRadius: 8,
    elevation: 4
  }
};
```

### Reusable Components

```typescript
/**
 * Trip card component
 */
interface TripCardProps {
  trip: Trip;
  onPress: () => void;
  onLongPress?: () => void;
  style?: any;
}

export const TripCard: React.FC<TripCardProps> = React.memo(({
  trip,
  onPress,
  onLongPress,
  style
}) => {
  const theme = useTheme();

  return (
    <TouchableOpacity
      style={[styles.card, { backgroundColor: theme.colors.background.elevated }, style]}
      onPress={onPress}
      onLongPress={onLongPress}
      activeOpacity={0.7}
    >
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.destination} numberOfLines={1}>
          {trip.destination}
        </Text>
        <StatusBadge status={trip.status} />
      </View>

      {/* Dates */}
      <Text style={styles.dates}>
        {formatDateRange(trip.startDate, trip.endDate)}
      </Text>

      {/* Customer info */}
      <View style={styles.customer}>
        <Avatar
          uri={trip.customer.avatar}
          name={trip.customer.name}
          size="small"
        />
        <Text style={styles.customerName} numberOfLines={1}>
          {trip.customer.name}
        </Text>
      </View>

      {/* Amount */}
      <Text style={styles.amount}>
        {formatCurrency(trip.amount)}
      </Text>

      {/* Last message */}
      {trip.lastMessage && (
        <View style={styles.messagePreview}>
          <Text style={styles.messageText} numberOfLines={1}>
            💬 {trip.lastMessage.text}
          </Text>
          <Text style={styles.messageTime}>
            {formatRelativeTime(trip.lastMessage.timestamp)}
          </Text>
        </View>
      )}
    </TouchableOpacity>
  );
});

TripCard.displayName = 'TripCard';

/**
 * Status badge component
 */
interface StatusBadgeProps {
  status: TripStatus;
  size?: 'small' | 'medium' | 'large';
}

export const StatusBadge: React.FC<StatusBadgeProps> = ({ status, size = 'medium' }) => {
  const theme = useTheme();
  const config = STATUS_CONFIG[status];

  return (
    <View
      style={[
        styles.badge,
        { backgroundColor: config.color + '20' },
        styles[`badge_${size}`]
      ]}
    >
      <View style={[styles.badgeDot, { backgroundColor: config.color }]} />
      <Text style={[styles.badgeText, { color: config.color }, styles[`badgeText_${size}`]]}>
        {config.label}
      </Text>
    </View>
  );
};

const STATUS_CONFIG: Record<TripStatus, { label: string; color: string }> = {
  pending: { label: 'Pending', color: Colors.warning },
  confirmed: { label: 'Confirmed', color: Colors.success },
  completed: { label: 'Completed', color: Colors.info },
  cancelled: { label: 'Cancelled', color: Colors.text.secondary },
  failed: { label: 'Failed', color: Colors.error }
};

/**
 * Avatar component with fallback
 */
interface AvatarProps {
  uri?: string;
  name?: string;
  size?: 'tiny' | 'small' | 'medium' | 'large' | 'xlarge';
}

export const Avatar: React.FC<AvatarProps> = React.memo(({ uri, name, size = 'medium' }) => {
  const [imageError, setImageError] = React.useState(false);
  const initials = getInitials(name || '');

  const sizeValue = AVATAR_SIZES[size];

  return (
    <View style={[styles.avatar, { width: sizeValue, height: sizeValue, borderRadius: sizeValue / 2 }]}>
      {uri && !imageError ? (
        <Image
          source={{ uri }}
          style={styles.avatarImage}
          onError={() => setImageError(true)}
        />
      ) : (
        <View style={[styles.avatarFallback, { backgroundColor: getAvatarColor(name || '') }]}>
          <Text style={styles.avatarInitials}>{initials}</Text>
        </View>
      )}
    </View>
  );
});

const AVATAR_SIZES = {
  tiny: 24,
  small: 32,
  medium: 40,
  large: 48,
  xlarge: 64
};

function getInitials(name: string): string {
  return name
    .split(' ')
    .map(n => n[0])
    .join('')
    .toUpperCase()
    .substring(0, 2);
}

function getAvatarColor(name: string): string {
  const colors = ['#007AFF', '#34C759', '#FF9500', '#5AC8FA', '#FF3B30', '#5856D6'];
  let hash = 0;
  for (let i = 0; i < name.length; i++) {
    hash = name.charCodeAt(i) + ((hash << 5) - hash);
  }
  return colors[Math.abs(hash) % colors.length];
}

const styles = StyleSheet.create({
  card: {
    padding: 16,
    marginVertical: 8,
    marginHorizontal: 16,
    borderRadius: 12,
    ...Shadows.md
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 8
  },
  destination: {
    ...Typography.headline,
    flex: 1,
    marginRight: 8
  },
  dates: {
    ...Typography.subhead,
    color: Colors.text.secondary,
    marginBottom: 8
  },
  customer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 8
  },
  customerName: {
    ...Typography.body,
    marginLeft: 8,
    flex: 1
  },
  amount: {
    ...Typography.title3,
    color: Colors.primary,
    marginBottom: 8
  },
  messagePreview: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center'
  },
  messageText: {
    ...Typography.footnote,
    color: Colors.text.secondary,
    flex: 1,
    marginRight: 8
  },
  messageTime: {
    ...Typography.caption2,
    color: Colors.text.tertiary
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    alignSelf: 'flex-start',
    paddingVertical: 4,
    paddingHorizontal: 8,
    borderRadius: 12
  },
  badge_small: {
    paddingVertical: 2,
    paddingHorizontal: 6
  },
  badgeDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    marginRight: 4
  },
  badgeText: {
    ...Typography.caption1,
    fontWeight: '600'
  },
  badgeText_small: {
    fontSize: 10
  },
  avatar: {
    overflow: 'hidden',
    backgroundColor: '#E5E5EA'
  },
  avatarImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover'
  },
  avatarFallback: {
    width: '100%',
    height: '100%',
    justifyContent: 'center',
    alignItems: 'center'
  },
  avatarInitials: {
    ...Typography.title3,
    color: '#fff'
  }
});
```

---

## Summary

This document covers UX/UI design for the mobile app:

1. **Mobile-First Design Principles** — Thumb-friendly zones, touch-optimized, content-first
2. **Touch Interactions & Gestures** — Touch targets, supported gestures, gesture handlers
3. **Navigation Patterns** — Tab navigation, stack navigation, deep linking
4. **Screen Layouts** — Inbox screen, trip detail, component layouts
5. **Platform Conventions** — iOS vs Android differences, platform-specific components
6. **Accessibility** — Checklist, accessible components, screen reader support
7. **Component Library** — Design tokens, reusable components (TripCard, StatusBadge, Avatar)

**Key Design Principles:**

- Place primary actions in thumb-friendly bottom zone
- 44pt minimum touch target size (iOS), 48dp (Android)
- Platform-appropriate navigation and components
- Full accessibility support (VoiceOver, TalkBack)
- Offline status always visible
- Smooth animations and transitions

**Related Documents:**
- [Technical Deep Dive](./MOBILE_APP_01_TECHNICAL_DEEP_DIVE.md) — Architecture
- [Sync Deep Dive](./MOBILE_APP_03_SYNC_DEEP_DIVE.md) — Data synchronization
