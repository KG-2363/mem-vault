"use client";

import { useEffect, useState } from "react";
import { collection, onSnapshot, query, orderBy } from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";
import { auth, db } from "@/lib/firebase";
import Link from "next/link";

interface Album {
  album_id: string;
  name: string;
  photo_count?: number;
  created_at?: string;
}

export default function DashboardPage() {
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [albums, setAlbums] = useState<Album[]>([]);

  useEffect(() => {
    return onAuthStateChanged(auth, async (user) => {
      if (!user) return;
      const token = await user.getIdTokenResult();
      const tid = token.claims.tenant_id as string;
      setTenantId(tid);
    });
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    const q = query(
      collection(db, "tenants", tenantId, "albums"),
      orderBy("created_at", "desc"),
    );
    return onSnapshot(q, (snap) => {
      setAlbums(snap.docs.map((d) => ({ album_id: d.id, ...d.data() } as Album)));
    });
  }, [tenantId]);

  return (
    <main className="max-w-5xl mx-auto p-8">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold">Albums</h1>
        <button className="px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 transition text-sm font-medium">
          New Album
        </button>
      </div>

      {albums.length === 0 && (
        <p className="text-gray-400 text-center mt-24">No albums yet. Create your first one.</p>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        {albums.map((album) => (
          <Link
            key={album.album_id}
            href={`/dashboard/albums/${album.album_id}`}
            className="block rounded-2xl border bg-white p-6 hover:shadow-md transition"
          >
            <h2 className="font-medium text-lg truncate">{album.name}</h2>
            <p className="text-sm text-gray-400 mt-1">{album.photo_count ?? 0} photos</p>
          </Link>
        ))}
      </div>
    </main>
  );
}
