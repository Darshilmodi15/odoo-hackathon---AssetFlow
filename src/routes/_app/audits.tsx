import { createFileRoute } from "@tanstack/react-router";
import { useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { auditService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { Progress } from "@/components/ui/progress";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Plus, ShieldAlert, ChevronLeft } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import type { AuditFindingStatus } from "@/types";

export const Route = createFileRoute("/_app/audits")({ component: AuditsPage });

function AuditsPage() {
  const { user, hasRole } = useAuth();
  const audits = useStore(() => store.audits);
  const departments = useStore(() => store.departments);
  const [openNew, setOpenNew] = useState(false);
  const [openId, setOpenId] = useState<string | null>(null);

  if (!hasRole(["admin","asset_manager"])) {
    return <Card><CardContent className="flex flex-col items-center gap-3 p-12 text-center">
      <ShieldAlert className="h-10 w-10 text-muted-foreground" />
      <h3 className="font-semibold">Restricted</h3>
      <p className="text-sm text-muted-foreground">Only admins and asset managers can access audits.</p>
    </CardContent></Card>;
  }

  if (openId) return <AuditExecution auditId={openId} actorId={user!.id} onBack={() => setOpenId(null)} canClose={hasRole("admin")} />;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Asset Audits</h2>
        {hasRole("admin") && (
          <Dialog open={openNew} onOpenChange={setOpenNew}>
            <DialogTrigger asChild><Button><Plus className="mr-1 h-4 w-4" />Create Audit Cycle</Button></DialogTrigger>
            <CreateAuditDialog actorId={user!.id} onClose={() => setOpenNew(false)} />
          </Dialog>
        )}
      </div>

      <Card><CardContent className="p-0">
        {audits.length === 0 ? <EmptyState title="No audit cycles yet" /> : (
          <div className="overflow-x-auto">
            <Table><TableHeader><TableRow>
              <TableHead>Audit</TableHead><TableHead>Scope</TableHead><TableHead>Period</TableHead><TableHead>Progress</TableHead><TableHead>Discrepancies</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead>
            </TableRow></TableHeader>
            <TableBody>
              {audits.map(a => {
                const total = a.findings.length;
                const done = a.findings.filter(f => f.status !== "pending").length;
                const disc = a.findings.filter(f => f.status === "missing" || f.status === "damaged").length;
                const dept = departments.find(d => d.id === a.scopeDepartmentId);
                return (
                  <TableRow key={a.id}>
                    <TableCell className="font-medium">{a.title}</TableCell>
                    <TableCell className="text-xs">{dept?.name || a.scopeLocation || "All"}</TableCell>
                    <TableCell className="text-xs">{format(new Date(a.startDate), "MMM d")} — {format(new Date(a.endDate), "MMM d")}</TableCell>
                    <TableCell className="min-w-32"><Progress value={total ? (done/total)*100 : 0} className="h-2" /><div className="mt-1 text-xs text-muted-foreground">{done}/{total}</div></TableCell>
                    <TableCell><span className={disc > 0 ? "text-destructive font-medium" : "text-muted-foreground"}>{disc}</span></TableCell>
                    <TableCell><StatusBadge status={a.status} /></TableCell>
                    <TableCell className="text-right"><Button size="sm" variant="outline" onClick={() => setOpenId(a.id)}>Open</Button></TableCell>
                  </TableRow>
                );
              })}
            </TableBody></Table>
          </div>
        )}
      </CardContent></Card>
    </div>
  );
}

function CreateAuditDialog({ actorId, onClose }: { actorId: string; onClose: () => void }) {
  const departments = useStore(() => store.departments);
  const employees = useStore(() => store.employees.filter(e => e.role === "admin" || e.role === "asset_manager"));
  const assets = useStore(() => store.assets);
  const [form, setForm] = useState({ title: "", scopeDepartmentId: "", startDate: new Date().toISOString().slice(0,10), endDate: new Date(Date.now()+30*86400000).toISOString().slice(0,10), auditorId: "", notes: "" });

  const submit = async () => {
    if (!form.title || !form.auditorId) { toast.error("Fill required fields"); return; }
    const assetIds = assets.filter(a => !form.scopeDepartmentId || a.departmentId === form.scopeDepartmentId).map(a => a.id);
    await auditService.create({
      title: form.title, scopeDepartmentId: form.scopeDepartmentId || undefined,
      startDate: form.startDate, endDate: form.endDate,
      auditorIds: [form.auditorId], notes: form.notes, assetIds,
    }, actorId);
    toast.success("Audit cycle created");
    onClose();
  };

  return (
    <DialogContent>
      <DialogHeader><DialogTitle>New Audit Cycle</DialogTitle></DialogHeader>
      <div className="space-y-3">
        <div className="space-y-2"><Label>Title *</Label><Input value={form.title} onChange={e => setForm(f => ({...f, title: e.target.value}))} /></div>
        <div className="space-y-2"><Label>Scope (department)</Label>
          <Select value={form.scopeDepartmentId} onValueChange={v => setForm(f => ({...f, scopeDepartmentId: v}))}>
            <SelectTrigger><SelectValue placeholder="All departments" /></SelectTrigger>
            <SelectContent>{departments.map(d => <SelectItem key={d.id} value={d.id}>{d.name}</SelectItem>)}</SelectContent>
          </Select></div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-2"><Label>Start</Label><Input type="date" value={form.startDate} onChange={e => setForm(f => ({...f, startDate: e.target.value}))} /></div>
          <div className="space-y-2"><Label>End</Label><Input type="date" value={form.endDate} onChange={e => setForm(f => ({...f, endDate: e.target.value}))} /></div>
        </div>
        <div className="space-y-2"><Label>Auditor *</Label>
          <Select value={form.auditorId} onValueChange={v => setForm(f => ({...f, auditorId: v}))}>
            <SelectTrigger><SelectValue /></SelectTrigger>
            <SelectContent>{employees.map(e => <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>)}</SelectContent>
          </Select></div>
        <div className="space-y-2"><Label>Notes</Label><Textarea rows={2} value={form.notes} onChange={e => setForm(f => ({...f, notes: e.target.value}))} /></div>
      </div>
      <DialogFooter><Button variant="outline" onClick={onClose}>Cancel</Button><Button onClick={submit}>Create</Button></DialogFooter>
    </DialogContent>
  );
}

