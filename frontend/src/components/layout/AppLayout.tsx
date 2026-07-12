import { Link, useRouterState, useNavigate } from "@tanstack/react-router";
import {
  LayoutDashboard,
  Building2,
  Package,
  ArrowLeftRight,
  Calendar,
  Wrench,
  ClipboardCheck,
  BarChart3,
  Bell,
  Settings,
  HelpCircle,
  LogOut,
  Menu,
  Search,
  Moon,
  Sun,
  User as UserIcon,
  ChevronDown,
  Sparkles,
} from "lucide-react";
import { useEffect, useState, type ReactNode } from "react";
import { useAuth, roleLabel } from "@/context/AuthContext";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
  DropdownMenuRadioGroup,
  DropdownMenuRadioItem,
} from "@/components/ui/dropdown-menu";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { store } from "@/mocks/store";
import { USE_MOCKS } from "@/services/apiClient";
import { useStore } from "@/hooks/useStore";
import { cn } from "@/lib/utils";
import type { Role } from "@/types";

interface NavItem {
  to: string;
  label: string;
  icon: typeof LayoutDashboard;
  roles?: Role[];
}

const NAV: NavItem[] = [
  { to: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  {
    to: "/employee/dashboard",
    label: "Employee Portal",
    icon: LayoutDashboard,
    roles: ["employee"],
  },
  { to: "/organization", label: "Organization Setup", icon: Building2, roles: ["admin"] },
  { to: "/assets", label: "Assets", icon: Package },
  { to: "/allocations", label: "Allocations & Transfers", icon: ArrowLeftRight },
  { to: "/bookings", label: "Resource Bookings", icon: Calendar },
  { to: "/maintenance", label: "Maintenance", icon: Wrench },
  { to: "/audits", label: "Asset Audits", icon: ClipboardCheck, roles: ["admin", "asset_manager"] },
  { to: "/reports", label: "Reports & Analytics", icon: BarChart3 },
  { to: "/activity", label: "Activity & Notifications", icon: Bell },
  { to: "/settings", label: "Settings", icon: Settings },
];

const PAGE_TITLES: Record<string, string> = {
  "/dashboard": "Dashboard",
  "/employee/dashboard": "Employee Portal",
  "/organization": "Organization Setup",
  "/assets": "Assets",
  "/allocations": "Allocations & Transfers",
  "/bookings": "Resource Bookings",
  "/maintenance": "Maintenance",
  "/audits": "Asset Audits",
  "/reports": "Reports & Analytics",
  "/activity": "Activity & Notifications",
  "/settings": "Settings",
  "/profile": "My Profile",
};

function useTheme() {
  const [dark, setDark] = useState(
    () => typeof window !== "undefined" && document.documentElement.classList.contains("dark"),
  );
  useEffect(() => {
    document.documentElement.classList.toggle("dark", dark);
  }, [dark]);
  return { dark, toggle: () => setDark((d) => !d) };
}

function SidebarContent({ onNavigate }: { onNavigate?: () => void }) {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const items = NAV.filter((i) => !i.roles || (user && i.roles.includes(user.role)));

  return (
    <div className="flex h-full flex-col bg-sidebar text-sidebar-foreground">
      <div className="flex h-14 items-center gap-2 border-b border-sidebar-border px-4">
        <div className="grid h-8 w-8 place-items-center rounded-md bg-primary text-primary-foreground font-bold shadow-sm">
          A
        </div>
        <div>
          <div className="font-semibold leading-tight">AssetFlow</div>
          <div className="text-[10px] font-medium uppercase tracking-[0.18em] text-sidebar-foreground/50">
            Operations
          </div>
        </div>
      </div>
      <nav className="flex-1 space-y-0.5 overflow-y-auto p-2">
        {items.map((item) => {
          const active =
            pathname === item.to ||
            (item.to !== "/dashboard" && pathname.startsWith(item.to + "/"));
          return (
            <Link
              key={item.to}
              to={item.to}
              onClick={onNavigate}
              className={cn(
                "flex items-center gap-3 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active
                  ? "bg-sidebar-primary text-sidebar-primary-foreground shadow-sm"
                  : "hover:bg-sidebar-accent hover:text-sidebar-accent-foreground text-sidebar-foreground/80",
              )}
            >
              <item.icon className="h-4 w-4 shrink-0" />
              <span className="truncate">{item.label}</span>
            </Link>
          );
        })}
      </nav>
      <div className="space-y-0.5 border-t border-sidebar-border p-2">
        <button
          onClick={() => {
            navigate({ to: "/settings" });
            onNavigate?.();
          }}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-sidebar-accent text-sidebar-foreground/80"
        >
          <HelpCircle className="h-4 w-4" /> Help
        </button>
        <button
          onClick={() => {
            navigate({ to: "/profile" });
            onNavigate?.();
          }}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-sidebar-accent text-sidebar-foreground/80"
        >
          <UserIcon className="h-4 w-4" /> Profile
        </button>
        <button
          onClick={() => {
            logout();
            navigate({ to: "/login" });
          }}
          className="flex w-full items-center gap-3 rounded-md px-3 py-2 text-sm hover:bg-sidebar-accent text-sidebar-foreground/80"
        >
          <LogOut className="h-4 w-4" /> Logout
        </button>
        {user && (
          <div className="mt-2 flex items-center gap-2 rounded-md bg-sidebar-accent/50 px-3 py-2">
            <Avatar className="h-8 w-8">
              <AvatarFallback>
                {user.name
                  .split(" ")
                  .map((n) => n[0])
                  .slice(0, 2)
                  .join("")}
              </AvatarFallback>
            </Avatar>
            <div className="min-w-0 flex-1">
              <div className="truncate text-xs font-medium">{user.name}</div>
              <div className="truncate text-[10px] text-sidebar-foreground/60">
                {roleLabel(user.role)}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

function Header({ onOpenSidebar }: { onOpenSidebar: () => void }) {
  const pathname = useRouterState({ select: (s) => s.location.pathname });
  const title =
    Object.entries(PAGE_TITLES).find(([p]) => pathname.startsWith(p))?.[1] || "AssetFlow";
  const { user, setDemoUser, logout } = useAuth();
  const navigate = useNavigate();
  const { dark, toggle } = useTheme();
  const unread = useStore(() =>
    user ? store.notifications.filter((n) => n.userId === user.id && !n.read).length : 0,
  );
  const employees = useStore(() => store.employees);

  return (
    <header className="sticky top-0 z-30 flex h-14 items-center gap-2 border-b border-border bg-background/88 px-3 backdrop-blur-xl sm:px-4">
      <Button variant="ghost" size="icon" className="md:hidden" onClick={onOpenSidebar}>
        <Menu className="h-5 w-5" />
      </Button>
      <h1 className="min-w-0 truncate text-base font-semibold sm:text-lg">{title}</h1>
      <div className="ml-auto flex items-center gap-1 sm:gap-2">
        <div className="relative hidden sm:block">
          <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder="Search assets, employees…"
            className="h-9 w-full max-w-64 border-input/70 bg-muted/40 pl-8 shadow-inner"
            onKeyDown={(e) => {
              if (e.key === "Enter")
                navigate({
                  to: "/assets",
                  search: { q: (e.target as HTMLInputElement).value } as never,
                });
            }}
          />
        </div>
        <Button variant="ghost" size="icon" onClick={toggle} aria-label="Toggle theme">
          {dark ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
        </Button>
        <Button
          variant="ghost"
          size="icon"
          className="relative"
          onClick={() => navigate({ to: "/activity" })}
          aria-label="Notifications"
        >
          <Bell className="h-4 w-4" />
          {unread > 0 && (
            <Badge
              className="absolute -right-1 -top-1 h-4 min-w-4 px-1 text-[10px]"
              variant="destructive"
            >
              {unread}
            </Badge>
          )}
        </Button>
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" className="h-9 gap-2 px-2 hover:bg-accent">
                <Avatar className="h-7 w-7">
                  <AvatarFallback className="text-xs">
                    {user.name
                      .split(" ")
                      .map((n) => n[0])
                      .slice(0, 2)
                      .join("")}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden text-left sm:block">
                  <div className="text-xs font-medium leading-tight">{user.name}</div>
                  <div className="text-[10px] leading-tight text-muted-foreground">
                    {roleLabel(user.role)}
                  </div>
                </div>
                <ChevronDown className="h-3 w-3 text-muted-foreground" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-64">
              <DropdownMenuLabel>{user.name}</DropdownMenuLabel>
              <DropdownMenuItem onClick={() => navigate({ to: "/profile" })}>
                My Profile
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate({ to: "/settings" })}>
                Settings
              </DropdownMenuItem>
              {USE_MOCKS && (
                <>
                  <DropdownMenuSeparator />
                  <DropdownMenuLabel className="text-xs text-muted-foreground">
                    Demo Role Switcher
                  </DropdownMenuLabel>
                  <DropdownMenuRadioGroup value={user.id} onValueChange={setDemoUser}>
                    {(["admin", "asset_manager", "department_head", "employee"] as Role[]).map(
                      (role) => {
                        const sample = employees.find((e) => e.role === role);
                        if (!sample) return null;
                        return (
                          <DropdownMenuRadioItem key={role} value={sample.id}>
                            {roleLabel(role)} — {sample.name}
                          </DropdownMenuRadioItem>
                        );
                      },
                    )}
                  </DropdownMenuRadioGroup>
                </>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => {
                  logout();
                  navigate({ to: "/login" });
                }}
              >
                <LogOut className="mr-2 h-4 w-4" /> Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}

export function AppLayout({ children }: { children: ReactNode }) {
  const [mobileOpen, setMobileOpen] = useState(false);
  return (
    <div className="flex min-h-screen w-full bg-background text-foreground">
      <aside className="hidden w-64 shrink-0 border-r border-sidebar-border bg-sidebar md:block">
        <div className="sticky top-0 h-screen">
          <SidebarContent />
        </div>
      </aside>
      <Sheet open={mobileOpen} onOpenChange={setMobileOpen}>
        <SheetTrigger asChild>
          <span className="hidden" />
        </SheetTrigger>
        <SheetContent side="left" className="w-64 p-0">
          <SidebarContent onNavigate={() => setMobileOpen(false)} />
        </SheetContent>
      </Sheet>
      <div className="flex min-w-0 flex-1 flex-col">
        <Header onOpenSidebar={() => setMobileOpen(true)} />
        <main className="flex-1 bg-[radial-gradient(circle_at_top_left,var(--muted),transparent_34rem)] p-4 sm:p-6">
          <div className="mb-4 flex items-center gap-2 rounded-md border border-border/70 bg-card/75 px-3 py-2 text-xs text-muted-foreground shadow-sm">
            <Sparkles className="h-3.5 w-3.5 text-primary" />
            <span className="font-medium text-foreground">Live workspace</span>
            <span className="hidden sm:inline">Updated just now</span>
          </div>
          {children}
        </main>
      </div>
    </div>
  );
}
