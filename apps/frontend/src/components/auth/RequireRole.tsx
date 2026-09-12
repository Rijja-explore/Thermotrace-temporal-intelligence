import React from 'react';
import { useAuth } from '../../services/AuthContext';

interface RequireRoleProps {
  allowedRoles?: string[];
  children: React.ReactNode;
  onNavigate?: (page: string, params?: any) => void;
}

export const RequireRole: React.FC<RequireRoleProps> = ({
  children,
}) => {
  const { currentUser, isAuthenticated } = useAuth();

  if (!isAuthenticated || !currentUser) {
    return (
      <div style={{ padding: '32px', textAlign: 'center', color: '#94A3B8' }}>
        Please log in to access this section.
      </div>
    );
  }

  return <>{children}</>;
};

export default RequireRole;

