import type { ReactNode } from "react";

import { usePermissions } from "@/features/auth/hooks/usePermissions";

type PermissionGateProps = {
  permission: string;
  children: ReactNode;
  fallback?: ReactNode;
};

export function PermissionGate({ permission, children, fallback = null }: PermissionGateProps) {
  const { hasPermission, isLoading } = usePermissions();

  if (isLoading) {
    return null;
  }

  if (!hasPermission(permission)) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
}
