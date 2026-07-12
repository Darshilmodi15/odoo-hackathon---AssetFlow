import { createFileRoute, Outlet, useNavigate } from "@tanstack/react-router";
import { useEffect } from "react";
import { useAuth } from "@/context/AuthContext";
import { AppLayout } from "@/components/layout/AppLayout";

export const Route = createFileRoute("/_app")({
  component: AppShell,
});

function AppShell() {
  const { isAuthenticated, hydrated } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    if (hydrated && !isAuthenticated) navigate({ to: "/login", replace: true });
  }, [isAuthenticated, hydrated, navigate]);
  if (!hydrated) return <div className="flex min-h-screen items-center justify-center bg-background"><div className="h-8 w-8 animate-spin rounded-full border-2 border-primary border-t-transparent" /></div>;
  if (!isAuthenticated) return null;
  return <AppLayout><Outlet /></AppLayout>;
}
