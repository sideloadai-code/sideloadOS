import { create } from "zustand";

export interface Workspace {
    id: string;
    name: string;
    created_at?: string;
}

interface WorkspaceState {
    workspaces: Workspace[];
    activeWorkspaceId: string | null;
    setWorkspaces: (workspaces: Workspace[]) => void;
    addWorkspace: (workspace: Workspace) => void;
    setActiveWorkspaceId: (id: string | null) => void;
}

export const useWorkspaceStore = create<WorkspaceState>((set) => ({
    workspaces: [],
    activeWorkspaceId: null,
    setWorkspaces: (workspaces) => set({ workspaces }),
    addWorkspace: (workspace) =>
        set((state) => ({ workspaces: [...state.workspaces, workspace] })),
    setActiveWorkspaceId: (id) => set({ activeWorkspaceId: id }),
}));
