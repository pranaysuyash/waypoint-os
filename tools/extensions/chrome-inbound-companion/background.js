/**
 * background.js — Waypoint OS Companion service worker.
 *
 * Responsibilities:
 *  1. Context menu: "Send selection to Waypoint OS" on text selection
 *  2. Offline queue drain: alarm fires every 2 minutes; attempts to flush
 *     IndexedDB pending_syncs entries to the configured backend
 *  3. Network recovery: also drains on chrome.runtime.onStartup
 *
 * Offline queue schema (IndexedDB: waypoint_offline_queue / pending_syncs):
 *   { id: auto, payload: {}, queuedAt: ISO string, retries: number }
 *
 * A pending entry is removed on success. On failure, retries++ up to 5;
 * after 5 failures the entry is discarded and an error is logged.
 */

'use strict';

const DEFAULT_BACKEND_URL = 'http://localhost:8000';
const DB_NAME = 'waypoint_offline_queue';
const DB_VERSION = 1;
const STORE_NAME = 'pending_syncs';
const MAX_RETRIES = 5;
const ALARM_NAME = 'waypoint_queue_drain';
const ALARM_PERIOD_MINUTES = 2;

// ===========================================================================
// Context menu setup
// ===========================================================================
chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({
    id: 'waypoint-parse-selection',
    title: 'Send selection to Waypoint OS',
    contexts: ['selection'],
  });

  // Schedule recurring drain alarm
  chrome.alarms.get(ALARM_NAME, (existing) => {
    if (!existing) {
      chrome.alarms.create(ALARM_NAME, { periodInMinutes: ALARM_PERIOD_MINUTES });
    }
  });
});

chrome.contextMenus.onClicked.addListener((info, _tab) => {
  if (info.menuItemId === 'waypoint-parse-selection' && info.selectionText) {
    chrome.storage.local.set({ pendingSelection: info.selectionText }, () => {
      chrome.action.openPopup();
    });
  }
});

// ===========================================================================
// Alarm: periodic offline queue drain
// ===========================================================================
chrome.alarms.onAlarm.addListener((alarm) => {
  if (alarm.name === ALARM_NAME) {
    drainOfflineQueue();
  }
});

// Also drain on startup / install (handles reconnect after sleep)
chrome.runtime.onStartup.addListener(() => {
  drainOfflineQueue();
});

// ===========================================================================
// IndexedDB helpers
// ===========================================================================
function openDb() {
  return new Promise((resolve, reject) => {
    const req = indexedDB.open(DB_NAME, DB_VERSION);
    req.onupgradeneeded = (ev) => {
      const db = ev.target.result;
      if (!db.objectStoreNames.contains(STORE_NAME)) {
        db.createObjectStore(STORE_NAME, { keyPath: 'id', autoIncrement: true });
      }
    };
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => reject(req.error);
  });
}

function getAllPending(db) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).getAll();
    req.onsuccess = () => resolve(req.result || []);
    req.onerror = () => reject(req.error);
  });
}

function deleteEntry(db, id) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).delete(id);
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
}

function updateEntry(db, entry) {
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).put(entry);
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
}

// ===========================================================================
// Queue drain
// ===========================================================================
async function drainOfflineQueue() {
  let db;
  try {
    db = await openDb();
  } catch (err) {
    console.warn('[background] Could not open IndexedDB:', err);
    return;
  }

  const pending = await getAllPending(db).catch(() => []);
  if (pending.length === 0) return;

  console.log(`[background] Draining ${pending.length} offline queue entries`);

  // Load settings for this drain run
  const { backendUrl, authToken } = await new Promise((resolve) => {
    chrome.storage.sync.get(
      { backendUrl: DEFAULT_BACKEND_URL, authToken: '' },
      resolve
    );
  });

  const endpoint = `${backendUrl}/api/v1/inbound/parse`;
  const headers = { 'Content-Type': 'application/json' };
  if (authToken) {
    headers['Authorization'] = `Bearer ${authToken}`;
  }

  for (const entry of pending) {
    try {
      const response = await fetch(endpoint, {
        method: 'POST',
        headers,
        body: JSON.stringify(entry.payload),
        signal: AbortSignal.timeout(10000),
      });

      if (response.ok) {
        await deleteEntry(db, entry.id);
        console.log(`[background] Queue entry ${entry.id} synced and removed`);
      } else if (response.status === 401 || response.status === 403) {
        // Auth failure — don't retry, leave in queue and surface to user
        console.warn(`[background] Auth failed for entry ${entry.id} — token may be expired`);
        // Intentional: keep in queue so user can update token and retry
      } else {
        await bumpRetry(db, entry);
      }
    } catch (err) {
      // Network error — bump retry counter
      await bumpRetry(db, entry);
      console.warn(`[background] Failed to drain entry ${entry.id}:`, err.message);
    }
  }
}

async function bumpRetry(db, entry) {
  const updated = { ...entry, retries: (entry.retries || 0) + 1 };
  if (updated.retries > MAX_RETRIES) {
    console.warn(`[background] Entry ${entry.id} exceeded max retries — discarding`);
    await deleteEntry(db, entry.id);
  } else {
    await updateEntry(db, updated);
  }
}
