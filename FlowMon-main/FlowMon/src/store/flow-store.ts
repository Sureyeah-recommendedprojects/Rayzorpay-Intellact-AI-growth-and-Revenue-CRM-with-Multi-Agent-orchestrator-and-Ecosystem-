// ============================================================
// RayzorFlow — Zustand Flow Store
// Parallel execution engine for governed commerce workflows.
// ============================================================

import { create } from "zustand";
import { type Node, type Edge, addEdge, applyNodeChanges, applyEdgeChanges } from "@xyflow/react";
import type {
  CanvasNodeData,
  ExecutionLogEntry,
  FlowExecutionStatus,
  AgentDefinition,
  NegotiationSession,
} from "@/types";
import { AGENT_REGISTRY } from "@/data/agent-registry";
import { buildExecutionPlan, getUpstreamNodeIds } from "@/lib/execution-engine";
import { generateId } from "@/lib/utils";

const AUTOSAVE_KEY = "rayzorflow-autosave";

export interface FlowStore {
  nodes: Node<CanvasNodeData>[];
  edges: Edge[];
  flowId: string;
  flowName: string;
  flowStatus: FlowExecutionStatus;
  executionLog: ExecutionLogEntry[];
  isLogVisible: boolean;
  selectedNodeId: string | null;
  inspectorOpen: boolean;
  isAgentXOpen: boolean;
  isChatOpen: boolean;
  abortController: AbortController | null;

  // ── Pipeline trigger modal ────────────────────────────────
  pipelineTriggerOpen: boolean;
  setPipelineTriggerOpen: (open: boolean) => void;

  // ── Publish modal ─────────────────────────────────────────
  isPublishModalOpen: boolean;
  setPublishModalOpen: (open: boolean) => void;

  // ── Negotiation ───────────────────────────────────────────
  negotiationSession: NegotiationSession | null;
  isNegotiating: boolean;
  runNegotiation: (nodeAId: string, nodeBId: string) => Promise<void>;
  clearNegotiation: () => void;

  onNodesChange: (changes: Parameters<typeof applyNodeChanges>[0]) => void;
  onEdgesChange: (changes: Parameters<typeof applyEdgeChanges>[0]) => void;
  onConnect: (connection: Parameters<typeof addEdge>[0]) => void;
  addAgentToCanvas: (agent: AgentDefinition, position?: { x: number; y: number }) => void;
  updateNodeParameter: (nodeId: string, paramName: string, value: string) => void;
  removeNode: (nodeId: string) => void;
  setFlowName: (name: string) => void;
  runFlow: (opts?: { globalParams?: Record<string, string> }) => Promise<void>;
  stopFlow: () => void;
  retryNode: (nodeId: string) => Promise<void>;
  clearLog: () => void;
  toggleLog: () => void;
  selectNode: (nodeId: string | null) => void;
  setInspectorOpen: (open: boolean) => void;
  setAgentXOpen: (open: boolean) => void;
  setChatOpen: (open: boolean) => void;
  loadDemoFlow: () => void;
  exportFlow: () => void;
  importFlow: (json: string) => void;
  clearCanvas: () => void;
  autoSave: () => void;
  loadAutoSave: () => void;
}

function addLog(
  state: Pick<FlowStore, "executionLog">,
  level: ExecutionLogEntry["level"],
  agentName: string,
  message: string,
  groupIndex?: number,
  data?: Record<string, unknown>
): ExecutionLogEntry[] {
  const entry: ExecutionLogEntry = {
    id: generateId("log"),
    timestamp: new Date(),
    agentName,
    message,
    level,
    groupIndex,
    data,
  };
  return [...state.executionLog, entry];
}

