import React from 'react';
import ReactDOM from 'react-dom/client';
import { RouterProvider } from './router/RouterContext';
import { AuthProvider } from './app/AuthContext';
import { App } from './App';
import './styles/global.css';

const rootElement = document.getElementById('root');
if (!rootElement) {
  throw new Error('Failed to find root element');
}

ReactDOM.createRoot(rootElement).render(
  <React.StrictMode>
    <AuthProvider>
      <RouterProvider>
        <App />
      </RouterProvider>
    </AuthProvider>
  </React.StrictMode>
);
