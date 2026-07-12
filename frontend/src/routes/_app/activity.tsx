import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { notificationService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Bell, Check, Search } from "lucide-react";
import { formatDistanceToNow, format } from "date-fns";
import { Link } from "@tanstack/react-router";
import type { NotificationType } from "@/types";

export const Route = createFileRoute("/_app/activity")({ component: ActivityPage });

function ActivityPage() {
  const { user } = useAuth();
  const notifs = useStore(() => store.notifications.filter(n => n.userId === user!.id));
  const logs = useStore(() => store.activityLogs);
  const employees = useStore(() => store.employees);
  const [q, setQ] = useState("");
  const [filter, setFilter] = useState<"all" | "unread" | NotificationType>("all");

  const filteredNotifs = notifs.filter(n =>
    (filter === "all" || (filter === "unread" ? !n.read : n.type === filter)) &&
    (n.title + n.message).toLowerCase().includes(q.toLowerCase())
  );

  return (
    <Tabs defaultValue="notifications">
      <TabsList><TabsTrigger value="notifications">Notifications</TabsTrigger><TabsTrigger value="activity">Activity Log</TabsTrigger></TabsList>

      <TabsContent value="notifications" className="space-y-4">
        <Card>
          <CardHeader className="space-y-3">
            <div className="flex flex-wrap items-center gap-2">
              <CardTitle className="flex-1 text-base flex items-center gap-2"><Bell className="h-4 w-4" />Notifications</CardTitle>
              <Button size="sm" variant="outline" onClick={() => { notificationService.markAllRead(user!.id); }}><Check className="mr-1 h-4 w-4" />Mark all read</Button>
            </div>
            <div className="flex flex-wrap gap-2">
              <div className="relative flex-1 min-w-40"><Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" /><Input placeholder="Search notifications" value={q} onChange={e => setQ(e.target.value)} className="h-9 pl-8" /></div>
              <div className="flex flex-wrap gap-1">
                {(["all","unread","allocation","transfer","maintenance","booking","audit","overdue"] as const).map(f => (
                  <Button key={f} size="sm" variant={filter === f ? "secondary" : "ghost"} onClick={() => setFilter(f as typeof filter)} className="h-8 capitalize">{f}</Button>
                ))}
              </div>
            </div>
          </CardHeader>
          <CardContent className="space-y-2">
            {filteredNotifs.length === 0 && <EmptyState icon={Bell} title="No notifications" />}
            {filteredNotifs.map(n => (
              <div key={n.id} className={`flex items-start gap-3 rounded-md border p-3 text-sm ${n.read ? "border-border bg-card" : "border-primary/30 bg-primary/5"}`}>
                <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <div className="font-medium">{n.title}</div>
                    <StatusBadge status={n.type} />
                  </div>
                  <div className="mt-0.5 text-muted-foreground">{n.message}</div>
                  <div className="mt-1 text-xs text-muted-foreground">{formatDistanceToNow(new Date(n.at), { addSuffix: true })}</div>
                </div>
                <div className="flex flex-col gap-1">
                  {n.link && <Button size="sm" variant="ghost" asChild><Link to={n.link}>Open</Link></Button>}
                  {!n.read && <Button size="sm" variant="ghost" onClick={() => notificationService.markRead(n.id)}>Mark read</Button>}
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="activity">
        <Card>
          <CardHeader><CardTitle className="text-base">Activity Log</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {logs.map(l => {
              const u = employees.find(e => e.id === l.userId);
              return (
                <div key={l.id} className="flex items-start gap-3 rounded-md border border-border p-3 text-sm">
                  <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                  <div className="min-w-0 flex-1">
                    <div className="flex flex-wrap items-center gap-2">
                      <span className="font-medium">{u?.name}</span>
                      <span className="rounded bg-muted px-1.5 py-0.5 text-[10px]">{l.module}</span>
                      <StatusBadge status={l.role} className="text-[10px]" />
                      {l.status && <StatusBadge status={l.status} className="text-[10px]" />}
                    </div>
                    <div className="mt-0.5 text-muted-foreground">{l.description}</div>
                    <div className="mt-1 text-xs text-muted-foreground">{format(new Date(l.at), "MMM d, yyyy HH:mm")}</div>
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
