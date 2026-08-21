import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "MemVault — Institution Portal",
  description: "School & college photo management with face-tagging and cohort search",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-slate-50 text-slate-900 antialiased">{children}</body>
    </html>
  );
}
