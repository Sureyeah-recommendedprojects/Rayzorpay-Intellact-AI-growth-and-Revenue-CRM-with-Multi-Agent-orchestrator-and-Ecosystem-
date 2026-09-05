// ============================================================
// RayzorFlow — Server Timeout Utility
// Caps fetch timeouts inside serverless functions.
// ============================================================

const DEFAULT_WALL_MS = 55000;

export function getServerTimeout(): number {
  const custom = process.env.FUNCTION_TIMEOUT_MS;
  if (custom) return parseInt(custom, 10);
  return DEFAULT_WALL_MS;
}

export function clampTimeout(preferredMs: number): number {
  const wall = getServerTimeout();
  return Math.max(Math.min(preferredMs, wall), 1000);
}

export function timeoutErrorMessage(agentId: string): string {
  return (
    `Agent "${agentId}" timed out. ` +
    `This operation requires longer execution time. ` +
    `If this persists, check the upstream API status.`
  );
}
