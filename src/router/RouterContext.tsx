import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { getRouteEntityParams, matchRoute, PAGE_ROUTES, PageRouteConfig, RouteEntityParams } from './routes';

export interface ToastMessage {
  id: string;
  type: 'success' | 'info' | 'warning' | 'error';
  title: string;
  message?: string;
  duration?: number;
}

export interface RouterContextType {
  currentPath: string;
  currentRoute: PageRouteConfig;
  currentState: string | null;
  queryParams: URLSearchParams;
  entityParams: RouteEntityParams;
  navigate: (to: string, stateId?: string, params?: Record<string, string>) => void;
  openState: (stateId: string) => void;
  closeState: () => void;
  toasts: ToastMessage[];
  showToast: (title: string, type?: 'success' | 'info' | 'warning' | 'error', message?: string) => void;
  dismissToast: (id: string) => void;
}

const RouterContext = createContext<RouterContextType | null>(null);

export const RouterProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentPath, setCurrentPath] = useState<string>(() => window.location.pathname || '/today');
  const [queryParams, setQueryParams] = useState<URLSearchParams>(() => new URLSearchParams(window.location.search));
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const currentState = queryParams.get('state');
  const currentRoute = matchRoute(currentPath);
  const entityParams = getRouteEntityParams(currentPath);

  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || '/today');
      setQueryParams(new URLSearchParams(window.location.search));
    };

    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  const navigate = useCallback((to: string, stateId?: string, extraParams?: Record<string, string>) => {
    let targetPath = to;
    // If passed a page ID like 'P01'
    if (PAGE_ROUTES[to]) {
      targetPath = PAGE_ROUTES[to].path;
    }

    const url = new URL(window.location.origin + targetPath);
    if (stateId) {
      url.searchParams.set('state', stateId);
    }
    if (extraParams) {
      Object.entries(extraParams).forEach(([k, v]) => {
        url.searchParams.set(k, v);
      });
    }

    window.history.pushState({}, '', url.pathname + url.search);
    setCurrentPath(url.pathname);
    setQueryParams(url.searchParams);
    window.scrollTo(0, 0);
  }, []);

  const openState = useCallback((stateId: string) => {
    const url = new URL(window.location.href);
    url.searchParams.set('state', stateId);
    window.history.pushState({}, '', url.pathname + url.search);
    setQueryParams(url.searchParams);
  }, []);

  const closeState = useCallback(() => {
    const url = new URL(window.location.href);
    url.searchParams.delete('state');
    window.history.pushState({}, '', url.pathname + url.search);
    setQueryParams(url.searchParams);
  }, []);

  const showToast = useCallback((title: string, type: 'success' | 'info' | 'warning' | 'error' = 'success', message?: string) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, type, message }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 3500);
  }, []);

  const dismissToast = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  return (
    <RouterContext.Provider
      value={{
        currentPath,
        currentRoute,
        currentState,
        queryParams,
        entityParams,
        navigate,
        openState,
        closeState,
        toasts,
        showToast,
        dismissToast,
      }}
    >
      {children}
    </RouterContext.Provider>
  );
};

export function useRouter() {
  const context = useContext(RouterContext);
  if (!context) {
    throw new Error('useRouter must be used within RouterProvider');
  }
  return context;
}
