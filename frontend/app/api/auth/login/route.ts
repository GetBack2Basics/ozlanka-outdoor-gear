import { NextResponse } from "next/server";

import { backendFetch } from "@/lib/backend";

const publicUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "http://185.208.207.241:8000";

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
  // Use the public frontend URL for redirect
  const frontendUrl = process.env.NEXT_PUBLIC_FRONTEND_URL ?? "http://localhost:3002";
  const nextResponse = NextResponse.redirect(new URL("/admin", frontendUrl), 303);
  nextResponse.cookies.set("ozlanka_token", token.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
  });
  return nextResponse;
}
