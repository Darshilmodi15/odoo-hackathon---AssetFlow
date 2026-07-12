import { createFileRoute } from "@tanstack/react-router";
import { useEffect, useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { maintenanceService, refreshRealData } from "@/services";
import { USE_MOCKS } from "@/services/apiClient";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
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
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Plus, Wrench } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import type { MaintenancePriority, MaintenanceStatus, MaintenanceRequest } from "@/types";

export const Route = createFileRoute("/_app/maintenance")({ component: MaintenancePage });

const COLUMNS: { key: MaintenanceStatus; label: string }[] = [
  { key: "pending", label: "Pending" },
  { key: "approved", label: "Approved" },
  { key: "assigned", label: "Technician Assigned" },
  { key: "in_progress", label: "In Progress" },
  { key: "resolved", label: "Resolved" },
  { key: "rejected", label: "Rejected" },
];

function MaintenancePage() {
  const { user, hasRole } = useAuth();
  const requests = useStore(() => store.maintenance);
  const [openNew, setOpenNew] = useState(false);
  const [detail, setDetail] = useState<string | null>(null);
  const [loading, setLoading] = useState(!USE_MOCKS);
  const [error, setError] = useState("");

  useEffect(() => {
    if (USE_MOCKS) return;
    setLoading(true);
    refreshRealData()
      .then(() => setError(""))
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load maintenance"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold flex items-center gap-2">
          <Wrench className="h-5 w-5" />
          Maintenance
        </h2>
        <Dialog open={openNew} onOpenChange={setOpenNew}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-1 h-4 w-4" />
              Raise Request
            </Button>
          </DialogTrigger>
          <NewMaintenanceDialog actorId={user!.id} onClose={() => setOpenNew(false)} />
        </Dialog>
      </div>

      {loading && (
        <Card>
          <CardContent className="py-8 text-sm text-muted-foreground">
            Loading maintenance requests...
          </CardContent>
        </Card>
      )}

      {error && (
        <Card className="border-destructive/40">
          <CardContent className="py-4 text-sm text-destructive">{error}</CardContent>
        </Card>
      )}

      {!loading && !error && (
        <Tabs defaultValue="kanban">
          <TabsList>
            <TabsTrigger value="kanban">Kanban</TabsTrigger>
            <TabsTrigger value="table">Table</TabsTrigger>
          </TabsList>
          <TabsContent value="kanban">
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3 2xl:grid-cols-6">
              {COLUMNS.map((col) => {
                const items = requests.filter((r) => r.status === col.key);
                return (
                  <Card key={col.key} className="min-w-0">
                    <CardHeader className="pb-2">
                      <CardTitle className="text-sm flex items-center justify-between">
                        {col.label}
                        <span className="rounded-full bg-muted px-2 py-0.5 text-xs font-normal">
                          {items.length}
                        </span>
                      </CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 max-h-[600px] overflow-y-auto">
                      {items.length === 0 && (
                        <div className="text-xs text-muted-foreground text-center py-4">Empty</div>
                      )}
                      {items.map((r) => (
                        <KanbanCard key={r.id} r={r} onClick={() => setDetail(r.id)} />
                      ))}
                    </CardContent>
                  </Card>
                );
              })}
            </div>
          </TabsContent>
          <TabsContent value="table">
            <Card>
              <CardContent className="p-0">
                <div className="overflow-x-auto">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Code</TableHead>
                        <TableHead>Asset</TableHead>
                        <TableHead>Issue</TableHead>
                        <TableHead>Priority</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Requested</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {requests.map((r) => {
                        const asset = store.assets.find((a) => a.id === r.assetId);
                        return (
                          <TableRow key={r.id}>
                            <TableCell className="font-mono text-xs">{r.code}</TableCell>
                            <TableCell>{asset?.name}</TableCell>
                            <TableCell>{r.title}</TableCell>
                            <TableCell>
                              <StatusBadge status={r.priority} />
                            </TableCell>
                            <TableCell>
                              <StatusBadge status={r.status} />
                            </TableCell>
                            <TableCell className="text-xs">
                              {format(new Date(r.requestedAt), "MMM d")}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button size="sm" variant="ghost" onClick={() => setDetail(r.id)}>
                                View
                              </Button>
                            </TableCell>
                          </TableRow>
                        );
                      })}
                    </TableBody>
                  </Table>
                </div>
                {requests.length === 0 && <EmptyState title="No maintenance requests" />}
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      )}

      {detail && (
        <DetailDialog
          id={detail}
          actorId={user!.id}
          canManage={hasRole(["admin", "asset_manager"])}
          onClose={() => setDetail(null)}
        />
      )}
    </div>
  );
}

function KanbanCard({ r, onClick }: { r: MaintenanceRequest; onClick: () => void }) {
  const asset = store.assets.find((a) => a.id === r.assetId);
  return (
    <button
      onClick={onClick}
      className="block w-full rounded-md border border-border bg-card p-3 text-left transition-shadow hover:shadow"
    >
      <div className="flex items-center justify-between text-xs">
        <span className="font-mono">{r.code}</span>
        <StatusBadge status={r.priority} />
      </div>
      <div className="mt-2 line-clamp-2 text-sm font-medium">{r.title}</div>
      <div className="mt-1 truncate text-xs text-muted-foreground">{asset?.name}</div>
      <div className="mt-2 text-[10px] text-muted-foreground">
        {format(new Date(r.requestedAt), "MMM d")}
      </div>
    </button>
  );
}

function NewMaintenanceDialog({ actorId, onClose }: { actorId: string; onClose: () => void }) {
  const assets = useStore(() => store.assets);
  const [saving, setSaving] = useState(false);
  const [form, setForm] = useState({
    assetId: "",
    title: "",
    description: "",
    priority: "medium" as MaintenancePriority,
    preferredDate: "",
  });
  const submit = async () => {
    if (!form.assetId || !form.title || !form.description) {
      toast.error("Fill required fields");
      return;
    }
    setSaving(true);
    try {
      await maintenanceService.create(form, actorId);
      toast.success("Maintenance request raised");
      onClose();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Could not raise request");
    } finally {
      setSaving(false);
    }
  };
  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Raise Maintenance Request</DialogTitle>
      </DialogHeader>
      <div className="space-y-3">
        <div className="space-y-2">
          <Label>Asset *</Label>
          <Select
            value={form.assetId}
            onValueChange={(v) => setForm((f) => ({ ...f, assetId: v }))}
          >
            <SelectTrigger>
              <SelectValue placeholder="Select asset" />
            </SelectTrigger>
            <SelectContent>
              {assets.map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.tag} — {a.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="space-y-2">
          <Label>Issue title *</Label>
          <Input
            value={form.title}
            onChange={(e) => setForm((f) => ({ ...f, title: e.target.value }))}
          />
        </div>
        <div className="space-y-2">
          <Label>Description *</Label>
          <Textarea
            rows={3}
            value={form.description}
            onChange={(e) => setForm((f) => ({ ...f, description: e.target.value }))}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-2">
            <Label>Priority</Label>
            <Select
              value={form.priority}
              onValueChange={(v) => setForm((f) => ({ ...f, priority: v as MaintenancePriority }))}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {["low", "medium", "high", "critical"].map((p) => (
                  <SelectItem key={p} value={p} className="capitalize">
                    {p}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
          <div className="space-y-2">
            <Label>Preferred date</Label>
            <Input
              type="date"
              value={form.preferredDate}
              onChange={(e) => setForm((f) => ({ ...f, preferredDate: e.target.value }))}
            />
          </div>
        </div>
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={submit} disabled={saving}>
          {saving ? "Submitting..." : "Submit"}
        </Button>
      </DialogFooter>
    </DialogContent>
  );
}

function DetailDialog({
  id,
  actorId,
  canManage,
  onClose,
}: {
  id: string;
  actorId: string;
  canManage: boolean;
  onClose: () => void;
}) {
  const req = useStore(() => store.maintenance.find((m) => m.id === id));
  const employees = useStore(() => store.employees);
  const [notes, setNotes] = useState("");
  const [technician, setTechnician] = useState("");
  const [estCost, setEstCost] = useState<number | "">("");
  const [saving, setSaving] = useState(false);

  if (!req) return null;
  const asset = store.assets.find((a) => a.id === req.assetId);
  const requester = employees.find((e) => e.id === req.requestedById);
  const technicians = employees.filter((e) => e.role === "asset_manager" || e.role === "admin");

  const move = async (status: MaintenanceStatus, extra?: Record<string, unknown>) => {
    setSaving(true);
    try {
      await maintenanceService.setStatus(id, status, actorId, extra);
      toast.success(`Moved to ${status.replace("_", " ")}`);
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Maintenance update failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent className="max-h-[90vh] overflow-y-auto sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <span className="font-mono">{req.code}</span>
            <StatusBadge status={req.status} />
            <StatusBadge status={req.priority} />
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-3 text-sm">
          <div>
            <div className="font-medium">{req.title}</div>
            <div className="text-muted-foreground">{req.description}</div>
          </div>
          <div className="grid grid-cols-2 gap-3 text-xs">
            <div>
              <span className="text-muted-foreground">Asset:</span> {asset?.name} ({asset?.tag})
            </div>
            <div>
              <span className="text-muted-foreground">Requested by:</span> {requester?.name}
            </div>
            <div>
              <span className="text-muted-foreground">Raised:</span>{" "}
              {format(new Date(req.requestedAt), "MMM d, yyyy")}
            </div>
            {req.technicianId && (
              <div>
                <span className="text-muted-foreground">Technician:</span>{" "}
                {employees.find((e) => e.id === req.technicianId)?.name}
              </div>
            )}
            {req.estimatedCost !== undefined && (
              <div>
                <span className="text-muted-foreground">Est. cost:</span> ₹{req.estimatedCost}
              </div>
            )}
            {req.actualCost !== undefined && (
              <div>
                <span className="text-muted-foreground">Actual cost:</span> ₹{req.actualCost}
              </div>
            )}
          </div>
          {req.resolutionNotes && (
            <div className="rounded bg-muted/50 p-2 text-xs">{req.resolutionNotes}</div>
          )}
          <div>
            <div className="mb-2 text-xs font-medium">History</div>
            <div className="space-y-1">
              {req.history.map((h, i) => (
                <div key={i} className="flex items-center gap-2 text-xs">
                  <div className="h-1.5 w-1.5 rounded-full bg-primary" />
                  <StatusBadge status={h.status} className="text-[10px]" />
                  <span className="text-muted-foreground">
                    {format(new Date(h.at), "MMM d HH:mm")}
                  </span>
                  {h.note && <span className="text-muted-foreground">— {h.note}</span>}
                </div>
              ))}
            </div>
          </div>

          {canManage && (
            <div className="space-y-2 rounded-md border border-border p-3">
              <div className="text-xs font-medium">Manage</div>
              {req.status === "pending" && (
                <>
                  <Textarea
                    placeholder="Rejection reason (if rejecting)"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                  />
                  <div className="flex gap-2">
                    <Button size="sm" disabled={saving} onClick={() => move("approved")}>
                      Approve
                    </Button>
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={saving}
                      onClick={() => move("rejected", { note: notes })}
                    >
                      Reject
                    </Button>
                  </div>
                </>
              )}
              {req.status === "approved" && (
                <>
                  <div className="grid grid-cols-2 gap-2">
                    <Select value={technician} onValueChange={setTechnician}>
                      <SelectTrigger>
                        <SelectValue placeholder="Technician" />
                      </SelectTrigger>
                      <SelectContent>
                        {technicians.map((t) => (
                          <SelectItem key={t.id} value={t.id}>
                            {t.name}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                    <Input
                      type="number"
                      placeholder="Est. cost ₹"
                      value={estCost}
                      onChange={(e) => setEstCost(e.target.value ? Number(e.target.value) : "")}
                    />
                  </div>
                  <Button
                    size="sm"
                    disabled={saving}
                    onClick={() =>
                      move("assigned", {
                        technicianId: technician,
                        estimatedCost: estCost || undefined,
                      })
                    }
                  >
                    Assign Technician
                  </Button>
                </>
              )}
              {req.status === "assigned" && (
                <Button size="sm" disabled={saving} onClick={() => move("in_progress")}>
                  Start Work
                </Button>
              )}
              {req.status === "in_progress" && (
                <>
                  <Textarea
                    placeholder="Resolution notes"
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    rows={2}
                  />
                  <Button
                    size="sm"
                    disabled={saving}
                    onClick={() =>
                      move("resolved", { resolutionNotes: notes, actualCost: estCost || undefined })
                    }
                  >
                    Mark Resolved
                  </Button>
                </>
              )}
            </div>
          )}
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
