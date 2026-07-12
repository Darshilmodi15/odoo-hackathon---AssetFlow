import { createFileRoute } from "@tanstack/react-router";
import { useMemo, useState, Fragment } from "react";
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
import { Tooltip, TooltipTrigger, TooltipContent, TooltipProvider } from "@/components/ui/tooltip";


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

  const isToday = useMemo(() => {
    return format(day, "yyyy-MM-dd") === format(new Date(), "yyyy-MM-dd");
  }, [day]);
  const currentHour = new Date().getHours();
  const currentMin = new Date().getMinutes();

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
          <div className="grid grid-cols-[60px_1fr] gap-2">
            <TooltipProvider>
              {HOURS.map((h) => (
                <Fragment key={h}>
                  <div className="text-xs text-muted-foreground pt-2.5 font-mono">
                    {String(h).padStart(2, "0")}:00
                  </div>
                  <div className="relative h-12 rounded-lg border border-border bg-card/65 transition-colors hover:bg-card/90 shadow-sm p-1">
                    {/* Current Time Indicator Line */}
                    {isToday && currentHour === h && (
                      <div
                        className="absolute left-0 right-0 border-t-2 border-destructive z-10 pointer-events-none"
                        style={{ top: `${(currentMin / 60) * 100}%` }}
                      >
                        <span className="absolute -left-1 -top-1 h-2.5 w-2.5 rounded-full bg-destructive animate-pulse" />
                      </div>
                    )}
                    
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
                        const dept = departments.find((d) => d.id === b.departmentId);
                        return (
                          <Tooltip key={b.id}>
                            <TooltipTrigger asChild>
                              <div
                                className="absolute inset-y-1.5 rounded-md bg-primary/90 px-3 py-1 text-[11px] font-semibold text-primary-foreground shadow-sm overflow-hidden hover:bg-primary hover:scale-[1.01] transition-all cursor-pointer flex flex-col justify-center"
                                style={{
                                  left: `${(startMin / 60) * 100}%`,
                                  width: `${((endMin - startMin) / 60) * 100}%`,
                                }}
                              >
                                <div className="truncate leading-none">{b.purpose}</div>
                                <div className="truncate opacity-90 text-[9px] mt-0.5 font-normal leading-none">{emp?.name}</div>
                              </div>
                            </TooltipTrigger>
                            <TooltipContent side="top" className="bg-popover border border-border p-3 rounded-lg shadow-lg text-popover-foreground">
                              <div className="space-y-1">
                                <p className="font-semibold text-sm text-foreground">{b.purpose}</p>
                                <p className="text-xs"><span className="font-medium text-muted-foreground">Booked By:</span> {emp?.name || "Unknown"}</p>
                                {dept && <p className="text-xs"><span className="font-medium text-muted-foreground">Department:</span> {dept.name}</p>}
                                <p className="text-xs font-mono text-primary font-medium">
                                  {format(bs, "HH:mm")} - {format(be, "HH:mm")}
                                </p>
                                {b.notes && (
                                  <p className="text-[10px] italic border-t border-border mt-1 pt-1 text-muted-foreground max-w-xs">{b.notes}</p>
                                )}
                              </div>
                            </TooltipContent>
                          </Tooltip>
                        );
                      }
                      return null;
                    })}
                  </div>
                </Fragment>
              ))}
            </TooltipProvider>
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
            <EmptyState
              title="No upcoming bookings"
              description="Book a shared resource by clicking the 'Book Resource' button above."
              icon={CalIcon}
            />
          )}
        </CardContent>
      </Card>
    </div>
  );
}

