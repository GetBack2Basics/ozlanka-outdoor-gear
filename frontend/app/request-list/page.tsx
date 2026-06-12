import { cookies } from "next/headers";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { backendFetchWithAuth } from "@/lib/backend";

type RequestItem = {
  id: number;
  product_name: string;
  quantity: number;
  notes: string | null;
  status: string;
};

export default async function RequestListPage() {
  const cookieStore = await cookies();
  const hasToken = Boolean(cookieStore.get("ozlanka_token")?.value);
  const response = hasToken ? await backendFetchWithAuth("/requests/me") : null;
  const requests: RequestItem[] = response?.ok ? await response.json() : [];

  return (
    <div className="grid gap-6 lg:grid-cols-2">
      <Card>
        <CardHeader>
          <CardTitle>Submit a request</CardTitle>
        </CardHeader>
        <CardContent>
          <form action="/api/request-list" method="post" className="space-y-4">
            <div>
              <Label htmlFor="product_name">Product name</Label>
              <Input id="product_name" name="product_name" required />
            </div>
            <div>
              <Label htmlFor="quantity">Quantity</Label>
              <Input id="quantity" name="quantity" type="number" min="1" defaultValue="1" />
            </div>
            <div>
              <Label htmlFor="notes">Notes</Label>
              <Textarea id="notes" name="notes" rows={4} />
            </div>
            <Button type="submit">Add to request list</Button>
          </form>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>My requests</CardTitle>
        </CardHeader>
        <CardContent>
          {requests.length === 0 ? <p className="text-sm text-slate-600">No requests yet.</p> : null}
          <div className="space-y-3">
            {requests.map((request) => (
              <div key={request.id} className="rounded-md border border-slate-200 p-3">
                <p className="font-medium">{request.product_name}</p>
                <p className="text-sm text-slate-600">
                  Qty {request.quantity} · {request.status}
                </p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
