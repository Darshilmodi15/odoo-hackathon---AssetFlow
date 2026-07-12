// All services: use mock store in demo mode, ready to swap to API client.
import { store, findBookingConflict, suggestAlternativeBookings } from "@/mocks/store";
import { USE_MOCKS, mockDelay, apiClient, setToken } from "./apiClient";
import type {
  Asset,
  Allocation,
  TransferRequest,
  Booking,
  MaintenanceRequest,
  AuditCycle,
  Notification,
  ActivityLog,
  User,
  Department,
  AssetCategory,
  AssetStatus,
  MaintenanceStatus,
  Role,
  AuditFindingStatus,
} from "@/types";

// -------- API shape helpers --------
type ApiUser = Omit<User, "departmentId" | "avatarUrl" | "joinedAt"> & {
  department_id?: string | null;
  avatar_url?: string | null;
  joined_at?: string;
};

type ApiLoginResponse = {
  access_token: string;
  token_type: "bearer";
  user: ApiUser;
};

type ApiDepartment = {
  id: string;
  name: string;
  code: string;
  head_id?: string | null;
  parent_id?: string | null;
  status: Department["status"];
};

type ApiCategory = {
  id: string;
  name: string;
  description?: string | null;
  status: AssetCategory["status"];
};

type ApiAsset = {
  id: string;
  tag: string;
  name: string;
  category_id: string;
  serial_number: string;
  department_id?: string | null;
  assigned_to_id?: string | null;
  location: string;
  condition: Asset["condition"];
  status: Asset["status"];
  shared: boolean;
  acquisition_date: string;
  acquisition_cost: number | string;
  notes?: string | null;
  updated_at: string;
};

type ApiAllocation = {
  id: string;
  asset_id: string;
  employee_id: string;
  department_id?: string | null;
  allocated_at: string;
  expected_return_at?: string | null;
  returned_at?: string | null;
  return_condition?: Asset["condition"] | null;
  return_notes?: string | null;
  status: Allocation["status"];
  notes?: string | null;
};

type ApiTransfer = {
  id: string;
  code: string;
  asset_id: string;
  from_employee_id: string;
  to_employee_id: string;
  reason: string;
  requested_by_id: string;
  requested_at: string;
  approver_id?: string | null;
  status: TransferRequest["status"];
};

type ApiBooking = {
  id: string;
  asset_id: string;
  booked_by_id: string;
  department_id?: string | null;
  start_at: string;
  end_at: string;
  purpose: string;
  attendees?: number | null;
  notes?: string | null;
  status: Booking["status"];
};

function mapDepartment(d: ApiDepartment): Department {
  return {
    id: d.id,
    name: d.name,
    code: d.code,
    headId: d.head_id ?? undefined,
    parentId: d.parent_id ?? undefined,
    status: d.status,
  };
}

function mapCategory(c: ApiCategory): AssetCategory {
  return {
    id: c.id,
    name: c.name,
    description: c.description ?? undefined,
    status: c.status,
  };
}

function mapAsset(a: ApiAsset): Asset {
  return {
    id: a.id,
    tag: a.tag,
    name: a.name,
    categoryId: a.category_id,
    serialNumber: a.serial_number,
    departmentId: a.department_id ?? undefined,
    assignedToId: a.assigned_to_id ?? undefined,
    location: a.location,
    condition: a.condition,
    status: a.status,
    shared: a.shared,
    acquisitionDate: a.acquisition_date,
    acquisitionCost: Number(a.acquisition_cost),
    notes: a.notes ?? undefined,
    updatedAt: a.updated_at,
  };
}

function mapUser(user: ApiUser): User {
  return {
    id: user.id,
    name: user.name,
    email: user.email,
    role: user.role,
    departmentId: user.department_id ?? undefined,
    avatarUrl: user.avatar_url ?? undefined,
    status: user.status,
    joinedAt: user.joined_at ?? new Date().toISOString(),
  };
}

function mapAllocation(a: ApiAllocation): Allocation {
  return {
    id: a.id,
    assetId: a.asset_id,
    employeeId: a.employee_id,
    departmentId: a.department_id ?? undefined,
    allocatedAt: a.allocated_at,
    expectedReturnAt: a.expected_return_at ?? undefined,
    returnedAt: a.returned_at ?? undefined,
    returnCondition: a.return_condition ?? undefined,
    returnNotes: a.return_notes ?? undefined,
    status: a.status,
    notes: a.notes ?? undefined,
  };
}

