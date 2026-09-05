// ============================================================
// RayzorFlow — Pipeline Store (Zustand)
// Named pipeline saves to localStorage.
// ============================================================

import { create } from "zustand";
import type { SavedPipeline } from "@/types";
import { generateId } from "@/lib/utils";

const STORAGE_KEY = "rayzorflow-pipelines";

function loadPipelines(): SavedPipeline[] {
  if (typeof window === "undefined") return [];
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return [];
    return JSON.parse(raw) as SavedPipeline[];
  } catch {
    return [];
  }
}

function persistPipelines(pipelines: SavedPipeline[]): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(STORAGE_KEY, JSON.stringify(pipelines));
}

interface PipelineStore {
  pipelines: SavedPipeline[];
  loadFromStorage: () => void;
  savePipeline: (name: string, nodes: unknown[], edges: unknown[]) => void;
  deletePipeline: (id: string) => void;
  getPipeline: (id: string) => SavedPipeline | undefined;
}

export const usePipelineStore = create<PipelineStore>((set, get) => ({
  pipelines: [],

  loadFromStorage: () => {
    set({ pipelines: loadPipelines() });
  },

  savePipeline: (name, nodes, edges) => {
    const now = new Date().toISOString();
    const pipeline: SavedPipeline = {
      id: generateId("pipe"),
      name,
      createdAt: now,
      updatedAt: now,
      nodes,
      edges,
    };
    const updated = [pipeline, ...get().pipelines];
    persistPipelines(updated);
    set({ pipelines: updated });
  },

  deletePipeline: (id) => {
    const updated = get().pipelines.filter((p) => p.id !== id);
    persistPipelines(updated);
    set({ pipelines: updated });
  },

  getPipeline: (id) => {
    return get().pipelines.find((p) => p.id === id);
  },
}));
