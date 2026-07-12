import { useState } from "react";
import { Link, createFileRoute } from "@tanstack/react-router";
import {
  ArrowRight,
  BarChart3,
  CalendarCheck,
  ClipboardCheck,
  PackageCheck,
  Wrench,
} from "lucide-react";
import { inquiryService } from "@/services";

const features = [
  {
    title: "Asset Lifecycle Management",
    icon: PackageCheck,
    detail: "Register, assign, return, retire, and audit every item with clear ownership.",
  },
  {
    title: "Allocation and Transfers",
    icon: ArrowRight,
    detail: "Move assets between employees and departments with approval history intact.",
  },
  {
    title: "Resource Booking",
    icon: CalendarCheck,
    detail: "Reserve rooms, vehicles, and shared equipment without double-booking.",
  },
  {
    title: "Maintenance Workflows",
    icon: Wrench,
    detail: "Triage repairs, assign technicians, track costs, and close requests cleanly.",
  },
  {
    title: "Asset Audits",
    icon: ClipboardCheck,
    detail: "Run cycle counts and capture findings for missing, damaged, or verified assets.",
  },
  {
    title: "Reports and Analytics",
    icon: BarChart3,
    detail: "See utilization, overdue returns, department load, and operational bottlenecks.",
  },
];

const steps = [
  "Register assets",
  "Allocate or book resources",
  "Track maintenance and transfers",
  "Audit and analyze",
];

export const Route = createFileRoute("/")({
  component: LandingPage,
});

