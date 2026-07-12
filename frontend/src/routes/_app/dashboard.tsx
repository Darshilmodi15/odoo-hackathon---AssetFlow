import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo } from "react";
import { useAuth } from "@/context/AuthContext";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import {
  Package,
  ArrowLeftRight,
  Calendar,
  Wrench,
  Plus,
  AlertTriangle,
  TrendingUp,
  Clock,
  CheckCircle2,
  ChevronRight,
} from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  LineChart,
  Line,
} from "recharts";

export const Route = createFileRoute("/_app/dashboard")({ component: DashboardPage });

function KPI({
  label,
  value,
  icon: Icon,
  tone = "primary",
  to,
}: {
  label: string;
  value: number | string;
  icon: typeof Package;
  tone?: "primary" | "success" | "warning" | "info" | "destructive";
  to?: string;
}) {
  const tones = {
    primary: "bg-primary/10 text-primary",
    success: "bg-success/10 text-success",
    warning: "bg-warning/15 text-warning-foreground",
    info: "bg-info/10 text-info",
    destructive: "bg-destructive/10 text-destructive",
  };
  const content = (
    <Card className="transition-shadow hover:shadow-md">
      <CardContent className="flex items-center gap-4 p-5">
        <div className={`grid h-11 w-11 shrink-0 place-items-center rounded-lg ${tones[tone]}`}>
          <Icon className="h-5 w-5" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="text-xs font-medium text-muted-foreground">{label}</div>
          <div className="mt-0.5 truncate text-2xl font-semibold tabular-nums">{value}</div>
        </div>
      </CardContent>
    </Card>
  );
  return to ? <Link to={to}>{content}</Link> : content;
}

