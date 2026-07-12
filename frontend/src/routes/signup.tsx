import { createFileRoute, Link, useNavigate } from "@tanstack/react-router";
import { useState } from "react";
import { useAuth } from "@/context/AuthContext";
import { authService } from "@/services";
import { useStore } from "@/hooks/useStore";
import { store } from "@/mocks/store";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { toast } from "sonner";

export const Route = createFileRoute("/signup")({
  validateSearch: (s: Record<string, unknown>): { next?: string } => ({
    next: typeof s.next === "string" && s.next.startsWith("/") ? s.next : undefined,
  }),
  component: SignupPage,
});

function SignupPage() {
  const { setDemoUser } = useAuth();
  const navigate = useNavigate();
  const { next } = Route.useSearch();
  const departments = useStore(() => store.departments);
  const [form, setForm] = useState({
    name: "",
    email: "",
    password: "",
    confirm: "",
    departmentId: "",
    agree: false,
  });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const update = <K extends keyof typeof form>(k: K, v: (typeof form)[K]) =>
    setForm((s) => ({ ...s, [k]: v }));

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    if (form.password.length < 6) return setError("Password must be at least 6 characters");
    if (form.password !== form.confirm) return setError("Passwords do not match");
    if (!form.agree) return setError("You must accept the terms");
    setLoading(true);
    try {
      const user = await authService.signup({
        name: form.name,
        email: form.email,
        password: form.password,
        departmentId: form.departmentId || undefined,
      });
      setDemoUser(user.id);
      toast.success("Account created — welcome!");

      if (next) {
        window.location.href = next;
      } else {
        navigate({ to: "/dashboard" });
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Signup failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/30 p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-3 text-center">
          <div className="mx-auto grid h-12 w-12 place-items-center rounded-lg bg-primary text-primary-foreground text-xl font-bold">
            A
          </div>
          <CardTitle className="text-2xl">Create your account</CardTitle>
          <CardDescription>Join your organization on AssetFlow</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
            <div className="space-y-2">
              <Label htmlFor="name">Full name</Label>
              <Input
                id="name"
                value={form.name}
                onChange={(e) => update("name", e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                value={form.email}
                onChange={(e) => update("email", e.target.value)}
                required
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-2">
                <Label htmlFor="pw">Password</Label>
                <Input
                  id="pw"
                  type="password"
                  value={form.password}
                  onChange={(e) => update("password", e.target.value)}
                  required
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="cpw">Confirm</Label>
                <Input
                  id="cpw"
                  type="password"
                  value={form.confirm}
                  onChange={(e) => update("confirm", e.target.value)}
                  required
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>Department (optional)</Label>
              <Select value={form.departmentId} onValueChange={(v) => update("departmentId", v)}>
                <SelectTrigger>
                  <SelectValue placeholder="Select department" />
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
            <div className="flex items-start gap-2">
              <Checkbox
                id="agree"
                checked={form.agree}
                onCheckedChange={(v) => update("agree", !!v)}
              />
              <Label htmlFor="agree" className="text-sm font-normal leading-snug">
                I agree to the terms and privacy policy
              </Label>
            </div>
            <p className="rounded-md bg-muted/50 p-3 text-xs text-muted-foreground">
              New accounts are created as{" "}
              <span className="font-medium text-foreground">Employees</span>. Roles are managed by
              your organization administrator.
            </p>
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Creating…" : "Create account"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Already have an account?{" "}
              <Link to="/login" className="font-medium text-primary hover:underline">
                Sign in
              </Link>
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}
