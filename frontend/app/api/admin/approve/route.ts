import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";

function buildRedirectTarget(request: Request): URL {
  const base = new URL(request.url);

  const forwardedProto = request.headers.get("x-forwarded-proto");
  const forwardedHost = request.headers.get("x-forwarded-host");
  const rawHost = forwardedHost ?? base.host;

  const [hostname, port] = rawHost.split(":");

  if (forwardedProto === "https") {
    return new URL("/admin", `https://${hostname}${port === "443" ? "" : ":" + port}/admin`);
  }

  return new URL("/admin", `${forwardedProto || base.protocol}//${hostname}${port === "80" || port === "443" ? "" : ":" + port}/admin`);
}

export async function POST(request: Request) {
  const formData = await request.formData();
  const userId = Number(formData.get("user_id"));

  const response = await backendFetchWithAuth(`/admin/users/${userId}/approve`, { method: "POST" });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to approve user" }, { status: response.status });
  }

  return NextResponse.redirect(buildRedirectTarget(request), 303);
}
