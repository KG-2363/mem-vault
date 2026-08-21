"use client";

import { useEffect, useState } from "react";
import { collection, onSnapshot, query, orderBy } from "firebase/firestore";
import { onAuthStateChanged } from "firebase/auth";
import { auth, db } from "@/lib/firebase";
import { UploadZone } from "@/components/UploadZone";
import { PhotoGrid } from "@/components/PhotoGrid";

interface Photo {
  photo_id: string;
  status: "UPLOADED" | "PROCESSING" | "ENHANCED" | "FAILED";
  original_filename: string;
  gcs_thumb_256?: string;
  gcs_enhanced_path?: string;
}

export default function AlbumPage({ params }: { params: { albumId: string } }) {
  const { albumId } = params;
  const [tenantId, setTenantId] = useState<string | null>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);

  useEffect(() => {
    return onAuthStateChanged(auth, async (user) => {
      if (!user) return;
      const token = await user.getIdTokenResult();
      setTenantId(token.claims.tenant_id as string);
    });
  }, []);

  useEffect(() => {
    if (!tenantId) return;
    const q = query(
      collection(db, "tenants", tenantId, "albums", albumId, "photos"),
      orderBy("uploaded_at", "desc"),
    );
    return onSnapshot(q, (snap) => {
      setPhotos(snap.docs.map((d) => ({ photo_id: d.id, ...d.data() } as Photo)));
    });
  }, [tenantId, albumId]);

  return (
    <main className="max-w-6xl mx-auto p-8">
      <h1 className="text-2xl font-semibold mb-6">Album: {albumId}</h1>

      {tenantId && (
        <UploadZone albumId={albumId} tenantId={tenantId} />
      )}

      <PhotoGrid photos={photos} tenantId={tenantId ?? ""} albumId={albumId} />
    </main>
  );
}
