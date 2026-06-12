import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(request: Request) {
  const formData = await request.formData();
  const body = {
    email: String(formData.get("email") ?? ""),
    password: String(formData.get("password") ?? ""),
  };

  const response = await backendFetch("/auth/signup", {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return NextResponse.redirect(new URL("/signup", request.url), 303);
  }

  return NextResponse.redirect(new URL("/login", request.url), 303);
}
