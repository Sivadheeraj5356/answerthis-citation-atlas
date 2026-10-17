import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Citation Atlas",
  description: "Explore the citation graph around any paper indexed by OpenAlex.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
