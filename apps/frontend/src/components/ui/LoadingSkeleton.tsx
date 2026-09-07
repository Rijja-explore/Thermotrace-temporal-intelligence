import React from 'react';

interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  borderRadius?: string | number;
  className?: string;
  style?: React.CSSProperties;
}

export const Skeleton: React.FC<SkeletonProps> = ({
  width = '100%',
  height = '16px',
  borderRadius = '4px',
  className = '',
  style = {},
}) => {
  return (
    <div
      className={`skeleton ${className}`}
      style={{
        width,
        height,
        borderRadius,
        ...style,
      }}
    />
  );
};

export const CardSkeleton: React.FC<{ height?: number | string }> = ({ height = 120 }) => {
  return (
    <div className="card skeleton" style={{ height, minHeight: height, display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>
      <Skeleton width="40%" height={14} />
      <Skeleton width="70%" height={28} />
      <Skeleton width="50%" height={12} />
    </div>
  );
};

export default Skeleton;
