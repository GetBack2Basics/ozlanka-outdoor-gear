import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function GET() {
  const response = await backendFetchWithAuth("/admin/scrape/latest");
  const payload = await response.json();
  return NextResponse.json(payload);
}