import { cn } from "@/lib/utils";

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
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [conflict, setConflict] = useState<BookingConflictErr | null>(null);

  const updateField = (key: string, value: any) => {
    setForm((f) => ({ ...f, [key]: value }));
    if (errors[key]) {
      setErrors((errs) => {
        const copy = { ...errs };
        delete copy[key];
        return copy;
      });
    }
  };

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
    setErrors({});
  };

  const validate = () => {
    const newErrors: Record<string, string> = {};
    if (!form.assetId) newErrors.assetId = "Please select a resource";
    if (!form.date) newErrors.date = "Date is required";
    if (!form.start) newErrors.start = "Start time is required";
    if (!form.end) newErrors.end = "End time is required";
    if (!form.purpose || !form.purpose.trim()) {
      newErrors.purpose = "Purpose is required";
    } else if (form.purpose.trim().length < 3) {
      newErrors.purpose = "Purpose must be at least 3 characters";
    }

    if (form.date && form.start) {
      const now = new Date();
      const startAtDate = new Date(`${form.date}T${form.start}:00`);
      if (isNaN(startAtDate.getTime())) {
        newErrors.start = "Invalid start time";
      } else if (startAtDate < now) {
        newErrors.start = "Start time must be in the future";
      }
    }

    if (form.date && form.start && form.end) {
      const startAtDate = new Date(`${form.date}T${form.start}:00`);
      const endAtDate = new Date(`${form.date}T${form.end}:00`);
      if (isNaN(endAtDate.getTime())) {
        newErrors.end = "Invalid end time";
      } else if (endAtDate <= startAtDate) {
        newErrors.end = "End time must be after start time";
      }
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const submit = async () => {
    if (!validate()) {
      toast.error("Please fix the validation errors.");
      return;
    }
    const startAt = new Date(`${form.date}T${form.start}:00`).toISOString();
    const endAt = new Date(`${form.date}T${form.end}:00`).toISOString();
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
          <Label className={cn(errors.assetId && "text-destructive")}>Resource *</Label>
          <Select
            value={form.assetId}
            onValueChange={(v) => updateField("assetId", v)}
          >
            <SelectTrigger className={cn(errors.assetId && "border-destructive focus:ring-destructive")}>
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
          {errors.assetId && (
            <p className="text-xs font-medium text-destructive">{errors.assetId}</p>
          )}
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="space-y-2">
            <Label className={cn(errors.date && "text-destructive")}>Date *</Label>
            <Input
              type="date"
              value={form.date}
              className={cn(errors.date && "border-destructive focus-visible:ring-destructive")}
              onChange={(e) => updateField("date", e.target.value)}
            />
            {errors.date && (
              <p className="text-xs font-medium text-destructive">{errors.date}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label className={cn(errors.start && "text-destructive")}>Start *</Label>
            <Input
              type="time"
              value={form.start}
              className={cn(errors.start && "border-destructive focus-visible:ring-destructive")}
              onChange={(e) => updateField("start", e.target.value)}
            />
            {errors.start && (
              <p className="text-xs font-medium text-destructive">{errors.start}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label className={cn(errors.end && "text-destructive")}>End *</Label>
            <Input
              type="time"
              value={form.end}
              className={cn(errors.end && "border-destructive focus-visible:ring-destructive")}
              onChange={(e) => updateField("end", e.target.value)}
            />
            {errors.end && (
              <p className="text-xs font-medium text-destructive">{errors.end}</p>
            )}
          </div>
        </div>
        <div className="space-y-2">
          <Label className={cn(errors.purpose && "text-destructive")}>Purpose *</Label>
          <Input
            value={form.purpose}
            className={cn(errors.purpose && "border-destructive focus-visible:ring-destructive")}
            onChange={(e) => updateField("purpose", e.target.value)}
          />
          {errors.purpose && (
            <p className="text-xs font-medium text-destructive">{errors.purpose}</p>
          )}
        </div>
        <div className="grid grid-cols-2 gap-2">
          <div className="space-y-2">
            <Label>Department</Label>
            <Select
              value={form.departmentId}
              onValueChange={(v) => updateField("departmentId", v)}
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
              onChange={(e) => updateField("attendees", Number(e.target.value))}
            />
          </div>
        </div>
        <div className="space-y-2">
          <Label>Notes</Label>
          <Textarea
            rows={2}
            value={form.notes}
            onChange={(e) => updateField("notes", e.target.value)}
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
                        type="button"
                        onClick={() => applySuggestion(s)}
                        className="block w-full rounded border border-border bg-card px-2 py-1.5 text-left text-xs hover:bg-accent cursor-pointer"
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
