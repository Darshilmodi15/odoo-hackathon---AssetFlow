export type Role = "admin" | "asset_manager" | "department_head" | "employee";

export interface User {
  id: string;
  name: string;
  email: string;
  role: Role;
  departmentId?: string;
  avatarUrl?: string;
  status: "active" | "inactive";
  joinedAt: string;
}

export interface Department {
  id: string;
  name: string;
  code: string;
  headId?: string;
  parentId?: string;
  status: "active" | "inactive";
}

export interface AssetCategory {
  id: string;
  name: string;
  description?: string;
  status: "active" | "inactive";
}

export type AssetStatus =
  | "available"
  | "allocated"
  | "reserved"
  | "under_maintenance"
  | "lost"
  | "retired"
  | "disposed";

export type AssetCondition = "excellent" | "good" | "fair" | "poor";

export interface Asset {
  id: string;
  tag: string;
  name: string;
  categoryId: string;
  serialNumber: string;
  departmentId?: string;
  assignedToId?: string;
  location: string;
  condition: AssetCondition;
  status: AssetStatus;
  shared: boolean;
  acquisitionDate: string;
  acquisitionCost: number;
  notes?: string;
  updatedAt: string;
}

export interface Allocation {
  id: string;
  assetId: string;
  employeeId: string;
  departmentId?: string;
  allocatedAt: string;
  expectedReturnAt?: string;
  returnedAt?: string;
  returnCondition?: AssetCondition;
  returnNotes?: string;
  status: "active" | "returned" | "overdue";
  notes?: string;
}

export interface TransferRequest {
  id: string;
  code: string;
  assetId: string;
  fromEmployeeId: string;
  toEmployeeId: string;
  reason: string;
  requestedById: string;
  requestedAt: string;
  approverId?: string;
  status: "requested" | "approved" | "rejected" | "completed";
}

export type BookingStatus = "upcoming" | "ongoing" | "completed" | "cancelled";

export interface Booking {
  id: string;
  assetId: string;
  bookedById: string;
  departmentId?: string;
  startAt: string;
  endAt: string;
  purpose: string;
  attendees?: number;
  notes?: string;
  status: BookingStatus;
}

export type MaintenancePriority = "low" | "medium" | "high" | "critical";
export type MaintenanceStatus =
  | "pending"
  | "approved"
  | "rejected"
  | "assigned"
  | "in_progress"
  | "resolved";

export interface MaintenanceRequest {
  id: string;
  code: string;
  assetId: string;
  requestedById: string;
  title: string;
  description: string;
  priority: MaintenancePriority;
  status: MaintenanceStatus;
  requestedAt: string;
  preferredDate?: string;
  technicianId?: string;
  estimatedCost?: number;
  actualCost?: number;
  resolutionNotes?: string;
  history: { at: string; status: MaintenanceStatus; note?: string; byId?: string }[];
}

export type AuditStatus = "draft" | "active" | "in_review" | "closed";
export type AuditFindingStatus = "pending" | "verified" | "missing" | "damaged";

export interface AuditFinding {
  id: string;
  assetId: string;
  status: AuditFindingStatus;
  notes?: string;
  auditorId?: string;
  at?: string;
}

export interface AuditCycle {
  id: string;
  title: string;
  scopeDepartmentId?: string;
  scopeLocation?: string;
  startDate: string;
  endDate: string;
  auditorIds: string[];
  status: AuditStatus;
  notes?: string;
  findings: AuditFinding[];
}

export type NotificationType =
  | "allocation"
  | "transfer"
  | "maintenance"
  | "booking"
  | "audit"
  | "overdue";

export interface Notification {
  id: string;
  userId: string;
  type: NotificationType;
  title: string;
  message: string;
  read: boolean;
  at: string;
  link?: string;
}

export interface ActivityLog {
  id: string;
  userId: string;
  action: string;
  module: string;
  entityId?: string;
  description: string;
  role: Role;
  at: string;
  status?: string;
}
