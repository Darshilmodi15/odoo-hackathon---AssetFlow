import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { StatusBadge } from "@/components/common/StatusBadge";
import { EmptyState } from "@/components/common/States";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { ArrowLeft, FileText, ImageIcon, QrCode } from "lucide-react";
import { format } from "date-fns";

export const Route = createFileRoute("/_app/assets/$assetId")({ component: AssetDetailPage });

function AssetDetailPage() {
  const { assetId } = Route.useParams();
  const navigate = useNavigate();
  const asset = useStore(() => store.assets.find((a) => a.id === assetId));
  const category = useStore(() =>
    asset ? store.categories.find((c) => c.id === asset.categoryId) : undefined,
  );
  const department = useStore(() =>
    asset ? store.departments.find((d) => d.id === asset.departmentId) : undefined,
  );
  const assignee = useStore(() =>
    asset?.assignedToId ? store.employees.find((e) => e.id === asset.assignedToId) : undefined,
  );
  const allocations = useStore(() => store.allocations.filter((al) => al.assetId === assetId));
  const maintenance = useStore(() => store.maintenance.filter((m) => m.assetId === assetId));
  const bookings = useStore(() => store.bookings.filter((b) => b.assetId === assetId));
  const audits = useStore(() =>
    store.audits.flatMap((a) =>
      a.findings.filter((f) => f.assetId === assetId).map((f) => ({ ...f, auditTitle: a.title })),
    ),
  );
  const activity = useStore(() => store.activityLogs.filter((l) => l.entityId === assetId));
  const employees = useStore(() => store.employees);

  if (!asset)
    return (
      <EmptyState
        title="Asset not found"
        action={
          <Button variant="outline" onClick={() => navigate({ to: "/assets" })}>
            Back
          </Button>
        }
      />
    );

  return (
    <div className="space-y-4">
      <Button variant="ghost" size="sm" asChild>
        <Link to="/assets">
          <ArrowLeft className="mr-1 h-4 w-4" />
          Back to Assets
        </Link>
      </Button>

      <Card>
        <CardContent className="flex flex-wrap items-start gap-4 p-6">
          <div className="grid h-24 w-24 shrink-0 place-items-center overflow-hidden rounded-lg border-2 border-dashed border-border bg-muted/40">
            {asset.photoUrl ? (
              <img src={asset.photoUrl} alt="" className="h-full w-full object-cover" />
            ) : (
              <QrCode className="h-10 w-10 text-muted-foreground" />
            )}
          </div>
          <div className="min-w-0 flex-1">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="text-xl font-semibold">{asset.name}</h2>
              <span className="font-mono text-sm text-muted-foreground">{asset.tag}</span>
            </div>
            <div className="mt-2 flex flex-wrap gap-2">
              <StatusBadge status={asset.status} />
              <StatusBadge status={asset.condition} />
              {asset.shared && (
                <span className="rounded bg-muted px-2 py-0.5 text-xs">Bookable</span>
              )}
            </div>
            <div className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
              <div>
                <span className="text-muted-foreground">Category:</span> {category?.name}
              </div>
              <div>
                <span className="text-muted-foreground">Department:</span> {department?.name || "—"}
              </div>
              <div>
                <span className="text-muted-foreground">Location:</span> {asset.location}
              </div>
              <div>
                <span className="text-muted-foreground">Assigned:</span> {assignee?.name || "—"}
              </div>
              <div>
                <span className="text-muted-foreground">Serial:</span> {asset.serialNumber}
              </div>
              <div>
                <span className="text-muted-foreground">Cost:</span> ₹
                {asset.acquisitionCost.toLocaleString("en-IN")}
              </div>
              <div>
                <span className="text-muted-foreground">QR Code:</span> {asset.tag}
              </div>
              <div>
                <span className="text-muted-foreground">Documents:</span>{" "}
                {asset.documentUrl || asset.photoUrl ? "Available" : "—"}
              </div>
            </div>
            {(asset.photoUrl || asset.documentUrl) && (
              <div className="mt-4 flex flex-wrap gap-2 text-xs">
                {asset.photoUrl && (
                  <a
                    href={asset.photoUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 rounded-md border bg-card px-2 py-1 hover:bg-accent"
                  >
                    <ImageIcon className="h-3.5 w-3.5 text-primary" />
                    {asset.photoName || asset.photoUrl}
                  </a>
                )}
                {asset.documentUrl && (
                  <a
                    href={asset.documentUrl}
                    target="_blank"
                    rel="noreferrer"
                    className="inline-flex items-center gap-1 rounded-md border bg-card px-2 py-1 hover:bg-accent"
                  >
                    <FileText className="h-3.5 w-3.5 text-primary" />
                    {asset.documentName || asset.documentUrl}
                  </a>
                )}
              </div>
            )}
            {category?.customFields && category.customFields.length > 0 && (
              <div className="mt-4 grid gap-2 text-sm sm:grid-cols-2">
                {category.customFields.map((field) => (
                  <div key={field.key}>
                    <span className="text-muted-foreground">{field.label}:</span>{" "}
                    {asset.customFields?.[field.key] || "—"}
                  </div>
                ))}
              </div>
            )}
          </div>
          <div className="flex gap-2">
            <Button variant="outline" asChild>
              <Link to="/allocations">Allocate</Link>
            </Button>
            <Button variant="outline" asChild>
              <Link to="/maintenance">Maintenance</Link>
            </Button>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="allocations">
        <TabsList className="flex-wrap">
          <TabsTrigger value="allocations">Allocations</TabsTrigger>
          <TabsTrigger value="maintenance">Maintenance</TabsTrigger>
          {asset.shared && <TabsTrigger value="bookings">Bookings</TabsTrigger>}
          <TabsTrigger value="audits">Audits</TabsTrigger>
          <TabsTrigger value="activity">Activity</TabsTrigger>
        </TabsList>
        <TabsContent value="allocations">
          <Card>
            <CardContent className="p-0">
              {allocations.length === 0 ? (
                <EmptyState title="No allocation history" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Employee</TableHead>
                      <TableHead>Allocated</TableHead>
                      <TableHead>Returned</TableHead>
                      <TableHead>Status</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {allocations.map((a) => (
                      <TableRow key={a.id}>
                        <TableCell>{employees.find((e) => e.id === a.employeeId)?.name}</TableCell>
                        <TableCell>{format(new Date(a.allocatedAt), "MMM d, yyyy")}</TableCell>
                        <TableCell>
                          {a.returnedAt ? format(new Date(a.returnedAt), "MMM d, yyyy") : "—"}
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={a.status} />
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="maintenance">
          <Card>
            <CardContent className="p-0">
              {maintenance.length === 0 ? (
                <EmptyState title="No maintenance history" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Code</TableHead>
                      <TableHead>Issue</TableHead>
                      <TableHead>Priority</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {maintenance.map((m) => (
                      <TableRow key={m.id}>
                        <TableCell className="font-mono text-xs">{m.code}</TableCell>
                        <TableCell>{m.title}</TableCell>
                        <TableCell>
                          <StatusBadge status={m.priority} />
                        </TableCell>
                        <TableCell>
                          <StatusBadge status={m.status} />
                        </TableCell>
                        <TableCell className="text-xs">
                          {format(new Date(m.requestedAt), "MMM d")}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        {asset.shared && (
          <TabsContent value="bookings">
            <Card>
              <CardContent className="p-0">
                {bookings.length === 0 ? (
                  <EmptyState title="No bookings yet" />
                ) : (
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Booked by</TableHead>
                        <TableHead>Purpose</TableHead>
                        <TableHead>Start</TableHead>
                        <TableHead>End</TableHead>
                        <TableHead>Status</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bookings.map((b) => (
                        <TableRow key={b.id}>
                          <TableCell>
                            {employees.find((e) => e.id === b.bookedById)?.name}
                          </TableCell>
                          <TableCell>{b.purpose}</TableCell>
                          <TableCell className="text-xs">
                            {format(new Date(b.startAt), "MMM d HH:mm")}
                          </TableCell>
                          <TableCell className="text-xs">
                            {format(new Date(b.endAt), "MMM d HH:mm")}
                          </TableCell>
                          <TableCell>
                            <StatusBadge status={b.status} />
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                )}
              </CardContent>
            </Card>
          </TabsContent>
        )}
        <TabsContent value="audits">
          <Card>
            <CardContent className="p-0">
              {audits.length === 0 ? (
                <EmptyState title="No audit history" />
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Audit</TableHead>
                      <TableHead>Status</TableHead>
                      <TableHead>Notes</TableHead>
                      <TableHead>Date</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {audits.map((f) => (
                      <TableRow key={f.id}>
                        <TableCell>{f.auditTitle}</TableCell>
                        <TableCell>
                          <StatusBadge status={f.status} />
                        </TableCell>
                        <TableCell className="text-xs">{f.notes || "—"}</TableCell>
                        <TableCell className="text-xs">
                          {f.at ? format(new Date(f.at), "MMM d") : "—"}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </CardContent>
          </Card>
        </TabsContent>
        <TabsContent value="activity">
          <Card>
            <CardContent className="space-y-2 p-4">
              {activity.length === 0 ? (
                <EmptyState title="No activity yet" />
              ) : (
                activity.map((l) => (
                  <div
                    key={l.id}
                    className="flex items-start gap-3 border-b border-border pb-2 last:border-0 text-sm"
                  >
                    <div className="mt-1 h-2 w-2 shrink-0 rounded-full bg-primary" />
                    <div className="min-w-0 flex-1">
                      <div>{l.description}</div>
                      <div className="text-xs text-muted-foreground">
                        {format(new Date(l.at), "MMM d, yyyy HH:mm")}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
