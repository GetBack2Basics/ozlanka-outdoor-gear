import { cookies } from "next/headers";
import Link from "next/link";
import { redirect } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Textarea } from "@/components/ui/textarea";
import { ScrapePanel } from "@/components/admin/scrape-panel";
import { FilteredProductsReview } from "@/components/admin/filtered-products-review";
import { backendFetchWithAuth } from "@/lib/backend";

type Dashboard = {
  users_total: number;
  pending_users: number;
  pending_user_rows: { id: number; email: string; approval_status: string }[];
  products_total: number;
  requests_total: number;
  latest_run: {
    id: number;
    status: string;
    stage: string;
    progress_percent: number;
    message: string | null;
    total_items: number;
    processed_items: number;
    started_at: string;
    finished_at: string | null;
  } | null;
  handling_fee_percent: number;
};

type SiteSettings = {
  panel_headers: {
    users: string;
    pending: string;
    products: string;
    requests: string;
    filtered_products: string;
    handling_fee: string;
    pending_users: string;
  };
  footer_text: string;
  product_template: {
    show_image: boolean;
    show_sku: boolean;
    show_category: boolean;
    show_description: boolean;
    show_price_aud: boolean;
    show_price_lkr: boolean;
    show_view_link: boolean;
    custom_label: string;
  };
  hero_title: string;
  hero_subtitle: string;
  typography: {
    heading_font: string;
    body_font: string;
    base_size: string;
  };
  style: {
    primary_color: string;
    accent_color: string;
    radius: string;
  };
};

const SAVED_DEFAULT_SETTINGS: SiteSettings = {
  panel_headers: {
    users: "Users",
    pending: "Pending",
    products: "Products",
    requests: "Requests",
    filtered_products: "Filtered Products Review",
    handling_fee: "Handling fee",
    pending_users: "Pending users",
  },
  footer_text: "",
  product_template: {
    show_image: true,
    show_sku: true,
    show_category: true,
    show_description: true,
    show_price_aud: true,
    show_price_lkr: true,
    show_view_link: true,
    custom_label: "",
  },
  hero_title: "OzLanka Outdoor Gear",
  hero_subtitle: "Request outdoor gear from Australia with manual approval, LKR pricing, and clear shipping and customs terms.",
  typography: {
    heading_font: "Inter",
    body_font: "Inter",
    base_size: "16",
  },
  style: {
    primary_color: "#0f172a",
    accent_color: "#0ea5e9",
    radius: "12",
  },
};

