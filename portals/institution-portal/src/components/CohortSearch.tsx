"use client";

import { useState } from "react";
import { collection, query, where, getDocs } from "firebase/firestore";
import { db } from "@/lib/firebase";
import Image from "next/image";
import clsx from "clsx";

interface SearchResult {
  photo_id: string;
  album_id: string;
  tenant_id: string;
  student_name: string;
  roll_number: string;
  gcs_thumb_256?: string;
}

interface Props {
  tenantId: string;
}

export function CohortSearch({ tenantId }: Props) {
  const [query_, setQuery] = useState("");
  const [results, setResults] = useState<SearchResult[]>([]);
  const [loading, setLoading] = useState(false);

  async function search() {
    if (!query_.trim()) return;
    setLoading(true);
    setResults([]);
    try {
      // Searches across all album photos by student name or roll number via Firestore
      // In production, this would call a Cloud Function with a full-text search backend
      const photosQuery = query(
        collection(db, "tenants", tenantId, "face_tags"),
        where("student_name", ">=", query_),
        where("student_name", "<=", query_ + ""),
      );
      const snap = await getDocs(photosQuery);
      setResults(snap.docs.map((d) => d.data() as SearchResult));
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex gap-2">
        <input
          type="text"
          value={query_}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && search()}
          placeholder="Search by name or roll number…"
          className="flex-1 border rounded-lg px-4 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-teal-500"
        />
        <button
          onClick={search}
          disabled={loading}
          className="px-5 py-2 bg-teal-600 text-white rounded-lg text-sm font-medium hover:bg-teal-700 disabled:opacity-50 transition"
        >
          {loading ? "Searching…" : "Search"}
        </button>
      </div>

      {results.length === 0 && !loading && query_ && (
        <p className="text-slate-400 text-sm">No results for "{query_}"</p>
      )}

      <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-4">
        {results.map((r) => (
          <div key={r.photo_id} className="rounded-xl border bg-white overflow-hidden">
            {r.gcs_thumb_256 && (
              <div className="relative aspect-square">
                <Image src={r.gcs_thumb_256} alt={r.student_name} fill className="object-cover" sizes="256px" />
              </div>
            )}
            <div className="p-3">
              <p className="font-medium text-sm">{r.student_name}</p>
              <p className="text-xs text-slate-400">{r.roll_number}</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
