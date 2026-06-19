import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function GET() {
  const response = await backendFetchWithAuth("/admin/products/filtered");
  if (!response.ok) {
    return NextResponse.json(
      { error: "Failed to fetch filtered products" },
      { status: response.status }
    );
  }
  const data = await response.json();
  return NextResponse.json(data);
}
