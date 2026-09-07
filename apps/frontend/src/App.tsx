import { useState, useEffect, useRef } from 'react';
import Dashboard from './pages/Dashboard';
import EventInvestigation from './pages/EventInvestigation';
import Alerts from './pages/Alerts';
import { FacilityProfile } from './pages/FacilityProfile';
import AuthPage from './pages/AuthPage';
import WhatIfSimulator from './pages/WhatIfSimulator';
import GuidedDemoOverlay from './components/ui/GuidedDemoOverlay';
import DataReductionVisualizer from './pages/DataReductionVisualizer';
import Methodology from './pages/Methodology';
import { AuthProvider, useAuth } from './services/AuthContext';

// ─── Page type ───────────────────────────────────────────────────────────────
type Page = 'dashboard' | 'investigation' | 'alerts' | 'facilities' | 'what-if' | 'reduction' | 'methodology';

// ─── Nav items ───────────────────────────────────────────────────────────────
const NAV_ITEMS: { id: Page; label: string; icon: React.ReactNode }[] = [
  {
    id: 'dashboard',
    label: 'Command Center',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    id: 'investigation',
    label: 'Event Investigations',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        <line x1="11" y1="8" x2="11" y2="14" /><line x1="8" y1="11" x2="14" y2="11" />
      </svg>
    ),
  },
  {
    id: 'what-if',
    label: 'Scenario Modeler',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
        <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
        <line x1="20" y1="21" x2="20" y2="16" /><line x1="20" y1="12" x2="20" y2="3" />
        <line x1="1" y1="14" x2="7" y2="14" /><line x1="9" y1="8" x2="15" y2="8" /><line x1="17" y1="16" x2="23" y2="16" />
      </svg>
    ),
  },
  {
    id: 'alerts',
    label: 'Alert Center',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
    ),
  },
  {
    id: 'facilities',
    label: 'Facilities',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="2" y="7" width="20" height="14" rx="2" /><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16" />
        <path d="M6 11h4" /><path d="M14 11h4" />
      </svg>
    ),
  },
  {
    id: 'reduction',
    label: 'Data Reduction',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="12 2 2 7 12 12 22 7 12 2" />
        <polyline points="2 17 12 22 22 17" />
        <polyline points="2 12 12 17 22 12" />
      </svg>
    ),
  },
  {
    id: 'methodology',
    label: 'Methodology',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
        <polyline points="10 9 9 9 8 9" />
      </svg>
    ),
  },
];

const PAGE_TITLES: Record<Page, string> = {
  dashboard: 'Command Center',
  investigation: 'Event Investigation',
  'what-if': 'Incident Scenario Modeler & Threat Simulator',
  alerts: 'Alert Center',
  facilities: 'Facilities',
  reduction: 'NASA FIRMS Data Reduction — Live Demo',
  methodology: 'System Methodology & Intelligence Pipeline',
};

// ─── Logo ─────────────────────────────────────────────────────────────────
function LogoMark() {
  return (
    <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
      <ellipse cx="14" cy="14" rx="12" ry="5" stroke="#43D9E8" strokeWidth="1.2" strokeDasharray="2 2" opacity="0.6" />
      <rect x="11" y="11" width="6" height="6" rx="1.5" fill="#43D9E8" opacity="0.9" />
      <rect x="5" y="12.5" width="5" height="3" rx="0.5" fill="#4D8DFF" opacity="0.7" />
      <rect x="18" y="12.5" width="5" height="3" rx="0.5" fill="#4D8DFF" opacity="0.7" />
      <circle cx="14" cy="22" r="2.5" fill="#FF7A45" opacity="0.85" />
      <circle cx="14" cy="22" r="1.2" fill="#FFB547" />
    </svg>
  );
}

