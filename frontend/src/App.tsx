import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import EventInvestigation from './pages/EventInvestigation';
import Alerts from './pages/Alerts';

type Page = 'dashboard' | 'investigation' | 'alerts';

function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [pageParams, setPageParams] = useState<any>({});

  const navigate = (target: string, params?: any) => {
    setPage(target as Page);
    setPageParams(params || {});
  };

  return (
    <div className="app-layout">
      {/* ─── Header Bar ─── */}
      <header className="header-bar">
        <div className="header-bar__brand">
          <div style={{ background: '#111827', color: 'white', padding: '4px 8px', borderRadius: '4px', fontWeight: 'bold' }}>T</div>
          <span className="header-bar__logo" style={{ color: '#111827', WebkitTextFillColor: '#111827', letterSpacing: '0px' }}>ThermoTrace</span>
        </div>

        <nav className="header-bar__nav">
          <button
            className={`header-bar__nav-btn ${page === 'dashboard' ? 'header-bar__nav-btn--active' : ''}`}
            onClick={() => navigate('dashboard')}
          >
            Overview
          </button>
          <button
            className={`header-bar__nav-btn ${page === 'investigation' ? 'header-bar__nav-btn--active' : ''}`}
            onClick={() => navigate('investigation')}
          >
            Investigations
          </button>
          <button
            className={`header-bar__nav-btn ${page === 'alerts' ? 'header-bar__nav-btn--active' : ''}`}
            onClick={() => navigate('alerts')}
          >
            Reports
          </button>
        </nav>

        <div className="header-bar__meta" style={{ gap: '12px' }}>
          <div className="search-input" style={{ width: '200px', margin: 0, padding: 0 }}>
             <input
               type="text"
               placeholder="Search"
               style={{ background: '#f9fafb', border: '1px solid #e5e7eb', padding: '6px 12px', borderRadius: '6px', width: '100%', fontSize: '13px' }}
             />
          </div>
          <div style={{ cursor: 'pointer', padding: '6px' }}>
            <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"></path><path d="M13.73 21a2 2 0 0 1-3.46 0"></path></svg>
          </div>
          <div style={{ background: '#dbeafe', color: '#1e40af', width: '32px', height: '32px', borderRadius: '50%', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 'bold', fontSize: '12px' }}>
            DA
          </div>
        </div>
      </header>

      {/* ─── Page Content ─── */}
      {page === 'dashboard' && <Dashboard onNavigate={navigate} />}
      {page === 'investigation' && (
        <EventInvestigation
          eventId={pageParams.eventId}
          onNavigate={navigate}
        />
      )}
      {page === 'alerts' && <Alerts onNavigate={navigate} />}
    </div>
  );
}

export default App;
