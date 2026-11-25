import type { KeyboardEvent } from 'react';

export function handleHorizontalScrollKey(event: KeyboardEvent<HTMLElement>) {
  if (event.defaultPrevented || event.target !== event.currentTarget ||
      event.altKey || event.ctrlKey || event.metaKey || event.shiftKey) return;

  const region = event.currentTarget;
  if (region.scrollWidth <= region.clientWidth) return;
  if (event.key !== 'ArrowLeft' && event.key !== 'ArrowRight') return;

  event.preventDefault();
  const direction = event.key === 'ArrowLeft' ? -1 : 1;
  region.scrollBy({ left: direction * 48 });
}
