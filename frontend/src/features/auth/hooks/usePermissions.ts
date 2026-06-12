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
  });

  const hasPermission = (permission: string): boolean =>
    (query.data ?? []).includes(permission);

  return {
    permissions: query.data ?? [],
    hasPermission,
    isLoading: query.isLoading,
  };
}
