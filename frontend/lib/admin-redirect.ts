import { NextResponse } from "next/server";

function getPublicOrigin(request: Request): string {
  const explicit = process.env.NEXT_PUBLIC_SITE_URL?.replace(/\/$/, "");
  if (explicit) return explicit;

  const base = new URL(request.url);
  const forwardedProto =
    request.headers.get("x-forwarded-proto") || base.protocol.replace(":", "");
  const forwardedHost = request.headers.get("x-forwarded-host");
  const rawHost = forwardedHost || base.host;

  const [hostname, port] = rawHost.split(":");
  const isHttps =
    forwardedProto === "https" ||
    base.protocol === "https:" ||
    port === "443";

  const scheme = isHttps ? "https" : "http";
  if (!port || port === "443" || port === "80") {
    return `${scheme}://${hostname}`;
  }
  return `${scheme}://${hostname}:${port}`;
}

export function adminRedirect(request: Request, path = "/admin"): NextResponse {
  const target = new URL(path, getPublicOrigin(request));
  return NextResponse.redirect(target, 303);
}
