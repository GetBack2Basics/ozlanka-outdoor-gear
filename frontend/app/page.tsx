import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { backendFetch } from "@/lib/backend";
import { CurrencyConverter, PriceDisplay } from "@/components/CurrencyConverter";

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
  const response = await backendFetch("/products");
  const products: Product[] = response.ok ? await response.json() : [];

  // Get the conversion rate from the first product or use default
  const defaultRate = products[0]?.price_lkr && products[0]?.price_aud 
    ? Math.round((products[0].price_lkr / products[0].price_aud) * 100) / 100
    : 190;

  return (
    <main className="space-y-8">
      <section className="relative rounded-3xl bg-slate-950 p-8 text-white">
        <CurrencyConverter />
        <Badge className="bg-amber-300 text-slate-950">MVP</Badge>
        <h1 className="mt-4 text-4xl font-bold">OzLanka Outdoor Gear</h1>
        <p className="mt-3 max-w-2xl text-slate-200">
          Request outdoor gear from Australia with manual approval, LKR pricing, and clear shipping and customs terms.
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
          "8 weeks shipping target",
          "Customer pays customs in Colombo",
          "Handling fee defaults to 25%",
        ].map((item) => (
          <Card key={item}>
            <CardTitle>{item}</CardTitle>
            <CardContent>
              <p className="text-sm text-slate-600">{item}</p>
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
                <a
                  href={buildProductPageUrl(product.source_url)}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="block"
                >
                  {product.image_url ? (
                    <img
                      src={product.image_url}
                      alt={product.name}
                      className="h-40 w-full rounded-md object-cover"
                    />
                  ) : (
                    <div className="h-40 w-full rounded-md bg-slate-100 flex items-center justify-center">
                      <span className="text-slate-400 text-sm text-center px-4 line-clamp-3">{product.name}</span>
                    </div>
                  )}
                </a>
                {product.description ? (
                  <p className="line-clamp-3 text-sm text-slate-600">{product.description}</p>
                ) : null}
                <div className="flex items-center justify-between">
                  <PriceDisplay priceAud={product.price_aud} rate={defaultRate} />
                  <a
                    href={buildProductPageUrl(product.source_url)}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-xs text-blue-600 hover:underline"
                  >
                    View on 4WD Supacentre →
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
