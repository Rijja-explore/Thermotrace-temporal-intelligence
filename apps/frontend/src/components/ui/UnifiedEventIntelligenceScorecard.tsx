import React from 'react';
import { Flame, TrendingUp, Layers } from 'lucide-react';

interface UnifiedScorecardProps {
  classificationLabel?: string;
  confidencePct?: number;
  abnormalityZ?: number;
  abnormalityLevel?: string;
  escalationState?: string;
  riskScore?: number;
  incidentPriority?: string;
  activeSection?: string;
  onSelectSection?: (sectionId: string) => void;
}

export const UnifiedEventIntelligenceScorecard: React.FC<UnifiedScorecardProps> = ({
  classificationLabel = 'Industrial Fire',
  confidencePct = 89,
  abnormalityZ = 4.2,
  abnormalityLevel = 'HIGHLY_ABNORMAL',
  escalationState = 'CRITICAL_ESCALATION',
  riskScore = 84,
  incidentPriority = 'CRITICAL',
  activeSection,
  onSelectSection,
}) => {
  const getAbnormalityBadge = (level: string) => {
    switch (level) {
      case 'HIGHLY_ABNORMAL':
        return { color: 'var(--risk-critical)', bg: 'rgba(255, 92, 108, 0.15)', border: 'rgba(255, 92, 108, 0.35)' };
      case 'ABNORMAL':
        return { color: 'var(--risk-high)', bg: 'rgba(255, 122, 69, 0.15)', border: 'rgba(255, 122, 69, 0.35)' };
      case 'SLIGHTLY_DEVIATING':
        return { color: 'var(--accent-amber)', bg: 'rgba(255, 181, 71, 0.15)', border: 'rgba(255, 181, 71, 0.35)' };
      default:
        return { color: 'var(--accent-green)', bg: 'rgba(79, 209, 139, 0.15)', border: 'rgba(79, 209, 139, 0.35)' };
    }
  };

  const getEscalationBadge = (state: string) => {
    switch (state) {
      case 'CRITICAL_ESCALATION':
      case 'CRITICAL':
        return { color: 'var(--risk-critical)', bg: 'rgba(255, 92, 108, 0.15)', border: 'rgba(255, 92, 108, 0.35)' };
      case 'ESCALATING':
        return { color: 'var(--risk-high)', bg: 'rgba(255, 122, 69, 0.15)', border: 'rgba(255, 122, 69, 0.35)' };
      case 'WATCH':
        return { color: 'var(--accent-amber)', bg: 'rgba(255, 181, 71, 0.15)', border: 'rgba(255, 181, 71, 0.35)' };
      default:
        return { color: 'var(--accent-green)', bg: 'rgba(79, 209, 139, 0.15)', border: 'rgba(79, 209, 139, 0.35)' };
    }
  };

  const getPriorityBadge = (p: string) => {
    switch (p) {
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

  const anomStyle = getAbnormalityBadge(abnormalityLevel);
  const escStyle = getEscalationBadge(escalationState);
  const prioStyle = getPriorityBadge(incidentPriority);

  const navItems = [
    { id: 'fingerprint', label: '1. Facility Baseline & Fingerprint' },
    { id: 'early-warning', label: '2. Early Warning & Forecast' },
    { id: 'xai', label: '3. Explainable AI (SHAP / DiCE / Attention)' },
    { id: 'impact', label: '4. Impact & Response Intelligence' },
  ];

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
      {/* Top Banner Header */}
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
              background: 'rgba(67, 217, 232, 0.12)',
              border: '1px solid rgba(67, 217, 232, 0.3)',
              color: 'var(--accent-cyan)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
            }}
          >
            <Layers size={18} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span
                style={{
                  fontSize: '11px',
                  fontWeight: 800,
                  color: 'var(--text-primary)',
                  letterSpacing: '1px',
                  textTransform: 'uppercase',
                  fontFamily: 'var(--font-mono)',
                }}
              >
                THERMOTRACE UNIFIED EVENT INTELLIGENCE
              </span>
              <span
                style={{
                  fontSize: '9px',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 800,
                  padding: '2px 6px',
                  borderRadius: 'var(--radius-xs)',
                  background: 'rgba(255, 92, 108, 0.15)',
                  color: 'var(--risk-critical)',
                  border: '1px solid rgba(255, 92, 108, 0.35)',
                }}
              >
                DOSSIER
              </span>
            </div>
            <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: '2px' }}>
              Multi-model operational synthesis: Satellite Observation → Learned Baseline → Temporal Trend → Risk Assessment
            </div>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
          <span
            style={{
              fontSize: '9px',
              fontFamily: 'var(--font-mono)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-xs)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--accent-green)',
            }}
          >
            FIRMS: LIVE
          </span>
          <span
            style={{
              fontSize: '9px',
              fontFamily: 'var(--font-mono)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-xs)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--accent-cyan)',
            }}
          >
            BASELINE: DERIVED
          </span>
          <span
            style={{
              fontSize: '9px',
              fontFamily: 'var(--font-mono)',
              padding: '2px 6px',
              borderRadius: 'var(--radius-xs)',
              background: 'var(--bg-secondary)',
              border: '1px solid var(--border-subtle)',
              color: 'var(--accent-purple)',
            }}
          >
            ATTENTION: DERIVED
          </span>
        </div>
      </div>

      {/* 4-Stat Core Pillar Grid */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(4, 1fr)',
          background: 'var(--bg-secondary)',
          borderBottom: '1px solid var(--border-subtle)',
        }}
      >
        {/* Stat 1: Classification */}
        <div
          style={{
            padding: '16px',
            borderRight: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '10px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '4px',
              }}
            >
              1. Classification
            </div>
            <div
              style={{
                fontSize: '14px',
                fontWeight: 700,
                color: 'var(--text-primary)',
                textTransform: 'capitalize',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
              title={classificationLabel}
            >
              {classificationLabel}
            </div>
          </div>
          <div style={{ marginTop: '12px', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
            <span style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--accent-cyan)' }}>
              {confidencePct}%
            </span>
            <span
              style={{
                fontSize: '9px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 700,
                padding: '2px 6px',
                borderRadius: 'var(--radius-xs)',
                background: 'rgba(67, 217, 232, 0.12)',
                color: 'var(--accent-cyan)',
                border: '1px solid rgba(67, 217, 232, 0.3)',
              }}
            >
              CONFIDENCE
            </span>
          </div>
        </div>

        {/* Stat 2: Facility Abnormality */}
        <div
          style={{
            padding: '16px',
            borderRight: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '10px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '4px',
              }}
            >
              2. Facility Abnormality
            </div>
            <div style={{ fontSize: '15px', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <Flame size={16} color="var(--risk-critical)" />
              <span style={{ fontFamily: 'var(--font-mono)' }}>+{abnormalityZ > 0 ? abnormalityZ : 4.2}σ</span>
            </div>
          </div>
          <div style={{ marginTop: '12px' }}>
            <span
              style={{
                display: 'block',
                textAlign: 'center',
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                padding: '3px 6px',
                borderRadius: 'var(--radius-xs)',
                textTransform: 'uppercase',
                color: anomStyle.color,
                background: anomStyle.bg,
                border: `1px solid ${anomStyle.border}`,
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
              }}
            >
              {abnormalityLevel.replace(/_/g, ' ')}
            </span>
          </div>
        </div>

        {/* Stat 3: Escalation State */}
        <div
          style={{
            padding: '16px',
            borderRight: '1px solid var(--border-subtle)',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '10px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '4px',
              }}
            >
              3. Escalation State
            </div>
            <div style={{ fontSize: '13px', fontWeight: 800, color: 'var(--text-primary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
              <TrendingUp size={16} color="var(--accent-amber)" />
              <span style={{ textTransform: 'capitalize' }}>{escalationState.replace(/_/g, ' ')}</span>
            </div>
          </div>
          <div style={{ marginTop: '12px' }}>
            <span
              style={{
                display: 'block',
                textAlign: 'center',
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                padding: '3px 6px',
                borderRadius: 'var(--radius-xs)',
                textTransform: 'uppercase',
                color: escStyle.color,
                background: escStyle.bg,
                border: `1px solid ${escStyle.border}`,
              }}
            >
              VELOCITY: SURGING
            </span>
          </div>
        </div>

        {/* Stat 4: Risk & Priority */}
        <div
          style={{
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
            justifyContent: 'space-between',
          }}
        >
          <div>
            <div
              style={{
                fontSize: '10px',
                fontWeight: 700,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.5px',
                marginBottom: '4px',
              }}
            >
              4. Risk & Incident Priority
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
              <span style={{ fontSize: '20px', fontWeight: 800, fontFamily: 'var(--font-mono)', color: 'var(--text-primary)' }}>
                {riskScore}
              </span>
              <span style={{ fontSize: '10px', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)' }}>
                / 100 RISK
              </span>
            </div>
          </div>
          <div style={{ marginTop: '12px' }}>
            <span
              style={{
                display: 'block',
                textAlign: 'center',
                fontSize: '10px',
                fontFamily: 'var(--font-mono)',
                fontWeight: 800,
                padding: '3px 6px',
                borderRadius: 'var(--radius-xs)',
                textTransform: 'uppercase',
                color: prioStyle.color,
                background: prioStyle.bg,
                border: `1px solid ${prioStyle.border}`,
              }}
            >
              PRIORITY: {incidentPriority}
            </span>
          </div>
        </div>
      </div>

      {/* Nav Flow Bar */}
      {onSelectSection && (
        <div
          style={{
            padding: '8px 16px',
            background: 'var(--bg-primary)',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
            overflowX: 'auto',
          }}
        >
          <span
            style={{
              fontSize: '10px',
              fontFamily: 'var(--font-mono)',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.5px',
              marginRight: '6px',
              whiteSpace: 'nowrap',
            }}
          >
            Intelligence Flow:
          </span>
          {navItems.map((item) => {
            const isActive = activeSection === item.id;
            return (
              <button
                key={item.id}
                onClick={() => onSelectSection(item.id)}
                style={{
                  padding: '4px 10px',
                  borderRadius: 'var(--radius-xs)',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '11px',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                  border: '1px solid',
                  transition: 'all var(--transition-fast)',
                  background: isActive ? 'rgba(67, 217, 232, 0.15)' : 'var(--bg-elevated)',
                  borderColor: isActive ? 'var(--accent-cyan)' : 'var(--border-subtle)',
                  color: isActive ? 'var(--accent-cyan)' : 'var(--text-secondary)',
                }}
              >
                {item.label}
              </button>
            );
          })}
        </div>
      )}
    </div>
  );
};
