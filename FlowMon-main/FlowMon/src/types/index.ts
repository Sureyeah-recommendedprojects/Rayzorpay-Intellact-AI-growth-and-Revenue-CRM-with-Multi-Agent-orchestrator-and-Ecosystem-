// ============================================================
// RayzorFlow — Core Type Definitions
// ============================================================

export type AgentCategory =
  | "core"
  | "payments"
  | "wallets"
  | "risk"
  | "customer"
  | "insights";

export type AgentStatus = "live" | "stub" | "degraded";
export type NodeExecutionStatus = "idle" | "running" | "success" | "error" | "timeout";
export type FlowExecutionStatus = "idle" | "running" | "completed" | "error";

export interface AgentParameter {
  name: string;
  label: string;
  defaultValue: string;
  description: string;
  type: "text" | "number" | "boolean" | "select" | "textarea";
  options?: string[];
  required?: boolean;
}

export interface AgentDefinition {
  id: string;
  name: string;
  description: string;
  category: AgentCategory;
  sponsor: string;
  version: string;
  iconKey: string;
  parameters: AgentParameter[];
  tags: string[];
  endpointUrl?: string;
  status: AgentStatus;
  isCustom?: boolean;
}

export interface CanvasNodeData extends Record<string, unknown> {
  agentId: string;
  agentName: string;
  category: AgentCategory;
  iconKey: string;
  sponsor: string;
  parameterValues: Record<string, string>;
  executionStatus: NodeExecutionStatus;
  executionResult?: Record<string, unknown>;
  executionError?: string;
  label: string;
  groupIndex?: number;
}

export interface AmpMessage {
  ampVersion: "1.0";
  flowId: string;
  step: number;
  fromAgent: { id: string; ensName?: string };
  toAgent: { id: string; ensName?: string };
  payload: Record<string, unknown>;
  timestamp: string;
}

export interface AmpResponse {
  success: boolean;
  agentId: string;
  outputs: Record<string, unknown>;
  error?: string;
  metadata: {
    executionTimeMs: number;
    source: string;
    cached: boolean;
  };
}

export interface ExecutionLogEntry {
  id: string;
  timestamp: Date;
  agentName: string;
  message: string;
  level: "info" | "success" | "error" | "warn";
  groupIndex?: number;
  data?: Record<string, unknown>;
}

// ── Negotiation types ────────────────────────────────────────

export interface NegotiationMessage {
  role: "user" | "assistant";
  agentId: string;
  agentName: string;
  content: string;
  timestamp: Date;
}

export interface NegotiationSession {
  sessionId: string;
  participants: string[];
  messages: NegotiationMessage[];
  status: "active" | "resolved" | "failed";
  resolution?: string;
}

// ── Publish Agent types ──────────────────────────────────────

export interface PublishAgentFormValues {
  name: string;
  sponsor: string;
  category: AgentCategory;
  description: string;
  endpointUrl: string;
}

/** A group of nodeIds that can execute concurrently */
export type ExecutionGroup = string[];

export interface SavedPipeline {
  id: string;
  name: string;
  createdAt: string;
  updatedAt: string;
  nodes: unknown[];
  edges: unknown[];
}

export interface AgentExecuteRequest {
  agentId: string;
  agentName: string;
  parameterValues: Record<string, string>;
  upstreamResult?: Record<string, unknown>;
  endpointUrl?: string;
  flowId: string;
  stepNumber: number;
}

export interface AgentExecuteResponse {
  success: boolean;
  agentId: string;
  result?: Record<string, unknown>;
  error?: string;
  executionTimeMs: number;
  source: string;
}

export interface AgentXRequest {
  prompt: string;
}

export interface AgentXResponse {
  success: boolean;
  nodes: Array<{ agentId: string; position: { x: number; y: number } }>;
  edges: Array<{ source: string; target: string }>;
  error?: string;
}
