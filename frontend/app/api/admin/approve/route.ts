import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function POST(request: Request) {
  const formData = await request.formData();
  const userId = Number(formData.get("user_id"));

  await backendFetchWithAuth(`/admin/users/${userId}/approve`, { method: "POST" });
  return NextResponse.redirect(new URL("/admin", request.url), 303);
}
