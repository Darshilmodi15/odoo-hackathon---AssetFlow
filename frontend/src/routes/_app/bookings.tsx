import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState } from "react";
import { useStore } from "@/hooks/useStore";
import { store, findBookingConflict } from "@/mocks/store";
import { bookingService } from "@/services";
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
  DialogDescription,
} from "@/components/ui/dialog";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Plus, AlertTriangle, Calendar as CalIcon } from "lucide-react";
import { toast } from "sonner";
import { format, addDays, startOfDay } from "date-fns";

export const Route = createFileRoute("/_app/bookings")({ component: BookingsPage });

const HOURS = Array.from({ length: 12 }, (_, i) => i + 8); // 8:00 - 19:00

interface BookingConflictErr {
  code: string;
  conflict: { assetId: string; startAt: string; endAt: string };
  suggestions: { assetId: string; startAt: string; endAt: string; reason: string }[];
}

function BookingsPage() {
  const { user } = useAuth();
  const assets = useStore(() => store.assets.filter((a) => a.shared));
  const employees = useStore(() => store.employees);
  const bookings = useStore(() => store.bookings);
  const departments = useStore(() => store.departments);
  const [resourceId, setResourceId] = useState<string>(assets[0]?.id || "");
  const [dayOffset, setDayOffset] = useState(0);
  const [openNew, setOpenNew] = useState(false);

  const day = useMemo(() => addDays(startOfDay(new Date()), dayOffset), [dayOffset]);
  const dayEnd = useMemo(() => addDays(day, 1), [day]);
  const dayBookings = useMemo(
    () =>
      bookings.filter(
        (b) =>
          b.assetId === resourceId &&
          b.status !== "cancelled" &&
          new Date(b.startAt) < dayEnd &&
          new Date(b.endAt) > day,
      ),
    [bookings, resourceId, day, dayEnd],
  );

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <Select value={resourceId} onValueChange={setResourceId}>
          <SelectTrigger className="w-64">
            <SelectValue placeholder="Select resource" />
          </SelectTrigger>
          <SelectContent>
            {assets.map((a) => (
              <SelectItem key={a.id} value={a.id}>
                {a.name}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <div className="flex items-center gap-1 ml-auto">
          <Button size="sm" variant="outline" onClick={() => setDayOffset((d) => d - 1)}>
            ‹
          </Button>
          <div className="min-w-32 text-center text-sm font-medium">
            {format(day, "EEE, MMM d")}
          </div>
          <Button size="sm" variant="outline" onClick={() => setDayOffset((d) => d + 1)}>
            ›
          </Button>
          <Button size="sm" variant="ghost" onClick={() => setDayOffset(0)}>
            Today
          </Button>
        </div>
        <Dialog open={openNew} onOpenChange={setOpenNew}>
          <DialogTrigger asChild>
            <Button>
              <Plus className="mr-1 h-4 w-4" />
              Book Resource
            </Button>
          </DialogTrigger>
          <BookingDialog
            actorId={user!.id}
            initialAssetId={resourceId}
            initialDate={format(day, "yyyy-MM-dd")}
            onClose={() => setOpenNew(false)}
          />
        </Dialog>
      </div>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <CalIcon className="h-4 w-4" />
            Timeline — {assets.find((a) => a.id === resourceId)?.name}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-[60px_1fr] gap-1">
            {HOURS.map((h) => (
              <>
                <div key={`h-${h}`} className="text-xs text-muted-foreground pt-1">
                  {String(h).padStart(2, "0")}:00
                </div>
                <div key={`c-${h}`} className="relative h-10 rounded border border-border bg-card">
                  {dayBookings.map((b) => {
                    const bs = new Date(b.startAt),
                      be = new Date(b.endAt);
                    const slotStart = new Date(day);
                    slotStart.setHours(h);
                    const slotEnd = new Date(day);
                    slotEnd.setHours(h + 1);
                    if (bs < slotEnd && be > slotStart) {
                      const startMin = Math.max(0, (bs.getTime() - slotStart.getTime()) / 60000);
                      const endMin = Math.min(60, (be.getTime() - slotStart.getTime()) / 60000);
                      const emp = employees.find((e) => e.id === b.bookedById);
                      return (
                        <div
                          key={b.id}
                          className="absolute inset-y-1 rounded bg-primary/85 px-2 py-0.5 text-[10px] font-medium text-primary-foreground shadow-sm overflow-hidden"
                          style={{
                            left: `${(startMin / 60) * 100}%`,
                            width: `${((endMin - startMin) / 60) * 100}%`,
                          }}
                        >
                          <div className="truncate">{b.purpose}</div>
                          <div className="truncate opacity-80">{emp?.name}</div>
                        </div>
                      );
                    }
                    return null;
                  })}
                </div>
              </>
            ))}
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base">Upcoming Bookings</CardTitle>
        </CardHeader>
        <CardContent className="space-y-2">
          {bookings
            .filter((b) => b.status === "upcoming")
            .slice(0, 10)
            .map((b) => {
              const asset =
                assets.find((a) => a.id === b.assetId) ||
                store.assets.find((a) => a.id === b.assetId);
              const emp = employees.find((e) => e.id === b.bookedById);
              const dept = departments.find((d) => d.id === b.departmentId);
              return (
                <div
                  key={b.id}
                  className="flex flex-wrap items-center gap-3 rounded-md border border-border p-3 text-sm"
                >
                  <div className="min-w-0 flex-1">
                    <div className="font-medium">{asset?.name}</div>
                    <div className="text-xs text-muted-foreground">
                      {b.purpose} · {emp?.name} · {dept?.name}
                    </div>
                  </div>
                  <div className="text-right text-xs">
                    <div>{format(new Date(b.startAt), "MMM d")}</div>
                    <div className="text-muted-foreground">
                      {format(new Date(b.startAt), "HH:mm")} — {format(new Date(b.endAt), "HH:mm")}
                    </div>
                  </div>
                  <StatusBadge status={b.status} />
                  {(b.bookedById === user?.id || user?.role === "admin") && (
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={async () => {
                        await bookingService.cancel(b.id, user!.id);
                        toast.success("Booking cancelled");
                      }}
                    >
                      Cancel
                    </Button>
                  )}
                </div>
              );
            })}
          {bookings.filter((b) => b.status === "upcoming").length === 0 && (
            <EmptyState title="No upcoming bookings" />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

function BookingDialog({
  actorId,
  initialAssetId,
  initialDate,
  onClose,
}: {
  actorId: string;
  initialAssetId: string;
  initialDate: string;
  onClose: () => void;
}) {
  const assets = useStore(() => store.assets.filter((a) => a.shared));
  const departments = useStore(() => store.departments);
  const [form, setForm] = useState({
    assetId: initialAssetId,
    date: initialDate,
    start: "09:00",
    end: "10:00",
    purpose: "",
    departmentId: "",
    attendees: 1,
    notes: "",
  });
  const [conflict, setConflict] = useState<BookingConflictErr | null>(null);

  const applySuggestion = (s: { assetId: string; startAt: string; endAt: string }) => {
    const st = new Date(s.startAt),
      en = new Date(s.endAt);
    setForm((f) => ({
      ...f,
      assetId: s.assetId,
      date: format(st, "yyyy-MM-dd"),
      start: format(st, "HH:mm"),
      end: format(en, "HH:mm"),
    }));
    setConflict(null);
  };

  const submit = async () => {
    if (!form.assetId || !form.purpose) {
      toast.error("Fill required fields");
      return;
    }
    const startAt = new Date(`${form.date}T${form.start}:00`).toISOString();
    const endAt = new Date(`${form.date}T${form.end}:00`).toISOString();
    if (new Date(endAt) <= new Date(startAt)) {
      toast.error("End must be after start");
      return;
    }
    try {
      await bookingService.create(
        {
          assetId: form.assetId,
          bookedById: actorId,
          departmentId: form.departmentId || undefined,
          startAt,
          endAt,
          purpose: form.purpose,
          attendees: form.attendees,
          notes: form.notes,
        },
        actorId,
      );
      toast.success("Booking created");
      onClose();
    } catch (err) {
      const anyErr = err as BookingConflictErr;
      if (anyErr.code === "BOOKING_OVERLAP") setConflict(anyErr);
      else toast.error(err instanceof Error ? err.message : "Failed");
    }
  };

  // Live conflict preview
  const previewConflict = useMemo(() => {
    if (!form.assetId) return null;
    try {
      const s = new Date(`${form.date}T${form.start}:00`).toISOString();
      const e = new Date(`${form.date}T${form.end}:00`).toISOString();
      return findBookingConflict(form.assetId, s, e);
    } catch {
      return null;
    }
  }, [form]);

  return (
    <DialogContent>
      <DialogHeader>
        <DialogTitle>Book Resource</DialogTitle>
        <DialogDescription>Reserve a shared resource for a time slot.</DialogDescription>
      </DialogHeader>
      <div className="space-y-3">
        <div className="space-y-2">
          <Label>Resource *</Label>
          <Select
            value={form.assetId}
            onValueChange={(v) => setForm((f) => ({ ...f, assetId: v }))}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {assets.map((a) => (
                <SelectItem key={a.id} value={a.id}>
                  {a.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="space-y-2">
            <Label>Date</Label>
            <Input
              type="date"
              value={form.date}
              onChange={(e) => setForm((f) => ({ ...f, date: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>Start</Label>
            <Input
              type="time"
              value={form.start}
              onChange={(e) => setForm((f) => ({ ...f, start: e.target.value }))}
            />
          </div>
          <div className="space-y-2">
            <Label>End</Label>
            <Input
              type="time"
              value={form.end}
              onChange={(e) => setForm((f) => ({ ...f, end: e.target.value }))}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Purpose *</Label>
          <Input
            value={form.purpose}
            onChange={(e) => setForm((f) => ({ ...f, purpose: e.target.value }))}
          />
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-2">
            <Label>Department</Label>
            <Select
              value={form.departmentId}
              onValueChange={(v) => setForm((f) => ({ ...f, departmentId: v }))}
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
            <Label>Attendees</Label>
            <Input
              type="number"
              min={1}
              value={form.attendees}
              onChange={(e) => setForm((f) => ({ ...f, attendees: Number(e.target.value) }))}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Notes</Label>
          <Textarea
            rows={2}
            value={form.notes}
            onChange={(e) => setForm((f) => ({ ...f, notes: e.target.value }))}
          />
        </div>

        {previewConflict && !conflict && (
          <div className="rounded-md border border-warning/40 bg-warning/10 p-3 text-xs">
            <div className="flex items-center gap-2 font-medium">
              <AlertTriangle className="h-4 w-4" />
              Time slot may conflict with an existing booking.
            </div>
          </div>
        )}

        {conflict && (
          <div className="rounded-md border border-destructive/30 bg-destructive/5 p-3 text-sm">
            <div className="flex items-center gap-2 font-medium text-destructive">
              <AlertTriangle className="h-4 w-4" />
              Booking conflict
            </div>
            <div className="mt-1 text-muted-foreground">
              {assets.find((a) => a.id === form.assetId)?.name} is already booked during this time.
            </div>
            {conflict.suggestions.length > 0 && (
              <div className="mt-2">
                <div className="text-xs font-medium">Suggested alternatives:</div>
                <div className="mt-1 space-y-1">
                  {conflict.suggestions.map((s, i) => {
                    const asset = store.assets.find((a) => a.id === s.assetId);
                    return (
                      <button
                        key={i}
                        onClick={() => applySuggestion(s)}
                        className="block w-full rounded border border-border bg-card px-2 py-1.5 text-left text-xs hover:bg-accent"
                      >
                        <span className="font-medium">{asset?.name}</span> ·{" "}
                        {format(new Date(s.startAt), "MMM d HH:mm")} –{" "}
                        {format(new Date(s.endAt), "HH:mm")}{" "}
                        <span className="text-muted-foreground">({s.reason})</span>
                      </button>
                    );
                  })}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
      <DialogFooter>
        <Button variant="outline" onClick={onClose}>
          Cancel
        </Button>
        <Button onClick={submit}>Confirm Booking</Button>
      </DialogFooter>
    </DialogContent>
  );
}
