import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const { id } = await params;
  const response = await backendFetchWithAuth(`/admin/products/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    return NextResponse.json(
      { error: "Failed to delete product" },
      { status: response.status }
    );
  }
  const data = await response.json();
  return NextResponse.json(data);
}
