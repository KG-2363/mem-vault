"use client";

import { useState } from "react";
import Image from "next/image";
import clsx from "clsx";
import { getDeliveryURLs, type DeliveryURLs } from "@/lib/api";

interface Photo {
  photo_id: string;
  status: "UPLOADED" | "PROCESSING" | "ENHANCED" | "FAILED";
  original_filename: string;
  gcs_thumb_256?: string;
}

interface Props {
  photos: Photo[];
  tenantId: string;
  albumId: string;
}

const statusColor: Record<Photo["status"], string> = {
  UPLOADED: "bg-blue-100 text-blue-700",
  PROCESSING: "bg-yellow-100 text-yellow-700",
  ENHANCED: "bg-green-100 text-green-700",
  FAILED: "bg-red-100 text-red-700",
};

export function PhotoGrid({ photos, tenantId, albumId }: Props) {
  const [urls, setUrls] = useState<Record<string, DeliveryURLs>>({});
  const [loading, setLoading] = useState<Record<string, boolean>>({});

  async function fetchUrls(photoId: string) {
    if (urls[photoId] || loading[photoId]) return;
    setLoading((p) => ({ ...p, [photoId]: true }));
    try {
      const result = await getDeliveryURLs(tenantId, albumId, photoId);
      setUrls((p) => ({ ...p, [photoId]: result }));
    } finally {
      setLoading((p) => ({ ...p, [photoId]: false }));
    }
  }

  if (photos.length === 0) {
    return <p className="text-gray-400 text-center mt-16">No photos yet. Upload some above.</p>;
  }

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-5 gap-4">
      {photos.map((photo) => (
        <div
          key={photo.photo_id}
          className="group relative rounded-xl overflow-hidden bg-gray-100 aspect-square cursor-pointer"
          onClick={() => photo.status === "ENHANCED" && fetchUrls(photo.photo_id)}
        >
          {urls[photo.photo_id]?.thumb_256_url ? (
            <Image
              src={urls[photo.photo_id].thumb_256_url!}
              alt={photo.original_filename}
              fill
              className="object-cover"
              sizes="256px"
            />
          ) : (
            <div className="absolute inset-0 flex items-center justify-center">
              <span className="text-gray-300 text-xs text-center px-2 break-all">
                {photo.original_filename}
              </span>
            </div>
          )}

          <span
            className={clsx(
              "absolute top-2 right-2 text-[10px] font-semibold px-2 py-0.5 rounded-full",
              statusColor[photo.status],
            )}
          >
            {photo.status}
          </span>

          {photo.status === "PROCESSING" && (
            <div className="absolute inset-0 bg-black/20 flex items-center justify-center">
              <div className="w-6 h-6 border-2 border-white border-t-transparent rounded-full animate-spin" />
            </div>
          )}
        </div>
      ))}
    </div>
  );
}
