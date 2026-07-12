import { createFileRoute, Link } from "@tanstack/react-router";
import { useEffect, useMemo, useState } from "react";
import { AppLayout } from "@/components/layout/AppLayout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { EmptyState, ErrorState, LoadingState } from "@/components/common/States";
import { StatusBadge } from "@/components/common/StatusBadge";
import { useAuth } from "@/context/AuthContext";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import type {
  Allocation,
  Booking,
  MaintenanceRequest,
  Notification,
  TransferRequest,
} from "@/types";
import {
  ArrowLeftRight,
  ArrowRight,
  BellRing,
  Box,
  CalendarClock,
  CheckCircle2,
  Clock3,
  Package,
  Sparkles,
  Wrench,
} from "lucide-react";
import { format, formatDistanceToNow } from "date-fns";

export const Route = createFileRoute("/employee/dashboard")({
  component: EmployeeDashboard,
});

function EmployeeDashboard() {
  const { user } = useAuth();
  const assets = useStore(() => store.assets);
  const bookings = useStore(() => store.bookings);
  const maintenance = useStore(() => store.maintenance);
  const transfers = useStore(() => store.transfers);
  const allocations = useStore(() => store.allocations);
  const notifications = useStore(() => store.notifications);
  const employees = useStore(() => store.employees);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const timer = window.setTimeout(() => {
      if (!user) {
        setError("We could not load your employee profile. Please sign in again.");
      } else {
        setError(null);
      }
      setLoading(false);
    }, 450);

    return () => window.clearTimeout(timer);
  }, [user]);

  const scoped = useMemo(() => {
    if (!user) {
      return {
        assets: [] as typeof assets,
        bookings: [] as Booking[],
        maintenance: [] as MaintenanceRequest[],
        transfers: [] as TransferRequest[],
        allocations: [] as Allocation[],
        notifications: [] as Notification[],
      };
    }

    return {
      assets: assets.filter((asset) => asset.assignedToId === user.id),
      bookings: bookings
        .filter((booking) => booking.bookedById === user.id)
        .sort((a, b) => new Date(a.startAt).getTime() - new Date(b.startAt).getTime()),
      maintenance: maintenance
        .filter((request) => request.requestedById === user.id)
        .sort((a, b) => new Date(b.requestedAt).getTime() - new Date(a.requestedAt).getTime()),
      transfers: transfers.filter(
        (transfer) => transfer.requestedById === user.id || transfer.toEmployeeId === user.id,
      ),
      allocations: allocations.filter(
        (allocation) => allocation.employeeId === user.id && allocation.status !== "returned",
      ),
      notifications: notifications.filter((notification) => notification.userId === user.id),
    };
  }, [assets, allocations, bookings, maintenance, notifications, transfers, user]);

  const stats = [
    {
      title: "My Allocated Assets",
      value: scoped.assets.length,
      detail: scoped.assets.length ? "Ready for daily use" : "No active assets yet",
      icon: Package,
      tone: "primary" as const,
    },
    {
      title: "My Upcoming Bookings",
      value: scoped.bookings.filter((booking) => booking.status === "upcoming").length,
      detail: scoped.bookings.length ? "Scheduled soon" : "No bookings yet",
      icon: CalendarClock,
      tone: "info" as const,
    },
    {
      title: "My Maintenance Requests",
      value: scoped.maintenance.length,
      detail: scoped.maintenance.length ? "Tracked for follow-up" : "Nothing in progress",
      icon: Wrench,
      tone: "warning" as const,
    },
    {
      title: "My Transfer/Return Requests",
      value:
        scoped.transfers.length +
        scoped.allocations.filter((allocation) => allocation.status === "active").length,
      detail: "Transfers and returns in motion",
      icon: ArrowLeftRight,
      tone: "success" as const,
    },
    {
      title: "My Notifications",
      value: scoped.notifications.filter((notification) => !notification.read).length,
      detail: scoped.notifications.length ? "Unread updates" : "All caught up",
      icon: BellRing,
      tone: "destructive" as const,
    },
  ];

  const sectionCards = [
    {
      title: "My Allocated Assets",
      description: "Assets currently assigned to you for work.",
      items: scoped.assets.slice(0, 4),
      empty: {
        title: "No allocated assets",
        description: "Assigned equipment will appear here as soon as it is allocated.",
      },
      render: (asset: (typeof scoped.assets)[number]) => (
        <div
          key={asset.id}
          className="flex flex-col gap-3 rounded-lg border border-border/70 bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="truncate font-medium">{asset.name}</p>
              <span className="truncate text-xs text-muted-foreground">{asset.tag}</span>
            </div>
            <p className="mt-1 break-words text-sm text-muted-foreground">{asset.location}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:justify-end">
            <StatusBadge status={asset.status} />
            <span className="text-xs text-muted-foreground">
              Updated {formatDistanceToNow(new Date(asset.updatedAt), { addSuffix: true })}
            </span>
          </div>
        </div>
      ),
    },
    {
      title: "My Upcoming Bookings",
      description: "Appointments and bookings you have scheduled.",
      items: scoped.bookings
        .filter((booking) => booking.status === "upcoming" || booking.status === "ongoing")
        .slice(0, 4),
      empty: {
        title: "No upcoming bookings",
        description: "Reserve a room, vehicle, or shared asset to see it here.",
      },
      render: (booking: Booking) => {
        const asset = assets.find((item) => item.id === booking.assetId);
        return (
          <div
            key={booking.id}
            className="flex flex-col gap-3 rounded-lg border border-border/70 bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between"
          >
            <div className="min-w-0 flex-1">
              <div className="flex flex-wrap items-center gap-2">
                <p className="truncate font-medium">{asset?.name ?? "Shared resource"}</p>
                <StatusBadge status={booking.status} />
              </div>
              <p className="mt-1 break-words text-sm text-muted-foreground">{booking.purpose}</p>
            </div>
            <div className="text-sm text-muted-foreground sm:text-right">
              <p className="font-medium text-foreground">
                {format(new Date(booking.startAt), "MMM d, yyyy")}
              </p>
              <p>
                {format(new Date(booking.startAt), "HH:mm")} –{" "}
                {format(new Date(booking.endAt), "HH:mm")}
              </p>
            </div>
          </div>
        );
      },
    },
    {
      title: "My Maintenance Requests",
      description: "Open issues and maintenance follow-ups.",
      items: scoped.maintenance.slice(0, 4),
      empty: {
        title: "No maintenance requests",
        description: "Anything you report will appear here with its status.",
      },
      render: (request: MaintenanceRequest) => (
        <div
          key={request.id}
          className="flex flex-col gap-3 rounded-lg border border-border/70 bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="truncate font-medium">{request.title}</p>
              <span className="truncate text-xs text-muted-foreground">{request.code}</span>
            </div>
            <p className="mt-1 break-words text-sm text-muted-foreground">{request.description}</p>
          </div>
          <div className="flex flex-wrap items-center gap-2 sm:justify-end">
            <StatusBadge status={request.priority} />
            <StatusBadge status={request.status} />
          </div>
        </div>
      ),
    },
    {
      title: "My Transfer/Return Requests",
      description: "Items moving between teams or pending return.",
      items: [
        ...scoped.transfers.slice(0, 2).map((transfer) => ({
          id: transfer.id,
          title: `Transfer request ${transfer.code}`,
          detail: `Requested to ${employees.find((employee) => employee.id === transfer.toEmployeeId)?.name ?? "another team"}`,
          status: transfer.status,
        })),
        ...scoped.allocations
          .filter((allocation) => allocation.status === "active")
          .slice(0, 2)
          .map((allocation) => ({
            id: allocation.id,
            title: "Return due",
            detail: allocation.expectedReturnAt
              ? `Expected by ${format(new Date(allocation.expectedReturnAt), "MMM d")}`
              : "Return timing pending",
            status: allocation.status,
          })),
      ].slice(0, 4),
      empty: {
        title: "No transfer or return requests",
        description: "Transfers and returns will appear here when they are requested.",
      },
      render: (item: { id: string; title: string; detail: string; status: string }) => (
        <div
          key={item.id}
          className="flex flex-col gap-3 rounded-lg border border-border/70 bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium">{item.title}</p>
            <p className="mt-1 break-words text-sm text-muted-foreground">{item.detail}</p>
          </div>
          <StatusBadge status={item.status} />
        </div>
      ),
    },
    {
      title: "My Notifications",
      description: "The latest updates for your account.",
      items: scoped.notifications.slice(0, 4),
      empty: {
        title: "No notifications",
        description: "You are all caught up for now.",
      },
      render: (notification: Notification) => (
        <div
          key={notification.id}
          className="flex flex-col gap-3 rounded-lg border border-border/70 bg-background/70 p-3 sm:flex-row sm:items-center sm:justify-between"
        >
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <p className="truncate font-medium">{notification.title}</p>
              {!notification.read && (
                <span className="rounded-full bg-primary/10 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-[0.2em] text-primary">
                  New
                </span>
              )}
            </div>
            <p className="mt-1 break-words text-sm text-muted-foreground">{notification.message}</p>
          </div>
          <div className="text-sm text-muted-foreground sm:text-right">
            <p>{formatDistanceToNow(new Date(notification.at), { addSuffix: true })}</p>
            <div className="mt-1 flex items-center gap-1 text-xs text-muted-foreground">
              <Clock3 className="h-3.5 w-3.5" />
              {format(new Date(notification.at), "MMM d")}
            </div>
          </div>
        </div>
      ),
    },
  ];

  const content = (
    <div className="space-y-6">
      <div className="flex flex-col gap-3 rounded-2xl border border-border/70 bg-card/80 p-4 shadow-sm sm:flex-row sm:items-end sm:justify-between sm:p-6">
        <div className="min-w-0">
          <div className="mb-2 inline-flex items-center gap-2 rounded-full border border-primary/20 bg-primary/10 px-2.5 py-1 text-xs font-semibold uppercase tracking-[0.2em] text-primary">
            <Sparkles className="h-3.5 w-3.5" />
            Employee Portal
          </div>
          <h1 className="text-2xl font-semibold leading-tight sm:text-3xl">
            Welcome back, {user?.name.split(" ")[0] ?? "there"}
          </h1>
          <p className="mt-2 max-w-2xl break-words text-sm text-muted-foreground">
            Keep track of your assets, bookings, requests, and updates from one responsive
            workspace.
          </p>
        </div>
        <Button asChild variant="outline" className="w-full sm:w-auto">
          <Link to="/bookings">
            Book a resource <ArrowRight className="h-4 w-4" />
          </Link>
        </Button>
      </div>

      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-5">
        {stats.map((stat) => {
          const Icon = stat.icon;
          return (
            <Card key={stat.title} className="overflow-hidden">
              <CardContent className="flex items-start gap-3 p-4">
                <div
                  className={`grid h-10 w-10 shrink-0 place-items-center rounded-lg ${stat.tone === "primary" ? "bg-primary/10 text-primary" : stat.tone === "info" ? "bg-info/10 text-info" : stat.tone === "warning" ? "bg-warning/15 text-warning-foreground" : stat.tone === "success" ? "bg-success/10 text-success" : "bg-destructive/10 text-destructive"}`}
                >
                  <Icon className="h-5 w-5" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-muted-foreground">{stat.title}</p>
                  <p className="mt-1 text-2xl font-semibold tabular-nums">{stat.value}</p>
                  <p className="mt-1 break-words text-xs text-muted-foreground">{stat.detail}</p>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      <div className="grid gap-4 xl:grid-cols-2">
        {sectionCards.map((section) => (
          <Card key={section.title} className="overflow-hidden">
            <CardHeader className="pb-3">
              <div className="flex flex-col gap-2 sm:flex-row sm:items-start sm:justify-between">
                <div className="min-w-0">
                  <CardTitle className="text-base">{section.title}</CardTitle>
                  <p className="mt-1 break-words text-sm text-muted-foreground">
                    {section.description}
                  </p>
                </div>
                <Button variant="ghost" size="sm" asChild>
                  <Link
                    to={
                      section.title === "My Allocated Assets"
                        ? "/assets"
                        : section.title === "My Maintenance Requests"
                          ? "/maintenance"
                          : section.title === "My Upcoming Bookings"
                            ? "/bookings"
                            : section.title === "My Transfer/Return Requests"
                              ? "/allocations"
                              : "/activity"
                    }
                  >
                    View all
                  </Link>
                </Button>
              </div>
            </CardHeader>
            <CardContent className="space-y-3">
              {loading ? (
                <LoadingState rows={3} />
              ) : error ? (
                <ErrorState error={error} onRetry={() => window.location.reload()} />
              ) : section.items.length ? (
                section.items.map((item) => section.render(item as never))
              ) : (
                <EmptyState
                  title={section.empty.title}
                  description={section.empty.description}
                  icon={Box}
                />
              )}
            </CardContent>
          </Card>
        ))}
      </div>
    </div>
  );

  return <AppLayout>{content}</AppLayout>;
}
