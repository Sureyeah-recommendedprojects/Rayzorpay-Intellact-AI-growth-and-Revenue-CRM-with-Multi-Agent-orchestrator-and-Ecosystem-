// ============================================================
// RayzorFlow — AMP (Agent Message Protocol) Utilities
// Standardized envelope for inter-agent communication.
// ============================================================

import type { AmpMessage, AmpResponse } from "@/types";
import { generateId } from "./utils";

export function buildAmpMessage(
  flowId: string,
  step: number,
  fromAgentId: string,
  toAgentId: string,
  payload: Record<string, unknown>
): AmpMessage {
  return {
    ampVersion: "1.0",
    flowId,
    step,
    fromAgent: { id: fromAgentId },
    toAgent: { id: toAgentId },
    payload,
    timestamp: new Date().toISOString(),
  };
}

export function buildAmpResponse(
  agentId: string,
  outputs: Record<string, unknown>,
  executionTimeMs: number,
  source: string,
  success = true,
  error?: string
): AmpResponse {
  return {
    success,
    agentId,
    outputs,
    error,
    metadata: {
      executionTimeMs,
      source,
      cached: false,
    },
  };
}

export function createFlowId(): string {
  return generateId("flow");
}
