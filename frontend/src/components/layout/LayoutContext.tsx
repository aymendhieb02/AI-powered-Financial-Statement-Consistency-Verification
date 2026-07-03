import { createContext, useContext, useState, type ReactNode } from 'react';

type LayoutContextValue = {
  sidebarCollapsed: boolean;
  setSidebarCollapsed: (value: boolean) => void;
  mobileNavOpen: boolean;
  setMobileNavOpen: (value: boolean) => void;
};

const LayoutContext = createContext<LayoutContextValue | null>(null);

export function LayoutProvider({ children }: { children: ReactNode }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);
  return (
    <LayoutContext.Provider value={{ sidebarCollapsed, setSidebarCollapsed, mobileNavOpen, setMobileNavOpen }}>
      {children}
    </LayoutContext.Provider>
  );
}

export function useLayout() {
  const ctx = useContext(LayoutContext);
  if (!ctx) throw new Error('useLayout must be used within LayoutProvider');
  return ctx;
}
