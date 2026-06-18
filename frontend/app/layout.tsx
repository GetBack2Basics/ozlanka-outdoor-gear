import type { Metadata } from "next";

import "./globals.css";

const appName = process.env.NEXT_PUBLIC_APP_NAME ?? "OzLanka Outdoor Gear";
const buildDate = "20260617-ver0";

export const metadata: Metadata = {
  title: appName,
  description: "OzLanka Outdoor Gear MVP storefront and request list",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body suppressHydrationWarning>
        <div className="mx-auto max-w-6xl px-4 py-6">{children}</div>
        <div className="mx-auto max-w-6xl px-4 pb-6">
          <div className="flex justify-end">
            <span className="text-xs text-gray-500">{buildDate}</span>
          </div>
        </div>
      </body>
    </html>
  );
}
