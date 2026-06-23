'use client';

export async function safeWriteClipboardText(text: string): Promise<boolean> {
  if (!text) return false;

  try {
    if (typeof navigator !== 'undefined' && navigator.clipboard?.writeText) {
      let clipboardGranted = false;
      const permissions = navigator.permissions;
      if (permissions?.query) {
        try {
          const result = await permissions.query({ name: 'clipboard-write' as PermissionName });
          clipboardGranted = result.state === 'granted';
        } catch {
          // If permissions are unavailable, fall through to the fallback path below.
        }
      }

      if (clipboardGranted) {
        try {
          await navigator.clipboard.writeText(text);
          return true;
        } catch {
          // Fall back below.
        }
      }
    }
  } catch {
    // Fall back below.
  }

  try {
    if (typeof document === 'undefined') return false;

    const textarea = document.createElement('textarea');
    textarea.value = text;
    textarea.setAttribute('readonly', 'true');
    textarea.style.position = 'fixed';
    textarea.style.opacity = '0';
    textarea.style.pointerEvents = 'none';
    textarea.style.left = '-9999px';
    document.body.appendChild(textarea);
    textarea.select();
    textarea.setSelectionRange(0, textarea.value.length);

    const copied = document.execCommand('copy');
    document.body.removeChild(textarea);
    return copied;
  } catch {
    return false;
  }
}
