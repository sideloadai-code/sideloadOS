"use client";

import { useEffect, useState, useCallback } from "react";
import {
  Group,
  Panel,
  Separator,
} from "react-resizable-panels";
import {
  Plus,
  Folder,
  ChevronRight,
  ChevronDown,
  Settings,
  SendHorizontal,
} from "lucide-react";

import { useLayoutStore } from "@/store/layoutStore";
import { useWorkspaceStore } from "@/store/workspaceStore";
import { useGlobalSocket } from "@/hooks/useGlobalSocket";
import { useAgentStream } from "@/hooks/useAgentStream";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { WalkthroughCard } from "@/components/WalkthroughCard";
import { Workbench } from "@/components/Workbench";
import { SettingsModal } from "@/components/SettingsModal";

// ── Types ──────────────────────────────────────────────────────────────────

interface AvailableModel {
  model_alias: string;
  provider: string;
  source: string;
  size: string | null;
}

// ── Command Center (Pane 1) ────────────────────────────────────────────────

interface CommandCenterProps {
  fetchModels: () => void;
}

function CommandCenter({ fetchModels }: CommandCenterProps) {
  const workspaces = useWorkspaceStore((s) => s.workspaces);
  const setWorkspaces = useWorkspaceStore((s) => s.setWorkspaces);
  const activeWorkspaceId = useWorkspaceStore((s) => s.activeWorkspaceId);
  const setActiveWorkspaceId = useWorkspaceStore(
    (s) => s.setActiveWorkspaceId
  );
  const [expanded, setExpanded] = useState<Record<string, boolean>>({});
  const [settingsOpen, setSettingsOpen] = useState(false);

  const toggle = (name: string) =>
    setExpanded((prev) => ({ ...prev, [name]: !prev[name] }));

  // Fetch existing workspaces on mount
  useEffect(() => {
    fetch("/api/workspaces/")
      .then((res) => (res.ok ? res.json() : []))
      .then((data) => setWorkspaces(data))
      .catch(() => { });
  }, [setWorkspaces]);

  return (
    <div className="flex h-full flex-col border-r border-white/10 bg-zinc-900/60">
      {/* Header */}
      <div className="p-3">
        <Button
          variant="outline"
          className="w-full justify-start gap-2 border-white/10 bg-transparent text-zinc-300 hover:bg-zinc-800 hover:text-zinc-100"
        >
          <Plus className="h-4 w-4" />
          Start conversation
        </Button>
      </div>

      {/* Workspace tree */}
      <ScrollArea className="flex-1 px-2">
        <div className="space-y-1 py-2">
          {workspaces.map((ws) => {
            const isActive = activeWorkspaceId === ws.id;
            return (
              <div key={ws.id}>
                <button
                  onClick={() => {
                    setActiveWorkspaceId(ws.id);
                    toggle(ws.name);
                  }}
                  className={`flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm transition-colors ${isActive
                    ? "bg-zinc-800 text-zinc-100 ring-1 ring-zinc-700"
                    : "text-zinc-400 hover:bg-zinc-800 hover:text-zinc-200"
                    }`}
                >
                  {expanded[ws.name] ? (
                    <ChevronDown className="h-3.5 w-3.5 shrink-0" />
                  ) : (
                    <ChevronRight className="h-3.5 w-3.5 shrink-0" />
                  )}
                  <Folder
                    className={`h-4 w-4 shrink-0 ${isActive ? "text-emerald-500" : "text-zinc-500"
                      }`}
                  />
                  <span className="truncate">{ws.name}</span>
                </button>
              </div>
            );
          })}
        </div>
      </ScrollArea>

      {/* Settings */}
      <div className="border-t border-white/10 p-3">
        <button
          onClick={() => setSettingsOpen(true)}
          className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-sm text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
        >
          <Settings className="h-4 w-4" />
          <span>Settings</span>
        </button>
      </div>

      {/* Settings Modal */}
      <SettingsModal
        open={settingsOpen}
        onOpenChange={setSettingsOpen}
        onProviderAdded={fetchModels}
      />
    </div>
  );
}

// ── Omnibar (bottom of Pane 2) ─────────────────────────────────────────────

interface OmnibarProps {
  onSend: (prompt: string, modelAlias: string) => void;
  disabled: boolean;
  models: AvailableModel[];
  modelsLoading: boolean;
}

