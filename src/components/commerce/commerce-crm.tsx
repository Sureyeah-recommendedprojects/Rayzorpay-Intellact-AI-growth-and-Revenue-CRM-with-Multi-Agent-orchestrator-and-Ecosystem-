"use client";

import Link from "next/link";
import {
  ArrowUpRight,
  CalendarCheck,
  CaretRight,
  CheckCircle,
  ClockCountdown,
  CurrencyInr,
  Phone,
  PhoneCall,
  Sparkle,
  TrendUp,
  UserPlus,
  WarningCircle,
} from "@phosphor-icons/react";
import { toast } from "sonner";

import { PageHeader } from "@/components/layout/page-header";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";

const calls = [
  { name: "Riya Sharma", detail: "Abandoned checkout · ₹4,800", time: "10:30 AM", accent: "bg-primary", action: "Call now" },
  { name: "Kabir Mehta", detail: "High intent · 3 product views", time: "11:15 AM", accent: "bg-warning", action: "Schedule" },
  { name: "Ananya Iyer", detail: "Payment failed · UPI retry", time: "12:00 PM", accent: "bg-info", action: "Call now" },
];

const payments = [
  { label: "Collected today", value: "₹1.84L", change: "+18.2%", icon: CurrencyInr },
  { label: "Recovery opportunity", value: "₹36,420", change: "47 customers", icon: TrendUp },
  { label: "Payment success", value: "91.8%", change: "+2.4 pts", icon: CheckCircle },
];

