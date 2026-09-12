import React, { useState } from 'react';
import { useAuth } from '../services/AuthContext';

interface AuthPageProps {
  onNavigate: (page: string, params?: any) => void;
}

export const AuthPage: React.FC<AuthPageProps> = ({ onNavigate }) => {
  const { loginWithCredentials } = useAuth();

  const [username, setUsername] = useState('analyst');
  const [password, setPassword] = useState('analyst');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleLogin = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    setError(null);

    const cleanUsername = username.trim();
    const cleanPassword = password.trim();

    if (!cleanUsername || !cleanPassword) {
      setError('Please enter both username and password.');
      return;
    }

    setIsSubmitting(true);
    const result = await loginWithCredentials(cleanUsername, cleanPassword);
    setIsSubmitting(false);

    if (result.success) {
      onNavigate('/command-center');
    } else {
      setError(result.error || 'Invalid credentials. Demo mode password: analyst');
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <div>
              <div className="auth-login-card__title">Analyst Sign In</div>
              <div className="auth-login-card__sub" style={{ fontSize: '11.5px', color: '#94A3B8' }}>
                Operational Thermal Intelligence Console
              </div>
            </div>
            <div style={{
              background: 'rgba(56, 189, 248, 0.15)',
              border: '1px solid #38BDF8',
              borderRadius: '4px',
              padding: '4px 10px',
              fontSize: '10px',
              fontWeight: 800,
              color: '#38BDF8',
              letterSpacing: '0.06em'
            }}>
              SIH DEMO MODE
            </div>
          </div>

          <div style={{
            padding: '10px 12px',
            borderRadius: '6px',
            background: 'rgba(15, 23, 42, 0.9)',
            border: '1px solid #1E293B',
            fontSize: '11px',
            color: '#CBD5E1',
            marginBottom: '16px',
            lineHeight: 1.5,
          }}>
            <div style={{ fontWeight: 700, color: '#38BDF8', marginBottom: '3px' }}>
              🔬 Single Analyst Intelligence Console
            </div>
            <div>• Full access to 4-Engine AI Pipeline, FIRMS telemetry, XAI &amp; Hazards</div>
            <div>• Approved dossiers dispatch directly to <strong>thermotrace.india@gmail.com</strong></div>
          </div>

          <form onSubmit={handleLogin} autoComplete="off">
            <div className="auth-login-field">
              <label className="auth-login-label" htmlFor="tt-username">Analyst Username</label>
              <input
                id="tt-username"
                type="text"
                className={`auth-login-input${error ? ' auth-login-input--error' : ''}`}
                placeholder="analyst"
                value={username}
                onChange={(e) => { setUsername(e.target.value); setError(null); }}
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
                placeholder="analyst"
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
                background: 'linear-gradient(135deg, #0284C7 0%, #2563EB 100%)',
              }}
            >
              {isSubmitting ? 'AUTHENTICATING...' : 'SIGN IN'}
            </button>
          </form>
        </div>

        <div style={{ marginTop: '14px', fontSize: '11px', color: '#64748B', textAlign: 'center' }}>
          ThermoTrace AI · NASA FIRMS Spaceborne Thermal Intelligence Platform
        </div>
      </div>
    </div>
  );
};

export default AuthPage;

