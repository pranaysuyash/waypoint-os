/**
 * popup.js — Waypoint OS Ingestion Companion popup logic.
 *
 * Features:
 *   1. Configurable backend URL (from chrome.storage.sync.backendUrl)
 *   2. JWT auth: reads authToken from storage, adds Authorization: Bearer header
 *   3. Offline queue: on network failure, queues to IndexedDB; background.js drains on recovery
 *   4. PII pre-scrubber: spawns pii-worker.js via Web Worker, shows amber/red banner,
 *      blocks Send for hard PII if user hasn't explicitly overridden
 *
 * Auth fallback: if authToken is empty, sends without auth (dev/localhost mode)
 *
 * Design principles:
 *   - Never fail silently: show concrete status for every outcome
 *   - Privacy-first: PII scan runs entirely client-side; no data sent externally
 *   - Offline-first: capture → queue → drain when reconnected
 */

'use strict';

const DEFAULT_BACKEND_URL = 'http://localhost:8000';

// ===========================================================================
// DOM refs (populated in DOMContentLoaded)
// ===========================================================================
let channelSelect, rawTextInput, customerNameInput, customerContactInput;
let parseBtn, statusPanel, stateTag, tripIdText, promptText;
let piiBanner, piiDetail, overridePiiBtn, offlineBadge, settingsLink;

// ===========================================================================
// State
// ===========================================================================
let settings = {
  backendUrl: DEFAULT_BACKEND_URL,
  authToken: '',
  piiGuardEnabled: true,
};

let piiHardBlock = false; // true = real PII found, requires explicit override
let piiOverridden = false; // user explicitly chose to send anyway

// ===========================================================================
// INIT
// ===========================================================================
document.addEventListener('DOMContentLoaded', async () => {
  channelSelect = document.getElementById('channel');
  rawTextInput = document.getElementById('rawText');
  customerNameInput = document.getElementById('customerName');
  customerContactInput = document.getElementById('customerContact');
  parseBtn = document.getElementById('parseBtn');
  statusPanel = document.getElementById('statusPanel');
  stateTag = document.getElementById('stateTag');
  tripIdText = document.getElementById('tripIdText');
  promptText = document.getElementById('promptText');
  piiBanner = document.getElementById('piiBanner');
  piiDetail = document.getElementById('piiDetail');
  overridePiiBtn = document.getElementById('overridePiiBtn');
  offlineBadge = document.getElementById('offlineBadge');
  settingsLink = document.getElementById('settingsLink');

  // Load settings from storage
  await loadSettings();

  // Wire settings link
  if (settingsLink) {
    settingsLink.addEventListener('click', () => {
      chrome.runtime.openOptionsPage();
    });
  }

  // Restore pending selection from context menu
  chrome.storage.local.get(['pendingSelection'], (result) => {
    if (result.pendingSelection && rawTextInput) {
      rawTextInput.value = result.pendingSelection;
      chrome.storage.local.remove(['pendingSelection']);
      triggerPiiScan(result.pendingSelection);
    }
  });

  // Auto-detect channel from active tab URL
  if (chrome.tabs) {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) return;
      const url = tabs[0].url || '';
      if (url.includes('web.whatsapp.com') && channelSelect) {
        channelSelect.value = 'whatsapp_web';
      } else if (url.includes('mail.google.com') && channelSelect) {
        channelSelect.value = 'email';
      }

      // Capture active selection
      chrome.scripting.executeScript(
        { target: { tabId: tabs[0].id }, func: () => window.getSelection().toString() },
        (results) => {
          if (results?.[0]?.result && rawTextInput) {
            rawTextInput.value = results[0].result;
            triggerPiiScan(results[0].result);
          }
        }
      );
    });
  }

  // Show offline queue badge
  refreshOfflineBadge();

  // PII override button
  if (overridePiiBtn) {
    overridePiiBtn.addEventListener('click', () => {
      piiOverridden = true;
      parseBtn.disabled = false;
      if (piiBanner) {
        piiBanner.className = 'pii-banner pii-amber';
        piiBanner.querySelector?.('.pii-banner-text').textContent =
          '⚠ PII override: sending data as-is. Review before submitting.';
      }
      overridePiiBtn.style.display = 'none';
    });
  }

  // Raw text PII scan on input
  if (rawTextInput) {
    rawTextInput.addEventListener('input', () => {
      const text = rawTextInput.value;
      if (text.length > 20) triggerPiiScan(text);
    });
  }

  // Parse/send button
  if (parseBtn) {
    parseBtn.addEventListener('click', handleSend);
  }
});

// ===========================================================================
// Settings
// ===========================================================================
async function loadSettings() {
  return new Promise((resolve) => {
    chrome.storage.sync.get(
      { backendUrl: DEFAULT_BACKEND_URL, authToken: '', piiGuardEnabled: true },
      (result) => {
        settings = {
          backendUrl: result.backendUrl || DEFAULT_BACKEND_URL,
          authToken: result.authToken || '',
          piiGuardEnabled: result.piiGuardEnabled !== false,
        };
        resolve();
      }
    );
  });
}

// ===========================================================================
// PII pre-scrubber (Web Worker)
// ===========================================================================
let piiWorker = null;

function getPiiWorker() {
  if (!piiWorker) {
    piiWorker = new Worker(chrome.runtime.getURL('pii-worker.js'));
    piiWorker.onmessage = handlePiiWorkerResult;
    piiWorker.onerror = (err) => {
      console.warn('[popup] PII worker error:', err);
      piiWorker = null; // reset so next call spawns fresh
    };
  }
  return piiWorker;
}

