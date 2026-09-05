"use client";

import { useState, useCallback } from "react";
import {
  Cpu, Shuffle, Flame, BrainCircuit, ShieldHalf, Sigma,
  Orbit, PlugZap, Dna, Activity, Dices, Gauge, Telescope,
  CircuitBoard, Hash, CandlestickChart, Sliders, GitCommitHorizontal,
  Vault, Radar, Route, Hexagon, Binary, Fuel, Milestone, Triangle,
  Target, Blocks, Aperture, Swords, Satellite, Wrench, GlobeLock,
  Variable, Magnet, Biohazard, RadioTower, TrendingUpDown,
  Zap, Coins, SendHorizontal, FileSearch, Box, Search, ChevronRight,
} from "lucide-react";
import { useFlowStore } from "@/store/flow-store";
import { AGENT_REGISTRY, AGENT_CATEGORIES, CATEGORY_COLORS } from "@/data/agent-registry";
import type { AgentDefinition, AgentStatus } from "@/types";
import { cn } from "@/lib/utils";

const ICON_MAP: Record<string, React.ComponentType<{ size?: number; style?: React.CSSProperties }>> = {
  Cpu, Shuffle, Flame, BrainCircuit, ShieldHalf, Sigma,
  Orbit, PlugZap, Dna, Activity, Dices, Gauge, Telescope,
  CircuitBoard, Hash, CandlestickChart, Sliders, GitCommitHorizontal,
  Vault, Radar, Route, Hexagon, Binary, Fuel, Milestone, Triangle,
  Target, Blocks, Aperture, Swords, Satellite, Wrench, GlobeLock,
  Variable, Magnet, Biohazard, RadioTower, TrendingUpDown,
  Zap, Coins, SendHorizontal, FileSearch,
};

const STATUS_CFG: Record<AgentStatus, { label: string; dotColor: string; bgColor: string; borderColor: string; textColor: string }> = {
  live: { label: "● LIVE", dotColor: "", bgColor: "#4ade8015", borderColor: "#4ade8040", textColor: "#4ade80" },
  stub: { label: "● STUB", dotColor: "", bgColor: "#fbbf2415", borderColor: "#fbbf2440", textColor: "#fbbf24" },
  degraded: { label: "● DEG", dotColor: "", bgColor: "#f8717115", borderColor: "#f8717140", textColor: "#f87171" },
};

function AgentCard({ agent, onAdd }: { agent: AgentDefinition; onAdd: (agent: AgentDefinition) => void }) {
  const IconComponent = ICON_MAP[agent.iconKey] ?? Box;
  const categoryColor = CATEGORY_COLORS[agent.category] ?? "#836EF9";
  const badge = STATUS_CFG[agent.status];

  return (
    <div
      className="group flex items-center gap-2.5 px-3 py-2.5 cursor-pointer transition-colors hover:bg-[#1a1a2e]"
      style={{ borderBottom: "1px solid #836EF908", fontFamily: "var(--font-jetbrains), monospace" }}
      onClick={() => onAdd(agent)}
      draggable
      onDragStart={(e) => { e.dataTransfer.setData("agent", JSON.stringify(agent)); e.dataTransfer.effectAllowed = "move"; }}
    >
      <div className="flex items-center justify-center w-7 h-7 rounded-md flex-shrink-0" style={{ backgroundColor: `${categoryColor}15` }}>
        <IconComponent size={14} style={{ color: categoryColor }} />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-1.5 min-w-0">
          <div className="text-[12px] font-medium truncate" style={{ color: "var(--text-primary)" }}>{agent.name}</div>
          <span className="text-[10px] tracking-[1px] px-2 py-[1px] rounded flex-shrink-0" style={{ background: badge.bgColor, border: `1px solid ${badge.borderColor}`, color: badge.textColor }}>
            {badge.label}
          </span>
        </div>
        <div className="text-[10px] truncate" style={{ color: "var(--text-muted)" }}>{agent.sponsor}</div>
      </div>
      <ChevronRight size={12} className="opacity-0 group-hover:opacity-50 transition-opacity flex-shrink-0" style={{ color: "var(--text-muted)" }} />
    </div>
  );
}

