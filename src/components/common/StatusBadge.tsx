import { cn } from "@/lib/utils";
import type { AssetStatus, AssetCondition, MaintenanceStatus, MaintenancePriority, BookingStatus, AuditStatus } from "@/types";
import { Badge } from "@/components/ui/badge";

const STATUS_STYLES: Record<string, string> = {
  available: "bg-success/15 text-success border-success/30",
  allocated: "bg-info/15 text-info border-info/30",
  reserved: "bg-primary/15 text-primary border-primary/30",
  under_maintenance: "bg-warning/15 text-warning-foreground border-warning/40",
  lost: "bg-destructive/15 text-destructive border-destructive/30",
  retired: "bg-muted text-muted-foreground border-border",
  disposed: "bg-muted text-muted-foreground border-border",
  active: "bg-info/15 text-info border-info/30",
  returned: "bg-success/15 text-success border-success/30",
  overdue: "bg-destructive/15 text-destructive border-destructive/30",
  pending: "bg-muted text-muted-foreground border-border",
  approved: "bg-success/15 text-success border-success/30",
  rejected: "bg-destructive/15 text-destructive border-destructive/30",
  assigned: "bg-info/15 text-info border-info/30",
  in_progress: "bg-warning/15 text-warning-foreground border-warning/40",
  resolved: "bg-success/15 text-success border-success/30",
  requested: "bg-warning/15 text-warning-foreground border-warning/40",
  completed: "bg-success/15 text-success border-success/30",
  upcoming: "bg-info/15 text-info border-info/30",
  ongoing: "bg-primary/15 text-primary border-primary/30",
  cancelled: "bg-muted text-muted-foreground border-border",
  draft: "bg-muted text-muted-foreground border-border",
  in_review: "bg-warning/15 text-warning-foreground border-warning/40",
  closed: "bg-muted text-muted-foreground border-border",
  low: "bg-muted text-muted-foreground border-border",
  medium: "bg-info/15 text-info border-info/30",
  high: "bg-warning/15 text-warning-foreground border-warning/40",
  critical: "bg-destructive/15 text-destructive border-destructive/30",
  excellent: "bg-success/15 text-success border-success/30",
  good: "bg-info/15 text-info border-info/30",
  fair: "bg-warning/15 text-warning-foreground border-warning/40",
  poor: "bg-destructive/15 text-destructive border-destructive/30",
  verified: "bg-success/15 text-success border-success/30",
  missing: "bg-destructive/15 text-destructive border-destructive/30",
  damaged: "bg-warning/15 text-warning-foreground border-warning/40",
};

export function StatusBadge({ status, className }: { status: AssetStatus | AssetCondition | MaintenanceStatus | MaintenancePriority | BookingStatus | AuditStatus | string; className?: string }) {
  const label = String(status).replace(/_/g, " ");
  return (
    <Badge variant="outline" className={cn("capitalize font-normal", STATUS_STYLES[status] || "", className)}>
      {label}
    </Badge>
  );
}