function LandingPage() {
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [company, setCompany] = useState("");
  const [message, setMessage] = useState("");

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitStatus, setSubmitStatus] = useState<"idle" | "success" | "error">("idle");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitStatus("idle");
    const newErrors: Record<string, string> = {};

    if (!name.trim()) {
      newErrors.name = "Name is required";
    }
    if (!email.trim()) {
      newErrors.email = "Email is required";
    } else if (!email.includes("@")) {
      newErrors.email = "Email must contain @";
    } else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      newErrors.email = "Please enter a valid email address";
    }
    if (!message.trim()) {
      newErrors.message = "Message is required";
    }

    if (Object.keys(newErrors).length > 0) {
      setErrors(newErrors);
      return;
    }

    setErrors({});
    setSubmitting(true);
    try {
      await inquiryService.submit({ name, email, company: company || undefined, message });
      setSubmitStatus("success");
      setName("");
      setEmail("");
      setCompany("");
      setMessage("");
    } catch (err) {
      console.error(err);
      setSubmitStatus("error");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="min-h-screen bg-background text-foreground">
      <header className="sticky top-0 z-50 border-b bg-background/90 backdrop-blur">
        <nav className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <a href="#hero" className="text-xl font-bold text-primary">
            AssetFlow
          </a>
          <div className="hidden items-center gap-7 text-sm font-medium text-muted-foreground md:flex">
            <a href="#product" className="hover:text-foreground">
              Product
            </a>
            <a href="#features" className="hover:text-foreground">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-foreground">
              How It Works
            </a>
            <a href="#about" className="hover:text-foreground">
              About
            </a>
            <a href="#contact" className="hover:text-foreground">
              Contact
            </a>
          </div>
          <div className="flex items-center gap-3">
            <Link
              to="/login"
              className="rounded-md border border-input bg-background px-4 py-2 text-sm font-semibold hover:bg-accent hover:text-accent-foreground"
            >
              Log In
            </Link>
            <Link
              to="/signup"
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-primary-foreground shadow-sm hover:bg-primary/90"
            >
              Sign Up
            </Link>
          </div>
        </nav>
      </header>

      <section
        id="hero"
        className="mx-auto grid max-w-7xl gap-10 px-6 py-16 lg:grid-cols-[1fr_1fr] lg:items-center lg:py-20"
      >
        <div className="max-w-2xl">
          <p className="mb-4 text-sm font-semibold uppercase tracking-widest text-primary">
            AssetFlow
          </p>
          <h1 className="text-4xl font-bold tracking-tight sm:text-6xl">
            Enterprise asset and resource operations.
          </h1>
          <p className="mt-6 text-lg leading-8 text-muted-foreground">
            Manage assets, shared resources, maintenance, audits, transfers, and reporting in one
            focused workspace for operations teams.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row">
            <Link
              to="/login"
              className="inline-flex items-center justify-center gap-2 rounded-md bg-primary px-6 py-3 font-semibold text-primary-foreground shadow-sm hover:bg-primary/90"
            >
              Log In <ArrowRight className="h-4 w-4" />
            </Link>
            <Link
              to="/signup"
              className="inline-flex items-center justify-center gap-2 rounded-md border border-input bg-background px-6 py-3 font-semibold hover:bg-accent hover:text-accent-foreground"
            >
              Sign Up
            </Link>
          </div>
        </div>
        <div id="product" className="rounded-lg border bg-card p-4 shadow-xl shadow-primary/10">
          <div className="rounded-md border bg-secondary/70 p-4">
            <div className="mb-4 flex items-center justify-between">
              <span className="font-semibold">Operations Overview</span>
              <span className="rounded-full bg-success px-3 py-1 text-xs font-semibold text-success-foreground">
                Live
              </span>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              {["Assets", "Bookings", "Maintenance", "Audits"].map((item, index) => (
                <div key={item} className="rounded-md border bg-background p-4 shadow-sm">
                  <p className="text-sm font-medium text-muted-foreground">{item}</p>
                  <p className="mt-2 text-3xl font-bold tabular-nums">
                    {[1248, 86, 19, 42][index]}
                  </p>
                </div>
              ))}
            </div>
            <div className="mt-4 rounded-md border bg-background p-4">
              <div className="mb-3 flex items-center justify-between text-sm">
                <span className="font-medium">Allocation health</span>
                <span className="text-success">92%</span>
              </div>
              <div className="h-2 rounded-full bg-muted">
                <div className="h-2 w-[92%] rounded-full bg-primary" />
              </div>
            </div>
          </div>
        </div>
      </section>

      <section id="features" className="border-y bg-secondary/50 py-20">
        <div className="mx-auto max-w-7xl px-6">
          <h2 className="text-3xl font-bold">Core Features</h2>
          <div className="mt-10 grid gap-5 md:grid-cols-2 lg:grid-cols-3">
            {features.map((feature) => (
              <div key={feature.title} className="rounded-lg border bg-card p-6 shadow-sm">
                <div className="mb-4 grid h-10 w-10 place-items-center rounded-md bg-primary/10 text-primary">
                  <feature.icon className="h-5 w-5" />
                </div>
                <h3 className="text-lg font-semibold">{feature.title}</h3>
                <p className="mt-3 text-sm leading-6 text-muted-foreground">{feature.detail}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="mx-auto max-w-7xl px-6 py-20">
        <h2 className="text-3xl font-bold">How It Works</h2>
        <div className="mt-10 grid gap-5 md:grid-cols-4">
          {steps.map((step, index) => (
            <div key={step} className="rounded-lg border bg-card p-6 shadow-sm">
              <span className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
                {index + 1}
              </span>
              <h3 className="mt-5 font-semibold">{step}</h3>
            </div>
          ))}
        </div>
      </section>

      <section className="bg-primary py-20 text-primary-foreground">
        <div className="mx-auto grid max-w-7xl gap-6 px-6 md:grid-cols-2">
          <div className="rounded-lg bg-white/10 p-8">
            <h2 className="text-2xl font-bold">Employee Portal</h2>
            <p className="mt-4 text-primary-foreground/80">
              Request resources, book shared equipment, view assigned assets, and report maintenance
              issues quickly.
            </p>
          </div>
          <div className="rounded-lg bg-white/10 p-8">
            <h2 className="text-2xl font-bold">Management Portal</h2>
            <p className="mt-4 text-primary-foreground/80">
              Approve allocations, monitor lifecycle status, schedule audits, and review
              organization-wide analytics.
            </p>
          </div>
        </div>
      </section>

      <section id="about" className="mx-auto max-w-7xl px-6 py-20">
        <div className="max-w-3xl">
          <h2 className="text-3xl font-bold">About AssetFlow</h2>
          <p className="mt-5 text-lg leading-8 text-muted-foreground">
            AssetFlow is built to give teams a dependable system of record for company assets and
            shared resources. It serves businesses, campuses, warehouses, IT teams, facilities
            teams, and growing organizations that need better visibility and accountability.
          </p>
        </div>
      </section>

      <section id="contact" className="border-t bg-secondary/50 py-20">
        <div className="mx-auto grid max-w-7xl gap-10 px-6 lg:grid-cols-[0.8fr_1fr]">
          <div>
            <h2 className="text-3xl font-bold">Contact / Inquiry</h2>
            <p className="mt-4 text-muted-foreground">
              Tell us about your asset and resource management needs.
            </p>
          </div>
          <form
            onSubmit={handleSubmit}
            className="grid gap-4 rounded-lg border bg-card p-6 shadow-sm"
          >
            <div className="grid gap-1">
              <input
                className="rounded-md border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Name"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              {errors.name && <span className="text-xs text-destructive">{errors.name}</span>}
            </div>

            <div className="grid gap-1">
              <input
                className="rounded-md border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Work email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              {errors.email && <span className="text-xs text-destructive">{errors.email}</span>}
            </div>

            <div className="grid gap-1">
              <input
                className="rounded-md border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Company"
                value={company}
                onChange={(e) => setCompany(e.target.value)}
              />
            </div>

            <div className="grid gap-1">
              <textarea
                className="min-h-32 rounded-md border bg-background px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-primary"
                placeholder="Message"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
              />
              {errors.message && <span className="text-xs text-destructive">{errors.message}</span>}
            </div>

            {submitStatus === "success" && (
              <div className="rounded-md bg-success/15 p-3 text-sm text-success font-medium">
                Thank you! Your inquiry has been submitted successfully.
              </div>
            )}
            {submitStatus === "error" && (
              <div className="rounded-md bg-destructive/15 p-3 text-sm text-destructive font-medium">
                Something went wrong. Please try again.
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="rounded-md bg-primary px-6 py-3 font-semibold text-primary-foreground hover:bg-primary/90 disabled:opacity-50"
            >
              {submitting ? "Submitting..." : "Submit Inquiry"}
            </button>
          </form>
        </div>
      </section>

      <footer className="border-t py-10">
        <div className="mx-auto flex max-w-7xl flex-col gap-6 px-6 md:flex-row md:items-center md:justify-between">
          <p className="font-bold text-primary">AssetFlow</p>
          <div className="flex flex-wrap gap-6 text-sm text-muted-foreground">
            <a href="#product">Product</a>
            <a href="#about">Company</a>
            <a href="#contact">Support</a>
            <Link to="/login" className="hover:text-foreground">
              Log In
            </Link>
            <Link to="/signup" className="hover:text-foreground">
              Sign Up
            </Link>
          </div>
        </div>
      </footer>
    </main>
  );
}
