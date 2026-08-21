import axios from "axios";
import { auth } from "./firebase";

const uploadApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_UPLOAD_SERVICE_URL,
});

const deliveryApi = axios.create({
  baseURL: process.env.NEXT_PUBLIC_DELIVERY_SERVICE_URL,
});

async function authHeader(): Promise<{ Authorization: string }> {
  const user = auth.currentUser;
  if (!user) throw new Error("Not authenticated");
  const token = await user.getIdToken();
  return { Authorization: `Bearer ${token}` };
}

export interface InitiateUploadPayload {
  album_id: string;
  filename: string;
  content_type: string;
  file_size_bytes: number;
}

export interface InitiateUploadResult {
  photo_id: string;
  resumable_uri: string;
  gcs_path: string;
}

export async function initiateUpload(payload: InitiateUploadPayload): Promise<InitiateUploadResult> {
  const headers = await authHeader();
  const { data } = await uploadApi.post<InitiateUploadResult>("/v1/uploads/initiate", payload, { headers });
  return data;
}

export async function resumableUpload(
  resumableUri: string,
  file: File,
  onProgress?: (pct: number) => void,
): Promise<void> {
  await axios.put(resumableUri, file, {
    headers: { "Content-Type": file.type },
    onUploadProgress: (e) => {
      if (onProgress && e.total) onProgress(Math.round((e.loaded / e.total) * 100));
    },
  });
}

export async function completeUpload(photoId: string, albumId: string): Promise<void> {
  const headers = await authHeader();
  await uploadApi.post("/v1/uploads/complete", { photo_id: photoId, album_id: albumId }, { headers });
}

export interface DeliveryURLs {
  photo_id: string;
  enhanced_url: string | null;
  thumb_256_url: string | null;
  thumb_1024_url: string | null;
  expires_at: string;
}

export async function getDeliveryURLs(
  tenantId: string,
  albumId: string,
  photoId: string,
): Promise<DeliveryURLs> {
  const headers = await authHeader();
  const { data } = await deliveryApi.get<DeliveryURLs>(
    `/v1/photos/${tenantId}/${albumId}/${photoId}/urls`,
    { headers },
  );
  return data;
}
