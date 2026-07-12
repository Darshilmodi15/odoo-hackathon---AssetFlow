import { useEffect } from "react";
import { useNavigate } from "@tanstack/react-router";
import { useAuth } from "@/context/AuthContext";
import { toast } from "sonner";
import type { Role } from "@/types";

/**
 * Redirect to /dashboard if the current user doesn't have one of the required roles.
 * Returns `{ permitted }` for conditional rendering inside the component body.
 *
 * Usage:
 *   const { permitted } = useRoleGuard(["admin", "asset_manager"]);
 *   if (!permitted) return null;
 */
export function useRoleGuard(roles: Role[]): { permitted: boolean } {
  const { user, hydrated } = useAuth();
  const navigate = useNavigate();

  const permitted = hydrated && !!user && roles.includes(user.role);

  useEffect(() => {
    if (!hydrated) return;
    if (!user) {
      navigate({ to: "/login", replace: true });
      return;
    }
    if (!roles.includes(user.role)) {
      toast.error("You don't have permission to access that page.");
      navigate({ to: "/dashboard", replace: true });
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [hydrated, user]);

  return { permitted };
}
