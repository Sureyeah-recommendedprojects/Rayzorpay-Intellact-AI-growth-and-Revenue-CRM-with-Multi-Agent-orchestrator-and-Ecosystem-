"use client";

// ============================================================
// RayzorFlow — Inspector Panel (Tabbed)
// Tabs: Params | Negotiate | Result (with TX Sign)
// ============================================================

import { useState } from "react";
import { X, RotateCw, Loader2, MessageSquare } from "lucide-react";
import { useFlowStore } from "@/store/flow-store";
import { AGENT_REGISTRY } from "@/data/agent-registry";

type InspectorTab = "params" | "negotiate" | "result";

export default function InspectorPanel() {
  const {
    nodes, edges, selectedNodeId, inspectorOpen, setInspectorOpen,
    updateNodeParameter, removeNode, retryNode, runFlow,
    negotiationSession, isNegotiating, runNegotiation, clearNegotiation,
  } = useFlowStore();

  const [activeTab, setActiveTab] = useState<InspectorTab>("params");

  if (!inspectorOpen || !selectedNodeId) return null;

  const node = nodes.find((n) => n.id === selectedNodeId);
  if (!node) return null;

  const { agentId, agentName, executionStatus, executionResult, executionError, parameterValues } = node.data;
  const agentDef = AGENT_REGISTRY.find((a) => a.id === agentId);
  const params = agentDef?.parameters ?? [];

  // Find connected neighbor nodes for negotiation
  const connectedNodeIds = edges
    .filter((e) => e.source === selectedNodeId || e.target === selectedNodeId)
    .map((e) => (e.source === selectedNodeId ? e.target : e.source));
  const connectedNodes = nodes.filter((n) => connectedNodeIds.includes(n.id));

  const inputStyle: React.CSSProperties = {
    background: "var(--bg-base)", border: "1px solid var(--purple-border)", borderRadius: "6px",
    padding: "8px 12px", fontSize: "13px", color: "var(--text-primary)", outline: "none",
    fontFamily: "var(--font-jetbrains), monospace", width: "100%",
  };

  const tabBtn = (tab: InspectorTab, label: string) => (
    <button
      key={tab}
      onClick={() => setActiveTab(tab)}
      className="flex-1 text-[10px] py-1.5 transition-colors rounded-md"
      style={{
        background: activeTab === tab ? "var(--purple-glow)" : "transparent",
        color: activeTab === tab ? "var(--purple-primary)" : "var(--text-muted)",
        border: activeTab === tab ? "1px solid var(--purple-border)" : "1px solid transparent",
      }}
    >
      {label}
    </button>
  );


  return (
    <div className="w-[300px] flex flex-col flex-shrink-0 overflow-hidden" style={{ background: "var(--bg-surface)", borderLeft: "1px solid #836EF918", fontFamily: "var(--font-jetbrains), monospace" }}>
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3" style={{ borderBottom: "1px solid #836EF918" }}>
        <span className="text-[13px] font-medium truncate" style={{ color: "var(--text-primary)" }}>{agentName as string}</span>
        <button onClick={() => setInspectorOpen(false)} style={{ color: "var(--text-muted)" }}><X size={14} /></button>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 px-3 py-2" style={{ borderBottom: "1px solid #836EF918" }}>
        {tabBtn("params", "PARAMS")}
        {tabBtn("negotiate", "NEGOTIATE")}
        {tabBtn("result", "RESULT")}
      </div>

      <div className="flex-1 overflow-y-auto">

        {/* ── Params Tab ── */}
        {activeTab === "params" && (
          <div className="px-4 py-3">
            <span className="text-[10px] font-semibold tracking-[1px]" style={{ color: "var(--text-muted)" }}>PARAMETERS</span>
            <div className="mt-3 space-y-3">
              {params.map((param) => (
                <div key={param.name}>
                  <label className="text-[11px] mb-1 block" style={{ color: "var(--text-secondary)" }}>{param.label}</label>
                  {param.type === "select" ? (
                    <select value={(parameterValues as Record<string, string>)[param.name] ?? param.defaultValue}
                      onChange={(e) => updateNodeParameter(selectedNodeId, param.name, e.target.value)} style={inputStyle}>
                      {param.options?.map((opt) => (<option key={opt} value={opt}>{opt}</option>))}
                    </select>
                  ) : param.type === "textarea" ? (
                    <textarea value={(parameterValues as Record<string, string>)[param.name] ?? param.defaultValue}
                      onChange={(e) => updateNodeParameter(selectedNodeId, param.name, e.target.value)} rows={3} style={{ ...inputStyle, resize: "none" }} />
                  ) : (
                    <input type={param.type === "number" ? "number" : "text"}
                      value={(parameterValues as Record<string, string>)[param.name] ?? param.defaultValue}
                      onChange={(e) => updateNodeParameter(selectedNodeId, param.name, e.target.value)}
                      style={inputStyle} placeholder={param.description} />
                  )}
                  <p className="text-[9px] mt-0.5" style={{ color: "var(--text-muted)" }}>{param.description}</p>
                </div>
              ))}
              {params.length === 0 && (
                <p className="text-[11px]" style={{ color: "var(--text-muted)" }}>No configurable parameters.</p>
              )}
            </div>
          </div>
        )}

        {/* ── Negotiate Tab ── */}
        {activeTab === "negotiate" && (
          <div className="px-4 py-3">
            <span className="text-[10px] font-semibold tracking-[1px]" style={{ color: "var(--text-muted)" }}>NEGOTIATE WITH</span>

            {connectedNodes.length === 0 ? (
              <div className="mt-3 text-[11px]" style={{ color: "var(--text-muted)" }}>
                <p>Connect this agent to another to enable negotiation.</p>
                <p className="mt-2 text-[10px] opacity-60">Negotiation uses AI to align parameters between connected agents for optimal handoff.</p>
              </div>
            ) : (
              <div className="mt-3 space-y-2">
                {connectedNodes.map((cn) => (
                  <button
                    key={cn.id}
                    onClick={() => runNegotiation(selectedNodeId, cn.id)}
                    disabled={isNegotiating}
                    className="w-full flex items-center gap-2 px-3 py-2.5 rounded-md text-[11px] transition-colors"
                    style={{
                      background: "var(--bg-base)",
                      border: "1px solid var(--purple-border)",
                      color: "var(--text-secondary)",
                      opacity: isNegotiating ? 0.5 : 1,
                    }}
                  >
                    {isNegotiating ? <Loader2 size={12} className="animate-spin" /> : <MessageSquare size={12} />}
                    <span className="truncate">{cn.data.agentName as string}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Negotiation result */}
            {negotiationSession && (
              <div className="mt-4 space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] font-semibold tracking-[1px]" style={{ color: "var(--text-muted)" }}>SESSION</span>
                  <button onClick={clearNegotiation} className="text-[9px]" style={{ color: "var(--purple-primary)" }}>Clear</button>
                </div>

                <div
                  className="text-[10px] px-2 py-1.5 rounded"
                  style={{
                    background: negotiationSession.status === "resolved" ? "#4ade8010" : "#fbbf2410",
                    border: `1px solid ${negotiationSession.status === "resolved" ? "#4ade8030" : "#fbbf2430"}`,
                    color: negotiationSession.status === "resolved" ? "var(--green-live)" : "#fbbf24",
                  }}
                >
                  {negotiationSession.status === "resolved" ? "✓ Agreement reached" : "⟳ Ongoing"}
                </div>

                {negotiationSession.messages.map((msg, i) => (
                  <div key={i} className="rounded-md px-3 py-2" style={{ background: "var(--bg-base)", border: "1px solid #836EF918" }}>
                    <p className="text-[10px] font-medium mb-1" style={{ color: "var(--text-code)" }}>{msg.agentName}</p>
                    <p className="text-[10px]" style={{ color: "var(--text-secondary)" }}>{msg.content}</p>
                  </div>
                ))}

                {negotiationSession.resolution && (
                  <div className="rounded-md px-3 py-2" style={{ background: "var(--purple-glow)", border: "1px solid var(--purple-border)" }}>
                    <p className="text-[10px] font-medium mb-1" style={{ color: "var(--purple-primary)" }}>Resolution</p>
                    <p className="text-[10px]" style={{ color: "var(--text-secondary)" }}>{negotiationSession.resolution}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* ── Result Tab ── */}
        {activeTab === "result" && (
          <div className="px-4 py-3">
            {!executionResult && !executionError ? (
              <div className="text-[11px] py-4 text-center" style={{ color: "var(--text-muted)" }}>
                Run the flow to see results here.
              </div>
            ) : (
              <>
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-semibold tracking-[1px]" style={{ color: "var(--text-muted)" }}>RESULT</span>
                  {(executionStatus === "error" || executionStatus === "timeout") && (
                    <button onClick={() => retryNode(selectedNodeId)} className="flex items-center gap-1 text-[10px] transition-colors" style={{ color: "var(--purple-primary)" }}>
                      <RotateCw size={10} /> Retry
                    </button>
                  )}
                </div>

                {executionError && (
                  <div className="rounded-md p-2 mb-2" style={{ background: "#f8717115", border: "1px solid #f8717140" }}>
                    <p className="text-[10px]" style={{ color: "var(--red-error)" }}>{executionError as string}</p>
                  </div>
                )}

                {executionResult && (
                  <>
                    {/* Raw JSON result */}
                    <pre
                      className="rounded-md p-2 text-[10px] overflow-auto max-h-48 whitespace-pre-wrap mt-2"
                      style={{ background: "var(--bg-base)", border: "1px solid var(--purple-border)", color: "var(--text-code)" }}
                    >
                      {JSON.stringify(executionResult, null, 2)}
                    </pre>
                  </>
                )}
              </>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="px-4 py-3 flex-shrink-0 space-y-2" style={{ borderTop: "1px solid #836EF918" }}>
        <button
          onClick={() => runFlow()}
          disabled={nodes.length === 0}
          className="w-full text-[11px] font-semibold py-2 rounded-md transition-colors disabled:opacity-30"
          style={{ background: "var(--purple-primary)", color: "var(--bg-base)" }}
        >
          ▸ Quick Run
        </button>
        <button onClick={() => removeNode(selectedNodeId)} className="w-full text-[11px] py-1.5 rounded-md transition-colors" style={{ color: "var(--red-error)", border: "1px solid #f8717140" }}>
          Remove Agent
        </button>
      </div>
    </div>
  );
}
