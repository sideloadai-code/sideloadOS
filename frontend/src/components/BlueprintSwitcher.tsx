"use client";

import { useEffect, useState } from "react";

interface Blueprint {
  id: string;
  name: string;
  description: string;
}

interface BlueprintSwitcherProps {
  activeBlueprint: string;
  onChange: (value: string) => void;
}

export function BlueprintSwitcher({
  activeBlueprint,
  onChange,
}: BlueprintSwitcherProps) {
  const [blueprints, setBlueprints] = useState<Blueprint[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/api/blueprints/")
      .then((res) => (res.ok ? res.json() : []))
      .then((data: Blueprint[]) => setBlueprints(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  const selectedBlueprint = blueprints.find((b) => b.id === activeBlueprint);

  return (
    <div className="px-3 pt-3 pb-2">
      <label className="mb-1.5 block text-[11px] font-medium uppercase tracking-wider text-zinc-500">
        Blueprint
      </label>
      <select
        value={activeBlueprint}
        onChange={(e) => onChange(e.target.value)}
        disabled={loading || blueprints.length === 0}
        className="w-full appearance-none rounded-md border border-zinc-800 bg-zinc-900 px-2.5 py-2 text-sm text-zinc-100 outline-none transition-colors focus:border-emerald-500/60 focus:ring-1 focus:ring-emerald-500/40 disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? (
          <option value="">Loading...</option>
        ) : blueprints.length === 0 ? (
          <option value="">No blueprints found</option>
        ) : (
          blueprints.map((bp) => (
            <option key={bp.id} value={bp.id}>
              {bp.name}
            </option>
          ))
        )}
      </select>
      {selectedBlueprint?.description && (
        <p className="mt-1.5 text-[11px] leading-relaxed text-zinc-600">
          {selectedBlueprint.description}
        </p>
      )}
    </div>
  );
}
