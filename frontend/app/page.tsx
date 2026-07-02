import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { backendFetch } from "@/lib/backend";

type Product = {
  id: number;
  name: string;
  source_name: string;
  source_url: string;
  description: string | null;
  image_url: string | null;
  sku: string | null;
  price_aud: number;
  price_lkr: number;
  handling_fee_percent: number;
};

type PublicSettings = {
  banner_title: string;
  banner_description: string;
  logo_image_url: string;
  promo_title_l: string;
  promo_text_l: string;
  promo_title_c: string;
  promo_text_c: string;
  promo_title_r: string;
  promo_text_r: string;
};

const DEFAULT_SETTINGS: PublicSettings = {
  banner_title: "OzLanka Outdoor Gear",
  banner_description: "Request outdoor gear from Australia with manual approval, LKR pricing, and clear shipping and customs terms.",
  logo_image_url: "",
  promo_title_l: "Shipping updates",
  promo_text_l: "8 weeks shipping target",
  promo_title_c: "Important",
  promo_text_c: "Customer pays customs in Colombo",
  promo_title_r: "Fees",
  promo_text_r: "Handling fee defaults to 25%",
};

function buildProductPageUrl(sourceUrl: string) {
  try {
    const url = new URL(sourceUrl);
    url.hash = "";
    url.search = "";
    const path = url.pathname.replace(/\.html$/i, "");
    if (!path || path === "/") return sourceUrl;
    return `https://www.4wdsupacentre.com.au${path}`;
  } catch {
    if (!sourceUrl.includes(".")) return `https://www.4wdsupacentre.com.au${sourceUrl.startsWith("/") ? sourceUrl : "/" + sourceUrl}`;
    return sourceUrl;
  }
}

export default async function HomePage() {
  const [productsRes, settingsRes] = await Promise.all([
    backendFetch("/products"),
    backendFetch("/public/settings"),
  ]);
  const products: Product[] = productsRes.ok ? await productsRes.json() : [];
  const settings: PublicSettings = settingsRes.ok ? await settingsRes.json() : DEFAULT_SETTINGS;

  return (
    <main className="space-y-8">
      <section className="rounded-3xl bg-slate-950 p-8 text-white">
        <Badge className="bg-amber-300 text-slate-950">MVP</Badge>
        <div className="mt-4 flex items-center gap-4">
          {settings.logo_image_url ? (
            <img src={settings.logo_image_url} alt="Logo" className="h-12 w-12 rounded-md object-cover" />
          ) : null}
          <h1 className="text-4xl font-bold">{settings.banner_title}</h1>
        </div>
        <p className="mt-3 max-w-2xl text-slate-200">
          {settings.banner_description}
        </p>
        <div className="mt-6 flex gap-3">
          <Link href="/signup" className="rounded-md bg-white px-4 py-2 text-sm font-medium text-slate-950">
            Create account
          </Link>
          <Link href="/request-list" className="rounded-md bg-slate-700 px-4 py-2 text-sm font-medium text-white">
            Request list
          </Link>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {[
          [settings.promo_title_l, settings.promo_text_l],
          [settings.promo_title_c, settings.promo_text_c],
          [settings.promo_title_r, settings.promo_text_r],
        ].map(([title, body]) => (
          <Card key={title}>
            <CardTitle>{title}</CardTitle>
            <CardContent>
              <p className="text-sm text-slate-600">{body}</p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="space-y-4">
        <h2 className="text-2xl font-semibold">Live products</h2>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => (
            <Card key={product.id} className="overflow-hidden">
              <CardHeader>
                <CardTitle>{product.name}</CardTitle>
                {product.sku ? (
                  <span className="text-xs text-slate-500">SKU: {product.sku}</span>
                ) : null}
              </CardHeader>
              <CardContent className="space-y-3">
                {product.image_url ? (
                  <a
                    href={buildProductPageUrl(product.source_url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="block"
                  >
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="h-40 w-full rounded-md object-cover"
                    />
                  </a>
                ) : null}
                <p className="text-sm text-slate-600">{product.source_name}</p>
                {product.description ? (
                  <p className="line-clamp-3 text-sm text-slate-600">{product.description}</p>
                ) : null}
                <div className="flex items-end justify-between">
                  <div>
                    <p className="text-lg font-semibold">AUD {product.price_aud.toFixed(2)}</p>
                    <p className="text-sm">LKR {product.price_lkr.toFixed(2)}</p>
                  </div>
                  <a
                    href={buildProductPageUrl(product.source_url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-sm font-medium underline"
                  >
                    4WD Supacentre listing
                  </a>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
