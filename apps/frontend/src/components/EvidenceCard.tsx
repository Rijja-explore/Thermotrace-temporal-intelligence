interface EvidenceCardProps {
  items: string[];
}

export default function EvidenceCard({ items }: EvidenceCardProps) {
  if (!items || items.length === 0) {
    return (
      <div className="evidence-card">
        <span className="evidence-card__text" style={{ color: 'var(--text-muted)' }}>
          No evidence factors recorded
        </span>
      </div>
    );
  }

  return (
    <div>
      {items.map((item, idx) => (
        <div className="evidence-card" key={idx}>
          <span className="evidence-card__icon">✓</span>
          <span className="evidence-card__text">{item}</span>
        </div>
      ))}
    </div>
  );
}
