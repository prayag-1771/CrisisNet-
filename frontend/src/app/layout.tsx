import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "CrisisNet — AI Crisis Triage Dashboard",
  description:
    "Research Prototype: Multi-agent crisis triage platform using LangGraph. For demonstration purposes only, using synthetic test data.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap"
          rel="stylesheet"
        />
      </head>
      <body className="grid-bg">{children}</body>
    </html>
  );
}
