import { useQuery } from "@tanstack/react-query";

import { fetchPermisosEfectivos } from "@/features/auth/services/authService";
import { useAuth } from "@/features/auth/hooks/AuthProvider";
import { resolvePersona, type UserPersona } from "@/shared/lib/navPersona";

export function usePermissions() {
  const { isAuthenticated } = useAuth();

  const query = useQuery({
    queryKey: ["permisos-efectivos"],
    queryFn: fetchPermisosEfectivos,
    enabled: isAuthenticated,
    staleTime: 60_000,
    retry: 1,
  });

  const permissions = query.data?.permisos ?? [];
  const roles = query.data?.roles ?? [];
  const persona: UserPersona = resolvePersona(roles, permissions);

  const hasPermission = (permission: string): boolean => permissions.includes(permission);

  return {
    permissions,
    roles,
    persona,
    hasPermission,
    isLoading: isAuthenticated && query.isPending,
    isError: query.isError,
  };
}
