import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "RamiBot Osiris Adapter Runtime",
  description: "Internal API-only adapter runtime owned by RamiBot.",
  robots: { index: false, follow: false },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}