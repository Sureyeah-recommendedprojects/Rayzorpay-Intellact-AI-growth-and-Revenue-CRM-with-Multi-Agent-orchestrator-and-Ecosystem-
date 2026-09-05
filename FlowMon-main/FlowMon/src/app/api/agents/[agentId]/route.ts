import { NextRequest, NextResponse } from "next/server";

export const maxDuration = 30;

const success = (agentId: string, result: Record<string, unknown>, started: number) => NextResponse.json({ success: true, agentId, result, executionTimeMs: Date.now() - started, source: "rayzorflow" });
const fail = (agentId: string, error: string, started: number) => NextResponse.json({ success: false, agentId, error, executionTimeMs: Date.now() - started, source: "rayzorflow" }, { status: 400 });

export async function POST(request: NextRequest, { params }: { params: Promise<{ agentId: string }> }) {
  const started = Date.now();
  const { agentId } = await params;
  const body = await request.json() as Record<string, string>;
  const flowId = request.headers.get("X-Flow-Id") ?? "local";
  const base = { flowId, step: Number(request.headers.get("X-Step") ?? 0), status: "ready_for_approval" };
  const amount = Number(body.amount || 0);
  if (["order-agent", "payment-link-agent", "refund-agent", "payout-agent", "risk-review-agent"].includes(agentId) && (!Number.isFinite(amount) || amount <= 0)) return fail(agentId, "A positive amount is required.", started);
  switch (agentId) {
    case "workflow-coordinator": return success(agentId, { ...base, action: "workflow_coordinated", executionMode: body.executionMode || "parallel", note: "Independent commerce operations can now run in parallel." }, started);
    case "payment-health-agent": return success(agentId, { ...base, action: "payment_health_review", window: body.window || "7d", insight: "Connect Razorpay credentials to analyze payment failures and recovery cohorts." }, started);
    case "order-agent": return success(agentId, { ...base, action: "order_prepared", amount, currency: "INR", receipt: body.receipt || `rayzorflow_${Date.now()}`, note: "Order is prepared; collection requires merchant approval." }, started);
    case "payment-link-agent": if (!body.customer) return fail(agentId, "A customer is required.", started); return success(agentId, { ...base, action: "payment_link_prepared", customer: body.customer, amount, currency: "INR", note: "Payment link is prepared; outreach requires merchant approval." }, started);
    case "refund-agent": if (!body.paymentId) return fail(agentId, "A payment ID is required.", started); return success(agentId, { ...base, action: "refund_review_prepared", paymentId: body.paymentId, amount, reason: body.reason || "customer_request", note: "Refund is queued for merchant approval." }, started);
    case "settlement-agent": return success(agentId, { ...base, action: "settlement_reconciliation", settlementDate: body.settlementDate || new Date().toISOString().slice(0, 10), expectedAmount: Number(body.expectedAmount || 0), note: "Connect settlement data to reconcile collections and exceptions." }, started);
    case "wallet-balance-agent": return success(agentId, { ...base, action: "wallet_balance_checked", walletId: body.walletId || "primary", note: "Connect RazorpayX credentials to retrieve a live wallet balance." }, started);
    case "payout-agent": if (!body.beneficiary) return fail(agentId, "A beneficiary is required.", started); return success(agentId, { ...base, action: "payout_prepared", beneficiary: body.beneficiary, amount, currency: "INR", note: "Payout requires merchant approval before release." }, started);
    case "customer-support-agent": if (!body.customerIssue) return fail(agentId, "A customer issue is required.", started); return success(agentId, { ...base, action: "support_brief_created", customerIssue: body.customerIssue, recommendation: "Acknowledge the issue, share the payment status, and provide the next expected update." }, started);
    case "risk-review-agent": return success(agentId, { ...base, action: "risk_review", amount, riskProfile: body.riskProfile || "standard", recommendation: amount > 50000 ? "manual_review" : "approve_with_audit_log" }, started);
    case "commerce-insights-agent": return success(agentId, { ...base, action: "commerce_insights", goal: body.goal || "improve payment recovery", recommendation: "Prioritize failed UPI attempts with a payment-link follow-up and track recovery by cohort." }, started);
    default: return fail(agentId, "Unknown RayzorFlow agent.", started);
  }
}
