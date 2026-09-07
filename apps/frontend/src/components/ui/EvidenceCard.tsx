import React from 'react';

export interface EvidenceCardProps {
  icon: string | React.ReactNode;
  title: string;
  explanation: string;
  confidence?: string;
  strength?: string;
  type?: 'positive' | 'warning' | 'limitation' | 'neutral';
  source?: string;
  className?: string;
}

export const EvidenceCard: React.FC<EvidenceCardProps> = ({
  icon,
  title,
  explanation,
  confidence,
  strength,
  type = 'positive',
  source,
  className = '',
}) => {
  const badgeText = strength || confidence;

  return (
    <div className={`evidence-card evidence-card--${type} ${className}`}>
      <div className="evidence-card__header">
        <div className="evidence-card__icon">{icon}</div>
        <div className="evidence-card__title">{title}</div>
      </div>
      <div className="evidence-card__explanation">{explanation}</div>
      <div className="evidence-card__footer">
        {badgeText && <span className="evidence-card__strength">{badgeText}</span>}
        {source && <span className="evidence-card__source">{source}</span>}
      </div>
    </div>
  );
};

export default EvidenceCard;
