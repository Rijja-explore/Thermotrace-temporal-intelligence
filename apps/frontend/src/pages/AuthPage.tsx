import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';

interface AuthPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onNavigate }) => {
  const { loginWithCredentials } = useAuth();

  const [email, setEmail] = useState('analyst');
  const [password, setPassword] = useState('analyst');
  const [selectedRole, setSelectedRole] = useState<'ANALYST' | 'OFFICIAL' | 'ADMIN'>('ANALYST');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forgotMsg, setForgotMsg] = useState(false);

  const handleRoleSelect = (role: 'ANALYST' | 'OFFICIAL' | 'ADMIN') => {
    setSelectedRole(role);
    setError(null);
    setForgotMsg(false);
    if (role === 'ANALYST') {
      setEmail('analyst');
      setPassword('analyst');
    } else if (role === 'OFFICIAL') {
      setEmail('official');
      setPassword('official');
    } else if (role === 'ADMIN') {
      setEmail('admin');
      setPassword('admin');
    }
  };

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);
    setForgotMsg(false);

    const cleanEmail = email.trim();
    const cleanPassword = password.trim();

    if (!cleanEmail || !cleanPassword) {
      setError('Please enter both username/email and password.');
      return;
    }

    setIsSubmitting(true);
    const result = await loginWithCredentials(cleanEmail, cleanPassword);
    setIsSubmitting(false);

    if (result.success) {
      onNavigate('dashboard');
    } else {
      setError(result.error || 'Invalid credentials. Please verify your password.');
    }
  };

  return (
    <div className="auth-page">
      <div className="auth-page__ambient-grid" />
      <div className="auth-page__radar-ring auth-page__radar-ring--1" />
      <div className="auth-page__radar-ring auth-page__radar-ring--2" />

      <div className="auth-login-center">
        {/* Brand Header */}
        <div className="auth-login-brand">
          <svg width="48" height="48" viewBox="0 0 28 28" fill="none">
            <ellipse cx="14" cy="14" rx="12" ry="5" stroke="#43D9E8" strokeWidth="1.4" strokeDasharray="2 2" opacity="0.7" />
            <rect x="11" y="11" width="6" height="6" rx="1.5" fill="#43D9E8" opacity="0.9" />
            <rect x="5" y="12.5" width="5" height="3" rx="0.5" fill="#4D8DFF" opacity="0.7" />
            <rect x="18" y="12.5" width="5" height="3" rx="0.5" fill="#4D8DFF" opacity="0.7" />
            <circle cx="14" cy="22" r="2.5" fill="#FF7A45" opacity="0.85" />
            <circle cx="14" cy="22" r="1.2" fill="#FFB547" />
          </svg>
          <div>
            <div className="auth-login-brand__name">
              THERMO<span>TRACE</span>
            </div>
            <div className="auth-login-brand__sub" style={{ letterSpacing: '0.05em', color: '#94A3B8' }}>
              Industrial Thermal Intelligence · SIH26162
            </div>
          </div>
        </div>

        {/* Login Form Card */}
        <div className="auth-login-card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '14px' }}>
            <div>
              <div className="auth-login-card__title">Sign In</div>
              <div className="auth-login-card__sub" style={{ fontSize: '11.5px' }}>
                Operational Defense Clearance Gateway
              </div>
            </div>
            <div style={{
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid #38BDF8',
              borderRadius: '4px',
              padding: '3px 8px',
              fontSize: '10px',
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: '0.06em'
            }}>
              SIH DEMO MODE
            </div>
          </div>

          {/* 1-Click Operational Roles Header */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ fontSize: '11px', color: '#94A3B8', fontWeight: 700, marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.04em' }}>
              SELECT SIH DEMO ACCOUNT:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '8px' }}>
              {/* ANALYST */}
              <button
                type="button"
                onClick={() => handleRoleSelect('ANALYST')}
                style={{
                  padding: '10px 6px',
                  background: selectedRole === 'ANALYST' ? 'rgba(56, 189, 248, 0.2)' : '#0F172A',
                  border: `1.5px solid ${selectedRole === 'ANALYST' ? '#38BDF8' : '#1E293B'}`,
                  borderRadius: '6px',
                  color: selectedRole === 'ANALYST' ? '#38BDF8' : '#94A3B8',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.15s ease',
                  boxShadow: selectedRole === 'ANALYST' ? '0 0 10px rgba(56, 189, 248, 0.25)' : 'none',
                }}
              >
                <div style={{ fontSize: '13px', marginBottom: '2px' }}>🔬</div>
                <div>ANALYST</div>
              </button>

              {/* OFFICIAL */}
              <button
                type="button"
                onClick={() => handleRoleSelect('OFFICIAL')}
                style={{
                  padding: '10px 6px',
                  background: selectedRole === 'OFFICIAL' ? 'rgba(245, 158, 11, 0.2)' : '#0F172A',
                  border: `1.5px solid ${selectedRole === 'OFFICIAL' ? '#F59E0B' : '#1E293B'}`,
                  borderRadius: '6px',
                  color: selectedRole === 'OFFICIAL' ? '#F59E0B' : '#94A3B8',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.15s ease',
                  boxShadow: selectedRole === 'OFFICIAL' ? '0 0 10px rgba(245, 158, 11, 0.25)' : 'none',
                }}
              >
                <div style={{ fontSize: '13px', marginBottom: '2px' }}>🛡️</div>
                <div>OFFICIAL</div>
              </button>

              {/* ADMIN */}
              <button
                type="button"
                onClick={() => handleRoleSelect('ADMIN')}
                style={{
                  padding: '10px 6px',
                  background: selectedRole === 'ADMIN' ? 'rgba(67, 217, 232, 0.2)' : '#0F172A',
                  border: `1.5px solid ${selectedRole === 'ADMIN' ? '#43D9E8' : '#1E293B'}`,
                  borderRadius: '6px',
                  color: selectedRole === 'ADMIN' ? '#43D9E8' : '#94A3B8',
                  fontSize: '11px',
                  fontWeight: 700,
                  cursor: 'pointer',
                  textAlign: 'center',
                  transition: 'all 0.15s ease',
                  boxShadow: selectedRole === 'ADMIN' ? '0 0 10px rgba(67, 217, 232, 0.25)' : 'none',
                }}
              >
                <div style={{ fontSize: '13px', marginBottom: '2px' }}>⚡</div>
                <div>ADMIN</div>
              </button>
            </div>
          </div>

          <form onSubmit={handleLogin} autoComplete="off">
            <div className="auth-login-field">
              <label className="auth-login-label" htmlFor="tt-email">Username / Account</label>
              <input
                id="tt-email"
                type="text"
                className={`auth-login-input${error ? ' auth-login-input--error' : ''}`}
                placeholder="e.g. analyst, official, admin"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(null); }}
                autoFocus
                autoComplete="username"
                disabled={isSubmitting}
              />
            </div>

            <div className="auth-login-field">
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <label className="auth-login-label" htmlFor="tt-password">Password</label>
                <button
                  type="button"
                  onClick={() => setForgotMsg(true)}
                  style={{ background: 'none', border: 'none', color: '#38BDF8', fontSize: '11px', cursor: 'pointer', padding: 0 }}
                >
                  Forgot Password?
                </button>
              </div>
              <input
                id="tt-password"
                type="password"
                className={`auth-login-input${error ? ' auth-login-input--error' : ''}`}
                placeholder="Enter password"
                value={password}
                onChange={(e) => { setPassword(e.target.value); setError(null); }}
                autoComplete="current-password"
                disabled={isSubmitting}
              />
            </div>

            {error && (
              <div className="auth-login-error" style={{ color: '#FF5C6C', fontSize: '12px', marginTop: '8px' }}>
                {error}
              </div>
            )}

            {forgotMsg && (
              <div style={{ background: 'rgba(56, 189, 248, 0.1)', border: '1px solid rgba(56, 189, 248, 0.3)', borderRadius: '4px', padding: '8px 10px', fontSize: '11px', color: '#38BDF8', marginTop: '8px' }}>
                Password corresponds to the role name (e.g. <strong>analyst</strong>, <strong>official</strong>, <strong>admin</strong>).
              </div>
            )}

            <button
              type="submit"
              className="auth-login-submit"
              disabled={isSubmitting}
              style={{
                marginTop: '18px',
                width: '100%',
                height: '42px',
                fontWeight: 800,
                fontSize: '13px',
                letterSpacing: '0.06em',
                background: selectedRole === 'ADMIN'
                  ? 'linear-gradient(135deg, #0284C7 0%, #0369A1 100%)'
                  : selectedRole === 'OFFICIAL'
                  ? 'linear-gradient(135deg, #D97706 0%, #B45309 100%)'
                  : 'linear-gradient(135deg, #0284C7 0%, #2563EB 100%)',
              }}
            >
              {isSubmitting ? 'AUTHENTICATING...' : 'LOGIN'}
            </button>
          </form>
        </div>

        <div style={{ marginTop: '14px', fontSize: '11px', color: '#64748B', textAlign: 'center' }}>
          ThermoTrace Operational Security · Defense Clearance Gateway
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
