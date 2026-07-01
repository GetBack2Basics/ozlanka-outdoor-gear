import { cookies } from "next/headers";

const backendUrl =
  process.env.NEXT_PUBLIC_BACKEND_URL ??
  process.env.BACKEND_INTERNAL_URL ??
  "http://backend:8000";

export async function backendFetch(path: string, init: RequestInit = {}) {
  return fetch(`${backendUrl}${path}`, {
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
  return fetch(`${backendUrl}${path}`, {
    ...init,
    headers: {
      "content-type": "application/json",
      ...(token ? { authorization: `Bearer ${token}` } : {}),
      ...(init.headers ?? {}),
    },
    cache: "no-store",
  });
}