function AuditExecution({ auditId, actorId, canClose, onBack }: { auditId: string; actorId: string; canClose: boolean; onBack: () => void }) {
  const audit = useStore(() => store.audits.find(a => a.id === auditId));
  const assets = useStore(() => store.assets);
  const [confirmClose, setConfirmClose] = useState(false);

  if (!audit) return null;
  const locked = audit.status === "closed";

  const updateFinding = async (findingId: string, status: AuditFindingStatus, notes?: string) => {
    await auditService.updateFinding(auditId, findingId, { status, notes }, actorId);
    if (status !== "verified") toast.warning(`Marked as ${status}`);
    else toast.success("Verified");
  };

  const disc = audit.findings.filter(f => f.status === "missing" || f.status === "damaged");

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Button variant="ghost" size="sm" onClick={onBack}><ChevronLeft className="mr-1 h-4 w-4" />Back</Button>
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <h2 className="text-lg font-semibold">{audit.title}</h2>
            <StatusBadge status={audit.status} />
          </div>
          <div className="text-xs text-muted-foreground">{format(new Date(audit.startDate), "MMM d")} — {format(new Date(audit.endDate), "MMM d, yyyy")}</div>
        </div>
        {!locked && canClose && (
          <AlertDialog open={confirmClose} onOpenChange={setConfirmClose}>
            <Button variant="destructive" onClick={() => setConfirmClose(true)}>Close Audit</Button>
            <AlertDialogContent>
              <AlertDialogHeader><AlertDialogTitle>Close audit?</AlertDialogTitle>
                <AlertDialogDescription>Missing assets will be marked as Lost and the audit will be locked from further editing.</AlertDialogDescription></AlertDialogHeader>
              <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={async () => { await auditService.close(auditId, actorId); toast.success("Audit closed"); setConfirmClose(false); onBack(); }}>Close audit</AlertDialogAction></AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        )}
      </div>

      {disc.length > 0 && (
        <Card className="border-warning/40 bg-warning/5">
          <CardHeader className="pb-2"><CardTitle className="text-sm">Discrepancy Report — {disc.length} item{disc.length>1?"s":""}</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-1 text-xs">
              {disc.map(f => {
                const a = assets.find(x => x.id === f.assetId);
                return <div key={f.id} className="flex items-center gap-2"><StatusBadge status={f.status} /> <span className="font-medium">{a?.name}</span> <span className="text-muted-foreground">({a?.tag})</span> {f.notes && <span className="text-muted-foreground">— {f.notes}</span>}</div>;
              })}
            </div>
          </CardContent>
        </Card>
      )}

      <Card>
        <CardHeader className="pb-2"><CardTitle className="text-sm">Verification</CardTitle></CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table><TableHeader><TableRow><TableHead>Asset</TableHead><TableHead>Location</TableHead><TableHead>Status</TableHead><TableHead>Notes</TableHead><TableHead className="text-right">Actions</TableHead></TableRow></TableHeader>
              <TableBody>
                {audit.findings.map(f => {
                  const a = assets.find(x => x.id === f.assetId);
                  return (
                    <TableRow key={f.id}>
                      <TableCell><div className="font-medium">{a?.name}</div><div className="font-mono text-xs text-muted-foreground">{a?.tag}</div></TableCell>
                      <TableCell className="text-xs">{a?.location}</TableCell>
                      <TableCell><StatusBadge status={f.status} /></TableCell>
                      <TableCell className="max-w-40 truncate text-xs">{f.notes || "—"}</TableCell>
                      <TableCell className="text-right">
                        {!locked && (
                          <div className="flex justify-end gap-1">
                            <Button size="sm" variant="outline" onClick={() => updateFinding(f.id, "verified")}>Verify</Button>
                            <Button size="sm" variant="outline" onClick={() => { const n = window.prompt("Notes (optional)") || undefined; updateFinding(f.id, "damaged", n); }}>Damaged</Button>
                            <Button size="sm" variant="outline" onClick={() => { const n = window.prompt("Where should it be?") || undefined; updateFinding(f.id, "missing", n); }}>Missing</Button>
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody></Table>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
