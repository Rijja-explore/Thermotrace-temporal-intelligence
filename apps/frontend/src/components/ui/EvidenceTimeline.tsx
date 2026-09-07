import React from 'react';

interface EvidenceTimelineProps {
  label?: string;
  isAbnormal?: boolean;
  persistenceRatio?: number;
  detectionCount30d?: number;
  firstDetection?: string;
  timeWindowStart?: string;
  timeWindowEnd?: string;
  facilityName?: string;
  landcover?: string;
}

const EvidenceTimeline: React.FC<EvidenceTimelineProps> = ({
  label = '',
  isAbnormal = false,
  persistenceRatio = 0,
  detectionCount30d = 0,
  firstDetection,
  timeWindowStart,
  timeWindowEnd,
  facilityName,
  landcover,
}) => {
  const isIndustrial = label.toLowerCase().includes('industrial') || label.toLowerCase().includes('persistent');
  const isNatural = label.toLowerCase().includes('agri') || label.toLowerCase().includes('forest') || label.toLowerCase().includes('wildfire');
  const isUnknown = label.toLowerCase().includes('unknown');

  const startDate = timeWindowStart?.split('T')[0] ?? '—';
  const endDate = timeWindowEnd?.split('T')[0] ?? 'Now';

  const milestones = [
    {
      label: 'First Detection',
      detail: firstDetection ?? startDate,
      status: 'normal' as const,
      desc: 'Initial thermal anomaly recorded',
    },
    {
      label: 'Recurring Pattern',
      detail: `${detectionCount30d || '—'} detections/30d`,
      status: persistenceRatio >= 0.6 ? ('active' as const) : ('normal' as const),
      desc: `Persistence: ${Math.round((persistenceRatio || 0) * 100)}%`,
    },
    {
      label: 'Facility Match',
      detail: facilityName ? '< 1 km' : 'None within 5 km',
      status: (isIndustrial && facilityName) ? ('active' as const) : ('normal' as const),
      desc: facilityName ?? 'No known facility',
    },
    {
      label: 'Land Cover',
      detail: landcover ?? 'Industrial',
      status: 'normal' as const,
      desc: isIndustrial ? 'Industrial land cover confirmed' : isNatural ? 'Agricultural / forest' : 'Mixed',
    },
    {
      label: 'Anomaly Flag',
      detail: isAbnormal ? 'Flagged' : 'Stable',
      status: isAbnormal ? ('critical' as const) : ('normal' as const),
      desc: isAbnormal ? 'Above baseline threshold' : 'Within expected range',
    },
    {
      label: 'Current Status',
      detail: isUnknown ? 'Verify' : isAbnormal ? 'Alert' : 'Monitored',
      status: isUnknown ? ('active' as const) : isAbnormal ? ('critical' as const) : ('active' as const),
      desc: endDate,
    },
  ];

  return (
    <div style={{ marginBottom: '20px' }}>
      <div className="section-title">Event Timeline — {startDate} → {endDate}</div>
      <div className="evidence-timeline">
        {milestones.map((m, i) => (
          <React.Fragment key={i}>
            <div className={`timeline-milestone timeline-milestone--${m.status}`}>
              <div className="timeline-milestone__dot" />
              <div className="timeline-milestone__label">{m.label}</div>
              <div className="timeline-milestone__detail">{m.detail}</div>
              <div style={{ fontSize: '9px', color: 'var(--text-disabled)', textAlign: 'center', maxWidth: '68px', lineHeight: '1.3', marginTop: '2px' }}>
                {m.desc}
              </div>
            </div>
            {i < milestones.length - 1 && (
              <div style={{
                width: '100%',
                height: '1px',
                background: 'var(--border-subtle)',
                flexShrink: 0,
                alignSelf: 'flex-start',
                marginTop: '7px',
              }} />
            )}
          </React.Fragment>
        ))}
      </div>
    </div>
  );
};

export default EvidenceTimeline;
