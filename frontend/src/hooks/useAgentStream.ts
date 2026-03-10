"use client";

import { useState, useCallback, useRef } from "react";

interface AgentStreamState {
    prompt: string;
    steps: string[];
    isStreaming: boolean;
    isPaused: boolean;
    draftArtifactId: string | null;
}

const initialState: AgentStreamState = {
    prompt: "",
    steps: [],
    isStreaming: false,
    isPaused: false,
    draftArtifactId: null,
};

export function useAgentStream() {
    const [state, setState] = useState<AgentStreamState>(initialState);
    const abortRef = useRef<AbortController | null>(null);

    const startExecution = useCallback(
        async (workspaceId: string, prompt: string, modelAlias: string) => {
            // Abort any in-flight stream
            abortRef.current?.abort();
            const controller = new AbortController();
            abortRef.current = controller;

            // Reset state and begin
            setState({
                prompt,
                steps: [],
                isStreaming: true,
                isPaused: false,
                draftArtifactId: null,
            });

            const threadId = crypto.randomUUID();

            try {
                const res = await fetch("/api/orchestrate", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({
                        workspace_id: workspaceId,
                        prompt,
                        thread_id: threadId,
                        model_alias: modelAlias,
                    }),
                    signal: controller.signal,
                });

                if (!res.ok || !res.body) {
                    console.error("[useAgentStream] Request failed:", res.status);
                    setState((prev) => ({ ...prev, isStreaming: false }));
                    return;
                }

                const reader = res.body.getReader();
                const decoder = new TextDecoder();
                let buffer = "";

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });

                    // Amendment 2: Cross-platform SSE delimiter (\n\n AND \r\n\r\n)
                    const parts = buffer.split(/\r?\n\r?\n/);
                    // Last element is either empty or an incomplete fragment — keep it
                    buffer = parts.pop() ?? "";

                    for (const part of parts) {
                        if (!part.trim()) continue;

                        const lines = part.split(/\r?\n/);
                        let eventType = "";
                        let dataStr = "";

                        for (const line of lines) {
                            if (line.startsWith("event:")) {
                                eventType = line.slice(6).trim();
                            } else if (line.startsWith("data:")) {
                                dataStr = line.slice(5).trim();
                            }
                        }

                        if (!dataStr) continue;

                        // Amendment 3: Safe JSON parsing — skip malformed frames
                        let json: Record<string, unknown>;
                        try {
                            json = JSON.parse(dataStr);
                        } catch (e) {
                            console.warn(
                                "[useAgentStream] Skipping malformed SSE frame:",
                                e
                            );
                            continue;
                        }

                        if (eventType === "status") {
                            const step = (json.step as string) ?? "";
                            if (step) {
                                setState((prev) => ({
                                    ...prev,
                                    steps: [...prev.steps, step],
                                }));
                            }
                        } else if (eventType === "paused") {
                            const artifactId = (json.artifact_id as string) ?? null;
                            setState((prev) => ({
                                ...prev,
                                isPaused: true,
                                draftArtifactId: artifactId,
                            }));
                        } else if (eventType === "error") {
                            const message = (json.message as string) ?? "Unknown error";
                            setState((prev) => ({
                                ...prev,
                                steps: [...prev.steps, `❌ Error: ${message}`],
                                isStreaming: false,
                            }));
                        } else if (eventType === "done") {
                            setState((prev) => ({
                                ...prev,
                                isStreaming: false,
                            }));
                        }
                    }
                }

                // Ensure we mark streaming as complete if loop exits
                setState((prev) => ({ ...prev, isStreaming: false }));
            } catch (err: unknown) {
                if (err instanceof DOMException && err.name === "AbortError") {
                    // Intentional abort — e.g., user started a new execution
                    return;
                }
                console.error("[useAgentStream] Stream error:", err);
                setState((prev) => ({ ...prev, isStreaming: false }));
            }
        },
        []
    );
    const clearPaused = useCallback(() => {
        setState((prev) => ({
            ...prev,
            isPaused: false,
            isStreaming: false,
        }));
    }, []);

    return {
        ...state,
        startExecution,
        clearPaused,
    };
}
