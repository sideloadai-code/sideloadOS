"use client";

import { useState, useEffect, useCallback } from "react";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogDescription,
} from "@/components/ui/dialog";
import {
    Table,
    TableBody,
    TableCell,
    TableHead,
    TableHeader,
    TableRow,
} from "@/components/ui/table";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";

// ── Types ──────────────────────────────────────────────────────────────────

interface ConfiguredProvider {
    id: string;
    provider_name: string;
    is_configured: boolean;
}

interface SettingsModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onProviderAdded: () => void;
}

// ── Component ──────────────────────────────────────────────────────────────

export function SettingsModal({
    open,
    onOpenChange,
    onProviderAdded,
}: SettingsModalProps) {
    const [providers, setProviders] = useState<ConfiguredProvider[]>([]);
    const [loading, setLoading] = useState(false);

    // Add-provider form state
    const [providerName, setProviderName] = useState("");
    const [apiKey, setApiKey] = useState("");
    const [saving, setSaving] = useState(false);

    // ── Fetch configured providers ──────────────────────────────────────────

    const fetchProviders = useCallback(async () => {
        setLoading(true);
        try {
            const res = await fetch("/api/settings/");
            if (res.ok) {
                const data: ConfiguredProvider[] = await res.json();
                setProviders(data);
            }
        } catch {
            // Backend unreachable — graceful fallback
        } finally {
            setLoading(false);
        }
    }, []);

    useEffect(() => {
        if (open) {
            fetchProviders();
        }
    }, [open, fetchProviders]);

    // ── Add provider ────────────────────────────────────────────────────────

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        const trimmedName = providerName.trim();
        const trimmedKey = apiKey.trim();
        if (!trimmedName || !trimmedKey) return;

        setSaving(true);
        try {
            const res = await fetch("/api/settings/", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    provider_name: trimmedName,
                    api_key: trimmedKey,
                }),
            });
            if (res.ok) {
                setProviderName("");
                setApiKey("");
                await fetchProviders();
                onProviderAdded(); // Refresh model dropdown in Omnibar
            }
        } catch {
            // Graceful fallback
        } finally {
            setSaving(false);
        }
    };

    // ── Delete provider ─────────────────────────────────────────────────────

    const handleDelete = async (name: string) => {
        try {
            const res = await fetch(`/api/settings/${name}`, { method: "DELETE" });
            if (res.ok) {
                await fetchProviders();
                onProviderAdded(); // Refresh model dropdown
            }
        } catch {
            // Graceful fallback
        }
    };

    // ── Render ──────────────────────────────────────────────────────────────

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="border-white/10 bg-zinc-900 text-zinc-100 sm:max-w-[520px]">
                <DialogHeader>
                    <DialogTitle className="text-zinc-100">Settings</DialogTitle>
                    <DialogDescription className="text-zinc-400">
                        Manage your AI provider API keys. Vertex AI uses Application
                        Default Credentials — configure via{" "}
                        <code className="rounded bg-zinc-800 px-1 text-xs text-emerald-400">
                            gcloud auth application-default login
                        </code>{" "}
                        and <code className="rounded bg-zinc-800 px-1 text-xs text-emerald-400">.env</code>.
                    </DialogDescription>
                </DialogHeader>

                {/* ── Configured Providers ──────────────────────────────────────── */}
                <div className="mt-4">
                    <h3 className="mb-2 text-sm font-medium text-zinc-300">
                        Configured Providers
                    </h3>
                    {loading ? (
                        <p className="text-sm text-zinc-500">Loading…</p>
                    ) : providers.length === 0 ? (
                        <p className="text-sm text-zinc-500">
                            No providers configured yet.
                        </p>
                    ) : (
                        <Table>
                            <TableHeader>
                                <TableRow className="border-white/10 hover:bg-transparent">
                                    <TableHead className="text-zinc-400">Provider</TableHead>
                                    <TableHead className="text-zinc-400">Status</TableHead>
                                    <TableHead className="w-[60px] text-zinc-400" />
                                </TableRow>
                            </TableHeader>
                            <TableBody>
                                {providers.map((p) => (
                                    <TableRow
                                        key={p.id}
                                        className="border-white/10 hover:bg-zinc-800/50"
                                    >
                                        <TableCell className="text-zinc-200">
                                            {p.provider_name}
                                        </TableCell>
                                        <TableCell>
                                            {p.is_configured ? (
                                                <span className="text-emerald-400">Configured ✓</span>
                                            ) : (
                                                <span className="text-zinc-500">—</span>
                                            )}
                                        </TableCell>
                                        <TableCell>
                                            <Button
                                                variant="ghost"
                                                size="icon"
                                                className="h-7 w-7 text-zinc-500 hover:text-red-400"
                                                onClick={() => handleDelete(p.provider_name)}
                                            >
                                                <Trash2 className="h-3.5 w-3.5" />
                                            </Button>
                                        </TableCell>
                                    </TableRow>
                                ))}
                            </TableBody>
                        </Table>
                    )}
                </div>

                {/* ── Add Provider Form ────────────────────────────────────────── */}
                <div className="mt-6 border-t border-white/10 pt-4">
                    <h3 className="mb-3 text-sm font-medium text-zinc-300">
                        Add Provider
                    </h3>
                    <form onSubmit={handleSubmit} className="space-y-3">
                        <div className="space-y-1.5">
                            <Label htmlFor="provider-name" className="text-zinc-400">
                                Provider Name
                            </Label>
                            <Input
                                id="provider-name"
                                value={providerName}
                                onChange={(e) => setProviderName(e.target.value)}
                                placeholder='e.g. "openai", "anthropic"'
                                className="border-white/10 bg-zinc-800/60 text-zinc-200 placeholder:text-zinc-600"
                            />
                        </div>
                        <div className="space-y-1.5">
                            <Label htmlFor="api-key" className="text-zinc-400">
                                API Key
                            </Label>
                            <Input
                                id="api-key"
                                type="password"
                                value={apiKey}
                                onChange={(e) => setApiKey(e.target.value)}
                                placeholder="sk-..."
                                className="border-white/10 bg-zinc-800/60 text-zinc-200 placeholder:text-zinc-600"
                            />
                        </div>
                        <Button
                            type="submit"
                            disabled={saving || !providerName.trim() || !apiKey.trim()}
                            className="w-full bg-emerald-600 text-white hover:bg-emerald-500 disabled:opacity-40"
                        >
                            {saving ? "Saving…" : "Save Provider Key"}
                        </Button>
                    </form>
                </div>
            </DialogContent>
        </Dialog>
    );
}
