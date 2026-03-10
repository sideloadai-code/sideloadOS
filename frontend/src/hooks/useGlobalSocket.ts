"use client";

import { useEffect, useRef } from "react";
import { useWorkspaceStore } from "@/store/workspaceStore";

export function useGlobalSocket() {
    const addWorkspace = useWorkspaceStore((s) => s.addWorkspace);
    const wsRef = useRef<WebSocket | null>(null);

    useEffect(() => {
        const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
        const ws = new WebSocket(`${protocol}//${window.location.host}/api/ws`);
        wsRef.current = ws;

        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            if (data.event === "workspace_created") {
                addWorkspace(data.payload);
            }
        };

        ws.onclose = () => {
            // Reconnect logic could be added in future steps
        };

        return () => {
            ws.close();
        };
    }, [addWorkspace]);
}