export default function RegistrySidebar() {
  const { addAgentToCanvas } = useFlowStore();
  const [searchQuery, setSearchQuery] = useState("");
  const [activeCategory, setActiveCategory] = useState("all");

  const filterFn = useCallback((agent: AgentDefinition) => {
    const matchesSearch = searchQuery === "" || agent.name.toLowerCase().includes(searchQuery.toLowerCase()) || agent.sponsor.toLowerCase().includes(searchQuery.toLowerCase()) || agent.tags.some((tag) => tag.toLowerCase().includes(searchQuery.toLowerCase()));
    const matchesCategory = activeCategory === "all" || agent.category === activeCategory;
    return matchesSearch && matchesCategory;
  }, [searchQuery, activeCategory]);

  const filtered = AGENT_REGISTRY.filter(filterFn);
  const handleAddAgent = useCallback((agent: AgentDefinition) => addAgentToCanvas(agent), [addAgentToCanvas]);

  return (
    <div className="w-[240px] flex flex-col flex-shrink-0" style={{ background: "var(--bg-surface)", borderRight: "1px solid #836EF918", fontFamily: "var(--font-jetbrains), monospace" }}>
      {/* Header */}
      <div className="px-3 py-3 flex-shrink-0 flex items-center justify-between" style={{ borderBottom: "1px solid #836EF918" }}>
        <span className="text-[11px] font-semibold tracking-[1px]" style={{ color: "var(--text-secondary)" }}>AGENTS</span>
        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>{AGENT_REGISTRY.length}</span>
      </div>

      {/* Search */}
      <div className="px-3 py-2 flex-shrink-0" style={{ borderBottom: "1px solid #836EF918" }}>
        <div className="flex items-center gap-2 px-3 py-2 rounded-md" style={{ background: "var(--bg-base)", border: "1px solid var(--purple-border)" }}>
          <Search size={12} style={{ color: "var(--text-muted)" }} className="flex-shrink-0" />
          <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search agents…"
            className="bg-transparent text-[12px] outline-none w-full"
            style={{ color: "var(--text-primary)", fontFamily: "var(--font-jetbrains), monospace" }} />
        </div>
      </div>

      {/* Categories */}
      <div className="flex overflow-x-auto gap-1 px-2 py-1.5 flex-shrink-0" style={{ borderBottom: "1px solid #836EF918", scrollbarWidth: "none" }}>
        {AGENT_CATEGORIES.map((cat) => (
          <button key={cat.id} onClick={() => setActiveCategory(cat.id)}
            className={cn("px-2 py-0.5 text-[10px] rounded-md whitespace-nowrap transition-colors flex-shrink-0")}
            style={{
              background: activeCategory === cat.id ? "var(--purple-primary)" : "transparent",
              color: activeCategory === cat.id ? "var(--bg-base)" : "var(--text-muted)",
            }}>
            {cat.label}
          </button>
        ))}
      </div>

      {/* Agent list */}
      <div className="flex-1 overflow-y-auto">
        {filtered.length > 0 ? (
          filtered.map((agent) => <AgentCard key={agent.id} agent={agent} onAdd={handleAddAgent} />)
        ) : (
          <div className="flex items-center justify-center h-16 text-[12px] text-center px-4" style={{ color: "var(--text-muted)" }}>No agents match search.</div>
        )}
      </div>

      {/* Footer */}
      <div className="px-3 py-2 flex-shrink-0" style={{ borderTop: "1px solid #836EF918" }}>
        <span className="text-[10px]" style={{ color: "var(--text-muted)" }}>Click or drag to canvas</span>
      </div>
    </div>
  );
}