function mapTransfer(t: ApiTransfer): TransferRequest {
  return {
    id: t.id,
    code: t.code,
    assetId: t.asset_id,
    fromEmployeeId: t.from_employee_id,
    toEmployeeId: t.to_employee_id,
    reason: t.reason,
    requestedById: t.requested_by_id,
    requestedAt: t.requested_at,
    approverId: t.approver_id ?? undefined,
    status: t.status,
  };
}

function mapBooking(b: ApiBooking): Booking {
  return {
    id: b.id,
    assetId: b.asset_id,
    bookedById: b.booked_by_id,
    departmentId: b.department_id ?? undefined,
    startAt: b.start_at,
    endAt: b.end_at,
    purpose: b.purpose,
    attendees: b.attendees ?? undefined,
    notes: b.notes ?? undefined,
    status: b.status,
  };
}

// -------- AUTH --------

export const authService = {
  async login(email: string, password: string): Promise<User> {
    if (USE_MOCKS) {
      await mockDelay();
      const user = store.employees.find((e) => e.email.toLowerCase() === email.toLowerCase());
      if (!user) throw new Error("Invalid credentials");
      return user;
    }
    const res = await apiClient.post<ApiLoginResponse>("/auth/login", { email, password });
    setToken(res.access_token);
    return mapUser(res.user);
  },
  async signup(input: {
    name: string;
    email: string;
    password: string;
    departmentId?: string;
  }): Promise<User> {
    if (USE_MOCKS) {
      await mockDelay();
      if (store.employees.some((e) => e.email.toLowerCase() === input.email.toLowerCase()))
        throw new Error("Email already registered");
      const user: User = {
        id: store.nextId("e"),
        name: input.name,
        email: input.email,
        role: "employee",
        departmentId: input.departmentId,
        status: "active",
        joinedAt: new Date().toISOString(),
      };
      store.employees.push(user);
      store.log({
        userId: user.id,
        action: "signup",
        module: "Auth",
        description: `${user.name} created an Employee account`,
        role: "employee",
      });
      store.emit();
      return user;
    }
    const user = await apiClient.post<ApiUser>("/auth/signup", {
      name: input.name,
      email: input.email,
      password: input.password,
      department_id: input.departmentId,
    });
    return mapUser(user);
  },
  async me(): Promise<User | null> {
    if (USE_MOCKS) return null;
    try {
      return mapUser(await apiClient.get<ApiUser>("/auth/me"));
    } catch {
      return null;
    }
  },
  async forgotPassword(email: string): Promise<void> {
    if (USE_MOCKS) {
      await mockDelay();
      return;
    }
    await apiClient.post("/auth/forgot-password", { email });
  },
  async logout(): Promise<void> {
    if (!USE_MOCKS) {
      try {
        await apiClient.post("/auth/logout");
      } catch {
        // best-effort
      }
    }
    setToken(null);
  },
};

// -------- DEPARTMENTS --------
export const departmentService = {
  async list(): Promise<Department[]> {
    if (USE_MOCKS) {
      await mockDelay(50);
      return store.departments;
    }
    return (await apiClient.get<ApiDepartment[]>("/departments")).map(mapDepartment);
  },
  async create(d: Omit<Department, "id">): Promise<Department> {
    if (!USE_MOCKS) {
      return mapDepartment(
        await apiClient.post<ApiDepartment>("/departments", {
          name: d.name,
          code: d.code,
          head_id: d.headId,
          parent_id: d.parentId,
          status: d.status,
        }),
      );
    }
    const dep = { ...d, id: store.nextId("d") };
    store.departments.push(dep);
    store.emit();
    return dep;
  },
  async update(id: string, patch: Partial<Department>) {
    if (!USE_MOCKS) {
      return mapDepartment(
        await apiClient.patch<ApiDepartment>(`/departments/${id}`, {
          name: patch.name,
          code: patch.code,
          head_id: patch.headId,
          parent_id: patch.parentId,
          status: patch.status,
        }),
      );
    }
    const i = store.departments.findIndex((d) => d.id === id);
    if (i >= 0) store.departments[i] = { ...store.departments[i], ...patch };
    store.emit();
    return store.departments[i];
  },
};

