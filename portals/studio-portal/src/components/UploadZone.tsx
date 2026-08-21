"use client";

import { useCallback, useState } from "react";
import { useDropzone } from "react-dropzone";
import { completeUpload, initiateUpload, resumableUpload } from "@/lib/api";
import clsx from "clsx";

interface Props {
  albumId: string;
  tenantId: string;
}

interface UploadItem {
  file: File;
  photoId?: string;
  progress: number;
  status: "pending" | "uploading" | "completing" | "done" | "error";
  error?: string;
}

export function UploadZone({ albumId, tenantId }: Props) {
  const [items, setItems] = useState<UploadItem[]>([]);

  const update = (index: number, patch: Partial<UploadItem>) => {
    setItems((prev) => prev.map((it, i) => (i === index ? { ...it, ...patch } : it)));
  };

  const uploadFile = useCallback(
    async (file: File, index: number) => {
      update(index, { status: "uploading" });
      try {
        const { photo_id, resumable_uri } = await initiateUpload({
          album_id: albumId,
          filename: file.name,
          content_type: file.type || "image/jpeg",
          file_size_bytes: file.size,
        });

        update(index, { photoId: photo_id });

        await resumableUpload(resumable_uri, file, (pct) => {
          update(index, { progress: pct });
        });

        update(index, { status: "completing" });
        await completeUpload(photo_id, albumId);
        update(index, { status: "done", progress: 100 });
      } catch (err: unknown) {
        update(index, {
          status: "error",
          error: err instanceof Error ? err.message : "Upload failed",
        });
      }
    },
    [albumId],
  );

  const onDrop = useCallback(
    (acceptedFiles: File[]) => {
      const startIndex = items.length;
      const newItems: UploadItem[] = acceptedFiles.map((file) => ({
        file,
        progress: 0,
        status: "pending",
      }));
      setItems((prev) => [...prev, ...newItems]);
      acceptedFiles.forEach((file, i) => uploadFile(file, startIndex + i));
    },
    [items.length, uploadFile],
  );

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { "image/*": [] },
    multiple: true,
  });

  return (
    <div className="mb-8 space-y-4">
      <div
        {...getRootProps()}
        className={clsx(
          "border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer transition",
          isDragActive ? "border-indigo-500 bg-indigo-50" : "border-gray-300 hover:border-indigo-400",
        )}
      >
        <input {...getInputProps()} />
        <p className="text-gray-500 text-sm">
          {isDragActive ? "Drop photos here…" : "Drag & drop photos, or click to select"}
        </p>
      </div>

      {items.length > 0 && (
        <ul className="space-y-2">
          {items.map((item, i) => (
            <li key={i} className="flex items-center gap-3 text-sm">
              <span className="truncate flex-1 text-gray-700">{item.file.name}</span>
              <span
                className={clsx("font-medium", {
                  "text-yellow-500": item.status === "uploading" || item.status === "completing",
                  "text-green-600": item.status === "done",
                  "text-red-500": item.status === "error",
                  "text-gray-400": item.status === "pending",
                })}
              >
                {item.status === "uploading" ? `${item.progress}%` : item.status.toUpperCase()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
