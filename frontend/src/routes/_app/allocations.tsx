import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { allocationService, transferService } from "@/services";
import { useAuth } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogTrigger, DialogDescription } from "@/components/ui/dialog";
import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle } from "@/components/ui/alert-dialog";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Plus, AlertTriangle } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import type { AssetCondition } from "@/types";

export const Route = createFileRoute("/_app/allocations")({ component: AllocationsPage });

interface ConflictInfo { asset: { id: string; name: string; tag: string }; currentHolder: { id: string; name: string } | null }

function AllocationsPage() {
  const { user, hasRole } = useAuth();
  const allocations = useStore(() => store.allocations);
  const transfers = useStore(() => store.transfers);
  const assets = useStore(() => store.assets);
  const employees = useStore(() => store.employees);

  const [openAlloc, setOpenAlloc] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Allocations & Transfers</h2>
        {hasRole(["admin","asset_manager"]) && (
          <Dialog open={openAlloc} onOpenChange={setOpenAlloc}>
            <DialogTrigger asChild><Button><Plus className="mr-1 h-4 w-4" />Allocate Asset</Button></DialogTrigger>
            <AllocateDialog actorId={user!.id} onClose={() => setOpenAlloc(false)} />
          </Dialog>
        )}
      </div>

      <Tabs defaultValue="active">
        <TabsList className="flex-wrap">
          <TabsTrigger value="active">Active ({allocations.filter(a => a.status === "active").length})</TabsTrigger>
          <TabsTrigger value="overdue">Overdue ({allocations.filter(a => a.status === "overdue").length})</TabsTrigger>
          <TabsTrigger value="transfers">Transfers ({transfers.filter(t => t.status === "requested").length})</TabsTrigger>
          <TabsTrigger value="history">History</TabsTrigger>
        </TabsList>

        <TabsContent value="active">
          <AllocationList allocations={allocations.filter(a => a.status === "active")} actorId={user!.id} />
        </TabsContent>
        <TabsContent value="overdue">
          <AllocationList allocations={allocations.filter(a => a.status === "overdue" || (a.status === "active" && a.expectedReturnAt && new Date(a.expectedReturnAt) < new Date()))} actorId={user!.id} highlightOverdue />
        </TabsContent>
        <TabsContent value="transfers">
          <Card><CardContent className="p-0">
            {transfers.length === 0 ? <EmptyState title="No transfer requests" /> : (
              <Table><TableHeader><TableRow>
                <TableHead>Code</TableHead><TableHead>Asset</TableHead><TableHead>From</TableHead><TableHead>To</TableHead><TableHead>Reason</TableHead><TableHead>Requested</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead>
              </TableRow></TableHeader>
              <TableBody>
                {transfers.map(t => {
                  const asset = assets.find(a => a.id === t.assetId);
                  const from = employees.find(e => e.id === t.fromEmployeeId);
                  const to = employees.find(e => e.id === t.toEmployeeId);
                  return (
                    <TableRow key={t.id}>
                      <TableCell className="font-mono text-xs">{t.code}</TableCell>
                      <TableCell>{asset?.name}</TableCell>
                      <TableCell>{from?.name || "—"}</TableCell>
                      <TableCell>{to?.name}</TableCell>
                      <TableCell className="max-w-40 truncate text-xs text-muted-foreground">{t.reason}</TableCell>
                      <TableCell className="text-xs text-muted-foreground">{format(new Date(t.requestedAt), "MMM d")}</TableCell>
                      <TableCell><StatusBadge status={t.status} /></TableCell>
                      <TableCell className="text-right">
                        {t.status === "requested" && hasRole(["admin","asset_manager","department_head"]) && (
                          <div className="flex justify-end gap-1">
                            <ConfirmButton label="Approve" onConfirm={async () => { await transferService.setStatus(t.id, "approved", user!.id); toast.success("Transfer approved"); }} />
                            <ConfirmButton label="Reject" variant="ghost" onConfirm={async () => { await transferService.setStatus(t.id, "rejected", user!.id); toast.success("Transfer rejected"); }} />
                          </div>
                        )}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody></Table>
            )}
          </CardContent></Card>
        </TabsContent>
        <TabsContent value="history">
          <AllocationList allocations={allocations.filter(a => a.status === "returned")} actorId={user!.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}

function AllocationList({ allocations, actorId, highlightOverdue }: { allocations: typeof store.allocations; actorId: string; highlightOverdue?: boolean }) {
  const assets = useStore(() => store.assets);
  const employees = useStore(() => store.employees);
  const [returning, setReturning] = useState<string | null>(null);

  if (allocations.length === 0) return <Card><CardContent><EmptyState title="No allocations to show" /></CardContent></Card>;

  return (
    <Card><CardContent className="p-0">
      <div className="overflow-x-auto">
        <Table><TableHeader><TableRow>
          <TableHead>Asset</TableHead><TableHead>Employee</TableHead><TableHead>Allocated</TableHead><TableHead>Expected Return</TableHead><TableHead>Status</TableHead><TableHead className="text-right">Actions</TableHead>
        </TableRow></TableHeader>
        <TableBody>
          {allocations.map(a => {
            const asset = assets.find(as => as.id === a.assetId);
            const emp = employees.find(e => e.id === a.employeeId);
            const overdue = a.expectedReturnAt && new Date(a.expectedReturnAt) < new Date() && a.status === "active";
            return (
              <TableRow key={a.id} className={highlightOverdue || overdue ? "bg-destructive/5" : ""}>
                <TableCell><div className="font-medium">{asset?.name}</div><div className="font-mono text-xs text-muted-foreground">{asset?.tag}</div></TableCell>
                <TableCell>{emp?.name}</TableCell>
                <TableCell className="text-xs">{format(new Date(a.allocatedAt), "MMM d, yyyy")}</TableCell>
                <TableCell className="text-xs">{a.expectedReturnAt ? <span className={overdue ? "text-destructive font-medium" : ""}>{format(new Date(a.expectedReturnAt), "MMM d, yyyy")}</span> : "—"}</TableCell>
                <TableCell><StatusBadge status={overdue ? "overdue" : a.status} /></TableCell>
                <TableCell className="text-right">
                  {a.status !== "returned" && <Button size="sm" variant="outline" onClick={() => setReturning(a.id)}>Return</Button>}
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody></Table>
      </div>
      {returning && <ReturnDialog allocationId={returning} actorId={actorId} onClose={() => setReturning(null)} />}
    </CardContent></Card>
  );
}

function ReturnDialog({ allocationId, actorId, onClose }: { allocationId: string; actorId: string; onClose: () => void }) {
  const [condition, setCondition] = useState<AssetCondition>("good");
  const [notes, setNotes] = useState("");
  return (
    <Dialog open onOpenChange={onClose}>
      <DialogContent>
        <DialogHeader><DialogTitle>Return Asset</DialogTitle><DialogDescription>Confirm the return and record the asset's condition.</DialogDescription></DialogHeader>
        <div className="space-y-3">
          <div className="space-y-2"><Label>Condition on return</Label>
            <Select value={condition} onValueChange={v => setCondition(v as AssetCondition)}><SelectTrigger><SelectValue /></SelectTrigger>
              <SelectContent>{["excellent","good","fair","poor"].map(c => <SelectItem key={c} value={c} className="capitalize">{c}</SelectItem>)}</SelectContent></Select></div>
          <div className="space-y-2"><Label>Notes (optional)</Label><Textarea value={notes} onChange={e => setNotes(e.target.value)} /></div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={onClose}>Cancel</Button>
          <Button onClick={async () => { await allocationService.return(allocationId, { returnCondition: condition, returnNotes: notes }, actorId); toast.success("Asset returned"); onClose(); }}>Confirm Return</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

function AllocateDialog({ actorId, onClose }: { actorId: string; onClose: () => void }) {
  const assets = useStore(() => store.assets);
  const employees = useStore(() => store.employees);
  const [assetId, setAssetId] = useState("");
  const [employeeId, setEmployeeId] = useState("");
  const [expectedReturn, setExpectedReturn] = useState("");
  const [notes, setNotes] = useState("");
  const [conflict, setConflict] = useState<ConflictInfo | null>(null);
  const [showTransfer, setShowTransfer] = useState(false);
  const [transferReason, setTransferReason] = useState("");

  const submit = async () => {
    if (!assetId || !employeeId) { toast.error("Select asset and employee"); return; }
    try {
      await allocationService.create({ assetId, employeeId, expectedReturnAt: expectedReturn || undefined, notes }, actorId);
      toast.success("Asset allocated");
      onClose();
    } catch (err) {
      const anyErr = err as { code?: string; currentHolder?: { id: string; name: string } | null; asset?: { id: string; name: string; tag: string } };
      if (anyErr.code === "ALLOCATION_CONFLICT") {
        setConflict({ asset: anyErr.asset!, currentHolder: anyErr.currentHolder ?? null });
      } else {
        toast.error(err instanceof Error ? err.message : "Failed");
      }
    }
  };

  const requestTransfer = async () => {
    if (!transferReason) { toast.error("Reason required"); return; }
    await transferService.create({ assetId, toEmployeeId: employeeId, reason: transferReason }, actorId);
    toast.success("Transfer request submitted");
    onClose();
  };

  return (
    <DialogContent>
      <DialogHeader><DialogTitle>Allocate Asset</DialogTitle></DialogHeader>
      {!conflict && !showTransfer && (
        <div className="space-y-3">
          <div className="space-y-2"><Label>Asset</Label>
            <Select value={assetId} onValueChange={setAssetId}><SelectTrigger><SelectValue placeholder="Select asset" /></SelectTrigger>
              <SelectContent>{assets.map(a => <SelectItem key={a.id} value={a.id}>{a.tag} — {a.name} ({a.status.replace("_"," ")})</SelectItem>)}</SelectContent></Select></div>
          <div className="space-y-2"><Label>Employee</Label>
            <Select value={employeeId} onValueChange={setEmployeeId}><SelectTrigger><SelectValue placeholder="Select employee" /></SelectTrigger>
              <SelectContent>{employees.map(e => <SelectItem key={e.id} value={e.id}>{e.name}</SelectItem>)}</SelectContent></Select></div>
          <div className="space-y-2"><Label>Expected return (optional)</Label><Input type="date" value={expectedReturn} onChange={e => setExpectedReturn(e.target.value)} /></div>
          <div className="space-y-2"><Label>Notes</Label><Textarea value={notes} onChange={e => setNotes(e.target.value)} rows={2} /></div>
        </div>
      )}
      {conflict && !showTransfer && (
        <div className="space-y-3">
          <div className="flex items-start gap-3 rounded-md border border-destructive/30 bg-destructive/5 p-3">
            <AlertTriangle className="mt-0.5 h-5 w-5 shrink-0 text-destructive" />
            <div className="text-sm">
              <div className="font-medium">Allocation Conflict</div>
              <div className="mt-1 text-muted-foreground">
                {conflict.currentHolder
                  ? <>This asset is currently held by <span className="font-medium text-foreground">{conflict.currentHolder.name}</span>.</>
                  : <>This asset is not available for allocation.</>}
              </div>
            </div>
          </div>
          <div className="flex flex-wrap gap-2">
            <Button variant="outline" onClick={() => setConflict(null)}>Select another asset</Button>
            {conflict.currentHolder && <Button onClick={() => setShowTransfer(true)}>Create Transfer Request</Button>}
          </div>
        </div>
      )}
      {showTransfer && (
        <div className="space-y-3">
          <div className="rounded-md bg-muted/50 p-3 text-sm">Requesting transfer of <b>{conflict?.asset.name}</b> ({conflict?.asset.tag}) from {conflict?.currentHolder?.name} to {employees.find(e => e.id === employeeId)?.name}.</div>
          <div className="space-y-2"><Label>Reason</Label><Textarea value={transferReason} onChange={e => setTransferReason(e.target.value)} rows={3} /></div>
        </div>
      )}
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>Close</Button>
        {!conflict && !showTransfer && <Button onClick={submit}>Allocate</Button>}
        {showTransfer && <Button onClick={requestTransfer}>Submit Request</Button>}
      </DialogFooter>
    </DialogContent>
  );
}

function ConfirmButton({ label, onConfirm, variant = "outline" }: { label: string; onConfirm: () => void; variant?: "outline" | "ghost" }) {
  const [open, setOpen] = useState(false);
  return (
    <AlertDialog open={open} onOpenChange={setOpen}>
      <Button size="sm" variant={variant} onClick={() => setOpen(true)}>{label}</Button>
      <AlertDialogContent>
        <AlertDialogHeader><AlertDialogTitle>{label}?</AlertDialogTitle><AlertDialogDescription>Please confirm this action.</AlertDialogDescription></AlertDialogHeader>
        <AlertDialogFooter><AlertDialogCancel>Cancel</AlertDialogCancel><AlertDialogAction onClick={onConfirm}>{label}</AlertDialogAction></AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}

// unused useMemo import to satisfy tsc
void useMemo;
