import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { backendFetch } from "@/lib/backend";
import { PriceDisplay } from "@/components/CurrencyConverter";

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

type SiteSettings = {
  hero_title: string;
  hero_subtitle: string;
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

export default async function CategoryPage({ params }: { params: { slug: string } }) {
  const categoryName = decodeURIComponent(params.slug);
  const [productsRes, settingsRes, allRes] = await Promise.all([
    backendFetch(`/products?category=${encodeURIComponent(categoryName)}`),
    backendFetch("/admin/settings/public"),
    backendFetch("/products"),
  ]);
  const products: Product[] = productsRes.ok ? await productsRes.json() : [];
  const settings: SiteSettings = settingsRes.ok ? await settingsRes.json() : {
    hero_title: "OzLanka Outdoor Gear",
    hero_subtitle: "Request outdoor gear from Australia with manual approval, LKR pricing, and clear shipping and customs terms.",
    footer_text: "",
    product_template: { show_image: true, show_sku: true, show_category: true, show_description: true, show_price_aud: true, show_price_lkr: true, show_view_link: true, custom_label: "" },
  };
  const allProducts: Product[] = allRes.ok ? await allRes.json() : [];

  const defaultRate = products[0]?.price_lkr && products[0]?.price_aud
    ? Math.round((products[0].price_lkr / products[0].price_aud) * 100) / 100
    : 190;

  const categoryMap = new Map<string, Product[]>();
  for (const product of allProducts) {
    const cat = product.category || "Other";
    if (!categoryMap.has(cat)) {
      categoryMap.set(cat, []);
    }
    categoryMap.get(cat)!.push(product);
  }
  const sortedCategories = Array.from(categoryMap.entries()).sort((a, b) => a[0].localeCompare(b[0]));
  const tmpl = settings.product_template;

  return (
    <div className="flex flex-col gap-6 md:flex-row">
      <aside className="w-full shrink-0 md:w-64">
        <div className="rounded-xl border border-slate-200 bg-white">
          <div className="px-4 py-3 border-b border-slate-100">
            <h3 className="text-sm font-semibold text-slate-900">Categories</h3>
          </div>
          <div className="p-3">
            <ul className="space-y-1 text-sm">
              {sortedCategories.map(([category, catProducts]) => (
                <li key={category}>
                  <Link
                    href={`/category/${encodeURIComponent(category)}`}
                    className={`flex items-center justify-between rounded-md px-3 py-1.5 transition-colors ${
                      category === categoryName
                        ? "bg-slate-900 text-white"
                        : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                    }`}
                  >
                    <span className="truncate">{category}</span>
                    <span className="ml-2 text-xs opacity-70">{catProducts.length}</span>
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      </aside>

      <div className="flex-1 space-y-4">
        <Link href="/" className="text-sm text-blue-600 hover:underline">
          ← Back to all categories
        </Link>
        <h1 className="mt-2 text-4xl font-bold">{categoryName}</h1>
        <p className="text-sm text-slate-500">{products.length} products in this category</p>
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {products.map((product) => {
            const productUrl = buildProductPageUrl(product.source_url);
            return (
              <Card key={product.id} className="overflow-hidden">
                <CardHeader>
                  <div className="flex items-center justify-between">
                    {tmpl.show_category ? (
                      <span className="text-xs text-slate-500">{product.category}</span>
                    ) : null}
                    {tmpl.show_sku && product.sku ? (
                      <span className="text-xs text-slate-400">SKU: {product.sku}</span>
                    ) : null}
                  </div>
                </CardHeader>
                <CardContent className="space-y-3">
                  {tmpl.show_image ? (
                    <Link href={productUrl} target="_blank" rel="noopener noreferrer" className="block">
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
                    </Link>
                  ) : null}
                  <p className="font-medium text-sm">{product.name}</p>
                  {tmpl.show_description && product.description ? (
                    <p className="line-clamp-2 text-sm text-slate-600">{product.description}</p>
                  ) : null}
                  <div className="flex items-center justify-between">
                    <PriceDisplay priceAud={product.price_aud} rate={defaultRate} />
                    {tmpl.show_view_link ? (
                      <Link
                        href={productUrl}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-xs text-blue-600 hover:underline"
                      >
                        View on 4WD Supacentre
                      </Link>
                    ) : null}
                  </div>
                </CardContent>
              </Card>
            );
          })}
          {products.length === 0 ? (
            <Card>
              <CardContent className="p-6 text-sm text-slate-600">No products found in this category.</CardContent>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
}