const DEMO_NODES: Node<CanvasNodeData>[] = [
  {
    id: "node-demo-1",
    type: "agentNode",
    position: { x: 80, y: 200 },
    data: {
      agentId: "payment-health-agent",
      agentName: "Payment Health Agent",
      category: "payments",
      iconKey: "Activity",
      sponsor: "Razorpay",
      label: "Payment Health Agent",
      parameterValues: { window: "7d" },
      executionStatus: "idle",
    },
  },
  {
    id: "node-demo-2",
    type: "agentNode",
    position: { x: 80, y: 400 },
    data: {
      agentId: "payment-link-agent",
      agentName: "Payment Link Agent",
      category: "payments",
      iconKey: "SendHorizontal",
      sponsor: "Razorpay",
      label: "Payment Link Agent",
      parameterValues: { customer: "Demo customer", amount: "2400" },
      executionStatus: "idle",
    },
  },
  {
    id: "node-demo-3",
    type: "agentNode",
    position: { x: 400, y: 300 },
    data: {
      agentId: "commerce-insights-agent",
      agentName: "Commerce Insights Agent",
      category: "insights",
      iconKey: "Sparkles",
      sponsor: "RayzorFlow",
      label: "Commerce Insights Agent",
      parameterValues: { goal: "improve payment recovery" },
      executionStatus: "idle",
    },
  },
  {
    id: "node-demo-4",
    type: "agentNode",
    position: { x: 720, y: 300 },
    data: {
      agentId: "order-agent",
      agentName: "Order Agent",
      category: "payments",
      iconKey: "ReceiptIndianRupee",
      sponsor: "Razorpay",
      label: "Order Agent",
      parameterValues: { amount: "2400", receipt: "demo_recovery" },
      executionStatus: "idle",
    },
  },
];

const DEMO_EDGES: Edge[] = [
  { id: "edge-demo-1", source: "node-demo-1", target: "node-demo-3", type: "smoothstep" },
  { id: "edge-demo-2", source: "node-demo-2", target: "node-demo-3", type: "smoothstep" },
  { id: "edge-demo-3", source: "node-demo-3", target: "node-demo-4", type: "smoothstep" },
];

