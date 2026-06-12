import Link from "next/link";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { backendFetch } from "@/lib/backend";

type Product = {
  id: number;
  name: string;
  source_name: string;
  price_aud: number;
  price_lkr: number;
  handling_fee_percent: number;
};

export default async function HomePage() {
  const response = await backendFetch("/products");
  const products: Product[] = response.ok ? await response.json() : [];

  return (
    <main className="space-y-8">
      <section className="rounded-3xl bg-slate-950 p-8 text-white">
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
            <Card key={product.id}>
              <CardHeader>
                <CardTitle>{product.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-slate-600">{product.source_name}</p>
                <p className="text-lg font-semibold">AUD {product.price_aud.toFixed(2)}</p>
                <p className="text-sm">LKR {product.price_lkr.toFixed(2)}</p>
              </CardContent>
            </Card>
          ))}
        </div>
      </section>
    </main>
  );
}