export function CommerceCrm() {
  const call = (name: string) => toast.success(`Calling ${name}`, { description: "Intellact has opened the customer context and call notes." });
  const schedule = (name: string) => toast.success(`Follow-up scheduled for ${name}`, { description: "A reminder and payment-ready message will be sent before the call." });

  return (
    <div className="mx-auto max-w-6xl space-y-6 p-4 md:p-6">
      <PageHeader
        title="Commerce CRM"
        description="Turn every conversation into a measurable revenue moment—from first intent to payment recovery."
        actions={
          <Button onClick={() => toast.success("Smart follow-up sequence started", { description: "47 payment-risk customers are being queued with consent-aware outreach." })} className="gap-2">
            <Sparkle weight="fill" /> Start recovery flow
          </Button>
        }
      />

      <section className="grid gap-3 md:grid-cols-3">
        {payments.map(({ label, value, change, icon: Icon }) => (
          <Card key={label} className="relative overflow-hidden border-border/70 p-4 shadow-depth-1">
            <div className="absolute right-0 top-0 h-20 w-20 rounded-bl-[4rem] bg-primary/10" />
            <div className="flex items-center justify-between text-muted-foreground">
              <span className="text-xs font-medium uppercase tracking-[0.12em]">{label}</span>
              <Icon className="size-4 text-primary" weight="duotone" />
            </div>
            <p className="mt-4 font-mono text-2xl font-semibold tracking-tight text-foreground">{value}</p>
            <p className="mt-1 text-xs font-medium text-success">{change} <span className="font-normal text-muted-foreground">vs. last 7 days</span></p>
          </Card>
        ))}
      </section>

      <section className="grid gap-4 lg:grid-cols-[1.35fr_0.9fr]">
        <Card className="overflow-hidden border-border/70 shadow-depth-1">
          <div className="flex items-center justify-between border-b border-border/60 px-4 py-3.5">
            <div>
              <div className="flex items-center gap-2 font-heading text-sm font-semibold"><PhoneCall className="size-4 text-primary" weight="fill" /> Revenue call queue</div>
              <p className="mt-0.5 text-xs text-muted-foreground">Prioritized by intent, cart value, and payment risk</p>
            </div>
            <span className="rounded-full bg-primary/10 px-2.5 py-1 text-[11px] font-semibold text-primary">12 due today</span>
          </div>
          <div className="divide-y divide-border/55">
            {calls.map((customer) => (
              <div key={customer.name} className="flex items-center gap-3 px-4 py-3.5 transition-colors hover:bg-muted/40">
                <div className={`grid size-9 place-items-center rounded-full ${customer.accent}/15 text-xs font-bold text-foreground ring-1 ring-inset ring-foreground/10`}>{customer.name.split(" ").map((n) => n[0]).join("")}</div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{customer.name}</p>
                  <p className="truncate text-xs text-muted-foreground">{customer.detail}</p>
                </div>
                <div className="hidden text-right sm:block"><p className="text-xs font-medium">{customer.time}</p><p className="text-[11px] text-muted-foreground">Today</p></div>
                <Button variant={customer.action === "Call now" ? "default" : "outline"} size="sm" className="gap-1.5" onClick={() => customer.action === "Call now" ? call(customer.name) : schedule(customer.name)}>
                  {customer.action === "Call now" ? <Phone weight="fill" /> : <CalendarCheck />} <span className="hidden sm:inline">{customer.action}</span>
                </Button>
              </div>
            ))}
          </div>
          <div className="border-t border-border/60 px-4 py-3"><Button variant="ghost" size="sm" className="w-full gap-1 text-muted-foreground" onClick={() => toast.info("Full customer queue will open here next.")}>Open all customer conversations <CaretRight /></Button></div>
        </Card>

        <Card className="overflow-hidden border-border/70 shadow-depth-1">
          <div className="border-b border-border/60 px-4 py-3.5"><div className="flex items-center gap-2 font-heading text-sm font-semibold"><WarningCircle className="size-4 text-primary" weight="fill" /> Payment pulse</div><p className="mt-0.5 text-xs text-muted-foreground">What is quietly costing you revenue</p></div>
          <div className="space-y-4 p-4">
            <Insight label="UPI retry failures" value="₹18,600 at risk" progress={68} tone="bg-primary" />
            <Insight label="COD confirmation pending" value="19 orders · ₹12,980" progress={45} tone="bg-warning" />
            <Insight label="High-value carts idle" value="8 carts · ₹4,840" progress={27} tone="bg-info" />
          </div>
          <div className="mx-4 mb-4 rounded-lg border border-primary/20 bg-primary/8 p-3"><div className="flex gap-2"><Sparkle className="mt-0.5 size-4 shrink-0 text-primary" weight="fill" /><p className="text-xs leading-5 text-foreground"><b>Intellact signal:</b> A 2-hour WhatsApp + call sequence is likely to recover ₹11,200 today.</p></div></div>
        </Card>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <Card className="border-border/70 p-4"><p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">Lifecycle</p><p className="mt-2 font-heading text-lg font-semibold">From lead to loyalist</p><p className="mt-1 text-sm leading-6 text-muted-foreground">Segment customers by RFM, recent call outcome, and payment behaviour—not just their last order.</p></Card>
        <Card className="border-border/70 p-4"><p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">Deployment</p><p className="mt-2 font-heading text-lg font-semibold">One-click revenue loops</p><p className="mt-1 text-sm leading-6 text-muted-foreground">Push the right landing page, campaign and recovery script from the same customer context.</p><Link href="/landing-pages" className="mt-3 inline-flex items-center gap-1 text-xs font-semibold text-primary hover:underline">Open deployment studio <ArrowUpRight /></Link></Card>
        <Card className="border-border/70 p-4"><p className="text-xs font-medium uppercase tracking-[0.12em] text-muted-foreground">Response SLA</p><p className="mt-2 flex items-center gap-2 font-mono text-2xl font-semibold">14 min <ClockCountdown className="size-5 text-success" weight="duotone" /></p><p className="mt-1 text-sm leading-6 text-muted-foreground">Your team is responding 36% faster than last week across high-intent customers.</p></Card>
      </section>
    </div>
  );
}

function Insight({ label, value, progress, tone }: { label: string; value: string; progress: number; tone: string }) {
  return <div><div className="flex items-center justify-between gap-3 text-xs"><span className="text-muted-foreground">{label}</span><span className="font-mono font-semibold text-foreground">{value}</span></div><div className="mt-2 h-1.5 overflow-hidden rounded-full bg-muted"><div className={`h-full rounded-full ${tone}`} style={{ width: `${progress}%` }} /></div></div>;
}
