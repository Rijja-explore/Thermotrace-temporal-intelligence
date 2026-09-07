import { useEffect, useState } from 'react';
import type { Alert } from '../services/api';
import { fetchAlerts } from '../services/api';

interface AlertsProps {
  onNavigate?: (page: string, params?: any) => void;
}

function getRiskColor(severity: string): string {
  if (severity === 'critical') return 'var(--risk-critical)';
  if (severity === 'high') return 'var(--risk-high)';
  if (severity === 'medium') return 'var(--risk-medium)';
  return 'var(--risk-low)';
}

export default function Alerts({ onNavigate }: AlertsProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);
  const [filterRegion, setFilterRegion] = useState('India');
  const [filterSeverity, setFilterSeverity] = useState('');
  const [criticalCount, setCriticalCount] = useState(0);
  const [highCount, setHighCount] = useState(0);
  const [mediumCount, setMediumCount] = useState(0);

  useEffect(() => {
    async function load() {
      setLoading(true);
      setError(false);
      try {
        const res = await fetchAlerts(filterSeverity || undefined, filterRegion);
        setAlerts(res.alerts);
        setCriticalCount(res.critical_count);
        setHighCount(res.high_count);
        setMediumCount(res.medium_count);
      } catch {
        setAlerts([]);
        setError(true);
      }
      setLoading(false);
    }
    load();
  }, [filterSeverity, filterRegion]);

  return (
    <div className="alerts-page">
      <div className="alerts-page-inner">
        {/* Header */}
        <div className="alerts-page-header">
          <div>
            <div className="page-title">Alert Center</div>
            <div className="page-subtitle">
              Priority thermal events requiring analyst attention — {filterRegion}
            </div>
            <div className="alerts-summary-strip">
              <span className="risk-badge risk-badge--critical">{criticalCount} Critical</span>
              <span className="risk-badge risk-badge--high">{highCount} High</span>
              <span className="risk-badge risk-badge--medium">{mediumCount} Medium</span>
              <span className="risk-badge risk-badge--cyan">{alerts.length} Total</span>
            </div>
          </div>

          <div className="alerts-filter-bar">
            <select
              className="toolbar-select"
              style={{ width: '200px' }}
              value={filterRegion}
              onChange={e => setFilterRegion(e.target.value)}
            >
              <optgroup label="Broad Geographies">
                <option value="India">🇮🇳 India (Primary Focus)</option>
                <option value="Global">🌍 Global</option>
                <option value="All">🌐 All Worldwide</option>
              </optgroup>
              <optgroup label="Indian States">
                <option value="Gujarat">Gujarat</option>
                <option value="Maharashtra">Maharashtra</option>
                <option value="Odisha">Odisha</option>
                <option value="West Bengal">West Bengal</option>
                <option value="Tamil Nadu">Tamil Nadu</option>
                <option value="Jharkhand">Jharkhand</option>
                <option value="Assam">Assam</option>
              </optgroup>
            </select>

            <select
              className="toolbar-select"
              style={{ width: '140px' }}
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
            >
              <option value="">All Severities</option>
              <option value="critical">Critical</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
            </select>
          </div>
        </div>

        {/* Loading */}
        {loading && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1px' }}>
            {Array.from({ length: 8 }).map((_, i) => (
              <div
                key={i}
                className="skeleton"
                style={{ height: '64px', borderRadius: i === 0 ? 'var(--radius-md) var(--radius-md) 0 0' : i === 7 ? '0 0 var(--radius-md) var(--radius-md)' : '0' }}
              />
            ))}
          </div>
        )}

        {/* Error */}
        {!loading && error && (
          <div className="error-state">
            <div className="error-state__icon">⚠</div>
            <div className="error-state__title">Alert feed unavailable</div>
            <div className="error-state__desc">
              The live alert feed could not be reached. Showing cached data if available.
            </div>
            <div className="error-state__cache-note">Live FIRMS refresh is unavailable. Showing cached demo dataset.</div>
            <button className="error-state__retry" onClick={() => setLoading(true)}>
              Retry Connection
            </button>
          </div>
        )}

        {/* Empty */}
        {!loading && !error && alerts.length === 0 && (
          <div className="empty-state">
            <div className="empty-state__icon">✓</div>
            <div className="empty-state__title">No alerts match the current filters</div>
            <div className="empty-state__desc">
              No high-risk events found for {filterRegion} with the current severity filter.
              Try expanding the region or removing the severity filter.
            </div>
            <button className="empty-state__action" onClick={() => { setFilterSeverity(''); setFilterRegion('India'); }}>
              Reset Filters
            </button>
          </div>
        )}

        {/* Alert list */}
        {!loading && !error && alerts.length > 0 && (
          <div className="alerts-list">
            {alerts.map(alert => (
              <div
                key={alert.alert_id}
                className="alerts-list-item"
                onClick={() => onNavigate?.('investigation', { eventId: alert.event_id })}
                role="button"
                tabIndex={0}
                onKeyDown={e => e.key === 'Enter' && onNavigate?.('investigation', { eventId: alert.event_id })}
              >
                {/* Priority bar */}
                <div className={`alerts-list-item__priority-bar alerts-list-item__priority-bar--${alert.severity}`} />

                {/* Main content */}
                <div className="alerts-list-item__main">
                  <div className="alerts-list-item__id">{alert.event_id}</div>
                  <div className="alerts-list-item__title">{alert.title}</div>
                  <div className="alerts-list-item__location">
                    📍 {alert.location}
                    <span className={`status-badge status-badge--${alert.status}`} style={{ marginLeft: '8px' }}>
                      {alert.status.replace(/_/g, ' ')}
                    </span>
                  </div>
                </div>

                {/* Scores */}
                <div className="alerts-list-item__scores">
                  <div className="alerts-list-item__score-block">
                    <div className="alerts-list-item__score-label">Risk</div>
                    <div
                      className="alerts-list-item__score-value"
                      style={{ color: getRiskColor(alert.severity) }}
                    >
                      {alert.operational_risk}
                    </div>
                  </div>
                  <div className="alerts-list-item__score-block">
                    <div className="alerts-list-item__score-label">Conf.</div>
                    <div
                      className="alerts-list-item__score-value"
                      style={{ color: 'var(--accent-cyan)' }}
                    >
                      {Math.round(alert.confidence <= 1 ? alert.confidence * 100 : alert.confidence)}%
                    </div>
                  </div>
                  <div className="alerts-list-item__score-block">
                    <div className="alerts-list-item__score-label">Severity</div>
                    <span className={`risk-badge risk-badge--${alert.severity}`}>{alert.severity}</span>
                  </div>
                </div>

                {/* Time */}
                <div className="alerts-list-item__time">
                  {alert.timestamp ? alert.timestamp.split('T')[0] : '—'}
                </div>

                {/* Action */}
                <div className="alerts-list-item__action">
                  <button
                    className="btn btn--ghost btn--sm"
                    onClick={e => {
                      e.stopPropagation();
                      onNavigate?.('investigation', { eventId: alert.event_id });
                    }}
                  >
                    Investigate →
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Footer note */}
        {!loading && alerts.length > 0 && (
          <div style={{ marginTop: '16px', fontSize: '11px', color: 'var(--text-disabled)', textAlign: 'center' }}>
            Showing {alerts.length} alert{alerts.length !== 1 ? 's' : ''} for {filterRegion}.
            Click any row to open the full event investigation.
          </div>
        )}
      </div>
    </div>
  );
}
