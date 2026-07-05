import type { ReactNode } from 'react';

export interface Tab {
  id: string;
  label: string;
  icon?: ReactNode;
  badge?: string | number;
}

interface TabsProps {
  tabs: Tab[];
  activeTab: string;
  onChange: (tabId: string) => void;
  children?: ReactNode;
}

export function Tabs({ tabs, activeTab, onChange }: TabsProps) {
  return (
    <div className="border-b border-gray-200">
      <nav className="-mb-px flex space-x-8" aria-label="Tabs">
        {tabs.map((tab) => {
          const isActive = tab.id === activeTab;
          return (
            <button
              key={tab.id}
              type="button"
              onClick={() => onChange(tab.id)}
              className={`
                flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm whitespace-nowrap
                ${
                  isActive
                    ? 'border-blue-500 text-blue-600'
                    : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                }
                transition-colors duration-200
              `}
              aria-current={isActive ? 'page' : undefined}
            >
              {tab.icon && <span className="text-lg">{tab.icon}</span>}
              <span>{tab.label}</span>
              {tab.badge !== undefined && tab.badge !== null && tab.badge !== '' && (
                <span
                  className={`
                    ml-2 py-0.5 px-2 rounded-full text-xs font-medium
                    ${
                      isActive
                        ? 'bg-blue-100 text-blue-600'
                        : 'bg-gray-100 text-gray-600'
                    }
                  `}
                >
                  {tab.badge}
                </span>
              )}
            </button>
          );
        })}
      </nav>
    </div>
  );
}

interface TabPanelProps {
  id: string;
  activeTab: string;
  children: ReactNode;
}

export function TabPanel({ id, activeTab, children }: TabPanelProps) {
  if (id !== activeTab) {
    return null;
  }

  return (
    <div className="py-6" role="tabpanel">
      {children}
    </div>
  );
}
