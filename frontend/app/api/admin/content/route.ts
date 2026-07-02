import { NextResponse } from "next/server";

import { backendFetchWithAuth } from "@/lib/backend";
import { adminRedirect } from "@/lib/admin-redirect";

export async function POST(request: Request) {
  const formData = await request.formData();
  const payload = {
    banner_title: String(formData.get("banner_title")),
    banner_description: String(formData.get("banner_description")),
    logo_image_url: String(formData.get("logo_image_url")),
    promo_title_l: String(formData.get("promo_title_l")),
    promo_text_l: String(formData.get("promo_text_l")),
    promo_title_c: String(formData.get("promo_title_c")),
    promo_text_c: String(formData.get("promo_text_c")),
    promo_title_r: String(formData.get("promo_title_r")),
    promo_text_r: String(formData.get("promo_text_r")),
  };

  const response = await backendFetchWithAuth("/admin/settings/content", {
    method: "POST",
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    return NextResponse.json({ error: "Failed to update content settings" }, { status: response.status });
  }

  return adminRedirect(request);
}