function DashboardPage() {
  const { user, hasRole } = useAuth();
  const assets = useStore(() => store.assets);
  const allocations = useStore(() => store.allocations);
  const bookings = useStore(() => store.bookings);
  const maintenance = useStore(() => store.maintenance);
  const transfers = useStore(() => store.transfers);
  const activityLogs = useStore(() => store.activityLogs);
  const employees = useStore(() => store.employees);
  const departments = useStore(() => store.departments);

  const scoped = useMemo(() => {
    if (!user) return { assets, allocations, bookings, maintenance, transfers };
    if (user.role === "employee") {
      return {
        assets: assets.filter((a) => a.assignedToId === user.id),
        allocations: allocations.filter((a) => a.employeeId === user.id),
        bookings: bookings.filter((b) => b.bookedById === user.id),
        maintenance: maintenance.filter((m) => m.requestedById === user.id),
        transfers: transfers.filter(
          (t) => t.requestedById === user.id || t.toEmployeeId === user.id,
        ),
      };
    }
    if (user.role === "department_head") {
      const deptId = user.departmentId;
      return {
        assets: assets.filter((a) => a.departmentId === deptId),
        allocations: allocations.filter((a) => a.departmentId === deptId),
        bookings: bookings.filter((b) => b.departmentId === deptId),
        maintenance,
        transfers,
      };
    }
    return { assets, allocations, bookings, maintenance, transfers };
  }, [user, assets, allocations, bookings, maintenance, transfers]);

  const kpis = {
    available: scoped.assets.filter((a) => a.status === "available").length,
    allocated: scoped.assets.filter((a) => a.status === "allocated").length,
    maintenanceToday: scoped.maintenance.filter((m) => {
      const requested = new Date(m.requestedAt);
      const today = new Date();
      return requested.toDateString() === today.toDateString();
    }).length,
    activeBookings: scoped.bookings.filter((b) => b.status === "upcoming" || b.status === "ongoing")
      .length,
    pendingTransfers: scoped.transfers.filter((t) => t.status === "requested").length,
    upcomingReturns: scoped.allocations.filter(
      (a) =>
        a.status === "active" &&
        a.expectedReturnAt &&
        new Date(a.expectedReturnAt) > new Date() &&
        new Date(a.expectedReturnAt).getTime() - Date.now() < 30 * 86400000,
    ).length,
  };

  const overdue = scoped.allocations.filter(
    (a) =>
      a.status === "overdue" ||
      (a.status === "active" && a.expectedReturnAt && new Date(a.expectedReturnAt) < new Date()),
  );

  const byStatus = Object.entries(
    assets.reduce(
      (acc, a) => {
        acc[a.status] = (acc[a.status] || 0) + 1;
        return acc;
      },
      {} as Record<string, number>,
    ),
  ).map(([name, value]) => ({ name: name.replace("_", " "), value }));

  const byDept = departments.map((d) => ({
    name: d.code,
    count: assets.filter((a) => a.departmentId === d.id).length,
  }));

  const utilization = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(Date.now() - (6 - i) * 86400000);
    const dayStart = new Date(date);
    dayStart.setHours(0, 0, 0, 0);
    const dayEnd = new Date(dayStart.getTime() + 86400000);
    const activeAllocations = allocations.filter(
      (a) =>
        new Date(a.allocatedAt) < dayEnd && (!a.returnedAt || new Date(a.returnedAt) >= dayStart),
    ).length;
    const activeBookings = bookings.filter(
      (b) =>
        b.status !== "cancelled" && new Date(b.startAt) < dayEnd && new Date(b.endAt) >= dayStart,
    ).length;
    const denominator = Math.max(assets.length + assets.filter((a) => a.shared).length, 1);
    return {
      day: format(date, "EEE"),
      utilized: Math.round(((activeAllocations + activeBookings) / denominator) * 100),
    };
  });

  const COLORS = [
    "oklch(0.55 0.2 275)",
    "oklch(0.65 0.15 160)",
    "oklch(0.7 0.15 75)",
    "oklch(0.6 0.2 27)",
    "oklch(0.6 0.15 240)",
    "oklch(0.5 0.05 260)",
    "oklch(0.4 0.04 260)",
  ];

  return (
    <div className="space-y-6">
      <div>
        <h2 className="text-2xl font-semibold">Welcome back, {user?.name.split(" ")[0]}</h2>
        <p className="text-sm text-muted-foreground">
          Here's what's happening with your assets today.
        </p>
      </div>

      {overdue.length > 0 && (
        <Card className="border-destructive/40 bg-destructive/5">
          <CardContent className="flex flex-wrap items-center gap-3 p-4">
            <div className="grid h-9 w-9 place-items-center rounded-full bg-destructive/15 text-destructive">
              <AlertTriangle className="h-4 w-4" />
            </div>
            <div className="min-w-0 flex-1">
              <div className="text-sm font-semibold">Overdue Returns</div>
              <div className="text-xs text-muted-foreground">
                {overdue.length} allocation{overdue.length > 1 ? "s" : ""} past expected return date
              </div>
            </div>
            <Button size="sm" variant="outline" asChild>
              <Link to="/allocations">View all</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid grid-cols-2 gap-3 sm:grid-cols-3 lg:grid-cols-7">
        <KPI
          label="Assets Available"
          value={kpis.available}
          icon={Package}
          tone="success"
          to="/assets"
        />
        <KPI
          label="Assets Allocated"
          value={kpis.allocated}
          icon={ArrowLeftRight}
          tone="info"
          to="/allocations"
        />
        <KPI
          label="Maintenance Today"
          value={kpis.maintenanceToday}
          icon={Wrench}
          tone="warning"
          to="/maintenance"
        />
        <KPI
          label="Active Bookings"
          value={kpis.activeBookings}
          icon={Calendar}
          tone="primary"
          to="/bookings"
        />
        <KPI
          label="Pending Transfers"
          value={kpis.pendingTransfers}
          icon={ArrowLeftRight}
          tone="warning"
          to="/allocations"
        />
        <KPI
          label="Upcoming Returns"
          value={kpis.upcomingReturns}
          icon={Clock}
          tone="info"
          to="/allocations"
        />
        <KPI
          label="Overdue Returns"
          value={overdue.length}
          icon={AlertTriangle}
          tone="destructive"
          to="/allocations"
        />
      </div>

      {(hasRole(["admin", "asset_manager", "department_head"]) || user?.role === "employee") && (
        <Card>
          <CardHeader className="pb-3">
            <CardTitle className="text-base">Quick actions</CardTitle>
          </CardHeader>
          <CardContent className="flex flex-wrap gap-2">
            {hasRole(["admin", "asset_manager"]) && (
              <Button asChild>
                <Link to="/assets">
                  <Plus className="mr-2 h-4 w-4" />
                  Register Asset
                </Link>
              </Button>
            )}
            {hasRole(["admin", "asset_manager"]) && (
              <Button variant="outline" asChild>
                <Link to="/allocations">Allocate Asset</Link>
              </Button>
            )}
            <Button variant="outline" asChild>
              <Link to="/bookings">Book Resource</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/maintenance">Raise Maintenance Request</Link>
            </Button>
          </CardContent>
        </Card>
      )}

      <div className="grid gap-4 lg:grid-cols-3">
        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Asset distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie
                  data={byStatus}
                  dataKey="value"
                  nameKey="name"
                  innerRadius={45}
                  outerRadius={80}
                  paddingAngle={2}
                >
                  {byStatus.map((_, i) => (
                    <Cell key={i} fill={COLORS[i % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
              </PieChart>
            </ResponsiveContainer>
            <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-xs">
              {byStatus.map((s, i) => (
                <div key={s.name} className="flex items-center gap-1.5">
                  <span
                    className="inline-block h-2 w-2 rounded-full"
                    style={{ background: COLORS[i % COLORS.length] }}
                  />
                  <span className="capitalize">{s.name}</span>
                  <span className="text-muted-foreground">{s.value}</span>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>

        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Department allocation</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={byDept}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="name" fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis fontSize={11} stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" fill="var(--primary)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card className="lg:col-span-1">
          <CardHeader>
            <CardTitle className="text-base">Utilization trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={220}>
              <LineChart data={utilization}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="day" fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis fontSize={11} stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Line
                  type="monotone"
                  dataKey="utilized"
                  stroke="var(--primary)"
                  strokeWidth={2}
                  dot={{ r: 3 }}
                />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Recent activity</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/activity">
                View all <ChevronRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-3">
            {activityLogs.slice(0, 6).map((l) => (
              <div key={l.id} className="flex items-start gap-3 text-sm">
                <div className="mt-0.5 h-2 w-2 shrink-0 rounded-full bg-primary" />
                <div className="min-w-0 flex-1">
                  <div className="truncate">{l.description}</div>
                  <div className="text-xs text-muted-foreground">
                    {formatDistanceToNow(new Date(l.at), { addSuffix: true })}
                  </div>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Upcoming bookings</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/bookings">
                View all <ChevronRight className="ml-1 h-3 w-3" />
              </Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-2">
            {scoped.bookings
              .filter((b) => b.status === "upcoming")
              .slice(0, 5)
              .map((b) => {
                const asset = assets.find((a) => a.id === b.assetId);
                const emp = employees.find((e) => e.id === b.bookedById);
                return (
                  <div
                    key={b.id}
                    className="flex items-center justify-between rounded-md border border-border p-3 text-sm"
                  >
                    <div className="min-w-0">
                      <div className="truncate font-medium">{asset?.name}</div>
                      <div className="truncate text-xs text-muted-foreground">
                        {b.purpose} · {emp?.name}
                      </div>
                    </div>
                    <div className="text-right text-xs">
                      <div>{format(new Date(b.startAt), "MMM d")}</div>
                      <div className="text-muted-foreground">
                        {format(new Date(b.startAt), "HH:mm")} -{" "}
                        {format(new Date(b.endAt), "HH:mm")}
                      </div>
                    </div>
                  </div>
                );
              })}
            {scoped.bookings.filter((b) => b.status === "upcoming").length === 0 && (
              <EmptyState
                title="No upcoming bookings"
                description="Book a resource to see it here."
                icon={CheckCircle2}
              />
            )}
          </CardContent>
        </Card>
      </div>

      {hasRole(["admin", "asset_manager"]) && (
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-3">
            <CardTitle className="text-base">Pending approvals</CardTitle>
            <TrendingUp className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent className="space-y-2">
            {[
              ...transfers
                .filter((t) => t.status === "requested")
                .map((t) => ({ id: t.id, type: "Transfer", label: t.code, link: "/allocations" })),
              ...maintenance
                .filter((m) => m.status === "pending")
                .map((m) => ({
                  id: m.id,
                  type: "Maintenance",
                  label: m.code,
                  link: "/maintenance",
                })),
            ]
              .slice(0, 6)
              .map((item) => (
                <div
                  key={item.id}
                  className="flex items-center justify-between rounded-md border p-3 text-sm"
                >
                  <div>
                    <StatusBadge status="pending" />{" "}
                    <span className="ml-2 font-medium">{item.label}</span>{" "}
                    <span className="text-muted-foreground">— {item.type}</span>
                  </div>
                  <Button size="sm" variant="ghost" asChild>
                    <Link to={item.link}>Review</Link>
                  </Button>
                </div>
              ))}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
