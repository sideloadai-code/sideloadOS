import { create } from "zustand";

interface LayoutState {
    leftPaneWidth: number;
    centerPaneWidth: number;
    rightPaneWidth: number;
    activeArtifactId: string | null;
    openWorkbench: () => void;
    closeWorkbench: () => void;
    setActiveArtifactId: (id: string | null) => void;
}

export const useLayoutStore = create<LayoutState>((set) => ({
    leftPaneWidth: 20,
    centerPaneWidth: 80,
    rightPaneWidth: 0,
    activeArtifactId: null,
    openWorkbench: () =>
        set({ leftPaneWidth: 20, centerPaneWidth: 40, rightPaneWidth: 40 }),
    closeWorkbench: () =>
        set({ leftPaneWidth: 20, centerPaneWidth: 80, rightPaneWidth: 0, activeArtifactId: null }),
    setActiveArtifactId: (id) => set({ activeArtifactId: id }),
}));