// ─── App Content ──────────────────────────────────────────────────────────
function AppContent() {
  const { currentUser, logout } = useAuth();
  const [page, setPage] = useState<Page>('dashboard');
  const [pageParams, setPageParams] = useState<any>({});
  const [showDemo, setShowDemo] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [alertCount] = useState(3);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const [lastUpdated] = useState(() => {
    const now = new Date();
    return now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST';
  });

  const navigate = (target: string, params?: any) => {
    setPage(target as Page);
    setPageParams(params || {});
    setShowUserMenu(false);
    window.scrollTo(0, 0);
  };

  // Close user dropdown on outside click or Escape
  useEffect(() => {
    const clickHandler = (e: MouseEvent) => {
      if (userMenuRef.current && !userMenuRef.current.contains(e.target as Node)) {
        setShowUserMenu(false);
      }
    };
    const escHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        setShowDemo(false);
        setShowUserMenu(false);
      }
    };
    window.addEventListener('mousedown', clickHandler);
    window.addEventListener('keydown', escHandler);
    return () => {
      window.removeEventListener('mousedown', clickHandler);
      window.removeEventListener('keydown', escHandler);
    };
  }, []);

  // ─── MANDATORY LOGIN GATE ───────────────────────────────────────────────
  if (!currentUser) {
    return (
      <div className="app-shell" style={{ overflowY: 'auto' }}>
        <header className="top-header">
          <div className="top-header__logo-zone" title="ThermoTrace">
            <LogoMark />
          </div>
          <div className="top-header__brand">
            <div className="top-header__product-name">
              THERMO<span>TRACE</span>
            </div>
            <div className="top-header__product-sub">Satellite GeoAI · SIH26162</div>
          </div>
          <div className="top-header__spacer" />
          <div className="top-header__meta">
            <div className="top-header__health">
              <div className="top-header__health-dot" style={{ background: 'var(--accent-amber)' }} />
              AUTH REQUIRED
            </div>
          </div>
        </header>

        <main className="main-workspace" style={{ flex: 1, overflowY: 'auto' }}>
          <AuthPage onNavigate={(target) => navigate(target || 'dashboard')} />
        </main>
      </div>
    );
  }

  return (
    <div className="app-shell">
      {/* ─── Top Header ─── */}
      <header className="top-header">
        <div className="top-header__logo-zone" onClick={() => navigate('dashboard')} title="ThermoTrace">
          <LogoMark />
        </div>

        <div className="top-header__brand" onClick={() => navigate('dashboard')}>
          <div className="top-header__product-name">
            THERMO<span>TRACE</span>
          </div>
          <div className="top-header__product-sub">Satellite GeoAI · SIH26162</div>
        </div>

        <div className="top-header__page-title">
          {PAGE_TITLES[page]}
        </div>

        <div className="top-header__spacer" />

        <div className="top-header__meta">
          {/* Last updated */}
          <span className="top-header__timestamp">Updated {lastUpdated}</span>

          {/* Health */}
          <div className="top-header__health">
            <div className="top-header__health-dot" />
            NOMINAL
          </div>

          {/* Alert count */}
          <button
            className="top-header__alert-badge"
            onClick={() => navigate('alerts')}
            title="View alerts"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            {alertCount}
          </button>

          {/* Demo button */}
          <button
            className="top-header__demo-btn"
            onClick={() => setShowDemo(true)}
            title="Run 3-minute guided demo"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="currentColor">
              <polygon points="5 3 19 12 5 21 5 3" />
            </svg>
            Run Demo
          </button>

          {/* User Profile */}
          <div className="top-header__user-wrapper" ref={userMenuRef}>
            <button
              className="top-header__user-btn"
              style={{ background: currentUser?.avatar_gradient || undefined }}
              onClick={() => setShowUserMenu(!showUserMenu)}
              title={`${currentUser?.name || 'Guest'}`}
            >
              {currentUser?.badge || '??'}
            </button>

            {showUserMenu && (
              <div className="user-dropdown-menu">
                <div className="user-dropdown-header">
                  <div className="user-dropdown-name">{currentUser?.name || 'Unauthenticated'}</div>
                  <div className="user-dropdown-role">{currentUser?.role || 'Guest Analyst'}</div>
                  {currentUser && (
                    <div className="user-dropdown-clearance">
                      {currentUser.clearance_level.split('—')[0].trim()}
                    </div>
                  )}
                </div>

                <div className="user-dropdown-divider" />

                <div style={{ padding: '8px 12px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                  <div style={{ color: 'var(--accent-cyan)', fontWeight: '700', marginBottom: '2px' }}>Session Active</div>
                  <div>Alert email: <strong>rijja2310119@ssn.edu.in</strong></div>
                </div>

                <div className="user-dropdown-divider" />

                <button
                  className="user-dropdown-nav-btn"
                  onClick={() => navigate('reduction')}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <polygon points="12 2 2 7 12 12 22 7 12 2" />
                    <polyline points="2 17 12 22 22 17" />
                  </svg>
                  Data Reduction Demo
                </button>

                <button
                  className="user-dropdown-nav-btn"
                  onClick={() => navigate('what-if')}
                >
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                    <line x1="4" y1="21" x2="4" y2="14" /><line x1="4" y1="10" x2="4" y2="3" />
                    <line x1="12" y1="21" x2="12" y2="12" /><line x1="12" y1="8" x2="12" y2="3" />
                  </svg>
                  What-If Threat Simulator
                </button>

                <div className="user-dropdown-divider" />

                <button
                  className="user-dropdown-signout"
                  onClick={() => {
                    logout();
                    setShowUserMenu(false);
                  }}
                >
                  Sign Out
                </button>
              </div>
            )}
          </div>
        </div>
      </header>

      {/* ─── App Body ─── */}
      <div className="app-body">
        {/* ─── Left Navigation Rail ─── */}
        <nav className="nav-rail" aria-label="Main navigation">
          <div className="nav-rail__items">
            {NAV_ITEMS.map(item => (
              <button
                key={item.id}
                className={`nav-item ${page === item.id ? 'nav-item--active' : ''}`}
                onClick={() => navigate(item.id)}
                title={item.label}
              >
                <span className="nav-item__icon">{item.icon}</span>
                <span className="nav-item__label">{item.label}</span>
              </button>
            ))}
          </div>

          <div className="nav-rail__footer">
            <div className="nav-rail__data-status">
              <div className="nav-rail__data-status-dot" />
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                FIRMS · MODIS/VIIRS
              </span>
            </div>
          </div>
        </nav>

        {/* ─── Main Workspace ─── */}
        <main className="main-workspace">
          {page === 'dashboard' && <Dashboard onNavigate={navigate} />}
          {page === 'investigation' && (
            <EventInvestigation eventId={pageParams.eventId} onNavigate={navigate} />
          )}
          {page === 'what-if' && (
            <WhatIfSimulator
              eventId={pageParams.eventId}
              onNavigate={navigate}
              onOpenNotificationModal={() => {}}
            />
          )}
          {page === 'alerts' && (
            <Alerts onNavigate={navigate} />
          )}
          {page === 'facilities' && (
            <FacilityProfile facilityId={pageParams.facilityId} onNavigate={navigate} />
          )}
          {page === 'reduction' && <DataReductionVisualizer />}
          {page === 'methodology' && <Methodology />}
        </main>
      </div>

      {/* ─── Guided Demo Overlay ─── */}
      {showDemo && (
        <GuidedDemoOverlay
          onClose={() => setShowDemo(false)}
          onNavigate={navigate}
        />
      )}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
    </AuthProvider>
  );
}

export default App;