// -------- CATEGORIES --------
export const categoryService = {
  async list(): Promise<AssetCategory[]> {
    if (USE_MOCKS) {
      await mockDelay(50);
      return store.categories;
    }
    return (await apiClient.get<ApiCategory[]>("/categories")).map(mapCategory);
  },
  async create(c: Omit<AssetCategory, "id">) {
    if (!USE_MOCKS) {
      return mapCategory(
        await apiClient.post<ApiCategory>("/categories", {
          name: c.name,
          description: c.description,
          status: c.status,
        }),
      );
    }
    const cat = { ...c, id: store.nextId("c") };
    store.categories.push(cat);
    store.emit();
    return cat;
  },
  async update(id: string, patch: Partial<AssetCategory>) {
    if (!USE_MOCKS) {
      return mapCategory(
        await apiClient.patch<ApiCategory>(`/categories/${id}`, {
          name: patch.name,
          description: patch.description,
          status: patch.status,
        }),
      );
    }
    const i = store.categories.findIndex((c) => c.id === id);
    if (i >= 0) store.categories[i] = { ...store.categories[i], ...patch };
    store.emit();
    return store.categories[i];
  },
};

// -------- EMPLOYEES --------
export const employeeService = {
  async list(): Promise<User[]> {
    if (USE_MOCKS) {
      await mockDelay(50);
      return store.employees;
    }
    return (await apiClient.get<ApiUser[]>("/users")).map(mapUser);
  },
  async updateRole(id: string, role: Role, actorId: string) {
    if (!USE_MOCKS) return mapUser(await apiClient.patch<ApiUser>(`/users/${id}/role`, { role }));
    const emp = store.employees.find((e) => e.id === id);
    if (!emp) throw new Error("Not found");
    const prev = emp.role;
    emp.role = role;
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "role_change",
      module: "Employees",
      entityId: id,
      description: `${actor?.name || "Admin"} changed ${emp.name}'s role from ${prev} to ${role}`,
      role: "admin",
    });
    store.emit();
    return emp;
  },
  async setStatus(id: string, status: "active" | "inactive") {
    if (!USE_MOCKS) {
      return mapUser(await apiClient.patch<ApiUser>(`/users/${id}/status`, { status }));
    }
    const emp = store.employees.find((e) => e.id === id);
    if (!emp) throw new Error("Not found");
    emp.status = status;
    store.emit();
    return emp;
  },
};

// -------- ASSETS --------
export const assetService = {
  async list(): Promise<Asset[]> {
    if (USE_MOCKS) {
      await mockDelay(50);
      return store.assets;
    }
    return (await apiClient.get<ApiAsset[]>("/assets")).map(mapAsset);
  },
  async get(id: string): Promise<Asset | undefined> {
    if (USE_MOCKS) return store.assets.find((a) => a.id === id);
    return mapAsset(await apiClient.get<ApiAsset>(`/assets/${id}`));
  },
  async create(
    input: Omit<Asset, "id" | "tag" | "updatedAt" | "status"> & { status?: AssetStatus },
    actorId: string,
  ) {
    if (!USE_MOCKS) {
      return mapAsset(
        await apiClient.post<ApiAsset>("/assets", {
          name: input.name,
          category_id: input.categoryId,
          serial_number: input.serialNumber,
          department_id: input.departmentId,
          location: input.location,
          condition: input.condition,
          shared: input.shared,
          acquisition_date: input.acquisitionDate,
          acquisition_cost: input.acquisitionCost,
          notes: input.notes,
          status: input.status,
        }),
      );
    }
    const asset: Asset = {
      ...input,
      id: store.nextId("a"),
      tag: store.nextTag(),
      status: input.status || "available",
      updatedAt: new Date().toISOString(),
    };
    store.assets.push(asset);
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "registered_asset",
      module: "Assets",
      entityId: asset.id,
      description: `${actor?.name} registered ${asset.name} (${asset.tag})`,
      role: actor?.role || "asset_manager",
    });
    store.emit();
    return asset;
  },
  async update(id: string, patch: Partial<Asset>) {
    if (!USE_MOCKS) {
      return mapAsset(
        await apiClient.patch<ApiAsset>(`/assets/${id}`, {
          name: patch.name,
          category_id: patch.categoryId,
          serial_number: patch.serialNumber,
          department_id: patch.departmentId,
          assigned_to_id: patch.assignedToId,
          location: patch.location,
          condition: patch.condition,
          status: patch.status,
          shared: patch.shared,
          acquisition_date: patch.acquisitionDate,
          acquisition_cost: patch.acquisitionCost,
          notes: patch.notes,
        }),
      );
    }
    const i = store.assets.findIndex((a) => a.id === id);
    if (i < 0) throw new Error("Not found");
    store.assets[i] = { ...store.assets[i], ...patch, updatedAt: new Date().toISOString() };
    store.emit();
    return store.assets[i];
  },
};

