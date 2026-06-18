import { cookies } from "next/headers";

const internalUrl = process.env.BACKEND_INTERNAL_URL ?? "http://backend:8000";
const publicUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://185.208.207.241:8000";

function getBackendUrl() {
  if (typeof window === "undefined") {
    return internalUrl;
  }
  return publicUrl;
}

export async function backendFetch(path: string, init: RequestInit = {}) {
  return fetch(`${getBackendUrl()}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
}

export async function backendFetchWithAuth(path: string, init: RequestInit = {}) {
  const cookieStore = await cookies();
  const token = cookieStore.get("ozlanka_token")?.value;
  return fetch(`${getBackendUrl()}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
}
