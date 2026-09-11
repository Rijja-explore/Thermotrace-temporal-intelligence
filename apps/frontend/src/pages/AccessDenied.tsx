import React from 'react';
import { ShieldAlert, ArrowLeft, Lock } from 'lucide-react';

interface AccessDeniedProps {
  requiredRoles: string[];
  userRole?: string;
  onNavigate?: (page: string, params?: any) => void;
}

export const AccessDenied: React.FC<AccessDeniedProps> = ({
  requiredRoles,
  userRole = 'GUEST',
  onNavigate,
}) => {
  const roleSlug = userRole.toLowerCase();
  const defaultHome = roleSlug === 'admin' ? '/admin' : roleSlug === 'official' ? '/official' : '/analyst';

  return (
    <div style={{
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      minHeight: '70vh',
      padding: '24px',
      color: 'var(--text-primary)',
    }}>
      <div style={{
        maxWidth: '560px',
        width: '100%',
        background: '#0B1321',
        border: '1px solid rgba(255, 92, 108, 0.35)',
        borderRadius: '12px',
        padding: '32px',
        boxShadow: '0 20px 40px rgba(0,0,0,0.6)',
        textAlign: 'center',
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '64px',
          height: '64px',
          borderRadius: '50%',
          background: 'rgba(255, 92, 108, 0.15)',
          border: '1px solid rgba(255, 92, 108, 0.4)',
          color: '#FF5C6C',
          marginBottom: '20px',
        }}>
          <ShieldAlert size={32} />
        </div>

        <div style={{
          fontSize: '11px',
          fontFamily: 'var(--font-mono)',
          fontWeight: 800,
          color: '#FF5C6C',
          letterSpacing: '1px',
          textTransform: 'uppercase',
          marginBottom: '8px',
        }}>
          HTTP 403 · ACCESS DENIED
        </div>

        <h1 style={{
          fontSize: '22px',
          fontWeight: 800,
          color: '#F8FAFC',
          marginBottom: '12px',
        }}>
          Insufficient Clearance Level
        </h1>

        <p style={{
          fontSize: '13px',
          color: '#94A3B8',
          lineHeight: 1.6,
          marginBottom: '20px',
        }}>
          You are authenticated with role <strong style={{ color: '#38BDF8' }}>{userRole.toUpperCase()}</strong>.
          This operational resource is strictly restricted to <strong style={{ color: '#FACC15' }}>{requiredRoles.join(' / ').toUpperCase()}</strong> clearance.
        </p>

        <div style={{
          padding: '12px 16px',
          background: 'rgba(15, 23, 42, 0.6)',
          border: '1px solid #1E293B',
          borderRadius: '8px',
          fontSize: '12px',
          color: '#64748B',
          textAlign: 'left',
          marginBottom: '24px',
          fontFamily: 'var(--font-mono)',
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', color: '#94A3B8', marginBottom: '4px' }}>
            <Lock size={12} />
            <span>RBAC Security Policy Guard:</span>
          </div>
          <div>• User Role: {userRole}</div>
          <div>• Required Role: {requiredRoles.join(', ')}</div>
          <div>• Enforcement: Application-Level Route Guard</div>
        </div>

        <div style={{ display: 'flex', gap: '10px', justifyContent: 'center' }}>
          <button
            onClick={() => onNavigate ? onNavigate(defaultHome) : (window.location.pathname = defaultHome)}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '8px',
              padding: '10px 20px',
              background: 'var(--accent-cyan)',
              color: '#0B1321',
              fontWeight: 700,
              fontSize: '12px',
              borderRadius: '6px',
              border: 'none',
              cursor: 'pointer',
              transition: 'all 0.15s ease',
            }}
          >
            <ArrowLeft size={14} />
            Return to {userRole.toUpperCase()} Center
          </button>
        </div>
      </div>
    </div>
  );
};

export default AccessDenied;
