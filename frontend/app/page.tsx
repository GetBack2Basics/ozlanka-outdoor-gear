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
  category: string | null;
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

  const defaultRate = products[0]?.price_lkr && products[0]?.price_aud
    ? Math.round((products[0].price_lkr / products[0].price_aud) * 100) / 100
    : 190;

  const categoryMap = new Map<string, Product[]>();
  for (const product of products) {
    const cat = product.category || "Other";
    if (!categoryMap.has(cat)) {
      categoryMap.set(cat, []);
    }
    categoryMap.get(cat)!.push(product);
  }

  const sortedCategories = Array.from(categoryMap.entries()).sort((a, b) => a[0].localeCompare(b[0]));

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
        <h2 className="text-2xl font-semibold">Shop by Category</h2>
        <p className="text-sm text-slate-500">{sortedCategories.length} categories available</p>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {sortedCategories.map(([category, catProducts]) => {
            const featured = catProducts[0];
            return (
              <Card key={category} className="overflow-hidden">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    <CardTitle>{category}</CardTitle>
                    <span className="text-xs text-slate-400">{catProducts.length} items</span>
                  </div>
                  {featured.sku ? (
                    <span className="text-xs text-slate-500">SKU: {featured.sku}</span>
                  ) : null}
                </CardHeader>
                <CardContent className="space-y-3">
                  <Link
                    href={`/category/${encodeURIComponent(category)}`}
                    className="block"
                  >
                    {featured.image_url ? (
                      <img
                        src={featured.image_url}
                        alt={featured.name}
                        className="h-40 w-full rounded-md object-cover"
                      />
                    ) : (
                      <div className="h-40 w-full rounded-md bg-slate-100 flex items-center justify-center">
                        <span className="text-slate-400 text-sm text-center px-4 line-clamp-3">{featured.name}</span>
                      </div>
                    )}
                  </Link>
                  <p className="font-medium text-sm">{featured.name}</p>
                  {featured.description ? (
                    <p className="line-clamp-2 text-sm text-slate-600">{featured.description}</p>
                  ) : null}
                  <div className="flex items-center justify-between">
                    <PriceDisplay priceAud={featured.price_aud} rate={defaultRate} />
                    <Link
                      href={`/category/${encodeURIComponent(category)}`}
                      className="text-xs text-blue-600 hover:underline"
                    >
                      View all {catProducts.length} →
                    </Link>
                  </div>
                </CardContent>
              </Card>
            );
          })}
        </div>
      </section>
    </main>
  );
}
