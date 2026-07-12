import { createFileRoute } from "@tanstack/react-router";
import { useAuth, roleLabel } from "@/context/AuthContext";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { StatusBadge } from "@/components/common/StatusBadge";
import { format } from "date-fns";
import { Link } from "@tanstack/react-router";
import { Button } from "@/components/ui/button";

export const Route = createFileRoute("/_app/profile")({ component: ProfilePage });

function ProfilePage() {
  const { user } = useAuth();
  const department = useStore(() =>
    user?.departmentId ? store.departments.find((d) => d.id === user.departmentId) : undefined,
  );
  const myAssets = useStore(() => store.assets.filter((a) => a.assignedToId === user?.id));
  const myAllocations = useStore(() =>
    store.allocations.filter((a) => a.employeeId === user?.id && a.status === "active"),
  );

  if (!user) return null;

  return (
    <div className="space-y-4">
      <Card>
        <CardContent className="flex flex-wrap items-center gap-4 p-6">
          <Avatar className="h-16 w-16">
            <AvatarFallback className="text-lg">
              {user.name
                .split(" ")
                .map((n) => n[0])
                .slice(0, 2)
                .join("")}
            </AvatarFallback>
          </Avatar>
          <div className="min-w-0 flex-1">
            <h2 className="text-xl font-semibold">{user.name}</h2>
            <div className="text-sm text-muted-foreground">{user.email}</div>
            <div className="mt-2 flex flex-wrap gap-2">
              <StatusBadge status={user.role} />
              <StatusBadge status={user.status} />
              {department && (
                <span className="rounded bg-muted px-2 py-0.5 text-xs">{department.name}</span>
              )}
            </div>
          </div>
          <div className="text-right text-xs text-muted-foreground">
            <div>Joined</div>
            <div className="font-medium text-foreground">
              {format(new Date(user.joinedAt), "MMM yyyy")}
            </div>
            <div className="mt-2">Role: {roleLabel(user.role)}</div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 md:grid-cols-2">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-base">My allocated assets ({myAssets.length})</CardTitle>
            <Button variant="ghost" size="sm" asChild>
              <Link to="/assets">View all</Link>
            </Button>
          </CardHeader>
          <CardContent className="space-y-2">
            {myAssets.length === 0 && (
              <div className="text-sm text-muted-foreground">No assets currently allocated.</div>
            )}
            {myAssets.map((a) => (
              <Link
                key={a.id}
                to="/assets/$assetId"
                params={{ assetId: a.id }}
                className="block rounded-md border border-border p-3 hover:bg-accent"
              >
                <div className="flex items-center justify-between">
                  <div>
                    <div className="font-medium text-sm">{a.name}</div>
                    <div className="font-mono text-xs text-muted-foreground">{a.tag}</div>
                  </div>
                  <StatusBadge status={a.condition} />
                </div>
              </Link>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-base">Active allocations</CardTitle>
          </CardHeader>
          <CardContent className="space-y-2 text-sm">
            {myAllocations.length === 0 && <div className="text-muted-foreground">None</div>}
            {myAllocations.map((a) => {
              const asset = store.assets.find((x) => x.id === a.assetId);
              return (
                <div key={a.id} className="flex items-center justify-between rounded-md border p-3">
                  <div>{asset?.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {a.expectedReturnAt
                      ? `Due ${format(new Date(a.expectedReturnAt), "MMM d")}`
                      : "No due date"}
                  </div>
                </div>
              );
            })}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