async function updateSettings(formData: FormData) {
  "use server";
  const cookieStore = await cookies();
  const token = cookieStore.get("ozlanka_token")?.value;
  if (!token) return redirect("/login");

  const panelHeaders: Record<string, string> = {};
  for (const key of ["users", "pending", "products", "requests", "filtered_products", "handling_fee", "pending_users"]) {
    const val = formData.get(`panel_header_${key}`);
    if (val) panelHeaders[key] = String(val);
  }

  const productTemplate: Record<string, unknown> = {};
  for (const key of ["show_image", "show_sku", "show_category", "show_description", "show_price_aud", "show_price_lkr", "show_view_link"]) {
    productTemplate[key] = formData.get(`pt_${key}`) === "on";
  }
  const customLabel = formData.get("pt_custom_label");
  if (customLabel) productTemplate["custom_label"] = String(customLabel);

  const typography: Record<string, string> = {};
  for (const key of ["heading_font", "body_font", "base_size"]) {
    const val = formData.get(`typo_${key}`);
    if (val) typography[key] = String(val);
  }

  const style: Record<string, string> = {};
  for (const key of ["primary_color", "accent_color", "radius"]) {
    const val = formData.get(`style_${key}`);
    if (val) style[key] = String(val);
  }

  const payload: Record<string, unknown> = {
    panel_headers: panelHeaders,
    product_template: productTemplate,
  };
  const footerText = formData.get("footer_text");
  if (footerText) payload["footer_text"] = String(footerText);
  const heroTitle = formData.get("hero_title");
  if (heroTitle) payload["hero_title"] = String(heroTitle);
  const heroSubtitle = formData.get("hero_subtitle");
  if (heroSubtitle) payload["hero_subtitle"] = String(heroSubtitle);
  if (Object.keys(typography).length) payload["typography"] = typography;
  if (Object.keys(style).length) payload["style"] = style;

  const res = await fetch(`admin/settings`, {
    method: "PUT",
    headers: {
      "content-type": "application/json",
      authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  return redirect("/admin");
}

export default async function AdminPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get("ozlanka_token")?.value;
  const response = token ? await backendFetchWithAuth("/admin/dashboard") : null;
  const dashboard: Dashboard | null = response?.ok ? await response.json() : null;

  const settingsResponse = token ? await backendFetchWithAuth("/admin/settings") : null;
  const remoteSettings = settingsResponse?.ok ? await settingsResponse.json() : null;

  const runtimeDefaults = reregisterAdminSettingsDefaults();
  const settings: SiteSettings = {
    ...runtimeDefaults,
    ...(remoteSettings ?? {}),
    panel_headers: { ...runtimeDefaults.panel_headers, ...(remoteSettings?.panel_headers ?? {}) },
    product_template: { ...runtimeDefaults.product_template, ...(remoteSettings?.product_template ?? {}) },
    typography: { ...runtimeDefaults.typography, ...(remoteSettings?.typography ?? {}) },
    style: { ...runtimeDefaults.style, ...(remoteSettings?.style ?? {}) },
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">Admin panel</h1>
      </div>

      {!dashboard ? (
        <Card>
          <CardContent className="p-4">
            <p className="text-sm text-slate-600">
              Please <Link className="underline" href="/login">log in</Link> with the seeded admin account.
            </p>
          </CardContent>
        </Card>
      ) : (
        <>
          <ScrapePanel initialRun={dashboard.latest_run} />

          <section className="grid gap-4 md:grid-cols-4">
            {[
              ["Users", dashboard.users_total],
              ["Pending", dashboard.pending_users],
              ["Products", dashboard.products_total],
              ["Requests", dashboard.requests_total],
            ].map(([label, value]) => (
              <Card key={label as string}>
                <CardHeader>
                  <CardTitle>{label as string}</CardTitle>
                </CardHeader>
                <CardContent>
                  <p className="text-3xl font-bold">{value as number}</p>
                </CardContent>
              </Card>
            ))}
          </section>

          <Card>
            <CardHeader>
              <CardTitle>Filtered Products Review</CardTitle>
            </CardHeader>
            <CardContent>
              <FilteredProductsReview token={token} />
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Handling fee</CardTitle>
            </CardHeader>
            <CardContent>
              <p>{dashboard.handling_fee_percent}%</p>
              <form action="/api/admin/fee" method="post" className="mt-3 flex gap-2">
                <input
                  name="handling_fee_percent"
                  type="number"
                  step="0.1"
                  defaultValue={dashboard.handling_fee_percent}
                  className="w-28 rounded-md border border-slate-300 px-3 py-2"
                />
                <Button type="submit" variant="secondary">Save</Button>
              </form>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Pending users</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {dashboard.pending_user_rows.length === 0 ? <p className="text-sm text-slate-600">No pending approvals.</p> : null}
              {dashboard.pending_user_rows.map((user) => (
                <div key={user.id} className="flex items-center justify-between rounded-md border border-slate-200 p-3">
                  <div>
                    <p className="font-medium">{user.email}</p>
                    <p className="text-sm text-slate-600">{user.approval_status}</p>
                  </div>
                  <form action="/api/admin/approve" method="post">
                    <input type="hidden" name="user_id" value={user.id} />
                    <Button type="submit" variant="secondary">Approve</Button>
                  </form>
                </div>
              ))}
            </CardContent>
          </Card>

          {/* Editable Current Settings */}
          <Card>
            <CardHeader>
              <CardTitle>Site Settings</CardTitle>
            </CardHeader>
            <CardContent>
              <form action={updateSettings} className="space-y-6">
                {/* Hero */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Hero Section</h4>
                  <div>
                    <Label htmlFor="hero_title">Title</Label>
                    <Input id="hero_title" name="hero_title" defaultValue={settings.hero_title} />
                  </div>
                  <div>
                    <Label htmlFor="hero_subtitle">Subtitle</Label>
                    <Textarea id="hero_subtitle" name="hero_subtitle" defaultValue={settings.hero_subtitle} rows={2} />
                  </div>
                </div>

                {/* Panel Headers */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Dashboard Panel Headers</h4>
                  <div className="grid gap-3 sm:grid-cols-2">
                    {(["users", "pending", "products", "requests", "filtered_products", "handling_fee", "pending_users"] as const).map((key) => (
                      <div key={key}>
                        <Label htmlFor={`panel_header_${key}`}>{key.replace(/_/g, " ")}</Label>
                        <Input
                          id={`panel_header_${key}`}
                          name={`panel_header_${key}`}
                          defaultValue={settings.panel_headers[key] ?? ""}
                        />
                      </div>
                    ))}
                  </div>
                </div>

                {/* Footer */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Footer</h4>
                  <div>
                    <Label htmlFor="footer_text">Footer text</Label>
                    <Textarea id="footer_text" name="footer_text" defaultValue={settings.footer_text} rows={2} />
                  </div>
                </div>

                {/* Typography */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Typography</h4>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <Label htmlFor="typo_heading_font">Heading font</Label>
                      <Input id="typo_heading_font" name="typo_heading_font" defaultValue={settings.typography.heading_font} />
                    </div>
                    <div>
                      <Label htmlFor="typo_body_font">Body font</Label>
                      <Input id="typo_body_font" name="typo_body_font" defaultValue={settings.typography.body_font} />
                    </div>
                    <div>
                      <Label htmlFor="typo_base_size">Base font size (px)</Label>
                      <Input id="typo_base_size" name="typo_base_size" defaultValue={settings.typography.base_size} />
                    </div>
                  </div>
                </div>

                {/* Style */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Style</h4>
                  <div className="grid gap-3 sm:grid-cols-3">
                    <div>
                      <Label htmlFor="style_primary_color">Primary color</Label>
                      <Input id="style_primary_color" name="style_primary_color" defaultValue={settings.style.primary_color} />
                    </div>
                    <div>
                      <Label htmlFor="style_accent_color">Accent color</Label>
                      <Input id="style_accent_color" name="style_accent_color" defaultValue={settings.style.accent_color} />
                    </div>
                    <div>
                      <Label htmlFor="style_radius">Corner radius (px)</Label>
                      <Input id="style_radius" name="style_radius" defaultValue={settings.style.radius} />
                    </div>
                  </div>
                </div>

                {/* Product Template */}
                <div className="space-y-3">
                  <h4 className="text-sm font-semibold text-slate-700">Product Card Template</h4>
                  <div className="grid gap-2 sm:grid-cols-2">
                    {(["show_image", "show_sku", "show_category", "show_description", "show_price_aud", "show_price_lkr", "show_view_link"] as const).map((key) => (
                      <label key={key} className="flex items-center gap-2 text-sm">
                        <input
                          type="checkbox"
                          name={`pt_${key}`}
                          defaultChecked={settings.product_template[key] !== false}
                          className="h-4 w-4 rounded border-slate-300"
                        />
                        {key.replace("show_", "").replace(/_/g, " ")}
                      </label>
                    ))}
                  </div>
                  <div>
                    <Label htmlFor="pt_custom_label">Custom label (added to each product card)</Label>
                    <Input id="pt_custom_label" name="pt_custom_label" defaultValue={settings.product_template.custom_label ?? ""} />
                  </div>
                </div>

                <Button type="submit">Save Settings</Button>
              </form>
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
