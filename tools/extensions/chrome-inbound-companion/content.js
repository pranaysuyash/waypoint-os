// Content script for floating quick-ingest button on text selection
let floatingBtn = null;

function createFloatingButton() {
  if (floatingBtn) return;
  floatingBtn = document.createElement('div');
  floatingBtn.id = 'waypoint-quick-ingest-btn';
  floatingBtn.textContent = '✈ Sync to Waypoint';
  floatingBtn.style.position = 'absolute';
  floatingBtn.style.zIndex = '999999';
  floatingBtn.style.background = '#0F172A';
  floatingBtn.style.color = '#38BDF8';
  floatingBtn.style.padding = '6px 10px';
  floatingBtn.style.borderRadius = '6px';
  floatingBtn.style.fontSize = '12px';
  floatingBtn.style.fontWeight = 'bold';
  floatingBtn.style.border = '1px solid #38BDF8';
  floatingBtn.style.cursor = 'pointer';
  floatingBtn.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
  floatingBtn.style.display = 'none';

  floatingBtn.addEventListener('mousedown', (e) => {
    e.preventDefault();
    e.stopPropagation();
    const selText = window.getSelection().toString().trim();
    if (selText && chrome.storage && chrome.storage.local) {
      chrome.storage.local.set({ pendingSelection: selText }, () => {
        alert('Selection saved! Click Waypoint extension icon to complete sync.');
      });
    }
  });

  document.body.appendChild(floatingBtn);
}

document.addEventListener('mouseup', (e) => {
  const sel = window.getSelection();
  const text = sel ? sel.toString().trim() : '';

  if (text.length > 10) {
    createFloatingButton();
    const range = sel.getRangeAt(0);
    const rect = range.getBoundingClientRect();
    floatingBtn.style.left = `${rect.left + window.scrollX}px`;
    floatingBtn.style.top = `${rect.bottom + window.scrollY + 8}px`;
    floatingBtn.style.display = 'block';
  } else if (floatingBtn) {
    floatingBtn.style.display = 'none';
  }
});
