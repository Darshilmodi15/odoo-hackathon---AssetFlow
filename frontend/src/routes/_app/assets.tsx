import { createFileRoute, Link } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { assetService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Switch } from "@/components/ui/switch";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Plus, Search, LayoutGrid, List } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import type { AssetCondition } from "@/types";

export const Route = createFileRoute("/_app/assets")({ component: AssetsPage });

function AssetsPage() {
  const { user, hasRole } = useAuth();
  const assets = useStore(() => store.assets);
  const categories = useStore(() => store.categories);
  const departments = useStore(() => store.departments);
  const employees = useStore(() => store.employees);

  const [q, setQ] = useState("");
  const [status, setStatus] = useState("all");
  const [cat, setCat] = useState("all");
  const [dept, setDept] = useState("all");
  const [view, setView] = useState<"table" | "grid">("table");
  const [openNew, setOpenNew] = useState(false);

  const filtered = useMemo(
    () =>
      assets.filter(
        (a) =>
          (a.name + a.tag + a.serialNumber).toLowerCase().includes(q.toLowerCase()) &&
          (status === "all" || a.status === status) &&
          (cat === "all" || a.categoryId === cat) &&
          (dept === "all" || a.departmentId === dept),
      ),
    [assets, q, status, cat, dept],
  );

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader className="space-y-3">
          <div className="flex flex-wrap items-center gap-2">
            <CardTitle className="flex-1 text-base">Asset Directory</CardTitle>
            <div className="flex rounded-md border border-border">
              <Button
                variant={view === "table" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setView("table")}
                className="rounded-r-none"
              >
                <List className="h-4 w-4" />
              </Button>
              <Button
                variant={view === "grid" ? "secondary" : "ghost"}
                size="sm"
                onClick={() => setView("grid")}
                className="rounded-l-none"
              >
                <LayoutGrid className="h-4 w-4" />
              </Button>
            </div>
            {hasRole(["admin", "asset_manager"]) && (
              <Dialog open={openNew} onOpenChange={setOpenNew}>
                <DialogTrigger asChild>
                  <Button size="sm">
                    <Plus className="mr-1 h-4 w-4" />
                    Register Asset
                  </Button>
                </DialogTrigger>
                <RegisterAssetDialog onDone={() => setOpenNew(false)} actorId={user!.id} />
              </Dialog>
            )}
          </div>
          <div className="flex flex-wrap gap-2">
            <div className="relative flex-1 min-w-40">
              <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
              <Input
                placeholder="Search by name, tag, serial…"
                value={q}
                onChange={(e) => setQ(e.target.value)}
                className="h-9 pl-8"
              />
            </div>
            <Select value={status} onValueChange={setStatus}>
              <SelectTrigger className="h-9 w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All statuses</SelectItem>
                {[
                  "available",
                  "allocated",
                  "reserved",
                  "under_maintenance",
                  "lost",
                  "retired",
                  "disposed",
                ].map((s) => (
                  <SelectItem key={s} value={s} className="capitalize">
                    {s.replace("_", " ")}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={cat} onValueChange={setCat}>
              <SelectTrigger className="h-9 w-36">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All categories</SelectItem>
                {categories.map((c) => (
                  <SelectItem key={c.id} value={c.id}>
                    {c.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={dept} onValueChange={setDept}>
              <SelectTrigger className="h-9 w-40">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All departments</SelectItem>
                {departments.map((d) => (
                  <SelectItem key={d.id} value={d.id}>
                    {d.name}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardHeader>
        <CardContent>
          {filtered.length === 0 ? (
            <EmptyState
              title="No assets match"
              description="Try clearing filters or register a new asset."
            />
          ) : view === "table" ? (
            <div className="overflow-x-auto">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Tag</TableHead>
                    <TableHead>Name</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead>Assigned</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead>Condition</TableHead>
                    <TableHead>Status</TableHead>
                    <TableHead>Shared</TableHead>
                    <TableHead>Updated</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filtered.map((a) => {
                    const category = categories.find((c) => c.id === a.categoryId);
                    const assignee = employees.find((e) => e.id === a.assignedToId);
                    return (
                      <TableRow
                        key={a.id}
                        className="cursor-pointer"
                        onClick={() => window.location.assign(`/assets/${a.id}`)}
                      >
                        <TableCell>
                          <Link
                            to="/assets/$assetId"
                            params={{ assetId: a.id }}
                            className="font-mono text-xs font-medium text-primary hover:underline"
                          >
                            {a.tag}
                          </Link>
                        </TableCell>
                        <TableCell className="font-medium">{a.name}</TableCell>
                        <TableCell className="text-muted-foreground">{category?.name}</TableCell>
                        <TableCell>{assignee?.name || "—"}</TableCell>
                        <TableCell className="text-muted-foreground">{a.location}</TableCell>
                        <TableCell>
                          <StatusBadge status={a.condition} />
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={a.status} />
                        </TableCell>
                        <TableCell>{a.shared ? "Yes" : "No"}</TableCell>
                        <TableCell className="text-xs text-muted-foreground">
                          {format(new Date(a.updatedAt), "MMM d")}
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </div>
          ) : (
            <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
              {filtered.map((a) => (
                <Link key={a.id} to="/assets/$assetId" params={{ assetId: a.id }}>
                  <Card className="transition-shadow hover:shadow-md">
                    <CardContent className="p-4">
                      <div className="flex items-center justify-between">
                        <span className="font-mono text-xs text-primary">{a.tag}</span>
                        <StatusBadge status={a.status} />
                      </div>
                      <div className="mt-2 line-clamp-1 font-medium">{a.name}</div>
                      <div className="mt-1 text-xs text-muted-foreground">
                        {categories.find((c) => c.id === a.categoryId)?.name} · {a.location}
                      </div>
                      <div className="mt-3 flex items-center justify-between text-xs">
                        <StatusBadge status={a.condition} />
                        {a.shared && <span className="text-muted-foreground">Bookable</span>}
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function RegisterAssetDialog({ onDone, actorId }: { onDone: () => void; actorId: string }) {
  const categories = useStore(() => store.categories);
  const departments = useStore(() => store.departments);
  const nextTagPreview = useMemo(() => store.nextTag(), []);
  const [form, setForm] = useState({
    name: "",
    categoryId: "",
    serialNumber: "",
    departmentId: "",
    location: "",
    condition: "excellent" as AssetCondition,
    acquisitionDate: new Date().toISOString().slice(0, 10),
    acquisitionCost: 0,
    shared: false,
    notes: "",
    fileName: "",
  });

  const submit = async () => {
    if (!form.name || !form.categoryId || !form.serialNumber || !form.location) {
      toast.error("Fill required fields");
      return;
    }
    await assetService.create(
      {
        name: form.name,
        categoryId: form.categoryId,
        serialNumber: form.serialNumber,
        departmentId: form.departmentId || undefined,
        location: form.location,
        condition: form.condition,
        acquisitionDate: form.acquisitionDate,
        acquisitionCost: Number(form.acquisitionCost),
        shared: form.shared,
        notes: form.notes,
        status: "available",
      },
      actorId,
    );
    toast.success("Asset registered");
    onDone();
  };

  return (
    <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
      <DialogHeader>
        <DialogTitle>Register New Asset</DialogTitle>
      </DialogHeader>
      <div className="grid gap-4 sm:grid-cols-2">
        <div className="space-y-2">
          <Label>Asset Name *</Label>
          <Input
            value={form.name}
            onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label>Asset Tag (auto)</Label>
          <Input value={nextTagPreview} disabled className="font-mono" />
        </div>
        <div className="space-y-2">
          <Label>Category *</Label>
          <Select
            value={form.categoryId}
            onValueChange={(v) => setForm((s) => ({ ...s, categoryId: v }))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select" />
            </SelectTrigger>
            <SelectContent>
              {categories.map((c) => (
                <SelectItem key={c.id} value={c.id}>
                  {c.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Serial Number *</Label>
          <Input
            value={form.serialNumber}
            onChange={(e) => setForm((s) => ({ ...s, serialNumber: e.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label>Department</Label>
          <Select
            value={form.departmentId}
            onValueChange={(v) => setForm((s) => ({ ...s, departmentId: v }))}
          >
            <SelectTrigger>
              <SelectValue placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              {departments.map((d) => (
                <SelectItem key={d.id} value={d.id}>
                  {d.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Location *</Label>
          <Input
            value={form.location}
            onChange={(e) => setForm((s) => ({ ...s, location: e.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label>Condition</Label>
          <Select
            value={form.condition}
            onValueChange={(v) => setForm((s) => ({ ...s, condition: v as AssetCondition }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {["excellent", "good", "fair", "poor"].map((c) => (
                <SelectItem key={c} value={c} className="capitalize">
                  {c}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Acquisition Date</Label>
          <Input
            type="date"
            value={form.acquisitionDate}
            onChange={(e) => setForm((s) => ({ ...s, acquisitionDate: e.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label>Acquisition Cost (₹)</Label>
          <Input
            type="number"
            value={form.acquisitionCost}
            onChange={(e) => setForm((s) => ({ ...s, acquisitionCost: Number(e.target.value) }))}
          />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label>Notes</Label>
          <Textarea
            rows={2}
            value={form.notes}
            onChange={(e) => setForm((s) => ({ ...s, notes: e.target.value }))}
          />
        </div>
        <div className="space-y-2 sm:col-span-2">
          <Label>Attachment</Label>
          <Input
            type="file"
            onChange={(e) => setForm((s) => ({ ...s, fileName: e.target.files?.[0]?.name || "" }))}
          />
          {form.fileName && (
            <div className="text-xs text-muted-foreground">Selected: {form.fileName}</div>
          )}
        </div>
        <div className="flex items-center gap-2 sm:col-span-2">
          <Switch
            checked={form.shared}
            onCheckedChange={(v) => setForm((s) => ({ ...s, shared: v }))}
            id="shared"
          />
          <Label htmlFor="shared" className="font-normal">
            Shared / Bookable resource
          </Label>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onDone}>
          Cancel
        </Button>
        <Button onClick={submit}>Register</Button>
      </DialogFooter>
    </DialogContent>
  );
}
