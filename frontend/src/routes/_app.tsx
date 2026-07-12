import { createFileRoute, Outlet, redirect } from "@tanstack/react-router";
import { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { AppLayout } from "@/components/layout/AppLayout";

export const Route = createFileRoute("/_app")({
  // Server-side / pre-render guard: redirect if no auth token present.
  // Works best in SSR mode; in SPA mode the component-level effect below
  // handles the case where the token is removed after initial hydration.
  beforeLoad: () => {
    if (typeof window !== "undefined") {
      const hasToken =
        window.localStorage.getItem("assetflow.userId") !== null ||
        window.localStorage.getItem("assetflow.token") !== null;
      if (!hasToken) {
        throw redirect({ to: "/login", replace: true });
      }
    }
  },
  component: AppShell,
});

function AppShell() {
  const { isAuthenticated, hydrated } = useAuth();

  // Handle token removal after mount (e.g., session expiry, manual logout)
  useEffect(() => {
    if (hydrated && !isAuthenticated) {
      window.location.replace("/login");
    }
  }, [isAuthenticated, hydrated]);

  if (!hydrated) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" />
      </div>
    );
  }
  if (!isAuthenticated) return null;
  return (
    <AppLayout>
      <Outlet />
    </AppLayout>
  );
}
