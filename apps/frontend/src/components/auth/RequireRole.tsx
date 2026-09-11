import React from 'react';
import { useAuth } from '../../services/AuthContext';
import { AccessDenied } from '../../pages/AccessDenied';

interface RequireRoleProps {
  allowedRoles: string[];
  children: React.ReactNode;
  onNavigate?: (page: string, params?: any) => void;
}

export const RequireRole: React.FC<RequireRoleProps> = ({
  allowedRoles,
  children,
  onNavigate,
}) => {
  const { currentUser, isAuthenticated } = useAuth();

  if (!isAuthenticated || !currentUser) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: '#94A3B8' }}>
        Please log in to access this section.
      </div>
    );
  }

  const userRole = (currentUser.role || 'ANALYST').toUpperCase();
  const allowedUpper = allowedRoles.map((r) => r.toUpperCase());

  if (!allowedUpper.includes(userRole)) {
    return (
      <AccessDenied
        requiredRoles={allowedUpper}
        userRole={userRole}
        onNavigate={onNavigate}
      />
    );
  }

  return <>{children}</>;
};

export default RequireRole;
