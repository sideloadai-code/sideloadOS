"use client";

import { useEffect, useState } from "react";
import { Loader2, X, CheckCircle } from "lucide-react";
import Editor from "@monaco-editor/react";

import { useLayoutStore } from "@/store/layoutStore";
import { Button } from "@/components/ui/button";
import { RichTextEditor } from "@/components/RichTextEditor";

// ── Types ──────────────────────────────────────────────────────────────────

interface ArtifactData {
    id: string;
    title: string;
    content_type: string;
    content: string;
    human_edits: string | null;
    status: string;
    thread_id: string | null;
}

// ── Workbench Component ────────────────────────────────────────────────────

interface WorkbenchProps {
    onApproved?: () => void;
}

export function Workbench({ onApproved }: WorkbenchProps) {
    const activeArtifactId = useLayoutStore((s) => s.activeArtifactId);
    const closeWorkbench = useLayoutStore((s) => s.closeWorkbench);

    const [artifact, setArtifact] = useState<ArtifactData | null>(null);
    const [loading, setLoading] = useState(false);
    const [content, setContent] = useState("");
    const [approving, setApproving] = useState(false);

    // Fetch artifact when activeArtifactId changes
    useEffect(() => {
        if (!activeArtifactId) {
            setArtifact(null);
            setContent("");
            return;
        }

        let cancelled = false;
        setLoading(true);

        fetch(`/api/artifacts/${activeArtifactId}`, {
            headers: { "Content-Type": "application/json" },
        })
            .then((res) => {
                if (!res.ok) throw new Error(`HTTP ${res.status}`);
                return res.json();
            })
            .then((data: ArtifactData) => {
                if (cancelled) return;
                setArtifact(data);
                setContent(data.human_edits ?? data.content);
            })
            .catch((err) => {
                if (cancelled) return;
                console.error("[Workbench] Failed to fetch artifact:", err);
            })
            .finally(() => {
                if (!cancelled) setLoading(false);
            });

        return () => {
            cancelled = true;
        };
    }, [activeArtifactId]);

    // Approve & Execute handler
    const handleApprove = async () => {
        if (!activeArtifactId) return;
        setApproving(true);

        try {
            const res = await fetch(`/api/artifacts/${activeArtifactId}/approve`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ human_edits: content }),
            });

            if (!res.ok) {
                console.error("[Workbench] Approve failed:", res.status);
                return;
            }

            // Update artifact status locally to show "approved" state
            setArtifact((prev) =>
                prev ? { ...prev, status: "approved" } : prev
            );

            // Notify parent to clear the paused state
            onApproved?.();

            // Brief delay so user sees the "Approved" state, then close
            setTimeout(() => {
                closeWorkbench();
            }, 1200);
        } catch (err) {
            console.error("[Workbench] Approve error:", err);
        } finally {
            setApproving(false);
        }
    };

    // ── Empty state (no artifact selected) ─────────────────────────────────

    if (!activeArtifactId) {
        return (
            <div className="flex h-full flex-col border-l border-white/10 bg-zinc-900/40">
                <div className="flex flex-1 items-center justify-center p-6">
                    <p className="text-sm text-zinc-600">
                        No artifact selected
                    </p>
                </div>
            </div>
        );
    }

    // ── Main workbench ─────────────────────────────────────────────────────

    return (
        <div className="flex h-full flex-col border-l border-white/10 bg-zinc-900/40">
            {/* Sticky Header */}
            <div className="flex items-center justify-between border-b border-white/10 px-4 py-3">
                <h3 className="text-sm font-medium text-zinc-300 truncate">
                    {loading ? "Loading..." : artifact?.title ?? "Artifact"}
                </h3>

                <div className="flex items-center gap-2">
                    {/* Approve & Execute button */}
                    {artifact && artifact.status !== "approved" && (
                        <Button
                            size="sm"
                            onClick={handleApprove}
                            disabled={approving || loading}
                            className="gap-1.5 bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40 transition-colors"
                        >
                            {approving ? (
                                <Loader2 className="h-3.5 w-3.5 animate-spin" />
                            ) : (
                                <CheckCircle className="h-3.5 w-3.5" />
                            )}
                            Approve & Execute
                        </Button>
                    )}
                    {artifact && artifact.status === "approved" && (
                        <span className="flex items-center gap-1.5 rounded-md bg-emerald-600/20 border border-emerald-500/40 px-3 py-1.5 text-sm font-medium text-emerald-400">
                            <CheckCircle className="h-3.5 w-3.5" />
                            Approved ✓
                        </span>
                    )}

                    {/* Close button */}
                    <button
                        onClick={closeWorkbench}
                        className="rounded p-1 text-zinc-500 hover:bg-zinc-800 hover:text-zinc-300 transition-colors"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>
            </div>

            {/* Body */}
            {loading ? (
                <div className="flex flex-1 items-center justify-center">
                    <Loader2 className="h-6 w-6 animate-spin text-zinc-500" />
                </div>
            ) : artifact ? (
                // Conditional editor rendering based on content_type
                artifact.content_type === "code" || artifact.content_type === "json" ? (
                    // Amendment 3: Monaco wrapped in flex-1 min-h-0 relative
                    <div className="flex-1 min-h-0 relative">
                        <Editor
                            theme="vs-dark"
                            language={artifact.content_type === "json" ? "json" : "javascript"}
                            value={content}
                            onChange={(val) => setContent(val ?? "")}
                            options={{
                                minimap: { enabled: false },
                                fontSize: 14,
                                lineNumbers: "on",
                                scrollBeyondLastLine: false,
                                wordWrap: "on",
                                padding: { top: 12 },
                            }}
                        />
                    </div>
                ) : (
                    // Amendment 1: RichTextEditor is a separate component with safe hook lifecycle
                    <RichTextEditor
                        initialContent={content}
                        onChange={setContent}
                    />
                )
            ) : (
                <div className="flex flex-1 items-center justify-center p-6">
                    <p className="text-sm text-zinc-600">
                        Failed to load artifact
                    </p>
                </div>
            )}
        </div>
    );
}
