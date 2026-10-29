/* eslint-disable react-refresh/only-export-components */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { api } from '../utils/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  // ── Restore session on initial load or refresh ─────────────
  const verifySession = useCallback(async () => {
    try {
      const response = await api.get('/api/auth/me');
      if (response.ok) {
        const userData = await response.json();
        setUser(userData);
        setIsAuthenticated(true);
      } else {
        setUser(null);
        setIsAuthenticated(false);
      }
    } catch {
      setUser(null);
      setIsAuthenticated(false);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // ── Multi-tab synchronization via BroadcastChannel & storage events ──
  useEffect(() => {
    verifySession();

    let channel;
    if (typeof window !== 'undefined' && 'BroadcastChannel' in window) {
      channel = new BroadcastChannel('auth_channel');
      channel.onmessage = (event) => {
        if (event.data?.type === 'LOGOUT') {
          setUser(null);
          setIsAuthenticated(false);
        } else if (event.data?.type === 'LOGIN') {
          verifySession();
        }
      };
    }

    // Storage event fallback for older browsers
    const handleStorage = (e) => {
      if (e.key === 'auth_event') {
        const data = JSON.parse(e.newValue || '{}');
        if (data.type === 'LOGOUT') {
          setUser(null);
          setIsAuthenticated(false);
        } else if (data.type === 'LOGIN') {
          verifySession();
        }
      }
    };
    window.addEventListener('storage', handleStorage);

    // Global unauthorized event triggered by api client
    const handleUnauthorized = () => {
      setUser(null);
      setIsAuthenticated(false);
    };
    window.addEventListener('auth:unauthorized', handleUnauthorized);

    return () => {
      if (channel) channel.close();
      window.removeEventListener('storage', handleStorage);
      window.removeEventListener('auth:unauthorized', handleUnauthorized);
    };
  }, [verifySession]);

  // ── Broadcast auth state changes to other tabs ─────────────
  const broadcastAuthEvent = (type) => {
    if (typeof window !== 'undefined') {
      try {
        if ('BroadcastChannel' in window) {
          const channel = new BroadcastChannel('auth_channel');
          channel.postMessage({ type, timestamp: Date.now() });
          channel.close();
        }
        localStorage.setItem('auth_event', JSON.stringify({ type, timestamp: Date.now() }));
      } catch {
        // Broadcast non-fatal
      }
    }
  };

  // ── Login Method ───────────────────────────────────────────
  const login = async (email, password) => {
    const response = await api.post('/api/auth/login', { email, password });
    const data = await response.json();

    if (!response.ok) {
      throw new Error(data.detail || 'Login failed.');
    }

    setUser(data.user);
    setIsAuthenticated(true);
    broadcastAuthEvent('LOGIN');
    return data.user;
  };

  // ── Logout Method ──────────────────────────────────────────
  const logout = async () => {
    try {
      await api.post('/api/auth/logout', {});
    } catch {
      // Proceed with client cleanup regardless
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      broadcastAuthEvent('LOGOUT');
    }
  };

  // ── Logout All Devices Method ──────────────────────────────
  const logoutAll = async () => {
    try {
      await api.post('/api/auth/logout-all', {});
    } catch {
      // Proceed with client cleanup regardless
    } finally {
      setUser(null);
      setIsAuthenticated(false);
      broadcastAuthEvent('LOGOUT');
    }
  };

  // ── Refresh Current User ───────────────────────────────────
  const refreshUser = async () => {
    return verifySession();
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isAuthenticated,
        isLoading,
        login,
        logout,
        logoutAll,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
