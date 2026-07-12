// Central in-memory mock store. Simulates FastAPI backend for demo mode.
import * as seed from "./data";
import type {
  Asset, Allocation, TransferRequest, Booking, MaintenanceRequest,
  AuditCycle, Notification, ActivityLog, User, Department, AssetCategory,
  AssetStatus, MaintenanceStatus, AuditFinding,
} from "@/types";

type Listener = () => void;

class Store {
  departments: Department[] = structuredClone(seed.departments);
  categories: AssetCategory[] = structuredClone(seed.categories);
  employees: User[] = structuredClone(seed.employees);
  assets: Asset[] = structuredClone(seed.assets);
  allocations: Allocation[] = structuredClone(seed.allocations);
  transfers: TransferRequest[] = structuredClone(seed.transfers);
  bookings: Booking[] = structuredClone(seed.bookings);
  maintenance: MaintenanceRequest[] = structuredClone(seed.maintenance);
  audits: AuditCycle[] = structuredClone(seed.audits);
  notifications: Notification[] = structuredClone(seed.notifications);
  activityLogs: ActivityLog[] = structuredClone(seed.activityLogs);

  private listeners = new Set<Listener>();
  subscribe(l: Listener) { this.listeners.add(l); return () => { this.listeners.delete(l); }; }
  emit() { this.listeners.forEach(l => l()); }

  nextId(prefix: string) { return `${prefix}${Date.now().toString(36)}${Math.floor(Math.random()*1000)}`; }
  nextTag() {
    const nums = this.assets.map(a => parseInt(a.tag.replace("AF-",""))).filter(n=>!isNaN(n));
    const max = nums.length ? Math.max(...nums) : 0;
    return `AF-${String(max+1).padStart(4,"0")}`;
  }

  log(entry: Omit<ActivityLog,"id"|"at">) {
    this.activityLogs.unshift({ ...entry, id: this.nextId("l"), at: new Date().toISOString() });
  }
  notify(n: Omit<Notification,"id"|"at"|"read">) {
    this.notifications.unshift({ ...n, id: this.nextId("n"), at: new Date().toISOString(), read: false });
  }

  setAssetStatus(assetId: string, status: AssetStatus, assignedToId?: string | null) {
    const a = this.assets.find(x => x.id === assetId); if (!a) return;
    a.status = status;
    if (assignedToId !== undefined) a.assignedToId = assignedToId ?? undefined;
    a.updatedAt = new Date().toISOString();
  }
}

export const store = new Store();

// Utility: overlap check for bookings
export function bookingsOverlap(a: {startAt: string; endAt: string}, b: {startAt: string; endAt: string}) {
  return new Date(a.startAt) < new Date(b.endAt) && new Date(b.startAt) < new Date(a.endAt);
}

export function findBookingConflict(assetId: string, startAt: string, endAt: string, excludeId?: string) {
  return store.bookings.find(b =>
    b.assetId === assetId &&
    b.status !== "cancelled" &&
    b.id !== excludeId &&
    bookingsOverlap({startAt, endAt}, b)
  );
}

export function suggestAlternativeBookings(assetId: string, startAt: string, endAt: string) {
  const duration = new Date(endAt).getTime() - new Date(startAt).getTime();
  const suggestions: { assetId: string; startAt: string; endAt: string; reason: string }[] = [];
  // same asset later same day
  const conflict = findBookingConflict(assetId, startAt, endAt);
  if (conflict) {
    const laterStart = new Date(conflict.endAt);
    suggestions.push({ assetId, startAt: laterStart.toISOString(), endAt: new Date(laterStart.getTime()+duration).toISOString(), reason: "Same resource, later time" });
  }
  // another bookable asset in same category
  const original = store.assets.find(a => a.id === assetId);
  if (original) {
    const alt = store.assets.find(a => a.id !== assetId && a.shared && a.categoryId === original.categoryId && !findBookingConflict(a.id, startAt, endAt));
    if (alt) suggestions.push({ assetId: alt.id, startAt, endAt, reason: `Alternative: ${alt.name}` });
  }
  return suggestions;
}

export type { AuditFinding, MaintenanceStatus };
