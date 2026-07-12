import { createFileRoute } from "@tanstack/react-router";
import { useAuth, roleLabel } from "@/context/AuthContext";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { useEffect, useState } from "react";

export const Route = createFileRoute("/_app/settings")({ component: SettingsPage });

function SettingsPage() {
  const { user } = useAuth();
  const [dark, setDark] = useState(() => typeof window !== "undefined" && document.documentElement.classList.contains("dark"));
  const [notifs, setNotifs] = useState(true);
  useEffect(() => { document.documentElement.classList.toggle("dark", dark); }, [dark]);

  return (
    <div className="max-w-2xl space-y-4">
      <Card>
        <CardHeader><CardTitle className="text-base">Preferences</CardTitle></CardHeader>
        <CardContent className="space-y-4">
          <div className="flex items-center justify-between">
            <div><Label>Dark mode</Label><p className="text-xs text-muted-foreground">Reduce eye strain in low light</p></div>
            <Switch checked={dark} onCheckedChange={setDark} />
          </div>
          <div className="flex items-center justify-between">
            <div><Label>Email notifications</Label><p className="text-xs text-muted-foreground">Get emails for critical events</p></div>
            <Switch checked={notifs} onCheckedChange={setNotifs} />
          </div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Account</CardTitle></CardHeader>
        <CardContent className="space-y-2 text-sm">
          <div className="flex justify-between"><span className="text-muted-foreground">Name</span><span>{user?.name}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Email</span><span>{user?.email}</span></div>
          <div className="flex justify-between"><span className="text-muted-foreground">Role</span><span>{user && roleLabel(user.role)}</span></div>
        </CardContent>
      </Card>

      <Card>
        <CardHeader><CardTitle className="text-base">Help & Support</CardTitle></CardHeader>
        <CardContent className="text-sm text-muted-foreground">
          Need help? Contact your organization administrator or reach out to support@assetflow.co.
        </CardContent>
      </Card>
    </div>
  );
}
