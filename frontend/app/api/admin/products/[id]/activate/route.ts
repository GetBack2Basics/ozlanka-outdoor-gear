import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const response = await backendFetchWithAuth(`/admin/products/${id}/activate`, {
    method: "POST",
  });
  if (!response.ok) {
    return NextResponse.json(
      { error: "Failed to activate product" },
      { status: response.status }
    );
  }
  const data = await response.json();
  return NextResponse.json(data);
}
