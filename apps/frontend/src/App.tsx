import { useState, useEffect, useRef } from 'react';
import Dashboard from './pages/Dashboard';
import EventInvestigation from './pages/EventInvestigation';
import { FacilityProfile } from './pages/FacilityProfile';
import AuthPage from './pages/AuthPage';
import WhatIfSimulator from './pages/WhatIfSimulator';
import GuidedDemoOverlay from './components/ui/GuidedDemoOverlay';
import DataReductionVisualizer from './pages/DataReductionVisualizer';
import Alerts from './pages/Alerts';
import Analytics from './pages/Analytics';
import Methodology from './pages/Methodology';
import ReportsView from './pages/ReportsView';
import { AuthProvider, useAuth } from './services/AuthContext';

// ─── 8 CANONICAL ORIGINAL THERMOTRACE PAGES ──────────────────────────────────

interface NavItem {
  id: string;
  path: string;
  label: string;
  icon: React.ReactNode;
}

const NAV_ITEMS: NavItem[] = [
  {
    id: 'tab-command-center',
    path: '/command-center',
    label: 'Command Center',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" />
        <rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" />
      </svg>
    ),
  },
  {
    id: 'tab-investigations',
    path: '/investigation/TT-CASE-001',
    label: 'Investigations',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <circle cx="11" cy="11" r="8" /><line x1="21" y1="21" x2="16.65" y2="16.65" />
        <line x1="11" y1="8" x2="11" y2="14" /><line x1="8" y1="11" x2="14" y2="11" />
      </svg>
    ),
  },
  {
    id: 'tab-scenario-modeler',
    path: '/scenario-modeler',
    label: 'Scenario Modeler',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <polygon points="1 6 1 22 8 18 16 22 23 18 23 2 16 6 8 2 1 6" />
        <line x1="8" y1="2" x2="8" y2="18" /><line x1="16" y1="6" x2="16" y2="22" />
      </svg>
    ),
  },
  {
    id: 'tab-data-reduction',
    path: '/data-reduction',
    label: 'Data Reduction',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <ellipse cx="12" cy="5" rx="9" ry="3" />
        <path d="M21 12c0 1.66-4 3-9 3s-9-1.34-9-3" />
        <path d="M3 5v14c0 1.66 4 3 9 3s9-1.34 9-3V5" />
      </svg>
    ),
  },
  {
    id: 'tab-alert-center',
    path: '/alert-center',
    label: 'Alert Center',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
        <path d="M13.73 21a2 2 0 0 1-3.46 0" />
      </svg>
    ),
  },
  {
    id: 'tab-facilities',
    path: '/facilities',
    label: 'Facilities',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 20a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V8l-7 5V8l-7 5V4a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z" />
        <path d="M18 18h.01" /><path d="M14 18h.01" /><path d="M6 18h.01" /><path d="M10 18h.01" />
      </svg>
    ),
  },
  {
    id: 'tab-analytics',
    path: '/analytics',
    label: 'Analytics',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      </svg>
    ),
  },
  {
    id: 'tab-methodology',
    path: '/methodology',
    label: 'Methodology',
    icon: (
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d="M2 3h6a4 4 0 0 1 4 4v14a3 3 0 0 0-3-3H2z" />
        <path d="M22 3h-6a4 4 0 0 0-4 4v14a3 3 0 0 1 3-3h7z" />
      </svg>
    ),
  },
];

// ─── LOGO ─────────────────────────────────────────────────────────────────
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

