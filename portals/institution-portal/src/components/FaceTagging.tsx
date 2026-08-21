"use client";

import { useRef, useState } from "react";
import Image from "next/image";

interface BoundingBox {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface FaceTag {
  face_id: string;
  student_name: string;
  roll_number: string;
  bounding_box: BoundingBox;
  confidence: number;
}

interface Props {
  photoUrl: string;
  photoId: string;
  initialTags?: FaceTag[];
  onTagSaved?: (tag: FaceTag) => void;
}

export function FaceTagging({ photoUrl, photoId, initialTags = [], onTagSaved }: Props) {
  const [tags, setTags] = useState<FaceTag[]>(initialTags);
  const [pendingBox, setPendingBox] = useState<BoundingBox | null>(null);
  const [studentName, setStudentName] = useState("");
  const [rollNumber, setRollNumber] = useState("");
  const containerRef = useRef<HTMLDivElement>(null);
  const dragStart = useRef<{ x: number; y: number } | null>(null);

  function onMouseDown(e: React.MouseEvent) {
    const rect = containerRef.current!.getBoundingClientRect();
    dragStart.current = {
      x: (e.clientX - rect.left) / rect.width,
      y: (e.clientY - rect.top) / rect.height,
    };
  }

  function onMouseUp(e: React.MouseEvent) {
    if (!dragStart.current) return;
    const rect = containerRef.current!.getBoundingClientRect();
    const endX = (e.clientX - rect.left) / rect.width;
    const endY = (e.clientY - rect.top) / rect.height;

    const box: BoundingBox = {
      x: Math.min(dragStart.current.x, endX),
      y: Math.min(dragStart.current.y, endY),
      width: Math.abs(endX - dragStart.current.x),
      height: Math.abs(endY - dragStart.current.y),
    };

    if (box.width > 0.02 && box.height > 0.02) {
      setPendingBox(box);
    }
    dragStart.current = null;
  }

  function saveTag() {
    if (!pendingBox || !studentName) return;
    const tag: FaceTag = {
      face_id: crypto.randomUUID(),
      student_name: studentName,
      roll_number: rollNumber,
      bounding_box: pendingBox,
      confidence: 1.0,
    };
    setTags((prev) => [...prev, tag]);
    onTagSaved?.(tag);
    setPendingBox(null);
    setStudentName("");
    setRollNumber("");
  }

  return (
    <div className="space-y-4">
      <div
        ref={containerRef}
        className="relative w-full aspect-[4/3] select-none cursor-crosshair overflow-hidden rounded-xl border"
        onMouseDown={onMouseDown}
        onMouseUp={onMouseUp}
      >
        <Image src={photoUrl} alt="Photo" fill className="object-contain" sizes="100vw" />

        {tags.map((tag) => (
          <div
            key={tag.face_id}
            className="absolute border-2 border-teal-400 rounded"
            style={{
              left: `${tag.bounding_box.x * 100}%`,
              top: `${tag.bounding_box.y * 100}%`,
              width: `${tag.bounding_box.width * 100}%`,
              height: `${tag.bounding_box.height * 100}%`,
            }}
          >
            <span className="absolute -top-5 left-0 bg-teal-400 text-white text-[10px] px-1 rounded whitespace-nowrap">
              {tag.student_name}
            </span>
          </div>
        ))}

        {pendingBox && (
          <div
            className="absolute border-2 border-yellow-400 rounded"
            style={{
              left: `${pendingBox.x * 100}%`,
              top: `${pendingBox.y * 100}%`,
              width: `${pendingBox.width * 100}%`,
              height: `${pendingBox.height * 100}%`,
            }}
          />
        )}
      </div>

      {pendingBox && (
        <div className="flex gap-2 items-end">
          <label className="flex flex-col gap-1 text-sm">
            Student Name
            <input
              className="border rounded px-2 py-1 text-sm"
              value={studentName}
              onChange={(e) => setStudentName(e.target.value)}
              placeholder="Rahul Sharma"
            />
          </label>
          <label className="flex flex-col gap-1 text-sm">
            Roll No.
            <input
              className="border rounded px-2 py-1 text-sm"
              value={rollNumber}
              onChange={(e) => setRollNumber(e.target.value)}
              placeholder="2024CS001"
            />
          </label>
          <button
            onClick={saveTag}
            className="px-4 py-1.5 bg-teal-600 text-white rounded text-sm hover:bg-teal-700"
          >
            Tag
          </button>
        </div>
      )}

      <p className="text-xs text-slate-400">
        Drag to draw a box around a face, then enter the student details.
      </p>
    </div>
  );
}