// -------- ALLOCATIONS --------
export const allocationService = {
  async list(): Promise<Allocation[]> {
    if (USE_MOCKS) return store.allocations;
    return (await apiClient.get<ApiAllocation[]>("/allocations")).map(mapAllocation);
  },
  async create(
    input: {
      assetId: string;
      employeeId: string;
      departmentId?: string;
      expectedReturnAt?: string;
      notes?: string;
    },
    actorId: string,
  ) {
    if (!USE_MOCKS) {
      return mapAllocation(
        await apiClient.post<ApiAllocation>("/allocations", {
          asset_id: input.assetId,
          employee_id: input.employeeId,
          department_id: input.departmentId,
          expected_return_at: input.expectedReturnAt,
          notes: input.notes,
        }),
      );
    }
    const asset = store.assets.find((a) => a.id === input.assetId);
    if (!asset) throw new Error("Asset not found");
    if (asset.status !== "available") {
      const holder = asset.assignedToId
        ? store.employees.find((e) => e.id === asset.assignedToId)
        : null;
      throw Object.assign(
        new Error(
          holder
            ? `This asset is currently held by ${holder.name}.`
            : `Asset is currently ${asset.status.replace("_", " ")} and cannot be allocated.`,
        ),
        { code: "ALLOCATION_CONFLICT", currentHolder: holder, asset },
      );
    }
    const alloc: Allocation = {
      id: store.nextId("al"),
      assetId: input.assetId,
      employeeId: input.employeeId,
      departmentId: input.departmentId,
      allocatedAt: new Date().toISOString(),
      expectedReturnAt: input.expectedReturnAt,
      status: "active",
      notes: input.notes,
    };
    store.allocations.unshift(alloc);
    store.setAssetStatus(input.assetId, "allocated", input.employeeId);
    const emp = store.employees.find((e) => e.id === input.employeeId);
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "allocated_asset",
      module: "Allocations",
      entityId: alloc.id,
      description: `${actor?.name} allocated ${asset.name} (${asset.tag}) to ${emp?.name}`,
      role: actor?.role || "asset_manager",
    });
    store.notify({
      userId: input.employeeId,
      type: "allocation",
      title: "Asset assigned",
      message: `${asset.name} (${asset.tag}) has been allocated to you`,
      link: `/assets/${asset.id}`,
    });
    store.emit();
    return alloc;
  },
  async return(
    id: string,
    input: { returnCondition: Asset["condition"]; returnNotes?: string },
    actorId: string,
  ) {
    if (!USE_MOCKS) {
      return mapAllocation(
        await apiClient.post<ApiAllocation>(`/allocations/${id}/return`, {
          condition_at_return: input.returnCondition,
          condition_notes: input.returnNotes,
        }),
      );
    }
    const a = store.allocations.find((x) => x.id === id);
    if (!a) throw new Error("Not found");
    a.returnedAt = new Date().toISOString();
    a.returnCondition = input.returnCondition;
    a.returnNotes = input.returnNotes;
    a.status = "returned";
    const asset = store.assets.find((x) => x.id === a.assetId);
    if (asset && !["lost", "retired", "disposed"].includes(asset.status)) {
      store.setAssetStatus(a.assetId, "available", null);
      if (asset) asset.condition = input.returnCondition;
    }
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "returned_asset",
      module: "Allocations",
      entityId: a.id,
      description: `${actor?.name} returned ${asset?.name}`,
      role: actor?.role || "employee",
      status: "returned",
    });
    store.emit();
    return a;
  },
};

