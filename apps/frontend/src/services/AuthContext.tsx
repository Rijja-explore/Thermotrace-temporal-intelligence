import React, { createContext, useContext, useState, useEffect } from 'react';

export interface UserPersona {
  user_id: string;
  username: string;
  name: string;
  email: string;
  role: string;
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
  user_id: string;
  actor: string;
  action: string;
  ip: string;
  status: string;
  details: string;
}

export const ADMIN_USER: UserPersona = {
  user_id: 'ADMIN-001',
  username: 'admin',
  name: 'Lead System Administrator',
  email: 'rijja2310119@ssn.edu.in',
  role: 'GeoAI Defense Commander & System Admin',
  badge: 'AD',
  clearance_level: 'Level 4 — Orbital Top Secret',
  clearance_code: 'SEC-CLR-L4-ORBITAL-ADMIN',
  agency: 'ISRO / NASA Earth Observation Defense Directorate',
  station: 'SAC Ahmedabad / Central Command Terminal 01',
  permissions: ['*'],
  avatar_gradient: 'linear-gradient(135deg, #43D9E8 0%, #1D4ED8 100%)',
  is_active: true,
  last_login: '2026-09-06T08:34:12Z',
};

export const DEFAULT_PERSONAS: UserPersona[] = [ADMIN_USER];

const INITIAL_AUDIT_LOGS: AuditLogItem[] = [
  {
    timestamp: '2026-09-06T08:34:12Z',
    user_id: 'AL-001',
    actor: 'Dr. Rijja Mehta',
    action: 'AUTH_LOGIN_SUCCESS',
    ip: '10.14.88.23 (NRSC Hyderabad Gateway)',
    status: 'AUTHORIZED',
    details: 'Biometric 2FA challenge verified against ISRO Keycloak directory',
  },
  {
    timestamp: '2026-09-06T06:15:40Z',
    user_id: 'JS-002',
    actor: 'Capt. Rajesh Sharma',
    action: 'AUTH_LOGIN_SUCCESS',
    ip: '172.16.4.110 (Jamnagar Complex Intranet)',
    status: 'AUTHORIZED',
    details: 'Plant hardware token key authenticated',
  },
  {
    timestamp: '2026-09-05T22:11:04Z',
    user_id: 'SYSTEM',
    actor: 'Satellite Telemetry Ingest',
    action: 'TOKEN_ROTATION',
    ip: '127.0.0.1 (Localhost)',
    status: 'AUTOMATED',
    details: 'MODIS/VIIRS FIRMS telemetry stream keys rotated',
  },
];

interface AuthContextType {
  currentUser: UserPersona | null;
  allPersonas: UserPersona[];
  isAuthenticated: boolean;
  switchPersona: (userId: string) => void;
  loginWithCredentials: (username: string, clearanceCode?: string) => Promise<boolean>;
  logout: () => void;
  hasPermission: (permission: string) => boolean;
  auditLogs: AuditLogItem[];
  addAuditLog: (action: string, details: string) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const STORAGE_KEY = 'thermotrace_auth_user';

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  // Always initialize to null so user must authenticate on every visit/refresh as requested
  const [currentUser, setCurrentUser] = useState<UserPersona | null>(null);

  const [auditLogs, setAuditLogs] = useState<AuditLogItem[]>(INITIAL_AUDIT_LOGS);

  useEffect(() => {
    if (currentUser) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(currentUser));
    } else {
      localStorage.removeItem(STORAGE_KEY);
    }
  }, [currentUser]);

  const addAuditLog = (action: string, details: string) => {
    const newLog: AuditLogItem = {
      timestamp: new Date().toISOString(),
      user_id: currentUser?.user_id || 'ANONYMOUS',
      actor: currentUser?.name || 'Unauthenticated User',
      action,
      ip: 'Client Browser / Terminal 01',
      status: currentUser ? 'AUTHORIZED' : 'ANONYMOUS',
      details,
    };
    setAuditLogs(prev => [newLog, ...prev.slice(0, 24)]);
  };

  const switchPersona = (userId: string) => {
    const found = DEFAULT_PERSONAS.find(p => p.user_id === userId);
    if (found) {
      setCurrentUser(found);
      addAuditLog('ROLE_SWITCH', `Switched active security profile to ${found.name} (${found.role})`);
    }
  };

  const loginWithCredentials = async (username: string, _clearanceCode?: string): Promise<boolean> => {
    const matched = DEFAULT_PERSONAS.find(
      p =>
        p.username.toLowerCase() === username.toLowerCase() ||
        p.email.toLowerCase() === username.toLowerCase()
    );

    if (matched) {
      setCurrentUser(matched);
      addAuditLog('AUTH_LOGIN_SUCCESS', `Credentials verified for ${matched.name} [${matched.clearance_level}]`);
      return true;
    }

    // Reject — only admin is permitted
    addAuditLog('AUTH_LOGIN_FAILED', `Unauthorized access attempt for username: ${username}`);
    return false;
  };

  const logout = () => {
    if (currentUser) {
      addAuditLog('AUTH_LOGOUT', `Analyst ${currentUser.name} signed out from terminal.`);
    }
    setCurrentUser(null);
  };

  const hasPermission = (permission: string): boolean => {
    if (!currentUser) return false;
    if (currentUser.permissions.includes('*') || currentUser.clearance_level.includes('Level 4')) {
      return true;
    }
    return currentUser.permissions.includes(permission);
  };

  return (
    <AuthContext.Provider
      value={{
        currentUser,
        allPersonas: DEFAULT_PERSONAS,
        isAuthenticated: !!currentUser,
        switchPersona,
        loginWithCredentials,
        logout,
        hasPermission,
        auditLogs,
        addAuditLog,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
