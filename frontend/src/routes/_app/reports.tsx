import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { toast } from "sonner";
import { Download, FileText } from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  LineChart,
  Line,
  Legend,
} from "recharts";
import { format, differenceInDays } from "date-fns";

export const Route = createFileRoute("/_app/reports")({ component: ReportsPage });

function exportCsv(filename: string, rows: Record<string, unknown>[]) {
  if (rows.length === 0) return;
  const headers = Object.keys(rows[0]);
  const csv = [
    headers.join(","),
    ...rows.map((r) => headers.map((h) => JSON.stringify(r[h] ?? "")).join(",")),
  ].join("\n");
  const blob = new Blob([csv], { type: "text/csv" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  a.click();
  URL.revokeObjectURL(url);
}

function ReportsPage() {
  const assets = useStore(() => store.assets);
  const departments = useStore(() => store.departments);
  const categories = useStore(() => store.categories);
  const maintenance = useStore(() => store.maintenance);
  const allocations = useStore(() => store.allocations);
  const bookings = useStore(() => store.bookings);
  const [dept, setDept] = useState("all");
  const [cat, setCat] = useState("all");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  const filteredAssets = useMemo(
    () =>
      assets.filter(
        (a) =>
          (dept === "all" || a.departmentId === dept) && (cat === "all" || a.categoryId === cat),
      ),
    [assets, dept, cat],
  );

  const utilizationTrend = Array.from({ length: 12 }, (_, i) => ({
    month: format(new Date(new Date().getFullYear(), i, 1), "MMM"),
    utilized: Math.floor(50 + Math.random() * 40),
    idle: Math.floor(10 + Math.random() * 30),
  }));

  const mostUsed = allocations.reduce(
    (acc, a) => {
      acc[a.assetId] = (acc[a.assetId] || 0) + 1;
      return acc;
    },
    {} as Record<string, number>,
  );
  const topAssets = Object.entries(mostUsed)
    .map(([id, n]) => ({ name: assets.find((a) => a.id === id)?.name || id, count: n }))
    .sort((a, b) => b.count - a.count)
    .slice(0, 6);

  const maintByCategory = categories.map((c) => ({
    name: c.name,
    count: maintenance.filter((m) => assets.find((a) => a.id === m.assetId)?.categoryId === c.id)
      .length,
  }));

  const idleAssets = filteredAssets.filter(
    (a) => a.status === "available" && differenceInDays(new Date(), new Date(a.updatedAt)) > 60,
  );

  const nearingRetirement = filteredAssets.filter(
    (a) =>
      differenceInDays(new Date(), new Date(a.acquisitionDate)) > 1500 &&
      a.status !== "retired" &&
      a.status !== "disposed",
  );

  const conditionDist = ["excellent", "good", "fair", "poor"].map((c) => ({
    name: c,
    value: filteredAssets.filter((a) => a.condition === c).length,
  }));

  const overdueAllocs = allocations.filter(
    (a) =>
      a.status === "overdue" ||
      (a.status === "active" && a.expectedReturnAt && new Date(a.expectedReturnAt) < new Date()),
  ).length;

  const deptAllocation = departments.map((d) => ({
    name: d.code,
    allocated: assets.filter((a) => a.departmentId === d.id && a.status === "allocated").length,
  }));

  const COLORS = [
    "oklch(0.62 0.15 160)",
    "oklch(0.6 0.15 240)",
    "oklch(0.75 0.15 75)",
    "oklch(0.58 0.22 27)",
  ];

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Filters</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            <div className="space-y-1">
              <Label className="text-xs">Department</Label>
              <Select value={dept} onValueChange={setDept}>
                <SelectTrigger className="h-9 w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {departments.map((d) => (
                    <SelectItem key={d.id} value={d.id}>
                      {d.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">Category</Label>
              <Select value={cat} onValueChange={setCat}>
                <SelectTrigger className="h-9 w-40">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All</SelectItem>
                  {categories.map((c) => (
                    <SelectItem key={c.id} value={c.id}>
                      {c.name}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div className="space-y-1">
              <Label className="text-xs">From</Label>
              <Input
                type="date"
                className="h-9 w-40"
                value={from}
                onChange={(e) => setFrom(e.target.value)}
              />
            </div>
            <div className="space-y-1">
              <Label className="text-xs">To</Label>
              <Input
                type="date"
                className="h-9 w-40"
                value={to}
                onChange={(e) => setTo(e.target.value)}
              />
            </div>
            <div className="ml-auto flex items-end gap-2">
              <Button
                variant="outline"
                size="sm"
                onClick={() =>
                  exportCsv(
                    "assets.csv",
                    filteredAssets.map((a) => ({
                      tag: a.tag,
                      name: a.name,
                      status: a.status,
                      condition: a.condition,
                      location: a.location,
                    })),
                  )
                }
              >
                <Download className="mr-1 h-4 w-4" />
                Export CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => toast.info("PDF export will connect to backend service")}
              >
                <FileText className="mr-1 h-4 w-4" />
                Export PDF
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      <div className="grid gap-4 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Asset utilization trend</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <LineChart data={utilizationTrend}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="month" fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis fontSize={11} stroke="var(--muted-foreground)" />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Legend wrapperStyle={{ fontSize: 12 }} />
                <Line type="monotone" dataKey="utilized" stroke="var(--primary)" strokeWidth={2} />
                <Line type="monotone" dataKey="idle" stroke="var(--warning)" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Most used assets</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={topAssets} layout="vertical">
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis type="number" fontSize={11} stroke="var(--muted-foreground)" />
                <YAxis
                  dataKey="name"
                  type="category"
                  fontSize={11}
                  width={120}
                  stroke="var(--muted-foreground)"
                />
                <Tooltip
                  contentStyle={{
                    background: "var(--card)",
                    border: "1px solid var(--border)",
                    borderRadius: 8,
                    fontSize: 12,
                  }}
                />
                <Bar dataKey="count" fill="var(--primary)" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Maintenance frequency by category</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={maintByCategory}>
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
                <Bar dataKey="count" fill="var(--warning)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Condition distribution</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <PieChart>
                <Pie data={conditionDist} dataKey="value" nameKey="name" outerRadius={90} label>
                  {conditionDist.map((_, i) => (
                    <Cell key={i} fill={COLORS[i]} />
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
                <Legend wrapperStyle={{ fontSize: 12 }} />
              </PieChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Department allocation</CardTitle>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={deptAllocation}>
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
                <Bar dataKey="allocated" fill="var(--primary)" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">Overview</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div className="flex justify-between">
              <span className="text-muted-foreground">Idle assets (60+ days)</span>
              <b>{idleAssets.length}</b>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Nearing retirement</span>
              <b>{nearingRetirement.length}</b>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Overdue returns</span>
              <b className="text-destructive">{overdueAllocs}</b>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total bookings this period</span>
              <b>{bookings.length}</b>
            </div>
            <div className="flex justify-between">
              <span className="text-muted-foreground">Total maintenance requests</span>
              <b>{maintenance.length}</b>
            </div>
          </CardContent>
        </Card>
      </div>

      {idleAssets.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Idle assets (60+ days without activity)</CardTitle>
          </CardHeader>
          <CardContent className="text-sm">
            <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-3">
              {idleAssets.slice(0, 9).map((a) => (
                <div key={a.id} className="rounded-md border border-border p-3">
                  <div className="font-medium">{a.name}</div>
                  <div className="text-xs text-muted-foreground">
                    {a.tag} · {a.location}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
