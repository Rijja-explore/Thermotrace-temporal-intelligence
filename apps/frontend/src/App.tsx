import { useState } from 'react';
import Dashboard from './pages/Dashboard';
import EventInvestigation from './pages/EventInvestigation';
import Alerts from './pages/Alerts';
import { FacilityProfile } from './pages/FacilityProfile';
import { EvaluationPage } from './pages/EvaluationPage';

type Page = 'dashboard' | 'investigation' | 'alerts' | 'facilities' | 'evaluation';

function App() {
  const [page, setPage] = useState<Page>('dashboard');
  const [pageParams, setPageParams] = useState<any>({});

  const navigate = (target: string, params?: any) => {
    setPage(target as Page);
    setPageParams(params || {});
    window.scrollTo(0, 0);
  };

  return (
    <div className="app-layout" style={{ minHeight: '100vh', background: '#0a0e1a', color: '#f8fafc' }}>
      {/* ─── Mission Control Navigation Header Bar ─── */}
      <header style={{
        background: '#0f172a',
        borderBottom: '1px solid #1e293b',
        padding: '12px 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        position: 'sticky',
        top: 0,
        zIndex: 2000,
        boxShadow: '0 4px 12px rgba(0,0,0,0.5)'
      }}>
        {/* Brand */}
        <div
          onClick={() => navigate('dashboard')}
          style={{ display: 'flex', alignItems: 'center', gap: '10px', cursor: 'pointer' }}
        >
          <div style={{
            background: 'linear-gradient(135deg, #f97316, #ef4444)',
            color: 'white',
            width: '32px',
            height: '32px',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            fontWeight: '800',
            fontSize: '16px'
          }}>
            T
          </div>
          <div>
            <span style={{ fontSize: '18px', fontWeight: '800', letterSpacing: '-0.5px', color: '#f8fafc' }}>
              THERMO<span style={{ color: '#f97316' }}>TRACE</span>
            </span>
            <div style={{ fontSize: '10px', color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Industrial Thermal GeoAI Platform
            </div>
          </div>
        </div>

        {/* Navigation Bar */}
        <nav style={{ display: 'flex', gap: '8px', background: '#1e293b', padding: '4px', borderRadius: '8px', border: '1px solid #334155' }}>
          <button
            onClick={() => navigate('dashboard')}
            style={{
              background: page === 'dashboard' ? '#2563eb' : 'transparent',
              color: page === 'dashboard' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            🕹️ Dashboard
          </button>

          <button
            onClick={() => navigate('investigation')}
            style={{
              background: page === 'investigation' ? '#2563eb' : 'transparent',
              color: page === 'investigation' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            🔍 Event Investigation
          </button>

          <button
            onClick={() => navigate('alerts')}
            style={{
              background: page === 'alerts' ? '#2563eb' : 'transparent',
              color: page === 'alerts' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            🚨 Alert Centre
          </button>

          <button
            onClick={() => navigate('facilities')}
            style={{
              background: page === 'facilities' ? '#2563eb' : 'transparent',
              color: page === 'facilities' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            🏭 Facility Profiles
          </button>

          <button
            onClick={() => navigate('evaluation')}
            style={{
              background: page === 'evaluation' ? '#2563eb' : 'transparent',
              color: page === 'evaluation' ? '#ffffff' : '#94a3b8',
              border: 'none',
              padding: '6px 14px',
              borderRadius: '6px',
              fontSize: '13px',
              fontWeight: '600',
              cursor: 'pointer',
              transition: 'all 0.15s ease'
            }}
          >
            📊 AI Evaluation
          </button>
        </nav>

        {/* Live System Status Indicator */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '6px',
            background: 'rgba(34, 197, 94, 0.1)',
            border: '1px solid rgba(34, 197, 94, 0.3)',
            padding: '4px 10px',
            borderRadius: '20px',
            fontSize: '12px',
            color: '#22c55e',
            fontWeight: '600'
          }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#22c55e' }}></span>
            <span>SYSTEM ACTIVE</span>
          </div>

          <div style={{
            background: '#1e293b',
            color: '#94a3b8',
            padding: '6px 12px',
            borderRadius: '6px',
            fontSize: '12px',
            fontWeight: '600',
            border: '1px solid #334155'
          }}>
            Analyst Lead
          </div>
        </div>
      </header>

      {/* ─── View Container ─── */}
      <main style={{ paddingBottom: '40px' }}>
        {page === 'dashboard' && <Dashboard onNavigate={navigate} />}
        {page === 'investigation' && (
          <EventInvestigation
            eventId={pageParams.eventId}
            onNavigate={navigate}
          />
        )}
        {page === 'alerts' && <Alerts onNavigate={navigate} />}
        {page === 'facilities' && (
          <FacilityProfile
            facilityId={pageParams.facilityId}
            onNavigate={navigate}
          />
        )}
        {page === 'evaluation' && <EvaluationPage />}
      </main>
    </div>
  );
}

export default App;