export const useFlowStore = create<FlowStore>((set, get) => ({
  nodes: [],
  edges: [],
  flowId: generateId("flow"),
  flowName: "Untitled Flow",
  flowStatus: "idle",
  executionLog: [],
  isLogVisible: false,
  selectedNodeId: null,
  inspectorOpen: false,
  isAgentXOpen: false,
  isChatOpen: false,
  abortController: null,
  pipelineTriggerOpen: false,
  isPublishModalOpen: false,
  negotiationSession: null,
  isNegotiating: false,

  setPipelineTriggerOpen: (open) => set({ pipelineTriggerOpen: open }),
  setPublishModalOpen: (open) => set({ isPublishModalOpen: open }),

  onNodesChange: (changes) => {
    set((state) => ({ nodes: applyNodeChanges(changes, state.nodes) as Node<CanvasNodeData>[] }));
    get().autoSave();
  },

  onEdgesChange: (changes) => {
    set((state) => ({ edges: applyEdgeChanges(changes, state.edges) }));
    get().autoSave();
  },

  onConnect: (connection) => {
    set((state) => ({ edges: addEdge({ ...connection, type: "smoothstep" }, state.edges) }));
    get().autoSave();
  },

  addAgentToCanvas: (agent, position = { x: 200 + Math.random() * 300, y: 150 + Math.random() * 200 }) => {
    const nodeId = `node-${generateId()}`;
    const defaultParams: Record<string, string> = {};
    for (const param of agent.parameters) {
      defaultParams[param.name] = param.defaultValue;
    }
    const newNode: Node<CanvasNodeData> = {
      id: nodeId,
      type: "agentNode",
      position,
      data: {
        agentId: agent.id,
        agentName: agent.name,
        category: agent.category,
        iconKey: agent.iconKey,
        sponsor: agent.sponsor,
        label: agent.name,
        parameterValues: defaultParams,
        executionStatus: "idle",
      },
    };
    set((state) => ({ nodes: [...state.nodes, newNode] }));
    get().autoSave();
  },

  updateNodeParameter: (nodeId, paramName, value) => {
    set((state) => ({
      nodes: state.nodes.map((node) =>
        node.id === nodeId
          ? { ...node, data: { ...node.data, parameterValues: { ...node.data.parameterValues, [paramName]: value } } }
          : node
      ),
    }));
    get().autoSave();
  },

  removeNode: (nodeId) => {
    set((state) => ({
      nodes: state.nodes.filter((n) => n.id !== nodeId),
      edges: state.edges.filter((e) => e.source !== nodeId && e.target !== nodeId),
      selectedNodeId: state.selectedNodeId === nodeId ? null : state.selectedNodeId,
    }));
    get().autoSave();
  },

  setFlowName: (name) => set({ flowName: name }),

  // ── Parallel Execution Engine ──────────────────────────────
  runFlow: async (opts?: { globalParams?: Record<string, string> }) => {
    const state = get();
    if (state.flowStatus === "running") return;
    if (state.nodes.length === 0) {
      set({ isLogVisible: true });
      set((s) => ({ executionLog: addLog(s, "warn", "System", "Canvas is empty. Add agents to run a flow.") }));
      return;
    }

    const controller = new AbortController();
    const flowId = state.flowId;
    const globalParams = opts?.globalParams ?? {};

    set({
      flowStatus: "running",
      isLogVisible: true,
      abortController: controller,
      pipelineTriggerOpen: false,
      executionLog: addLog(state, "info", "System", `Starting flow "${state.flowName}" — ${state.nodes.length} agents`),
    });

    // Reset all nodes to idle
    set((s) => ({
      nodes: s.nodes.map((n) => ({
        ...n,
        data: { ...n.data, executionStatus: "idle" as const, executionResult: undefined, executionError: undefined },
      })) as Node<CanvasNodeData>[],
    }));

    // Build parallel execution plan
    const plan = buildExecutionPlan(
      state.nodes.map((n) => n.id),
      state.edges
    );

    set((s) => ({
      executionLog: addLog(
        s, "info", "System",
        `Execution plan: ${plan.length} group(s) — ${plan.map((g, i) => `G${i}[${g.length}]`).join(" → ")}`
      ),
    }));

    let hasError = false;
    const outputCache = new Map<string, Record<string, unknown>>();

    for (let groupIndex = 0; groupIndex < plan.length; groupIndex++) {
      if (get().flowStatus !== "running") break;

      const group = plan[groupIndex];
      const isParallel = group.length > 1;

      if (isParallel) {
        set((s) => ({
          executionLog: addLog(s, "info", "System", `⚡ Parallel group ${groupIndex + 1}: executing ${group.length} agents simultaneously`, groupIndex),
        }));
      }

      await Promise.all(
        group.map(async (nodeId) => {
          if (get().flowStatus !== "running") return;

          const currentState = get();
          const node = currentState.nodes.find((n) => n.id === nodeId);
          if (!node) return;

          const { agentId, agentName, parameterValues } = node.data;
          const agentDef = AGENT_REGISTRY.find((a) => a.id === agentId);

          // Merge: globalParams first, then node-specific params win
          const mergedParams: Record<string, string> = {
            ...globalParams,
            ...parameterValues,
          };

          // Collect upstream outputs
          const upstreamIds = getUpstreamNodeIds(nodeId, currentState.edges);
          const upstreamResult: Record<string, unknown> = {};
          for (const uid of upstreamIds) {
            const cached = outputCache.get(uid);
            if (cached) {
              Object.assign(upstreamResult, cached);
            }
          }

          // Mark as running
          set((s) => ({
            nodes: s.nodes.map((n) =>
              n.id === nodeId
                ? { ...n, data: { ...n.data, executionStatus: "running" as const, groupIndex } }
                : n
            ) as Node<CanvasNodeData>[],
            executionLog: addLog(s, "info", agentName, `Executing${isParallel ? ` (parallel G${groupIndex + 1})` : ""}…`, groupIndex),
          }));

          try {
            const response = await fetch("/api/agent-execute", {
              method: "POST",
              headers: { "Content-Type": "application/json" },
              body: JSON.stringify({
                agentId,
                agentName,
                parameterValues: mergedParams,
                upstreamResult: Object.keys(upstreamResult).length > 0 ? upstreamResult : undefined,
                endpointUrl: agentDef?.endpointUrl,
                flowId,
                stepNumber: groupIndex + 1,
              }),
              signal: controller.signal,
            });

            const data = await response.json();

            if (!response.ok || !data.success) {
              throw new Error(data.error || `HTTP ${response.status}`);
            }

            outputCache.set(nodeId, data.result ?? {});

            set((s) => ({
              nodes: s.nodes.map((n) =>
                n.id === nodeId
                  ? { ...n, data: { ...n.data, executionStatus: "success" as const, executionResult: data.result } }
                  : n
              ) as Node<CanvasNodeData>[],
              executionLog: addLog(s, "success", agentName, `Completed in ${data.executionTimeMs}ms`, groupIndex, data.result),
            }));
          } catch (error) {
            hasError = true;
            let errorMessage = error instanceof Error ? error.message : "Unknown error";
            if (error instanceof DOMException && error.name === "AbortError") {
              errorMessage = "Stopped by user";
            } else if (error instanceof DOMException && error.name === "TimeoutError") {
              errorMessage = "Timed out after 30s";
            }

            set((s) => ({
              nodes: s.nodes.map((n) =>
                n.id === nodeId
                  ? { ...n, data: { ...n.data, executionStatus: "error" as const, executionError: errorMessage } }
                  : n
              ) as Node<CanvasNodeData>[],
              executionLog: addLog(s, "error", agentName, `Failed: ${errorMessage}`, groupIndex),
            }));
          }
        })
      );
    }

    const finalStatus: FlowExecutionStatus = hasError ? "error" : "completed";
    set((s) => ({
      flowStatus: finalStatus,
      abortController: null,
      executionLog: addLog(
        s,
        hasError ? "error" : "success",
        "System",
        hasError ? "Flow completed with errors." : `Flow completed — ${plan.length} group(s) executed.`
      ),
    }));
  },

  stopFlow: () => {
    const { abortController } = get();
    if (abortController) abortController.abort();
    set((state) => ({
      flowStatus: "idle",
      abortController: null,
      nodes: state.nodes.map((n) => ({
        ...n,
        data: {
          ...n.data,
          executionStatus: n.data.executionStatus === "running" ? "idle" : n.data.executionStatus,
        },
      })) as Node<CanvasNodeData>[],
      executionLog: addLog(state, "warn", "System", "Flow stopped by user."),
    }));
  },

  retryNode: async (nodeId) => {
    const state = get();
    const node = state.nodes.find((n) => n.id === nodeId);
    if (!node) return;

    const { agentId, agentName, parameterValues } = node.data;
    const agentDef = AGENT_REGISTRY.find((a) => a.id === agentId);

    set((s) => ({
      nodes: s.nodes.map((n) =>
        n.id === nodeId
          ? { ...n, data: { ...n.data, executionStatus: "running" as const, executionError: undefined } }
          : n
      ) as Node<CanvasNodeData>[],
      isLogVisible: true,
      executionLog: addLog(s, "info", agentName, "Retrying…"),
    }));

    try {
      const response = await fetch("/api/agent-execute", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          agentId,
          agentName,
          parameterValues,
          endpointUrl: agentDef?.endpointUrl,
          flowId: state.flowId,
          stepNumber: 0,
        }),
      });
      const data = await response.json();
      if (!response.ok || !data.success) throw new Error(data.error || `HTTP ${response.status}`);

      set((s) => ({
        nodes: s.nodes.map((n) =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, executionStatus: "success" as const, executionResult: data.result } }
            : n
        ) as Node<CanvasNodeData>[],
        executionLog: addLog(s, "success", agentName, `Retry succeeded in ${data.executionTimeMs}ms`),
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Retry failed";
      set((s) => ({
        nodes: s.nodes.map((n) =>
          n.id === nodeId
            ? { ...n, data: { ...n.data, executionStatus: "error" as const, executionError: errorMessage } }
            : n
        ) as Node<CanvasNodeData>[],
        executionLog: addLog(s, "error", agentName, `Retry failed: ${errorMessage}`),
      }));
    }
  },

  clearLog: () => set({ executionLog: [] }),
  toggleLog: () => set((state) => ({ isLogVisible: !state.isLogVisible })),
  selectNode: (nodeId) => set({ selectedNodeId: nodeId, inspectorOpen: nodeId !== null }),
  setInspectorOpen: (open) => set({ inspectorOpen: open }),
  setAgentXOpen: (open) => set({ isAgentXOpen: open }),
  setChatOpen: (open) => set({ isChatOpen: open }),

  // ── Negotiation ───────────────────────────────────────────
  runNegotiation: async (nodeAId, nodeBId) => {
    const state = get();
    const nodeA = state.nodes.find((n) => n.id === nodeAId);
    const nodeB = state.nodes.find((n) => n.id === nodeBId);
    if (!nodeA || !nodeB) return;

    set({ isNegotiating: true, isLogVisible: true });
    set((s) => ({
      executionLog: addLog(s, "info", "Negotiation", `Starting negotiation between ${nodeA.data.agentName} and ${nodeB.data.agentName}`),
    }));

    try {
      const response = await fetch("/api/negotiate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          initiatorAgentId: nodeA.data.agentId,
          initiatorAgentName: nodeA.data.agentName,
          receiverAgentId: nodeB.data.agentId,
          receiverAgentName: nodeB.data.agentName,
          initiatorParams: nodeA.data.parameterValues,
          receiverParams: nodeB.data.parameterValues,
          negotiationGoal: "Optimize inter-agent parameter handoff for maximum flow efficiency",
          conversationHistory: [],
        }),
      });

      const result = await response.json();

      const session: NegotiationSession = {
        sessionId: generateId("neg"),
        participants: [nodeA.data.agentId, nodeB.data.agentId],
        messages: [
          {
            role: "user",
            agentId: nodeA.data.agentId,
            agentName: nodeA.data.agentName,
            content: result.agentAMessage || "Initiating negotiation.",
            timestamp: new Date(),
          },
          {
            role: "assistant",
            agentId: nodeB.data.agentId,
            agentName: nodeB.data.agentName,
            content: result.agentBMessage || "Acknowledged.",
            timestamp: new Date(),
          },
        ],
        status: result.agreed ? "resolved" : "active",
        resolution: result.summary,
      };

      set((s) => ({
        negotiationSession: session,
        isNegotiating: false,
        executionLog: addLog(
          s,
          result.agreed ? "success" : "warn",
          "Negotiation",
          result.agreed
            ? `Agreement reached (confidence: ${Math.round((result.confidence || 0) * 100)}%): ${result.summary}`
            : `Negotiation ongoing: ${result.summary}`
        ),
      }));
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : "Negotiation failed";
      set((s) => ({
        isNegotiating: false,
        executionLog: addLog(s, "error", "Negotiation", errorMessage),
      }));
    }
  },

  clearNegotiation: () => set({ negotiationSession: null }),

  loadDemoFlow: () => {
    set({
      nodes: DEMO_NODES,
      edges: DEMO_EDGES,
      flowName: "Payment Recovery Flow",
      flowId: generateId("flow"),
      flowStatus: "idle",
      executionLog: [],
      selectedNodeId: null,
    });
  },

  exportFlow: () => {
    const state = get();
    const data = {
      flowName: state.flowName,
      flowId: state.flowId,
      nodes: state.nodes,
      edges: state.edges,
      exportedAt: new Date().toISOString(),
    };
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `${state.flowName.replace(/\s+/g, "-").toLowerCase()}.rayzorflow.json`;
    link.click();
    URL.revokeObjectURL(url);
  },

  importFlow: (json: string) => {
    try {
      const parsed = JSON.parse(json);
      const flow = parsed.flow ?? parsed;
      set((s) => ({
        nodes: (flow.nodes ?? []) as Node<CanvasNodeData>[],
        edges: (flow.edges ?? []) as Edge[],
        flowName: flow.flowName ?? flow.name ?? "Imported Flow",
        flowId: generateId("flow"),
        flowStatus: "idle" as FlowExecutionStatus,
        selectedNodeId: null,
        inspectorOpen: false,
        executionLog: addLog(s, "success", "System", `Imported flow "${flow.flowName ?? "Imported"}" — ${(flow.nodes ?? []).length} agents.`),
        isLogVisible: true,
      }));
    } catch {
      set((s) => ({
        executionLog: addLog(s, "error", "System", "Import failed: invalid JSON file."),
        isLogVisible: true,
      }));
    }
  },

  clearCanvas: () => {
    set({
      nodes: [],
      edges: [],
      flowId: generateId("flow"),
      flowStatus: "idle",
      selectedNodeId: null,
      inspectorOpen: false,
      executionLog: [],
    });
  },

  autoSave: () => {
    if (typeof window === "undefined") return;
    const { nodes, edges, flowName } = get();
    localStorage.setItem(AUTOSAVE_KEY, JSON.stringify({ nodes, edges, flowName }));
  },

  loadAutoSave: () => {
    if (typeof window === "undefined") return;
    try {
      const raw = localStorage.getItem(AUTOSAVE_KEY);
      if (!raw) return;
      const data = JSON.parse(raw);
      if (data.nodes && data.nodes.length > 0) {
        set({
          nodes: data.nodes as Node<CanvasNodeData>[],
          edges: data.edges as Edge[],
          flowName: data.flowName ?? "Untitled Flow",
        });
      }
    } catch {
      // Ignore corrupted autosave
    }
  },
}));
