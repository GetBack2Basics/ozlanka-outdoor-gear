import { cookies } from "next/headers";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ScrapePanel } from "@/components/admin/scrape-panel";
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
  content_settings: {
    banner_title: string;
    banner_description: string;
    promo_text_l: string;
    promo_text_c: string;
    promo_text_r: string;
  };
};

export default async function AdminPage() {
  const cookieStore = await cookies();
  const token = cookieStore.get("ozlanka_token")?.value;
  const response = token ? await backendFetchWithAuth("/admin/dashboard") : null;
  const dashboard: Dashboard | null = response?.ok ? await response.json() : null;

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
              <CardTitle>Homepage text</CardTitle>
            </CardHeader>
            <CardContent>
              <form action="/api/admin/content" method="post" className="space-y-3">
                <div className="grid gap-3 md:grid-cols-2">
                  <div>
                    <label className="block text-sm font-medium">Banner title</label>
                    <input
                      name="banner_title"
                      defaultValue={dashboard.content_settings.banner_title}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium">Banner description</label>
                    <input
                      name="banner_description"
                      defaultValue={dashboard.content_settings.banner_description}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                </div>
                <div className="grid gap-3 md:grid-cols-3">
                  <div>
                    <label className="block text-sm font-medium">Text L</label>
                    <input
                      name="promo_text_l"
                      defaultValue={dashboard.content_settings.promo_text_l}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium">Text C</label>
                    <input
                      name="promo_text_c"
                      defaultValue={dashboard.content_settings.promo_text_c}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium">Text R</label>
                    <input
                      name="promo_text_r"
                      defaultValue={dashboard.content_settings.promo_text_r}
                      className="mt-1 w-full rounded-md border border-slate-300 px-3 py-2"
                    />
                  </div>
                </div>
                <Button type="submit" variant="secondary">Save homepage text</Button>
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
                    <button type="submit" className="rounded-md border border-slate-300 px-3 py-2 text-sm hover:bg-slate-50">
                      Approve
                    </button>
                  </form>
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </div>
  );
}
