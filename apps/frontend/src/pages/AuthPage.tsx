import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';

interface AuthPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onNavigate }) => {
  const { loginWithCredentials } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [forgotMsg, setForgotMsg] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setForgotMsg(false);

    const cleanEmail = email.trim();
    const cleanPassword = password.trim();

    if (!cleanEmail || !cleanPassword) {
      setError('Please enter both email and password.');
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

  const handleQuickSelect = (selEmail: string) => {
    setEmail(selEmail);
    setPassword('ThermoTrace2026!');
    setError(null);
    setForgotMsg(false);
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
          <div className="auth-login-card__header" style={{ marginBottom: '16px' }}>
            <div className="auth-login-card__title">Sign In</div>
            <div className="auth-login-card__sub">
              Access the ThermoTrace Operational Intelligence Platform
            </div>
          </div>

          {/* Quick Account Switcher Pills for Judging / Presentation */}
          <div style={{ marginBottom: '18px' }}>
            <div style={{ fontSize: '11px', color: '#64748B', textTransform: 'uppercase', fontWeight: 700, marginBottom: '8px' }}>
              Select Operational Role Profile:
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '6px' }}>
              <button
                type="button"
                onClick={() => handleQuickSelect('anagesh2410198@ssn.edu.in')}
                style={{
                  padding: '8px 4px',
                  background: email === 'anagesh2410198@ssn.edu.in' ? 'rgba(56, 189, 248, 0.2)' : '#0F172A',
                  border: `1px solid ${email === 'anagesh2410198@ssn.edu.in' ? '#38BDF8' : '#1E293B'}`,
                  borderRadius: '5px',
                  color: email === 'anagesh2410198@ssn.edu.in' ? '#38BDF8' : '#94A3B8',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                🔬 ANALYST
              </button>
              <button
                type="button"
                onClick={() => handleQuickSelect('rijja2310119@ssn.edu.in')}
                style={{
                  padding: '8px 4px',
                  background: email === 'rijja2310119@ssn.edu.in' ? 'rgba(245, 158, 11, 0.2)' : '#0F172A',
                  border: `1px solid ${email === 'rijja2310119@ssn.edu.in' ? '#F59E0B' : '#1E293B'}`,
                  borderRadius: '5px',
                  color: email === 'rijja2310119@ssn.edu.in' ? '#F59E0B' : '#94A3B8',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                🛡️ OFFICIAL
              </button>
              <button
                type="button"
                onClick={() => handleQuickSelect('admin@thermotrace.gov.in')}
                style={{
                  padding: '8px 4px',
                  background: email === 'admin@thermotrace.gov.in' ? 'rgba(67, 217, 232, 0.2)' : '#0F172A',
                  border: `1px solid ${email === 'admin@thermotrace.gov.in' ? '#43D9E8' : '#1E293B'}`,
                  borderRadius: '5px',
                  color: email === 'admin@thermotrace.gov.in' ? '#43D9E8' : '#94A3B8',
                  fontSize: '11px',
                  fontWeight: 600,
                  cursor: 'pointer',
                  textAlign: 'center',
                }}
              >
                ⚡ ADMIN
              </button>
            </div>
          </div>

          <form onSubmit={handleLogin} autoComplete="off">
            <div className="auth-login-field">
              <label className="auth-login-label" htmlFor="tt-email">Email</label>
              <input
                id="tt-email"
                type="text"
                className={`auth-login-input${error ? ' auth-login-input--error' : ''}`}
                placeholder="e.g. anagesh2410198@ssn.edu.in"
                value={email}
                onChange={(e) => { setEmail(e.target.value); setError(null); }}
                autoFocus
                autoComplete="email"
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
                Default judging evaluation password is: <strong>ThermoTrace2026!</strong>
              </div>
            )}

            <button
              type="submit"
              className="auth-login-submit"
              disabled={isSubmitting}
              style={{ marginTop: '18px', width: '100%', height: '42px', fontWeight: 700 }}
            >
              {isSubmitting ? 'AUTHENTICATING...' : 'LOGIN'}
            </button>
          </form>
        </div>

        <div style={{ marginTop: '16px', fontSize: '11px', color: '#64748B', textAlign: 'center' }}>
          ThermoTrace Operational Security · Defense Clearance Level Gateway
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
