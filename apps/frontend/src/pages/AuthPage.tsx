import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';

interface AuthPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onNavigate }) => {
  const { loginWithCredentials } = useAuth();

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [phase, setPhase] = useState<'idle' | 'checking' | 'granted'>('idle');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    const u = username.trim().toLowerCase();
    const p = password.trim();

    if (!u || !p) {
      setError('Please enter both username and password.');
      return;
    }

    if (u !== 'admin' || p !== 'admin') {
      setError('Invalid credentials. Access denied.');
      return;
    }

    setIsSubmitting(true);
    setPhase('checking');

    await new Promise(r => setTimeout(r, 900));
    await loginWithCredentials('admin', 'SEC-CLR-L4-ORBITAL-ADMIN');

    setPhase('granted');
    await new Promise(r => setTimeout(r, 500));
    onNavigate('dashboard');
  };

  return (
    <div className="auth-page">
      <div className="auth-page__ambient-grid" />
      <div className="auth-page__radar-ring auth-page__radar-ring--1" />
      <div className="auth-page__radar-ring auth-page__radar-ring--2" />

      <div className="auth-login-center">
        {/* Brand */}
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
            <div className="auth-login-brand__sub">
              Satellite GeoAI · Explainable Industrial Thermal Intelligence
            </div>
          </div>
        </div>

        {/* Card */}
        <div className="auth-login-card">
          <div className="auth-login-card__header">
            <div className="auth-login-card__title">Sign In</div>
            <div className="auth-login-card__sub">
              Access the ThermoTrace Command Center
            </div>
          </div>

          <form onSubmit={handleLogin} autoComplete="off">
            <div className="auth-login-field">
              <label className="auth-login-label" htmlFor="tt-username">Username</label>
              <input
                id="tt-username"
                type="text"
                className={`auth-login-input${error ? ' auth-login-input--error' : ''}`}
                placeholder="Enter username"
                value={username}
                onChange={e => { setUsername(e.target.value); setError(null); }}
                autoFocus
                autoComplete="username"
                disabled={isSubmitting}
              />
            </div>

            <div className="auth-login-field">
              <label className="auth-login-label" htmlFor="tt-password">Password</label>
              <input
                id="tt-password"
                type="password"
                className={`auth-login-input${error ? ' auth-login-input--error' : ''}`}
                placeholder="Enter password"
                value={password}
                onChange={e => { setPassword(e.target.value); setError(null); }}
                autoComplete="current-password"
                disabled={isSubmitting}
              />
            </div>

            {error && (
              <div className="auth-login-error">
                <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                {error}
              </div>
            )}

            <button
              type="submit"
              className="auth-login-btn"
              disabled={isSubmitting}
            >
              {phase === 'checking' && (
                <>
                  <span className="spinner-small" />
                  Authenticating…
                </>
              )}
              {phase === 'granted' && (
                <>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                    <polyline points="20 6 9 17 4 12" />
                  </svg>
                  Access Granted
                </>
              )}
              {phase === 'idle' && 'Sign In →'}
            </button>
          </form>

          <div className="auth-login-hint">
            Demo credentials: <strong>admin</strong> / <strong>admin</strong>
          </div>
        </div>

        {/* System badges */}
        <div className="auth-login-badges">
          <span className="auth-badge">🛰️ NASA FIRMS Live</span>
          <span className="auth-badge">🤖 XAI Engine v2</span>
          <span className="auth-badge">🔒 SIH26162</span>
        </div>
      </div>
    </div>
  );
};

export default AuthPage;
