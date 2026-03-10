\# UI/UX MANIFESTO: The 3-Pane Layout



The entire application runs on a single page using Zustand state to manipulate three panes via `react-resizable-panels`.



1\. \*\*Pane 1 (Left - Default 20%): 'Command Center'\*\*

&nbsp;  - Zustand-driven tree-view of Workspaces and nested Tasks using `lucide-react`.

2\. \*\*Pane 2 (Center - Default 80%): 'Action Stream'\*\*

&nbsp;  - Replaces text chat. Renders `<WalkthroughCard />` components (shadcn Accordions) to show execution steps. 

&nbsp;  - Bottom sticky absolute footer contains the Omnibar with dynamic 'Model' and 'Agent' dropdown menus.

3\. \*\*Pane 3 (Right - Default 0%): 'Artifact Workbench'\*\*

&nbsp;  - Hidden by default. Opens (resizing panes to 20/40/40) ONLY when `\[Review Artifact]` is clicked in Pane 2. 

&nbsp;  - Renders `@monaco-editor/react` (for code) or `@tiptap/react` (for text) with a green `Approve \& Execute` button in the header.

