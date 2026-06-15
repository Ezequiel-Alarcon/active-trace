import { useAuth } from '@/features/auth/components/AuthProvider';
import Forbidden403 from './Forbidden403';
import type { ReactNode } from 'react';

interface RequirePermissionProps {
  permission: string;
  children: ReactNode;
}

/**
 * Renders children only when the session includes the required permission.
 * Fail-closed: no permission → Forbidden403. Empty permissions → blocked.
 */
export default function RequirePermission({
  permission,
  children,
}: RequirePermissionProps) {
  const { hasPermission } = useAuth();

  if (!hasPermission(permission)) {
    return <Forbidden403 />;
  }

  return <>{children}</>;
}
