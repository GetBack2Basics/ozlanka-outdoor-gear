import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function POST(request: Request) {
  const formData = await request.formData();
  const handling_fee_percent = Number(formData.get("handling_fee_percent"));

  await backendFetchWithAuth("/admin/settings/handling-fee", {
    method: "POST",
    body: JSON.stringify({ handling_fee_percent }),
  });
  return NextResponse.redirect(new URL("/admin", request.url), 303);
}
