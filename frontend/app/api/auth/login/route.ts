import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

export async function POST(request: Request) {
  const formData = await request.formData();
  const body = {
    email: String(formData.get("email") ?? ""),
    password: String(formData.get("password") ?? ""),
  };

  const response = await backendFetch("/auth/login", {
    method: "POST",
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    return NextResponse.redirect(new URL("/login", request.url), 303);
  }

  const token = await response.json();
  const nextResponse = NextResponse.redirect(new URL("/admin", request.url), 303);
  nextResponse.cookies.set("ozlanka_token", token.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
  });
  return nextResponse;
}