// -------- TRANSFERS --------
export const transferService = {
  async list(): Promise<TransferRequest[]> {
    if (USE_MOCKS) return store.transfers;
    return (await apiClient.get<ApiTransfer[]>("/transfers")).map(mapTransfer);
  },
  async create(
    input: { assetId: string; toEmployeeId: string; reason: string },
    requestedById: string,
  ) {
    if (!USE_MOCKS) {
      return mapTransfer(
        await apiClient.post<ApiTransfer>("/transfers", {
          asset_id: input.assetId,
          to_employee_id: input.toEmployeeId,
          reason: input.reason,
        }),
      );
    }
    const asset = store.assets.find((a) => a.id === input.assetId);
    if (!asset) throw new Error("Asset not found");
    const fromEmployeeId = asset.assignedToId || "";
    const code = `TR-${String(store.transfers.length + 25).padStart(4, "0")}`;
    const req: TransferRequest = {
      id: store.nextId("t"),
      code,
      assetId: input.assetId,
      fromEmployeeId,
      toEmployeeId: input.toEmployeeId,
      reason: input.reason,
      requestedById,
      requestedAt: new Date().toISOString(),
      status: "requested",
    };
    store.transfers.unshift(req);
    const actor = store.employees.find((e) => e.id === requestedById);
    store.log({
      userId: requestedById,
      action: "requested_transfer",
      module: "Transfers",
      entityId: req.id,
      description: `${actor?.name} requested transfer ${code}`,
      role: actor?.role || "employee",
    });
    store.emit();
    return req;
  },
  async setStatus(id: string, status: TransferRequest["status"], approverId: string) {
    if (!USE_MOCKS)
      return mapTransfer(await apiClient.patch<ApiTransfer>(`/transfers/${id}/status`, { status }));
    const t = store.transfers.find((x) => x.id === id);
    if (!t) throw new Error("Not found");
    t.status = status;
    t.approverId = approverId;
    const actor = store.employees.find((e) => e.id === approverId);
    if (status === "approved") {
      const asset = store.assets.find((a) => a.id === t.assetId);
      if (asset) {
        asset.assignedToId = t.toEmployeeId;
        asset.updatedAt = new Date().toISOString();
      }
      store.notify({
        userId: t.toEmployeeId,
        type: "transfer",
        title: "Transfer approved",
        message: `Transfer ${t.code} was approved`,
      });
    } else if (status === "rejected") {
      store.notify({
        userId: t.requestedById,
        type: "transfer",
        title: "Transfer rejected",
        message: `Transfer ${t.code} was rejected`,
      });
    }
    store.log({
      userId: approverId,
      action: `${status}_transfer`,
      module: "Transfers",
      entityId: t.id,
      description: `${actor?.name} ${status} transfer ${t.code}`,
      role: actor?.role || "asset_manager",
      status,
    });
    store.emit();
    return t;
  },
};

// -------- BOOKINGS --------
export const bookingService = {
  async list(): Promise<Booking[]> {
    if (USE_MOCKS) return store.bookings;
    return (await apiClient.get<ApiBooking[]>("/bookings")).map(mapBooking);
  },
  async create(input: Omit<Booking, "id" | "status">, actorId: string) {
    if (!USE_MOCKS) {
      return mapBooking(
        await apiClient.post<ApiBooking>("/bookings", {
          asset_id: input.assetId,
          department_id: input.departmentId,
          start_at: input.startAt,
          end_at: input.endAt,
          purpose: input.purpose,
          attendees: input.attendees,
          notes: input.notes,
        }),
      );
    }
    const conflict = findBookingConflict(input.assetId, input.startAt, input.endAt);
    if (conflict) {
      const asset = store.assets.find((a) => a.id === input.assetId);
      const suggestions = suggestAlternativeBookings(input.assetId, input.startAt, input.endAt);
      throw Object.assign(
        new Error(`${asset?.name || "Resource"} is already booked during this time.`),
        {
          code: "BOOKING_OVERLAP",
          conflict,
          suggestions,
        },
      );
    }
    const b: Booking = { ...input, id: store.nextId("b"), status: "upcoming" };
    store.bookings.unshift(b);
    const asset = store.assets.find((a) => a.id === input.assetId);
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "booked_resource",
      module: "Bookings",
      entityId: b.id,
      description: `${actor?.name} booked ${asset?.name} for ${input.purpose}`,
      role: actor?.role || "employee",
    });
    store.notify({
      userId: actorId,
      type: "booking",
      title: "Booking confirmed",
      message: `${asset?.name} booked successfully`,
    });
    store.emit();
    return b;
  },
  async cancel(id: string, actorId: string) {
    if (!USE_MOCKS) return mapBooking(await apiClient.del<ApiBooking>(`/bookings/${id}`));
    const b = store.bookings.find((x) => x.id === id);
    if (!b) throw new Error("Not found");
    b.status = "cancelled";
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "cancelled_booking",
      module: "Bookings",
      entityId: b.id,
      description: `${actor?.name} cancelled a booking`,
      role: actor?.role || "employee",
      status: "cancelled",
    });
    store.emit();
    return b;
  },
  async reschedule(id: string, input: { startAt: string; endAt: string }, actorId: string) {
    const b = store.bookings.find((x) => x.id === id);
    if (!b) throw new Error("Not found");
    const conflict = findBookingConflict(b.assetId, input.startAt, input.endAt, id);
    if (conflict) {
      const suggestions = suggestAlternativeBookings(b.assetId, input.startAt, input.endAt);
      throw Object.assign(new Error("Selected time overlaps another booking."), {
        code: "BOOKING_OVERLAP",
        conflict,
        suggestions,
      });
    }
    b.startAt = input.startAt;
    b.endAt = input.endAt;
    b.status = "upcoming";
    const actor = store.employees.find((e) => e.id === actorId);
    const asset = store.assets.find((a) => a.id === b.assetId);
    store.log({
      userId: actorId,
      action: "rescheduled_booking",
      module: "Bookings",
      entityId: b.id,
      description: `${actor?.name} rescheduled ${asset?.name || "a resource"} booking`,
      role: actor?.role || "employee",
      status: "upcoming",
    });
    store.notify({
      userId: b.bookedById,
      type: "booking",
      title: "Booking rescheduled",
      message: `${asset?.name || "Resource"} booking was moved to ${new Date(input.startAt).toLocaleString()}`,
    });
    store.emit();
    return b;
  },
  suggestAlternatives: suggestAlternativeBookings,
};

