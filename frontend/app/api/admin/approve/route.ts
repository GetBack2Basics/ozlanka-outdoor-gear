import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";
import { adminRedirect } from "@/lib/admin-redirect";

export async function POST(request: Request) {
  const formData = await request.formData();
  const userId = Number(formData.get("user_id"));

  const response = await backendFetchWithAuth(`/admin/users/${userId}/approve`, { method: "POST" });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to approve user" }, { status: response.status });
  }

  return adminRedirect(request);
}
