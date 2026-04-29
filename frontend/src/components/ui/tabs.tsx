'use client';

import { cn } from '@/lib/utils';

interface TabsProps {
  tabs: readonly { readonly id: string; readonly label: string; count?: number }[];
  activeTab: string;
  onTabChange: (tabId: string) => void;
  ariaLabel?: string;
}

const TAB_ID_PREFIX = 'wt-tab';
const PANEL_ID_PREFIX = 'wt-panel';

export function getTabButtonId(tabId: string): string {
  return `${TAB_ID_PREFIX}-${tabId}`;
}

export function getTabPanelId(tabId: string): string {
  return `${PANEL_ID_PREFIX}-${tabId}`;
}

export function Tabs({ tabs, activeTab, onTabChange, ariaLabel = 'Tab navigation' }: TabsProps) {
  const handleKeyDown = (e: React.KeyboardEvent<HTMLDivElement>) => {
    const tabElements = Array.from(
      e.currentTarget.querySelectorAll('[role="tab"]')
    ) as HTMLButtonElement[];
    const currentIndex = tabElements.findIndex(
      (tab) => tab.getAttribute('aria-selected') === 'true'
    );
    if (currentIndex === -1) return;

    let nextIndex = currentIndex;
    switch (e.key) {
      case 'ArrowLeft':
        nextIndex = currentIndex > 0 ? currentIndex - 1 : tabElements.length - 1;
        break;
      case 'ArrowRight':
        nextIndex = currentIndex < tabElements.length - 1 ? currentIndex + 1 : 0;
        break;
      case 'Home':
        nextIndex = 0;
        break;
      case 'End':
        nextIndex = tabElements.length - 1;
        break;
      default:
        return;
    }
    e.preventDefault();
    tabElements[nextIndex].focus();
    onTabChange(tabs[nextIndex].id);
  };

  return (
    <div
      role='tablist'
      style={{ borderBottom: '1px solid var(--border-default)' }}
      aria-label={ariaLabel}
      onKeyDown={handleKeyDown}
    >
      <div className='flex overflow-x-auto'>
        {tabs.map((tab) => {
          const isActive = activeTab === tab.id;
          return (
            <button
              type='button'
              key={tab.id}
              role='tab'
              aria-selected={isActive}
              aria-controls={getTabPanelId(tab.id)}
              tabIndex={isActive ? 0 : -1}
              id={getTabButtonId(tab.id)}
              onClick={() => onTabChange(tab.id)}
              className={cn(
                'relative px-4 py-2.5 text-sm font-medium transition-colors outline-none shrink-0',
              )}
              style={
                isActive
                  ? { color: 'var(--text-primary)', background: 'var(--bg-elevated)' }
                  : { color: 'var(--text-muted)' }
              }
              onMouseEnter={(e) => {
                if (!isActive) e.currentTarget.style.color = 'var(--text-primary)';
              }}
              onMouseLeave={(e) => {
                if (!isActive) e.currentTarget.style.color = 'var(--text-muted)';
              }}
            >
              <div className='flex items-center gap-2'>
                {tab.label}
                {tab.count !== undefined && tab.count > 0 && (
                  <span
                    className='ml-1 px-1.5 py-0.5 text-xs rounded-sm font-mono'
                    style={{
                      background: 'var(--bg-count-badge)',
                      color: 'var(--text-muted)',
                    }}
                  >
                    {tab.count}
                  </span>
                )}
              </div>
              {isActive && (
                <div
                  className='absolute bottom-0 left-0 right-0 h-0.5'
                  style={{ background: 'var(--accent-blue)' }}
                />
              )}
            </button>
          );
        })}
      </div>
    </div>
  );
}