// ─── MAIN APP CONTENT WITH ROUTER ─────────────────────────────────────────
function AppContent() {
  const { currentUser, logout, isAuthenticated } = useAuth();
  
  // URL-driven routing state
  const [currentPath, setCurrentPath] = useState<string>(() => {
    return window.location.pathname || '/';
  });
  const [routeParams, setRouteParams] = useState<any>({});
  const [showDemo, setShowDemo] = useState<boolean>(false);
  const [showUserMenu, setShowUserMenu] = useState<boolean>(false);
  const userMenuRef = useRef<HTMLDivElement>(null);

  const [lastUpdated] = useState(() => {
    const now = new Date();
    return now.toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata' }) + ' IST';
  });

  // Navigate function with URL history synchronization
  const navigate = (pathOrPage: string, params?: any) => {
    let targetPath = pathOrPage;

    // Convert legacy/short page IDs to URL paths
    if (!pathOrPage.startsWith('/')) {
      if (pathOrPage === 'command-center' || pathOrPage === 'dashboard' || pathOrPage === 'map') targetPath = '/command-center';
      else if (pathOrPage === 'investigations' || pathOrPage === 'investigation') targetPath = '/investigation/TT-CASE-001';
      else if (pathOrPage === 'scenario-modeler' || pathOrPage === 'whatif' || pathOrPage === 'what-if' || pathOrPage === 'hazard') targetPath = '/scenario-modeler';
      else if (pathOrPage === 'data-reduction' || pathOrPage === 'reduction' || pathOrPage === 'pipeline') targetPath = '/data-reduction';
      else if (pathOrPage === 'alert-center' || pathOrPage === 'alerts') targetPath = '/alert-center';
      else if (pathOrPage === 'facilities' || pathOrPage === 'facility') targetPath = '/facilities';
      else if (pathOrPage === 'analytics' || pathOrPage === 'intelligence') targetPath = '/analytics';
      else if (pathOrPage === 'methodology') targetPath = '/methodology';
      else if (pathOrPage === 'reports') targetPath = '/reports';
      else targetPath = `/${pathOrPage}`;
    }

    if (params?.eventId) {
      targetPath = `/investigation/${params.eventId}`;
    } else if (params?.facilityId) {
      targetPath = `/facility/${params.facilityId}`;
    }

    window.history.pushState({}, '', targetPath);
    setCurrentPath(targetPath);
    setRouteParams(params || {});
    setShowUserMenu(false);
    window.scrollTo(0, 0);
  };

  // Listen to browser popstate (back/forward navigation)
  useEffect(() => {
    const handlePopState = () => {
      setCurrentPath(window.location.pathname || '/');
    };
    window.addEventListener('popstate', handlePopState);
    return () => window.removeEventListener('popstate', handlePopState);
  }, []);

  // Post-login automatic redirection to Command Center
  useEffect(() => {
    if (currentUser) {
      const p = window.location.pathname;
      if (p === '/' || p === '/login') {
        navigate('/command-center');
      }
    }
  }, [currentUser]);

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

  // ─── MANDATORY AUTHENTICATION GATE ──────────────────────────────────────
  if (!isAuthenticated || !currentUser) {
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
              AUTHENTICATION REQUIRED
            </div>
          </div>
        </header>

        <main className="main-workspace" style={{ flex: 1, overflowY: 'auto' }}>
          <AuthPage onNavigate={(target) => navigate(target || '/dashboard')} />
        </main>
      </div>
    );
  }

  const themeColor = '#38BDF8';

  return (
    <div className="app-shell">
      {/* ─── Top Header ─── */}
      <header className="top-header">
        <div
          className="top-header__logo-zone"
          onClick={() => navigate('/command-center')}
          title="ThermoTrace"
          style={{ cursor: 'pointer' }}
        >
          <LogoMark />
        </div>

        <div
          className="top-header__brand"
          onClick={() => navigate('/command-center')}
          style={{ cursor: 'pointer' }}
        >
          <div className="top-header__product-name">
            THERMO<span>TRACE</span>
          </div>
          <div className="top-header__product-sub">Industrial Thermal Intelligence Platform · SIH 26162</div>
        </div>

        {/* Central Platform Badge */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '4px 14px',
          background: 'rgba(15, 23, 42, 0.9)',
          border: `1px solid ${themeColor}`,
          borderRadius: '20px',
          boxShadow: `0 0 12px ${themeColor}33`,
        }}>
          <span style={{ fontSize: '10px', color: '#94A3B8', fontWeight: 700, letterSpacing: '0.04em' }}>
            SIH DEMO MODE ·
          </span>
          <span style={{ fontSize: '11px', fontWeight: 800, color: themeColor, letterSpacing: '0.05em' }}>
            ANALYST
          </span>
          <span style={{ fontSize: '10px', color: '#CBD5E1', paddingLeft: '4px', borderLeft: '1px solid #334155' }}>
            INTELLIGENCE CONSOLE
          </span>
        </div>

        <div className="top-header__spacer" />

        <div className="top-header__meta">
          {/* Last updated */}
          <span className="top-header__timestamp">Updated {lastUpdated}</span>

          {/* Satellite Telemetry Pipeline Status */}
          <div
            className="top-header__health"
            title="Near-Real-Time NASA FIRMS Ingestion Pipeline"
            onClick={() => navigate('/pipeline')}
            style={{ cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '11px', padding: '3px 8px', background: 'rgba(67, 217, 232, 0.08)', border: '1px solid rgba(67, 217, 232, 0.3)', borderRadius: '4px' }}
          >
            <div className="top-header__health-dot" style={{ background: '#38BDF8' }} />
            <span style={{ color: '#E2E8F0', fontWeight: 600 }}>NRT SATELLITE PIPELINE</span>
            <span style={{ color: '#94A3B8', fontSize: '10px' }}>· Latency: 2.4h</span>
          </div>

          {/* Alert count */}
          <button
            className="top-header__alert-badge"
            onClick={() => navigate('/investigation/TT-CASE-001')}
            title="View critical events"
          >
            <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
              <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9" />
              <path d="M13.73 21a2 2 0 0 1-3.46 0" />
            </svg>
            3
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
              title={`${currentUser?.name || 'Analyst'}`}
            >
              {currentUser?.badge || 'LA'}
            </button>

            {showUserMenu && (
              <div className="user-dropdown-menu">
                <div className="user-dropdown-header">
                  <div className="user-dropdown-name">{currentUser?.name || 'Lead Thermal Analyst'}</div>
                  <div className="user-dropdown-role">THERMOTRACE ANALYST</div>
                  {currentUser && (
                    <div className="user-dropdown-clearance">
                      {currentUser.clearance_level.split('—')[0].trim()}
                    </div>
                  )}
                </div>

                <div className="user-dropdown-divider" />

                <div style={{ padding: '8px 12px', fontSize: '11px', color: 'var(--text-muted)', lineHeight: '1.5' }}>
                  <div style={{ color: themeColor, fontWeight: '700', marginBottom: '2px' }}>Role: ANALYST</div>
                  <div>Report Delivery: <strong>thermotrace.india@gmail.com</strong></div>
                </div>

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
        {/* ─── 8 Canonical Pages Navigation Rail ─── */}
        <nav className="nav-rail" aria-label="Analyst platform navigation">
          <div className="nav-rail__items">
            {NAV_ITEMS.map((item) => {
              const isActive =
                (item.id === 'tab-command-center' && (currentPath === '/command-center' || currentPath === '/dashboard' || currentPath === '/' || currentPath === '/analyst' || currentPath === '/map')) ||
                (item.id === 'tab-investigations' && (currentPath.startsWith('/investigation') || currentPath === '/investigations')) ||
                (item.id === 'tab-scenario-modeler' && (currentPath === '/scenario-modeler' || currentPath === '/what-if' || currentPath === '/hazard')) ||
                (item.id === 'tab-data-reduction' && (currentPath === '/data-reduction' || currentPath === '/pipeline' || currentPath === '/reduction')) ||
                (item.id === 'tab-alert-center' && (currentPath === '/alert-center' || currentPath === '/alerts' || currentPath === '/reports')) ||
                (item.id === 'tab-facilities' && (currentPath === '/facilities' || currentPath.startsWith('/facility'))) ||
                (item.id === 'tab-analytics' && (currentPath === '/analytics' || currentPath === '/intelligence')) ||
                (item.id === 'tab-methodology' && currentPath === '/methodology');

              return (
                <button
                  key={item.id}
                  className={`nav-item ${isActive ? 'nav-item--active' : ''}`}
                  onClick={() => navigate(item.path)}
                  title={item.label}
                >
                  <span className="nav-item__icon">{item.icon}</span>
                  <span className="nav-item__label">{item.label}</span>
                </button>
              );
            })}
          </div>

          <div className="nav-rail__footer">
            <div className="nav-rail__data-status">
              <div className="nav-rail__data-status-dot" style={{ background: themeColor }} />
              <span style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)' }}>
                ANALYST ACTIVE
              </span>
            </div>
          </div>
        </nav>

        {/* ─── Main Workspace (8 Canonical Pages) ─── */}
        <main className="main-workspace">
          {/* 2. INVESTIGATIONS */}
          {currentPath.startsWith('/investigation') || currentPath === '/investigations' ? (
            <EventInvestigation
              eventId={
                currentPath.split('/investigation/')[1]?.split('/')[0] ||
                routeParams.eventId ||
                'TT-CASE-001'
              }
              onNavigate={navigate}
            />
          ) : /* 3. SCENARIO MODELER */
          currentPath === '/scenario-modeler' || currentPath === '/what-if' || currentPath === '/hazard' ? (
            <WhatIfSimulator eventId={routeParams.eventId} onNavigate={navigate} onOpenNotificationModal={() => {}} />
          ) : /* 4. DATA REDUCTION */
          currentPath === '/data-reduction' || currentPath === '/reduction' || currentPath === '/pipeline' ? (
            <DataReductionVisualizer />
          ) : /* 5. ALERT CENTER */
          currentPath === '/alert-center' || currentPath === '/alerts' ? (
            <Alerts onNavigate={navigate} />
          ) : /* REPORTS DOSSIER VIEW */
          currentPath === '/reports' ? (
            <ReportsView onNavigate={navigate} />
          ) : /* 6. FACILITIES */
          currentPath === '/facilities' || currentPath.startsWith('/facility') ? (
            <FacilityProfile facilityId={routeParams.facilityId} onNavigate={navigate} />
          ) : /* 7. ANALYTICS */
          currentPath === '/analytics' || currentPath === '/intelligence' ? (
            <Analytics onNavigate={navigate} />
          ) : /* 8. METHODOLOGY */
          currentPath === '/methodology' ? (
            <Methodology />
          ) : /* 1. COMMAND CENTER (DEFAULT / DASHBOARD / MAP) */
            <Dashboard onNavigate={navigate} />
          }
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
