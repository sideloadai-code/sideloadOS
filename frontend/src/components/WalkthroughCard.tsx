"use client";

import { Loader2, Sparkles, Eye } from "lucide-react";
import { Card, CardHeader, CardContent, CardFooter } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { useLayoutStore } from "@/store/layoutStore";

interface WalkthroughCardProps {
    prompt: string;
    steps: string[];
    isStreaming: boolean;
    isPaused: boolean;
    draftArtifactId: string | null;
}

export function WalkthroughCard({
    prompt,
    steps,
    isStreaming,
    isPaused,
    draftArtifactId,
}: WalkthroughCardProps) {
    const openWorkbench = useLayoutStore((s) => s.openWorkbench);
    const setActiveArtifactId = useLayoutStore((s) => s.setActiveArtifactId);

    const handleReviewArtifact = () => {
        if (draftArtifactId) {
            setActiveArtifactId(draftArtifactId);
            openWorkbench();
        }
    };

    return (
        <Card className="border-zinc-800 bg-zinc-900/80 shadow-lg">
            {/* Header — user prompt */}
            <CardHeader className="pb-3">
                <div className="flex items-start gap-3">
                    <div className="mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-zinc-800">
                        <Sparkles className="h-4 w-4 text-zinc-400" />
                    </div>
                    <div className="min-w-0 flex-1">
                        <p className="text-sm font-medium text-zinc-200">{prompt}</p>
                    </div>
                    {isStreaming && (
                        <Badge
                            variant="secondary"
                            className="shrink-0 bg-emerald-900/40 text-emerald-400 border-emerald-800/50"
                        >
                            Streaming
                        </Badge>
                    )}
                    {isPaused && (
                        <Badge
                            variant="secondary"
                            className="shrink-0 bg-amber-900/40 text-amber-400 border-amber-800/50"
                        >
                            Awaiting Review
                        </Badge>
                    )}
                    {!isStreaming && !isPaused && steps.length > 0 && (
                        <Badge
                            variant="secondary"
                            className="shrink-0 bg-zinc-800 text-zinc-400"
                        >
                            Complete
                        </Badge>
                    )}
                </div>
            </CardHeader>

            {/* Body — step list (Amendment 4: static vertical list, no Accordion) */}
            <CardContent className="pt-0">
                {steps.length > 0 && (
                    <div className="ml-[22px] flex flex-col gap-2 border-l-2 border-zinc-800 pl-4">
                        {steps.map((step, i) => (
                            <div key={i} className="flex items-baseline gap-2">
                                <span className="shrink-0 text-[10px] font-mono text-zinc-600">
                                    {String(i + 1).padStart(2, "0")}
                                </span>
                                <span className="text-sm text-zinc-400">{step}</span>
                            </div>
                        ))}
                    </div>
                )}

                {/* Streaming spinner */}
                {isStreaming && (
                    <div className="ml-[22px] mt-3 flex items-center gap-2 pl-4">
                        <Loader2 className="h-4 w-4 animate-spin text-emerald-500" />
                        <span className="text-xs text-zinc-500">Processing...</span>
                    </div>
                )}
            </CardContent>

            {/* Footer — HITL Bridge */}
            {isPaused && draftArtifactId && (
                <CardFooter className="pt-0">
                    <Button
                        onClick={handleReviewArtifact}
                        className="w-full gap-2 bg-emerald-600 text-white hover:bg-emerald-500 transition-colors"
                    >
                        <Eye className="h-4 w-4" />
                        Review Artifact
                    </Button>
                </CardFooter>
            )}
        </Card>
    );
}
