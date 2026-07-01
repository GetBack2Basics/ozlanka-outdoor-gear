import { NextResponse } from "next/server";
import { backendFetch } from "@/lib/backend";

export async function GET() {
  const response = await backendFetch("/public/settings");
  if (!response.ok) {
    return NextResponse.json({ error: "Failed to load settings" }, { status: response.status });
  }
  const data = await response.json();
  return NextResponse.json(data);
}
