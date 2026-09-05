"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps, type Node } from "@xyflow/react";
import {
  Cpu, Shuffle, Flame, BrainCircuit, ShieldHalf, Sigma,
  Orbit, PlugZap, Dna, Activity, Dices, Gauge, Telescope,
  CircuitBoard, Hash, CandlestickChart, Sliders, GitCommitHorizontal,
  Vault, Radar, Route, Hexagon, Binary, Fuel, Milestone, Triangle,
  Target, Blocks, Aperture, Swords, Satellite, Wrench, GlobeLock,
  Variable, Magnet, Biohazard, RadioTower, TrendingUpDown,
  Zap, Coins, SendHorizontal, FileSearch, Box, AlertCircle,
  type LucideProps,
} from "lucide-react";
import { cn } from "@/lib/utils";
import type { CanvasNodeData } from "@/types";
import { CATEGORY_COLORS } from "@/data/agent-registry";

type IconComponent = React.FC<LucideProps>;

const ICON_MAP: Record<string, IconComponent> = {
  Cpu, Shuffle, Flame, BrainCircuit, ShieldHalf, Sigma,
  Orbit, PlugZap, Dna, Activity, Dices, Gauge, Telescope,
  CircuitBoard, Hash, CandlestickChart, Sliders, GitCommitHorizontal,
  Vault, Radar, Route, Hexagon, Binary, Fuel, Milestone, Triangle,
  Target, Blocks, Aperture, Swords, Satellite, Wrench, GlobeLock,
  Variable, Magnet, Biohazard, RadioTower, TrendingUpDown,
  Zap, Coins, SendHorizontal, FileSearch,
} as Record<string, IconComponent>;

type AgentFlowNode = Node<CanvasNodeData>;

function AgentNode({ data, selected }: NodeProps<AgentFlowNode>) {
  const IconComp = (ICON_MAP[data.iconKey as string] ?? Box) as IconComponent;
  const categoryColor = CATEGORY_COLORS[data.category as string] ?? "#836EF9";
  const execStatus = (data.executionStatus as string) ?? "idle";
  const hasError = execStatus === "error" && data.executionError;

  const statusClass =
    execStatus === "running" ? "node-running" :
    execStatus === "error" ? "node-error" :
    execStatus === "success" ? "node-done" : "";

  const dotClass =
    execStatus === "running" ? "bg-[#836EF9] animate-pulse" :
    execStatus === "error" ? "bg-[#f87171]" :
    execStatus === "success" ? "bg-[#4ade80]" : "bg-[#5a587a]";

  return (
    <div
      className={cn(
        "w-[210px] cursor-pointer select-none rounded-[10px] transition-all duration-200",
        statusClass,
        selected && "ring-1 ring-[#836EF9]"
      )}
      style={{
        background: "var(--bg-node)",
        border: statusClass ? undefined : "1px solid var(--purple-border)",
        fontFamily: "var(--font-jetbrains), monospace",
      }}
    >
      {/* Accent bar */}
      <div className="h-[3px] rounded-t-[10px] w-full" style={{ backgroundColor: categoryColor }} />

      {/* Header */}
      <div className="flex items-center gap-2 px-3 py-2.5" style={{ borderBottom: "1px solid var(--purple-border)" }}>
        <div className="flex items-center justify-center w-7 h-7 rounded-md flex-shrink-0" style={{ backgroundColor: `${categoryColor}18` }}>
          <IconComp size={14} color={categoryColor} />
        </div>
        <span className="text-[12px] font-medium truncate flex-1" style={{ color: "var(--text-primary)" }}>
          {data.agentName as string}
        </span>
        <div className={cn("w-2 h-2 rounded-full flex-shrink-0", dotClass)} />
      </div>

      {/* Sponsor + parallel group badge */}
      <div className="px-3 py-1.5 flex items-center justify-between">
        <span className="text-[10px] tracking-[1px]" style={{ color: "var(--text-muted)" }}>
          {(data.sponsor as string).toUpperCase()}
        </span>
        {(data.groupIndex as number | undefined) !== undefined && execStatus === "running" && (
          <span className="text-[9px] font-semibold px-1.5 py-0.5 rounded" style={{ background: "var(--purple-glow)", color: "var(--purple-primary)" }}>
            G{((data.groupIndex as number) + 1)}
          </span>
        )}
      </div>

      {/* Error inline */}
      {hasError && (
        <div className="px-3 pb-2">
          <div className="flex items-center gap-1.5 rounded px-2 py-1" style={{ background: "#f8717115", border: "1px solid #f8717140" }}>
            <AlertCircle size={10} className="flex-shrink-0" style={{ color: "var(--red-error)" }} />
            <span className="text-[9px] truncate" style={{ color: "var(--red-error)" }}>
              {data.executionError as string}
            </span>
          </div>
        </div>
      )}

      {/* Handles */}
      <Handle type="target" position={Position.Left} className="!w-2.5 !h-2.5 !border !rounded-full transition-colors" style={{ background: "var(--text-muted)", borderColor: "var(--purple-border)" }} />
      <Handle type="source" position={Position.Right} className="!w-2.5 !h-2.5 !border !rounded-full transition-colors" style={{ background: "var(--text-muted)", borderColor: "var(--purple-border)" }} />
    </div>
  );
}

export default memo(AgentNode);
