import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";
import { adminRedirect } from "@/lib/admin-redirect";

export async function POST(request: Request) {
  const formData = await request.formData();
  const handling_fee_percent = Number(formData.get("handling_fee_percent"));

  const response = await backendFetchWithAuth("/admin/settings/handling-fee", {
    method: "POST",
    body: JSON.stringify({ handling_fee_percent }),
  });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to update handling fee" }, { status: response.status });
  }

  return adminRedirect(request);
}
