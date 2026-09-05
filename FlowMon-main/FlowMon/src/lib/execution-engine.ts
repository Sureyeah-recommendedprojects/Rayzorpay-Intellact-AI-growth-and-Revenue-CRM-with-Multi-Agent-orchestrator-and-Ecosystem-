// ============================================================
// RayzorFlow — Parallel Execution Engine
// Kahn's algorithm for topological sort → parallel groups.
// Runs independent commerce operations in parallel.
// ============================================================

import type { ExecutionGroup } from "@/types";

/**
 * Build a parallel execution plan using Kahn's algorithm.
 * Returns ordered groups of nodeIds that can run concurrently.
 *
 * Nodes with in-degree 0 form the first parallel group.
 * After processing, newly-unblocked nodes form the next group.
 */
export function buildExecutionPlan(
  nodeIds: string[],
  edges: Array<{ source: string; target: string }>
): ExecutionGroup[] {
  const inDegreeMap = new Map<string, number>();
  const adjacencyList = new Map<string, string[]>();

  // Initialize
  for (const id of nodeIds) {
    inDegreeMap.set(id, 0);
    adjacencyList.set(id, []);
  }

  // Build graph
  for (const edge of edges) {
    const targets = adjacencyList.get(edge.source);
    if (targets) {
      targets.push(edge.target);
    }
    const current = inDegreeMap.get(edge.target);
    if (current !== undefined) {
      inDegreeMap.set(edge.target, current + 1);
    }
  }

  const groups: ExecutionGroup[] = [];
  let remaining = new Set(nodeIds);

  while (remaining.size > 0) {
    // Find all nodes with in-degree 0
    const currentGroup: string[] = [];
    for (const id of remaining) {
      if ((inDegreeMap.get(id) ?? 0) === 0) {
        currentGroup.push(id);
      }
    }

    // If no nodes have in-degree 0, we have a cycle — break to avoid infinite loop
    if (currentGroup.length === 0) {
      // Add remaining nodes as a final group (best effort)
      groups.push([...remaining]);
      break;
    }

    groups.push(currentGroup);

    // Remove processed nodes and decrement in-degrees
    for (const id of currentGroup) {
      remaining.delete(id);
      const neighbors = adjacencyList.get(id) ?? [];
      for (const neighbor of neighbors) {
        const deg = inDegreeMap.get(neighbor);
        if (deg !== undefined) {
          inDegreeMap.set(neighbor, deg - 1);
        }
      }
    }

    // Rebuild remaining set (already done via delete above)
    remaining = new Set(remaining);
  }

  return groups;
}

/**
 * Get upstream node IDs for a given node.
 */
export function getUpstreamNodeIds(
  nodeId: string,
  edges: Array<{ source: string; target: string }>
): string[] {
  return edges
    .filter((e) => e.target === nodeId)
    .map((e) => e.source);
}

/**
 * Flat topological sort (for sequential fallback).
 */
export function buildTopologicalOrder(
  nodeIds: string[],
  edges: Array<{ source: string; target: string }>
): string[] {
  const plan = buildExecutionPlan(nodeIds, edges);
  return plan.flat();
}
