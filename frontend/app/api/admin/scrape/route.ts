import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function POST(request: Request) {
  const response = await backendFetchWithAuth("/admin/scrape/trigger", { method: "POST" });
  const payload = await response.json();
  const latest = await backendFetchWithAuth("/admin/scrape/latest");
  const latestPayload = await latest.json();
  return NextResponse.json({
    ...payload,
    run: latestPayload.run ?? null,
  });
}
