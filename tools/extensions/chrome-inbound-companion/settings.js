/**
 * settings.js — Waypoint OS Chrome Companion settings page logic.
 *
 * Manages:
 * - Backend URL (chrome.storage.sync: 'backendUrl')
 * - JWT auth token (chrome.storage.sync: 'authToken')
 * - PII guard enabled toggle (chrome.storage.sync: 'piiGuardEnabled')
 *
 * Default backend: http://localhost:8000
 *
 * Security:
 * - Auth token is stored in chrome.storage.sync (encrypted at rest by the browser,
 *   synced across devices if the user is signed into Chrome).
 * - Token is never logged or sent to third parties.
 * - In-memory only during the settings page session; cleared on page close.
 */

const DEFAULT_BACKEND_URL = 'http://localhost:8000';

// ---------------------------------------------------------------------------
// DOM refs
// ---------------------------------------------------------------------------
const backendUrlInput = document.getElementById('backendUrl');
const authTokenInput = document.getElementById('authToken');
const toggleTokenBtn = document.getElementById('toggleToken');
const piiGuardCheckbox = document.getElementById('piiGuardEnabled');
const saveBtn = document.getElementById('saveBtn');
const resetBtn = document.getElementById('resetBtn');
const testBtn = document.getElementById('testBtn');
const savedBadge = document.getElementById('savedBadge');
const statusDot = document.getElementById('statusDot');
const statusText = document.getElementById('statusText');
const noTokenWarning = document.getElementById('noTokenWarning');

// ---------------------------------------------------------------------------
// Load saved settings on open
// ---------------------------------------------------------------------------
chrome.storage.sync.get(
  { backendUrl: DEFAULT_BACKEND_URL, authToken: '', piiGuardEnabled: true },
  (result) => {
    backendUrlInput.value = result.backendUrl || DEFAULT_BACKEND_URL;
    authTokenInput.value = result.authToken || '';
    piiGuardCheckbox.checked = result.piiGuardEnabled !== false;
    updateTokenWarning(result.authToken);
  }
);

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------
function updateTokenWarning(token) {
  if (!token || token.trim() === '') {
    noTokenWarning.classList.add('visible');
  } else {
    noTokenWarning.classList.remove('visible');
  }
}

function showSaved() {
  savedBadge.classList.add('visible');
  setTimeout(() => savedBadge.classList.remove('visible'), 2500);
}

function setConnectionStatus(state, message) {
  statusDot.className = `status-dot ${state}`;
  statusText.textContent = message;
}

// ---------------------------------------------------------------------------
// Token visibility toggle
// ---------------------------------------------------------------------------
toggleTokenBtn.addEventListener('click', () => {
  const isPassword = authTokenInput.type === 'password';
  authTokenInput.type = isPassword ? 'text' : 'password';
  toggleTokenBtn.textContent = isPassword ? '🙈' : '👁';
});

authTokenInput.addEventListener('input', () => {
  updateTokenWarning(authTokenInput.value);
});

// ---------------------------------------------------------------------------
// Test connection
// ---------------------------------------------------------------------------
testBtn.addEventListener('click', async () => {
  const url = backendUrlInput.value.trim() || DEFAULT_BACKEND_URL;
  setConnectionStatus('checking', 'Testing connection...');
  testBtn.disabled = true;

  try {
    const token = authTokenInput.value.trim();
    const headers = { 'Content-Type': 'application/json' };
    if (token) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const response = await fetch(`${url}/health`, {
      method: 'GET',
      headers,
      signal: AbortSignal.timeout(5000),
    });

    if (response.ok) {
      const data = await response.json().catch(() => ({}));
      setConnectionStatus('connected', `Connected ✓ — ${data.status || 'OK'}`);
    } else {
      setConnectionStatus('error', `HTTP ${response.status} — Check URL and token`);
    }
  } catch (err) {
    if (err.name === 'TimeoutError' || err.name === 'AbortError') {
      setConnectionStatus('error', 'Timeout — Backend unreachable');
    } else {
      setConnectionStatus('error', `Connection failed: ${err.message}`);
    }
  } finally {
    testBtn.disabled = false;
  }
});

// ---------------------------------------------------------------------------
// Save settings
// ---------------------------------------------------------------------------
saveBtn.addEventListener('click', () => {
  const backendUrl = backendUrlInput.value.trim() || DEFAULT_BACKEND_URL;
  const authToken = authTokenInput.value.trim();
  const piiGuardEnabled = piiGuardCheckbox.checked;

  chrome.storage.sync.set({ backendUrl, authToken, piiGuardEnabled }, () => {
    showSaved();
    updateTokenWarning(authToken);
  });
});

// ---------------------------------------------------------------------------
// Reset to defaults
// ---------------------------------------------------------------------------
resetBtn.addEventListener('click', () => {
  if (!confirm('Reset all settings to defaults? This will clear your auth token.')) return;

  const defaults = {
    backendUrl: DEFAULT_BACKEND_URL,
    authToken: '',
    piiGuardEnabled: true,
  };

  chrome.storage.sync.set(defaults, () => {
    backendUrlInput.value = defaults.backendUrl;
    authTokenInput.value = '';
    piiGuardCheckbox.checked = true;
    updateTokenWarning('');
    setConnectionStatus('', 'Not tested');
    showSaved();
  });
});