function Omnibar({ onSend, disabled, models, modelsLoading }: OmnibarProps) {
  const [inputValue, setInputValue] = useState("");
  const [selectedModel, setSelectedModel] = useState("");

  const canSend = !disabled && !!inputValue.trim() && !!selectedModel;

  // Amendment 5: preventDefault on form submit to avoid page reload
  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const trimmed = inputValue.trim();
    if (!trimmed || !selectedModel || disabled) return;
    onSend(trimmed, selectedModel);
    setInputValue("");
  };

  return (
    <div className="absolute bottom-0 left-0 right-0 border-t border-white/10 bg-zinc-900/80 backdrop-blur-sm p-4">
      {/* Dropdown row */}
      <div className="mb-3 flex items-center gap-3">
        {/* Model dropdown — dynamically populated */}
        <Select value={selectedModel} onValueChange={(v) => setSelectedModel(v ?? "")}>
          <SelectTrigger className="w-[200px] border-white/10 bg-zinc-800/80 text-zinc-300 text-sm">
            <SelectValue
              placeholder={
                modelsLoading
                  ? "Loading models..."
                  : models.length > 0
                    ? "Select model"
                    : "No models available"
              }
            />
          </SelectTrigger>
          <SelectContent className="border-white/10 bg-zinc-800">
            {models.map((m) => (
              <SelectItem
                key={m.model_alias}
                value={m.model_alias}
                className="text-zinc-300 focus:bg-zinc-700 focus:text-zinc-100"
              >
                {m.model_alias}
                {m.size && (
                  <span className="ml-2 text-xs text-zinc-500">
                    ({m.size})
                  </span>
                )}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* Agent dropdown — static placeholder */}
        <Select defaultValue="orchestrator">
          <SelectTrigger className="w-[200px] border-white/10 bg-zinc-800/80 text-zinc-300 text-sm">
            <SelectValue placeholder="Select agent" />
          </SelectTrigger>
          <SelectContent className="border-white/10 bg-zinc-800">
            <SelectItem
              value="orchestrator"
              className="text-zinc-300 focus:bg-zinc-700 focus:text-zinc-100"
            >
              System Orchestrator
            </SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Input row */}
      <form onSubmit={handleSubmit} className="flex items-center gap-2">
        <Input
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          disabled={disabled}
          placeholder={
            disabled
              ? "Select a workspace to begin..."
              : !selectedModel
                ? "Select a model above to begin..."
                : "What would you like to do?"
          }
          className="flex-1 border-white/10 bg-zinc-800/60 text-zinc-200 placeholder:text-zinc-600 disabled:opacity-50 disabled:cursor-not-allowed"
        />
        <Button
          type="submit"
          size="icon"
          disabled={!canSend}
          className="shrink-0 bg-zinc-700 hover:bg-zinc-600 text-zinc-200 disabled:opacity-40"
        >
          <SendHorizontal className="h-4 w-4" />
        </Button>
      </form>
    </div>
  );
}

// ── Action Stream (Pane 2) ─────────────────────────────────────────────────

interface ActionStreamProps {
  onSend: (prompt: string, modelAlias: string) => void;
  disabled: boolean;
  prompt: string;
  steps: string[];
  isStreaming: boolean;
  isPaused: boolean;
  draftArtifactId: string | null;
  models: AvailableModel[];
  modelsLoading: boolean;
}

function ActionStream({
  onSend,
  disabled,
  prompt,
  steps,
  isStreaming,
  isPaused,
  draftArtifactId,
  models,
  modelsLoading,
}: ActionStreamProps) {
  return (
    <div className="relative flex h-full flex-col bg-zinc-950">
      {/* Scrollable content area — pb-40 prevents Omnibar obscurity */}
      <ScrollArea className="flex-1">
        <div className="p-6 pb-40">
          {prompt ? (
            <WalkthroughCard
              prompt={prompt}
              steps={steps}
              isStreaming={isStreaming}
              isPaused={isPaused}
              draftArtifactId={draftArtifactId}
            />
          ) : (
            <div className="flex h-full min-h-[60vh] items-center justify-center">
              <div className="text-center">
                <h2 className="text-lg font-medium text-zinc-500">
                  SideloadOS
                </h2>
                <p className="mt-1 text-sm text-zinc-600">
                  Start a conversation to begin
                </p>
              </div>
            </div>
          )}
        </div>
      </ScrollArea>

      {/* Omnibar */}
      <Omnibar
        onSend={onSend}
        disabled={disabled}
        models={models}
        modelsLoading={modelsLoading}
      />
    </div>
  );
}

// ── Artifact Workbench (Pane 3) is now <Workbench /> from components/ ───────

// ── Main Page ──────────────────────────────────────────────────────────────

export default function Home() {
  useGlobalSocket();

  const rightPaneWidth = useLayoutStore((s) => s.rightPaneWidth);
  const isWorkbenchOpen = rightPaneWidth > 0;

  const activeWorkspaceId = useWorkspaceStore((s) => s.activeWorkspaceId);
  const { prompt, steps, isStreaming, isPaused, draftArtifactId, startExecution, clearPaused } =
    useAgentStream();

  // ── Lifted model state (shared between Omnibar and SettingsModal) ─────
  const [models, setModels] = useState<AvailableModel[]>([]);
  const [modelsLoading, setModelsLoading] = useState(true);

  const fetchModels = useCallback(async () => {
    setModelsLoading(true);
    try {
      const res = await fetch("/api/models/available");
      if (res.ok) {
        const data: AvailableModel[] = await res.json();
        setModels(data);
      }
    } catch {
      // Backend unreachable — graceful fallback
    } finally {
      setModelsLoading(false);
    }
  }, []);

  // Fetch models on mount
  useEffect(() => {
    fetchModels();
  }, [fetchModels]);

  const handleSend = useCallback(
    (userPrompt: string, modelAlias: string) => {
      if (!activeWorkspaceId) return;
      startExecution(activeWorkspaceId, userPrompt, modelAlias);
    },
    [activeWorkspaceId, startExecution]
  );

  return (
    <Group
      orientation="horizontal"
      className="h-full w-full"
    >
      {/* Pane 1: Command Center */}
      <Panel id="sidebar" defaultSize="20%" minSize="15%" maxSize="30%">
        <CommandCenter fetchModels={fetchModels} />
      </Panel>

      <Separator />

      {/* Pane 2: Action Stream */}
      <Panel id="stream" defaultSize="80%" minSize="30%">
        <ActionStream
          onSend={handleSend}
          disabled={!activeWorkspaceId}
          prompt={prompt}
          steps={steps}
          isStreaming={isStreaming}
          isPaused={isPaused}
          draftArtifactId={draftArtifactId}
          models={models}
          modelsLoading={modelsLoading}
        />
      </Panel>

      {/* Pane 3: Artifact Workbench — conditionally rendered */}
      {isWorkbenchOpen && (
        <>
          <Separator />
          <Panel id="workbench" defaultSize="40%" minSize="20%" maxSize="60%">
            <Workbench onApproved={clearPaused} />
          </Panel>
        </>
      )}
    </Group>
  );
}