// -------- MAINTENANCE --------
export const maintenanceService = {
  async list(): Promise<MaintenanceRequest[]> {
    if (USE_MOCKS) return store.maintenance;
    return apiClient.get("/maintenance");
  },
  async create(
    input: {
      assetId: string;
      title: string;
      description: string;
      priority: MaintenanceRequest["priority"];
      preferredDate?: string;
    },
    actorId: string,
  ) {
    const code = `MR-${String(store.maintenance.length + 38).padStart(4, "0")}`;
    const req: MaintenanceRequest = {
      id: store.nextId("m"),
      code,
      assetId: input.assetId,
      requestedById: actorId,
      title: input.title,
      description: input.description,
      priority: input.priority,
      status: "pending",
      requestedAt: new Date().toISOString(),
      preferredDate: input.preferredDate,
      history: [{ at: new Date().toISOString(), status: "pending", byId: actorId }],
    };
    store.maintenance.unshift(req);
    const actor = store.employees.find((e) => e.id === actorId);
    const asset = store.assets.find((a) => a.id === input.assetId);
    store.log({
      userId: actorId,
      action: "raised_maintenance",
      module: "Maintenance",
      entityId: req.id,
      description: `${actor?.name} raised maintenance ${code} for ${asset?.name}`,
      role: actor?.role || "employee",
    });
    store.emit();
    return req;
  },
  async setStatus(
    id: string,
    status: MaintenanceStatus,
    actorId: string,
    extra?: {
      note?: string;
      technicianId?: string;
      estimatedCost?: number;
      actualCost?: number;
      resolutionNotes?: string;
    },
  ) {
    const req = store.maintenance.find((x) => x.id === id);
    if (!req) throw new Error("Not found");
    const prev = req.status;
    req.status = status;
    if (extra?.technicianId) req.technicianId = extra.technicianId;
    if (extra?.estimatedCost !== undefined) req.estimatedCost = extra.estimatedCost;
    if (extra?.actualCost !== undefined) req.actualCost = extra.actualCost;
    if (extra?.resolutionNotes) req.resolutionNotes = extra.resolutionNotes;
    req.history.push({ at: new Date().toISOString(), status, byId: actorId, note: extra?.note });

    const asset = store.assets.find((a) => a.id === req.assetId);
    if (asset) {
      if (status === "approved") store.setAssetStatus(asset.id, "under_maintenance");
      else if (status === "resolved" && !["lost", "retired", "disposed"].includes(asset.status)) {
        store.setAssetStatus(asset.id, asset.assignedToId ? "allocated" : "available");
      }
    }

    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: `${status}_maintenance`,
      module: "Maintenance",
      entityId: req.id,
      description: `${actor?.name} moved ${req.code} from ${prev} to ${status}`,
      role: actor?.role || "asset_manager",
      status,
    });
    if (status === "approved")
      store.notify({
        userId: req.requestedById,
        type: "maintenance",
        title: "Maintenance approved",
        message: `${req.code} has been approved`,
      });
    if (status === "rejected")
      store.notify({
        userId: req.requestedById,
        type: "maintenance",
        title: "Maintenance rejected",
        message: `${req.code} was rejected${extra?.note ? ": " + extra.note : ""}`,
      });
    store.emit();
    return req;
  },
};