function triggerPiiScan(text) {
  if (!settings.piiGuardEnabled) return;
  if (!text || text.trim().length < 10) return;
  try {
    const worker = getPiiWorker();
    worker.postMessage({ type: 'SCAN', text });
  } catch (err) {
    console.warn('[popup] Could not spawn PII worker:', err);
  }
}

function handlePiiWorkerResult(event) {
  const { findings, severity } = event.data;
  piiHardBlock = severity === 'red';

  if (!piiBanner) return;

  if (findings.length === 0) {
    piiBanner.className = 'pii-banner pii-hidden';
    piiHardBlock = false;
    if (!piiOverridden) parseBtn.disabled = false;
    return;
  }

  piiBanner.className = `pii-banner pii-${severity}`;
  if (piiDetail) {
    piiDetail.textContent = findings.map((f) => `• ${f.label}: ${f.redacted}`).join('\n');
  }

  if (severity === 'red') {
    // Hard block — disable send unless override
    parseBtn.disabled = !piiOverridden;
    if (overridePiiBtn) overridePiiBtn.style.display = 'inline-block';
  } else {
    // Amber — warn but allow send
    parseBtn.disabled = false;
    if (overridePiiBtn) overridePiiBtn.style.display = 'none';
  }
}

// ===========================================================================
// SEND
// ===========================================================================
async function handleSend() {
  const rawText = rawTextInput?.value?.trim() || '';
  if (!rawText) {
    alert('Please enter or select inquiry text.');
    return;
  }

  parseBtn.disabled = true;
  parseBtn.textContent = 'Parsing & Syncing...';

  const payload = {
    channel: channelSelect?.value || 'manual',
    raw_text: rawText,
    customer_name: customerNameInput?.value?.trim() || undefined,
    customer_contact: customerContactInput?.value?.trim() || undefined,
    strict_leakage: false,
  };

  const headers = { 'Content-Type': 'application/json' };
  if (settings.authToken) {
    headers['Authorization'] = `Bearer ${settings.authToken}`;
  }

  const endpoint = `${settings.backendUrl}/api/v1/inbound/parse`;

  try {
    const response = await fetch(endpoint, {
      method: 'POST',
      headers,
      body: JSON.stringify(payload),
      signal: AbortSignal.timeout(15000),
    });

    if (response.status === 401 || response.status === 403) {
      showError(`Auth failed (${response.status}) — update your token in ⚙ Settings.`);
      return;
    }

    if (!response.ok) {
      throw new Error(`API returned HTTP ${response.status}`);
    }

    const data = await response.json();
    showSuccess(data);

  } catch (err) {
    const isOffline =
      err instanceof TypeError ||
      err.name === 'NetworkError' ||
      err.name === 'TimeoutError' ||
      err.name === 'AbortError';

    if (isOffline) {
      await enqueueOffline(payload);
      showOfflineQueued();
    } else {
      showError(err.message);
    }
  } finally {
    parseBtn.disabled = false;
    parseBtn.textContent = 'Ingest & Sync to Waypoint OS';
  }
}

// ===========================================================================
// SUCCESS / ERROR display
// ===========================================================================
function showSuccess(data) {
  if (!statusPanel) return;
  statusPanel.classList.add('active');
  if (stateTag) stateTag.textContent = `✓ STATE: ${data.decision_state}`;
  if (tripIdText) tripIdText.textContent = `Trip ID: ${data.trip_id}`;
  if (promptText) {
    promptText.textContent =
      data.draft_followup_prompt ||
      'Trip parsed successfully. Ready for strategy generation in Waypoint OS dashboard.';
  }
}

function showError(message) {
  if (statusPanel) statusPanel.classList.remove('active');
  alert(`Ingestion failed: ${message}`);
}

function showOfflineQueued() {
  if (statusPanel) {
    statusPanel.classList.add('active');
    if (stateTag) stateTag.textContent = '📥 QUEUED OFFLINE';
    if (tripIdText) tripIdText.textContent = 'Will sync when backend is reachable.';
    if (promptText) promptText.textContent = 'Your inquiry has been saved locally.';
  }
  refreshOfflineBadge();
}

// ===========================================================================
// OFFLINE QUEUE (IndexedDB)
// ===========================================================================
const DB_NAME = 'waypoint_offline_queue';
const DB_VERSION = 1;
const STORE_NAME = 'pending_syncs';

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

async function enqueueOffline(payload) {
  const db = await openDb();
  return new Promise((resolve, reject) => {
    const tx = db.transaction(STORE_NAME, 'readwrite');
    tx.objectStore(STORE_NAME).add({
      payload,
      queuedAt: new Date().toISOString(),
      retries: 0,
    });
    tx.oncomplete = resolve;
    tx.onerror = () => reject(tx.error);
  });
}

async function getOfflineQueueCount() {
  const db = await openDb();
  return new Promise((resolve) => {
    const tx = db.transaction(STORE_NAME, 'readonly');
    const req = tx.objectStore(STORE_NAME).count();
    req.onsuccess = () => resolve(req.result);
    req.onerror = () => resolve(0);
  });
}

async function refreshOfflineBadge() {
  if (!offlineBadge) return;
  try {
    const count = await getOfflineQueueCount();
    if (count > 0) {
      offlineBadge.textContent = `${count} pending`;
      offlineBadge.style.display = 'inline-block';
    } else {
      offlineBadge.style.display = 'none';
    }
  } catch {
    offlineBadge.style.display = 'none';
  }
}
