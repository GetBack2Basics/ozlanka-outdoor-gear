import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

export async function POST(request: Request) {
  const formData = await request.formData();
  const body = {
    product_name: String(formData.get("product_name") ?? ""),
    quantity: Number(formData.get("quantity") ?? 1),
    notes: String(formData.get("notes") ?? "") || null,
  };

  const response = await backendFetchWithAuth("/requests", {
    method: "POST",
    body: JSON.stringify(body),
  });

  return NextResponse.redirect(new URL("/request-list", request.url), 303);
}
