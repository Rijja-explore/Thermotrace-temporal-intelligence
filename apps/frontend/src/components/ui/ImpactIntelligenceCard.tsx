import React from 'react';
import type { ImpactIntelligence } from '../../services/api';
import { ShieldAlert, Wind, Users, Flame, Navigation, CheckCircle2, AlertCircle, FileText } from 'lucide-react';

interface ImpactIntelligenceCardProps {
  impact?: ImpactIntelligence | null;
  loading?: boolean;
}

export const ImpactIntelligenceCard: React.FC<ImpactIntelligenceCardProps> = ({ impact, loading }) => {
  if (loading) {
    return (
      <div className="card skeleton" style={{ height: '220px', marginBottom: '20px' }}>
        <div style={{ height: '100%' }} />
      </div>
    );
  }

  if (!impact) {
    return (
      <div className="card" style={{ padding: '24px', textAlign: 'center', color: 'var(--text-muted)', marginBottom: '20px' }}>
        No impact intelligence data available.
      </div>
    );
  }

  const {
    incident_priority,
    impact_score,
    impact_tier,
    hazard_radius_m,
    dispersion_length_km,
    population_exposure_formatted,
    wind_vector,
    downwind_impact_summary,
    facility_vulnerability,
    response_recommendations,
    decision_support_mode,
    provenance,
  } = impact;

  const getPriorityBadgeStyle = (priority: string) => {
    switch (priority) {
      case 'CRITICAL':
        return { color: 'var(--risk-critical)', bg: 'rgba(255, 92, 108, 0.15)', border: 'rgba(255, 92, 108, 0.35)' };
      case 'HIGH':
        return { color: 'var(--risk-high)', bg: 'rgba(255, 122, 69, 0.15)', border: 'rgba(255, 122, 69, 0.35)' };
      case 'MEDIUM':
        return { color: 'var(--accent-amber)', bg: 'rgba(255, 181, 71, 0.15)', border: 'rgba(255, 181, 71, 0.35)' };
      default:
        return { color: 'var(--accent-green)', bg: 'rgba(79, 209, 139, 0.15)', border: 'rgba(79, 209, 139, 0.35)' };
    }
  };

  const prioBadge = getPriorityBadgeStyle(incident_priority);

  return (
    <div
      style={{
        background: 'var(--bg-elevated)',
        border: '1px solid var(--border-subtle)',
        borderRadius: 'var(--radius-md)',
        overflow: 'hidden',
        boxShadow: 'var(--shadow-md)',
        marginBottom: '20px',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 18px',
          background: 'var(--bg-primary)',
          borderBottom: '1px solid var(--border-subtle)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          flexWrap: 'wrap',
          gap: '10px',
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <div
            style={{
              padding: '6px',
              borderRadius: 'var(--radius-sm)',
              background: 'rgba(255, 122, 69, 0.12)',
              border: '1px solid rgba(255, 122, 69, 0.3)',
              color: 'var(--risk-high)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <ShieldAlert size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '12px',
                  fontWeight: 700,
                  color: 'var(--text-primary)',
                  letterSpacing: '0.5px',
                  textTransform: 'uppercase',
                }}
              >
                Impact & Response Intelligence
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 800,
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'rgba(67, 217, 232, 0.12)',
                  color: 'var(--accent-cyan)',
                  border: '1px solid rgba(67, 217, 232, 0.3)',
                }}
              >
                MODULE C
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'rgba(167, 139, 250, 0.12)',
                  color: 'var(--accent-purple)',
                  border: '1px solid rgba(167, 139, 250, 0.3)',
                }}
              >
                {provenance || 'DERIVED'}
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Downwind plume dispersion, API 521 radiant hazard, exposure & response SOP
            </div>
          </div>
        </div>

        <span
          style={{
            fontSize: '10px',
            fontFamily: 'var(--font-mono)',
            fontWeight: 800,
            padding: '4px 10px',
            borderRadius: 'var(--radius-full)',
            textTransform: 'uppercase',
            color: prioBadge.color,
            background: prioBadge.bg,
            border: `1px solid ${prioBadge.border}`,
          }}
        >
          {incident_priority} PRIORITY
        </span>
      </div>

      <div style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
        {/* Metric Grid */}
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
          {/* Impact Score */}
          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <Flame size={13} color="var(--risk-critical)" />
              Impact Index
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '22px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                {impact_score}
              </span>
              <span style={{ fontSize: '11px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>/ 100</span>
            </div>
            <div style={{ marginTop: '6px' }}>
              <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', fontWeight: 700, padding: '2px 6px', borderRadius: '3px', background: 'rgba(255, 92, 108, 0.12)', color: 'var(--risk-critical)', border: '1px solid rgba(255, 92, 108, 0.3)' }}>
                TIER: {impact_tier}
              </span>
            </div>
          </div>

          {/* Hazard Radius */}
          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <AlertCircle size={13} color="var(--accent-amber)" />
              Radiant & Plume
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-amber)' }}>
                {hazard_radius_m}
              </span>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>m (API 521)</span>
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', fontFamily: 'var(--font-mono)', marginTop: '4px' }}>
              Plume: <strong style={{ color: 'var(--text-secondary)' }}>{dispersion_length_km} km</strong>
            </div>
          </div>

          {/* Wind Vector */}
          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <Wind size={13} color="var(--accent-cyan)" />
              Wind Vector
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
                {wind_vector.speed_kmh}
              </span>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>km/h ({wind_vector.direction_cardinal})</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '4px', fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px' }}>
              <Navigation size={11} color="var(--accent-cyan)" />
              <span>Heading {wind_vector.downwind_plume_heading}</span>
            </div>
          </div>

          {/* Population Exposure */}
          <div
            style={{
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              borderRadius: 'var(--radius-sm)',
              padding: '12px',
            }}
          >
            <div style={{ fontSize: '10px', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', display: 'flex', alignItems: 'center', gap: '6px', marginBottom: '6px' }}>
              <Users size={13} color="var(--accent-purple)" />
              Downwind Pop.
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '4px' }}>
              <span style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-purple)' }}>
                {population_exposure_formatted}
              </span>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>people</span>
            </div>
            <div style={{ fontSize: '10px', color: 'var(--text-muted)', marginTop: '4px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={downwind_impact_summary}>
              {downwind_impact_summary}
            </div>
          </div>
        </div>

        {/* Facility Vulnerability Banner */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '12px',
            display: 'flex',
            alignItems: 'flex-start',
            gap: '10px',
          }}
        >
          <div
            style={{
              padding: '4px',
              borderRadius: 'var(--radius-xs)',
              background: 'rgba(255, 181, 71, 0.12)',
              color: 'var(--accent-amber)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexShrink: 0,
            }}
          >
            <AlertCircle size={15} />
          </div>
          <div style={{ fontSize: '11px', lineHeight: 1.5 }}>
            <div style={{ fontSize: '10px', fontWeight: 700, color: 'var(--text-muted)', textTransform: 'uppercase', marginBottom: '2px' }}>
              Facility Vulnerability & Receptor Profile
            </div>
            <div style={{ color: 'var(--text-primary)', fontFamily: 'var(--font-mono)' }}>
              {facility_vulnerability}
            </div>
          </div>
        </div>

        {/* Recommended SOP Actions */}
        <div
          style={{
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border-subtle)',
            borderRadius: 'var(--radius-sm)',
            padding: '14px',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
              <FileText size={15} color="var(--accent-green)" />
              <span style={{ fontSize: '11px', fontWeight: 700, color: 'var(--text-primary)', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                Recommended Decision-Support Response SOP
              </span>
            </div>
            <span style={{ fontSize: '9px', fontFamily: 'var(--font-mono)', padding: '2px 8px', borderRadius: 'var(--radius-xs)', background: 'var(--bg-elevated)', border: '1px solid var(--border-subtle)', color: 'var(--text-muted)' }}>
              {decision_support_mode}
            </span>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {response_recommendations.map((action, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'flex-start',
                  gap: '10px',
                  padding: '10px 12px',
                  background: 'var(--bg-elevated)',
                  border: '1px solid var(--border-subtle)',
                  borderRadius: 'var(--radius-sm)',
                }}
              >
                <span
                  style={{
                    width: '18px',
                    height: '18px',
                    borderRadius: '50%',
                    background: 'rgba(79, 209, 139, 0.15)',
                    border: '1px solid rgba(79, 209, 139, 0.4)',
                    color: 'var(--accent-green)',
                    fontSize: '10px',
                    fontFamily: 'var(--font-mono)',
                    fontWeight: 800,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                    marginTop: '2px',
                  }}
                >
                  {idx + 1}
                </span>
                <div style={{ fontSize: '11px', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  {action}
                </div>
              </div>
            ))}
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '12px', paddingTop: '10px', borderTop: '1px solid var(--border-subtle)', fontSize: '10px', color: 'var(--text-muted)' }}>
            <span style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
              <CheckCircle2 size={12} color="var(--accent-cyan)" />
              Formulated via unified risk matrix (Radiant flux, wind vector, population buffer, facility tier)
            </span>
            <span style={{ fontStyle: 'italic' }}>Analyst confirmation required before dispatch</span>
          </div>
        </div>
      </div>
    </div>
  );
};
