import { useQuery } from "@tanstack/react-query";

import { fetchPermisosEfectivos } from "@/features/auth/services/authService";
import { useAuth } from "@/features/auth/hooks/AuthProvider";

export function usePermissions() {
  const { isAuthenticated } = useAuth();

  const query = useQuery({
    queryKey: ["permisos-efectivos"],
    queryFn: fetchPermisosEfectivos,
    enabled: isAuthenticated,
    staleTime: 60_000,
    retry: 1,
  });

  const permissions = query.data ?? [];

  const hasPermission = (permission: string): boolean => permissions.includes(permission);

  return {
    permissions,
    hasPermission,
    isLoading: isAuthenticated && query.isPending,
    isError: query.isError,
  };
}
