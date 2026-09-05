"use client";

// ============================================================
// RayzorFlow — Pipeline Trigger Modal
// Pre-execution confirmation with execution plan preview,
// global merchant inputs and parallel group visualization.
// ============================================================

import { useState, useMemo, useEffect } from "react";
import { Play, X, ArrowRight, ChevronRight, Zap, Building2, Coins, CheckCircle2 } from "lucide-react";
import { useFlowStore } from "@/store/flow-store";
import { buildExecutionPlan } from "@/lib/execution-engine";
import { CATEGORY_COLORS } from "@/data/agent-registry";
import { cn } from "@/lib/utils";

function CategoryDot({ category }: { category: string }) {
  const color = CATEGORY_COLORS[category] ?? "var(--purple-primary)";
  return (
    <span
      className="inline-block w-2 h-2 rounded-full flex-shrink-0 mt-0.5"
      style={{ backgroundColor: color }}
    />
  );
}

export default function PipelineTriggerModal() {
  const {
    nodes,
    edges,
    flowName,
    pipelineTriggerOpen,
    setPipelineTriggerOpen,
    runFlow,
    flowStatus,
  } = useFlowStore();

  const [merchantReference, setMerchantReference] = useState("");
  const [initialAmount, setInitialAmount] = useState("");
  const [amountUnit, setAmountUnit] = useState("INR");

  // Build parallel execution plan for preview
  const executionPlan = useMemo(() => {
    if (nodes.length === 0) return [];
    return buildExecutionPlan(
      nodes.map((n) => n.id),
      edges
    );
  }, [nodes, edges]);

  if (!pipelineTriggerOpen) return null;

  const handleExecute = () => {
    const globalParams: Record<string, string> = {};

    if (merchantReference.trim()) {
      globalParams.merchantReference = merchantReference.trim();
    }

    if (initialAmount.trim()) {
      const amountKeys = ["amount", "initialAmount"];
      for (const k of amountKeys) globalParams[k] = initialAmount.trim();
    }

    runFlow({ globalParams });
  };

  const isRunning = flowStatus === "running";
  const totalAgents = executionPlan.reduce((sum, g) => sum + g.length, 0);

  const inputStyle: React.CSSProperties = {
    background: "var(--bg-base)",
    border: "1px solid var(--purple-border)",
    borderRadius: "6px",
    padding: "8px 12px",
    fontSize: "12px",
    color: "var(--text-primary)",
    outline: "none",
    fontFamily: "var(--font-jetbrains), monospace",
    width: "100%",
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: "rgba(0,0,0,0.6)", backdropFilter: "blur(4px)" }}
      onClick={(e) => { if (e.target === e.currentTarget) setPipelineTriggerOpen(false); }}
    >
      <div
        className="w-[440px] max-h-[90vh] flex flex-col rounded-xl shadow-2xl overflow-hidden"
        style={{ background: "var(--bg-surface)", border: "1px solid var(--purple-border)", fontFamily: "var(--font-jetbrains), monospace" }}
      >
        {/* ── Header ── */}
        <div className="flex items-center px-5 py-4" style={{ borderBottom: "1px solid #836EF918" }}>
          <div className="flex items-center gap-2.5 flex-1">
            <div
              className="w-7 h-7 rounded-lg flex items-center justify-center"
              style={{ background: "var(--purple-glow)", border: "1px solid var(--purple-border)" }}
            >
              <Zap size={13} style={{ color: "var(--purple-primary)" }} />
            </div>
            <div>
              <p className="text-[13px] font-semibold" style={{ color: "var(--text-primary)" }}>Run Pipeline</p>
              <p className="text-[10px]" style={{ color: "var(--text-muted)" }}>
                {flowName} · {totalAgents} agent{totalAgents !== 1 ? "s" : ""} · {executionPlan.length} group{executionPlan.length !== 1 ? "s" : ""}
              </p>
            </div>
          </div>
          <button
            onClick={() => setPipelineTriggerOpen(false)}
            className="p-1 rounded transition-colors"
            style={{ color: "var(--text-muted)" }}
          >
            <X size={15} />
          </button>
        </div>

        {/* ── Execution plan preview ── */}
        <div className="px-5 py-4 overflow-y-auto max-h-48" style={{ borderBottom: "1px solid #836EF908" }}>
          <p className="text-[10px] font-semibold tracking-[1px] mb-3" style={{ color: "var(--text-muted)" }}>
            EXECUTION PLAN
          </p>
          <div className="flex flex-col gap-2">
            {executionPlan.map((group, gi) => {
              const isParallel = group.length > 1;
              return (
                <div key={gi}>
                  <div className="flex items-center gap-2 mb-1">
                    <span
                      className="text-[9px] px-1.5 py-0.5 rounded flex items-center gap-1"
                      style={{
                        background: isParallel ? "var(--purple-glow)" : "#5a587a15",
                        border: `1px solid ${isParallel ? "var(--purple-border)" : "#5a587a30"}`,
                        color: isParallel ? "var(--purple-primary)" : "var(--text-muted)",
                      }}
                    >
                      {isParallel && <Zap size={8} />}
                      G{gi + 1}{isParallel ? ` · ${group.length} parallel` : ""}
                    </span>
                  </div>
                  <div className="flex flex-col gap-1 ml-2">
                    {group.map((nodeId) => {
                      const node = nodes.find((n) => n.id === nodeId);
                      if (!node) return null;
                      return (
                        <div key={nodeId} className="flex items-center gap-2">
                          <CategoryDot category={node.data.category} />
                          <span className="text-[11px] truncate" style={{ color: "var(--text-primary)" }}>
                            {node.data.agentName}
                          </span>
                          <span className="text-[9px] flex-shrink-0" style={{ color: "var(--text-muted)" }}>
                            {node.data.sponsor}
                          </span>
                        </div>
                      );
                    })}
                  </div>
                  {gi < executionPlan.length - 1 && (
                    <div className="flex items-center justify-center my-1">
                      <ChevronRight size={10} style={{ color: "var(--text-muted)", transform: "rotate(90deg)" }} />
                    </div>
                  )}
                </div>
              );
            })}
            {executionPlan.length === 0 && (
              <p className="text-[12px]" style={{ color: "var(--text-muted)" }}>No agents on canvas yet.</p>
            )}
          </div>
        </div>

        {/* ── Global inputs ── */}
        <div className="px-5 py-4 space-y-3" style={{ borderBottom: "1px solid #836EF908" }}>
          <p className="text-[10px] font-semibold tracking-[1px]" style={{ color: "var(--text-muted)" }}>
            GLOBAL INPUTS <span className="normal-case font-normal">(optional — applied to all agents)</span>
          </p>

          {/* Merchant reference */}
          <div>
            <label className="flex items-center gap-1.5 text-[11px] mb-1.5" style={{ color: "var(--text-secondary)" }}>
              <Building2 size={11} />
              Merchant Reference
            </label>
            <input
              type="text"
              value={merchantReference}
              onChange={(e) => setMerchantReference(e.target.value)}
              placeholder="Optional internal merchant reference"
              style={inputStyle}
            />
          </div>

          {/* Amount */}
          <div>
            <label className="flex items-center gap-1.5 text-[11px] mb-1.5" style={{ color: "var(--text-secondary)" }}>
              <Coins size={11} />
              Initial Amount
            </label>
            <div className="flex gap-2">
              <input
                type="text"
                value={initialAmount}
                onChange={(e) => setInitialAmount(e.target.value)}
                placeholder="2500"
                style={{ ...inputStyle, flex: 1 }}
              />
              <select
                value={amountUnit}
                onChange={(e) => setAmountUnit(e.target.value)}
                style={{ ...inputStyle, width: "auto", padding: "8px" }}
              >
                <option value="INR">INR</option>
              </select>
            </div>
          </div>
        </div>

        {/* ── Output chaining notice ── */}
        <div className="px-5 py-3" style={{ borderBottom: "1px solid #836EF908" }}>
          <div className="flex items-center gap-2 text-[11px]" style={{ color: "var(--text-muted)" }}>
            <ArrowRight size={11} style={{ color: "var(--green-live)" }} className="flex-shrink-0" />
            <span>
              Each agent&apos;s output is automatically passed as context to downstream agents. Parallel groups share upstream data.
            </span>
          </div>
        </div>

        {/* ── Footer actions ── */}
        <div className="flex items-center justify-between px-5 py-4 gap-3">
          <button
            onClick={() => setPipelineTriggerOpen(false)}
            className="px-4 py-2 text-[12px] rounded-md transition-colors"
            style={{ color: "var(--text-secondary)", background: "var(--bg-base)", border: "1px solid var(--purple-border)" }}
          >
            Cancel
          </button>
          <button
            onClick={handleExecute}
            disabled={totalAgents === 0 || isRunning}
            className={cn(
              "flex items-center gap-2 px-5 py-2 text-[13px] font-semibold rounded-md transition-colors",
              (totalAgents === 0 || isRunning) ? "cursor-not-allowed opacity-40" : ""
            )}
            style={{
              background: (totalAgents === 0 || isRunning) ? "var(--bg-elevated)" : "var(--purple-primary)",
              color: (totalAgents === 0 || isRunning) ? "var(--text-muted)" : "var(--bg-base)",
            }}
          >
            <Play size={12} />
            Execute Pipeline
          </button>
        </div>
      </div>
    </div>
  );
}
