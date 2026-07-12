import { createFileRoute } from "@tanstack/react-router";
import { useRoleGuard } from "@/hooks/useRoleGuard";
import { useEffect, useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { departmentService, categoryService, employeeService } from "@/services";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogTrigger,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import { Plus, Search, ShieldAlert } from "lucide-react";
import { toast } from "sonner";
import { format } from "date-fns";
import { roleLabel } from "@/context/AuthContext";
import type { Role } from "@/types";

export const Route = createFileRoute("/_app/organization")({ component: OrganizationPage });

function OrganizationPage() {
  const { user } = useAuth();
  const { permitted } = useRoleGuard(["admin"]);
  if (!permitted) return null;
  return (
    <Tabs defaultValue="departments">
      <TabsList>
        <TabsTrigger value="departments">Departments</TabsTrigger>
        <TabsTrigger value="categories">Asset Categories</TabsTrigger>
        <TabsTrigger value="employees">Employee Directory</TabsTrigger>
      </TabsList>
      <TabsContent value="departments" className="mt-4">
        <DepartmentsTab />
      </TabsContent>
      <TabsContent value="categories" className="mt-4">
        <CategoriesTab />
      </TabsContent>
      <TabsContent value="employees" className="mt-4">
        <EmployeesTab actorId={user!.id} />
      </TabsContent>
    </Tabs>
  );
}

function DepartmentsTab() {
  const departments = useStore(() => store.departments);
  const employees = useStore(() => store.employees);
  const assets = useStore(() => store.assets);
  const [q, setQ] = useState("");
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", code: "", headId: "" });

  const filtered = departments.filter((d) =>
    (d.name + d.code).toLowerCase().includes(q.toLowerCase()),
  );

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2 flex-wrap">
        <CardTitle className="text-base">Departments</CardTitle>
        <div className="flex items-center gap-2">
          <div className="relative">
            <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="h-9 w-48 pl-8"
            />
          </div>
          <Dialog open={open} onOpenChange={setOpen}>
            <DialogTrigger asChild>
              <Button size="sm">
                <Plus className="mr-1 h-4 w-4" />
                New
              </Button>
            </DialogTrigger>
            <DialogContent>
              <DialogHeader>
                <DialogTitle>Create Department</DialogTitle>
              </DialogHeader>
              <div className="space-y-3">
                <div>
                  <Label>Name</Label>
                  <Input
                    value={form.name}
                    onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
                  />
                </div>
                <div>
                  <Label>Code</Label>
                  <Input
                    value={form.code}
                    onChange={(e) => setForm((s) => ({ ...s, code: e.target.value.toUpperCase() }))}
                  />
                </div>
                <div>
                  <Label>Department Head</Label>
                  <Select
                    value={form.headId}
                    onValueChange={(v) => setForm((s) => ({ ...s, headId: v }))}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select head" />
                    </SelectTrigger>
                    <SelectContent>
                      {employees.map((e) => (
                        <SelectItem key={e.id} value={e.id}>
                          {e.name}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <DialogFooter>
                <Button variant="outline" onClick={() => setOpen(false)}>
                  Cancel
                </Button>
                <Button
                  onClick={async () => {
                    if (!form.name || !form.code) {
                      toast.error("Name and code required");
                      return;
                    }
                    await departmentService.create({ ...form, status: "active" });
                    toast.success("Department created");
                    setOpen(false);
                    setForm({ name: "", code: "", headId: "" });
                  }}
                >
                  Create
                </Button>
              </DialogFooter>
            </DialogContent>
          </Dialog>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Code</TableHead>
                <TableHead>Head</TableHead>
                <TableHead>Employees</TableHead>
                <TableHead>Assets</TableHead>
                <TableHead>Status</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((d) => {
                const head = employees.find((e) => e.id === d.headId);
                return (
                  <TableRow key={d.id}>
                    <TableCell className="font-medium">{d.name}</TableCell>
                    <TableCell>
                      <span className="rounded bg-muted px-2 py-0.5 font-mono text-xs">
                        {d.code}
                      </span>
                    </TableCell>
                    <TableCell>{head?.name || "—"}</TableCell>
                    <TableCell>{employees.filter((e) => e.departmentId === d.id).length}</TableCell>
                    <TableCell>{assets.filter((a) => a.departmentId === d.id).length}</TableCell>
                    <TableCell>
                      <StatusBadge status={d.status} />
                    </TableCell>
                    <TableCell className="text-right">
                      <AlertDialog>
                        <AlertDialogTrigger asChild>
                          <Button size="sm" variant="ghost">
                            {d.status === "active" ? "Deactivate" : "Activate"}
                          </Button>
                        </AlertDialogTrigger>
                        <AlertDialogContent>
                          <AlertDialogHeader>
                            <AlertDialogTitle>Confirm</AlertDialogTitle>
                            <AlertDialogDescription>
                              Toggle status for {d.name}?
                            </AlertDialogDescription>
                          </AlertDialogHeader>
                          <AlertDialogFooter>
                            <AlertDialogCancel>Cancel</AlertDialogCancel>
                            <AlertDialogAction
                              onClick={() =>
                                departmentService.update(d.id, {
                                  status: d.status === "active" ? "inactive" : "active",
                                })
                              }
                            >
                              Confirm
                            </AlertDialogAction>
                          </AlertDialogFooter>
                        </AlertDialogContent>
                      </AlertDialog>
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
        {filtered.length === 0 && <EmptyState title="No departments" />}
      </CardContent>
    </Card>
  );
}

function CategoriesTab() {
  const categories = useStore(() => store.categories);
  const assets = useStore(() => store.assets);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState({ name: "", description: "" });

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle className="text-base">Asset Categories</CardTitle>
        <Dialog open={open} onOpenChange={setOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="mr-1 h-4 w-4" />
              New Category
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Category</DialogTitle>
            </DialogHeader>
            <div className="space-y-3">
              <div>
                <Label>Name</Label>
                <Input
                  value={form.name}
                  onChange={(e) => setForm((s) => ({ ...s, name: e.target.value }))}
                />
              </div>
              <div>
                <Label>Description</Label>
                <Input
                  value={form.description}
                  onChange={(e) => setForm((s) => ({ ...s, description: e.target.value }))}
                />
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setOpen(false)}>
                Cancel
              </Button>
              <Button
                onClick={async () => {
                  if (!form.name) {
                    toast.error("Name required");
                    return;
                  }
                  await categoryService.create({ ...form, status: "active" });
                  toast.success("Category created");
                  setOpen(false);
                  setForm({ name: "", description: "" });
                }}
              >
                Create
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardHeader>
      <CardContent>
        <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {categories.map((c) => (
            <Card key={c.id}>
              <CardContent className="p-4">
                <div className="flex items-start justify-between">
                  <div className="min-w-0">
                    <div className="font-medium">{c.name}</div>
                    <div className="line-clamp-2 text-xs text-muted-foreground">
                      {c.description}
                    </div>
                  </div>
                  <StatusBadge status={c.status} />
                </div>
                <div className="mt-3 text-xs text-muted-foreground">
                  {assets.filter((a) => a.categoryId === c.id).length} assets
                </div>
                <div className="mt-3 flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() =>
                      categoryService.update(c.id, {
                        status: c.status === "active" ? "inactive" : "active",
                      })
                    }
                  >
                    {c.status === "active" ? "Deactivate" : "Activate"}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}

function EmployeesTab({ actorId }: { actorId: string }) {
  const employees = useStore(() => store.employees);
  const departments = useStore(() => store.departments);
  const [q, setQ] = useState("");
  const [deptFilter, setDeptFilter] = useState("all");
  const [roleFilter, setRoleFilter] = useState("all");
  const [statusFilter, setStatusFilter] = useState("all");

  const filtered = employees.filter(
    (e) =>
      (e.name + e.email).toLowerCase().includes(q.toLowerCase()) &&
      (deptFilter === "all" || e.departmentId === deptFilter) &&
      (roleFilter === "all" || e.role === roleFilter) &&
      (statusFilter === "all" || e.status === statusFilter),
  );

  return (
    <Card>
      <CardHeader className="space-y-3">
        <div className="flex flex-wrap items-center gap-2">
          <CardTitle className="text-base flex-1">Employee Directory</CardTitle>
        </div>
        <div className="flex flex-wrap gap-2">
          <div className="relative flex-1 min-w-40">
            <Search className="pointer-events-none absolute left-2 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              placeholder="Search employees"
              value={q}
              onChange={(e) => setQ(e.target.value)}
              className="h-9 pl-8"
            />
          </div>
          <Select value={deptFilter} onValueChange={setDeptFilter}>
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
          <Select value={roleFilter} onValueChange={setRoleFilter}>
            <SelectTrigger className="h-9 w-40">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All roles</SelectItem>
              <SelectItem value="admin">Admin</SelectItem>
              <SelectItem value="asset_manager">Asset Manager</SelectItem>
              <SelectItem value="department_head">Department Head</SelectItem>
              <SelectItem value="employee">Employee</SelectItem>
            </SelectContent>
          </Select>
          <Select value={statusFilter} onValueChange={setStatusFilter}>
            <SelectTrigger className="h-9 w-32">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="inactive">Inactive</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Name</TableHead>
                <TableHead>Email</TableHead>
                <TableHead>Department</TableHead>
                <TableHead>Role</TableHead>
                <TableHead>Status</TableHead>
                <TableHead>Joined</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {filtered.map((e) => {
                const dept = departments.find((d) => d.id === e.departmentId);
                return (
                  <TableRow key={e.id}>
                    <TableCell className="font-medium">{e.name}</TableCell>
                    <TableCell className="text-muted-foreground">{e.email}</TableCell>
                    <TableCell>{dept?.name || "—"}</TableCell>
                    <TableCell>
                      <StatusBadge status={e.role} />
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={e.status} />
                    </TableCell>
                    <TableCell className="text-xs text-muted-foreground">
                      {format(new Date(e.joinedAt), "MMM d, yyyy")}
                    </TableCell>
                    <TableCell className="text-right">
                      <RoleActions employee={e} actorId={actorId} />
                    </TableCell>
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  );
}

function RoleActions({
  employee,
  actorId,
}: {
  employee: { id: string; name: string; role: Role; status: "active" | "inactive" };
  actorId: string;
}) {
  const [targetRole, setTargetRole] = useState<Role | null>(null);
  const promote = async (role: Role) => {
    await employeeService.updateRole(employee.id, role, actorId);
    toast.success(`${employee.name} is now ${roleLabel(role)}`);
    setTargetRole(null);
  };
  return (
    <div className="flex justify-end gap-1">
      <Select onValueChange={(v) => setTargetRole(v as Role)}>
        <SelectTrigger className="h-8 w-32 text-xs">
          <SelectValue placeholder="Change role" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="employee">Reset to Employee</SelectItem>
          <SelectItem value="department_head">Promote to Dept Head</SelectItem>
          <SelectItem value="asset_manager">Promote to Asset Manager</SelectItem>
        </SelectContent>
      </Select>
      <AlertDialog open={!!targetRole} onOpenChange={(o) => !o && setTargetRole(null)}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Confirm role change</AlertDialogTitle>
            <AlertDialogDescription>
              Change {employee.name}'s role to {targetRole && roleLabel(targetRole)}?
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>Cancel</AlertDialogCancel>
            <AlertDialogAction onClick={() => targetRole && promote(targetRole)}>
              Confirm
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
      <Button
        size="sm"
        variant="ghost"
        onClick={() =>
          employeeService.setStatus(
            employee.id,
            employee.status === "active" ? "inactive" : "active",
          )
        }
      >
        {employee.status === "active" ? "Deactivate" : "Activate"}
      </Button>
    </div>
  );
}