// -------- AUDITS --------
export const auditService = {
  async list(): Promise<AuditCycle[]> {
    if (USE_MOCKS) return store.audits;
    return apiClient.get("/audits");
  },
  async create(
    input: Omit<AuditCycle, "id" | "findings" | "status"> & { assetIds: string[] },
    actorId: string,
  ) {
    const cycle: AuditCycle = {
      id: store.nextId("au"),
      title: input.title,
      scopeDepartmentId: input.scopeDepartmentId,
      scopeLocation: input.scopeLocation,
      startDate: input.startDate,
      endDate: input.endDate,
      auditorIds: input.auditorIds,
      status: "active",
      notes: input.notes,
      findings: input.assetIds.map((aid) => ({
        id: store.nextId("af"),
        assetId: aid,
        status: "pending" as AuditFindingStatus,
      })),
    };
    store.audits.unshift(cycle);
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "created_audit",
      module: "Audits",
      entityId: cycle.id,
      description: `${actor?.name} created audit cycle ${cycle.title}`,
      role: "admin",
    });
    store.emit();
    return cycle;
  },
  async updateFinding(
    auditId: string,
    findingId: string,
    patch: Partial<{ status: AuditFindingStatus; notes: string }>,
    actorId: string,
  ) {
    const a = store.audits.find((x) => x.id === auditId);
    if (!a) throw new Error("Not found");
    const f = a.findings.find((x) => x.id === findingId);
    if (!f) throw new Error("Finding not found");
    Object.assign(f, patch, { auditorId: actorId, at: new Date().toISOString() });
    if (patch.status === "damaged" || patch.status === "missing") {
      const asset = store.assets.find((as) => as.id === f.assetId);
      store.notify({
        userId: actorId,
        type: "audit",
        title: "Audit discrepancy flagged",
        message: `${asset?.name || "Asset"} marked as ${patch.status}`,
      });
    }
    store.emit();
    return f;
  },
  async close(id: string, actorId: string) {
    const a = store.audits.find((x) => x.id === id);
    if (!a) throw new Error("Not found");
    a.status = "closed";
    a.findings
      .filter((f) => f.status === "missing")
      .forEach((f) => {
        store.setAssetStatus(f.assetId, "lost");
      });
    const actor = store.employees.find((e) => e.id === actorId);
    store.log({
      userId: actorId,
      action: "closed_audit",
      module: "Audits",
      entityId: a.id,
      description: `Audit ${a.title} was closed by ${actor?.name}`,
      role: "admin",
      status: "closed",
    });
    store.emit();
    return a;
  },
};

// -------- NOTIFICATIONS --------
export const notificationService = {
  async list(userId?: string): Promise<Notification[]> {
    if (USE_MOCKS)
      return userId ? store.notifications.filter((n) => n.userId === userId) : store.notifications;
    return apiClient.get("/notifications");
  },
  async markRead(id: string) {
    const n = store.notifications.find((x) => x.id === id);
    if (n) n.read = true;
    store.emit();
  },
  async markAllRead(userId: string) {
    store.notifications.forEach((n) => {
      if (n.userId === userId) n.read = true;
    });
    store.emit();
  },
};

// -------- ACTIVITY --------
export const activityService = {
  async list(): Promise<ActivityLog[]> {
    if (USE_MOCKS) return store.activityLogs;
    return apiClient.get("/activity-logs");
  },
};

// -------- REPORTS --------
export const reportService = {
  async dashboard() {
    if (USE_MOCKS) {
      const byStatus: Record<string, number> = {};
      store.assets.forEach((a) => {
        byStatus[a.status] = (byStatus[a.status] || 0) + 1;
      });
      return { byStatus };
    }
    return apiClient.get("/reports/dashboard");
  },
};

// -------- INQUIRIES --------
export const inquiryService = {
  async submit(payload: { name: string; email: string; company?: string; message: string }) {
    return apiClient.post("/inquiries", payload);
  },
};
