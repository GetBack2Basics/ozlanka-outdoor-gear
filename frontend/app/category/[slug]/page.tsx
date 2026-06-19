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

export default async function CategoryPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = await params;
  const categoryName = decodeURIComponent(slug);

  const response = await backendFetch("/products");
  const allProducts: Product[] = response.ok ? await response.json() : [];

  const products = allProducts.filter(
    (p) => (p.category || "Other") === categoryName
  );

  const defaultRate = allProducts[0]?.price_lkr && allProducts[0]?.price_aud
    ? Math.round((allProducts[0].price_lkr / allProducts[0].price_aud) * 100) / 100
    : 190;

  return (
    <main className="space-y-8">
      <section className="relative rounded-3xl bg-slate-950 p-8 text-white">
        <CurrencyConverter />
        <Badge className="bg-amber-300 text-slate-950">{categoryName}</Badge>
        <h1 className="mt-4 text-4xl font-bold">{categoryName}</h1>
        <p className="mt-3 max-w-2xl text-slate-200">
          {products.length} products in this category from 4WD Supacentre, Australia.
        </p>
        <div className="mt-6 flex gap-3">
          <Link href="/" className="rounded-md bg-white px-4 py-2 text-sm font-medium text-slate-950">
            ← Back to all categories
          </Link>
        </div>
      </section>

      {products.length === 0 ? (
        <p className="text-slate-500 text-center py-12">No products found in this category.</p>
      ) : (
        <section className="space-y-4">
          <h2 className="text-2xl font-semibold">{products.length} Products</h2>
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
      )}
    </main>
  );
}
