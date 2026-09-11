import React, { createContext, useContext, useState, useEffect } from 'react';
import { API_BASE } from './api';

export interface UserPersona {
  user_id: string;
  username: string;
  name: string;
  email: string;
  role: 'ADMIN' | 'ANALYST' | 'OFFICIAL' | string;
  badge: string;
  clearance_level: string;
  clearance_code: string;
  agency: string;
  station: string;
  permissions: string[];
  avatar_gradient: string;
  is_active: boolean;
  last_login?: string;
}

export interface AuditLogItem {
  timestamp: string;
  user_email: string;
  actor: string;
  role: string;
  action: string;
  ip: string;
  status: string;
  details: string;
}

interface AuthContextType {
  currentUser: UserPersona | null;
  authToken: string | null;
  isAuthenticated: boolean;
  loginWithCredentials: (emailOrUsername: string, password: string) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  hasRole: (roles: string[]) => boolean;
  auditLogs: AuditLogItem[];
  addAuditLog: (action: string, details: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'thermotrace_auth_token';
const USER_KEY = 'thermotrace_auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserPersona | null>(() => {
    try {
      const stored = localStorage.getItem(USER_KEY);
      return stored ? JSON.parse(stored) : null;
    } catch {
      return null;
    }
  });

  const [authToken, setAuthToken] = useState<string | null>(() => {
    return localStorage.getItem(TOKEN_KEY);
  });

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>([]);

  useEffect(() => {
    if (authToken) {
      // Fetch fresh audit logs from backend
      fetch(`${API_BASE}/api/auth/audit-logs`, {
        headers: { Authorization: `Bearer ${authToken}` },
      })
        .then((res) => res.json())
        .then((data) => {
          if (data && data.logs) {
            setAuditLogs(data.logs);
          }
        })
        .catch(() => {});
    }
  }, [authToken]);

  const loginWithCredentials = async (emailOrUsername: string, password: string) => {
    try {
      const res = await fetch(`${API_BASE}/api/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_or_username: emailOrUsername,
          password: password,
        }),
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        return {
          success: false,
          error: errData.detail || 'Authentication failed. Please check your credentials.',
        };
      }

      const session = await res.json();
      setCurrentUser(session.user);
      setAuthToken(session.token);

      localStorage.setItem(USER_KEY, JSON.stringify(session.user));
      localStorage.setItem(TOKEN_KEY, session.token);

      return { success: true };
    } catch (err: any) {
      return { success: false, error: err.message || 'Connection to authentication gateway failed.' };
    }
  };

  const logout = () => {
    if (authToken) {
      fetch(`${API_BASE}/api/auth/logout`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${authToken}` },
      }).catch(() => {});
    }
    setCurrentUser(null);
    setAuthToken(null);
    localStorage.removeItem(USER_KEY);
    localStorage.removeItem(TOKEN_KEY);
  };

  const hasPermission = (permission: string): boolean => {
    if (!currentUser) return false;
    if (currentUser.role === 'ADMIN' || currentUser.permissions.includes('*')) return true;
    return currentUser.permissions.includes(permission);
  };

  const hasRole = (roles: string[]): boolean => {
    if (!currentUser) return false;
    const userRole = currentUser.role.toUpperCase();
    return roles.map((r) => r.toUpperCase()).includes(userRole);
  };

  const addAuditLog = (action: string, details: string) => {
    const newLog: AuditLogItem = {
      timestamp: new Date().toISOString(),
      user_email: currentUser?.email || 'unauthenticated',
      actor: currentUser?.name || 'Anonymous',
      role: currentUser?.role || 'NONE',
      action,
      ip: 'Client Browser Console',
      status: 'RECORDED',
      details,
    };
    setAuditLogs((prev) => [newLog, ...prev]);
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        authToken,
        isAuthenticated: !!currentUser,
        loginWithCredentials,
        logout,
        hasPermission,
        hasRole,
        auditLogs,
        addAuditLog,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
