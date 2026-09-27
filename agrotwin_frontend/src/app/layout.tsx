import type { Metadata } from "next";
import React from "react";
import "./globals.css";
import Nav from "@/components/Nav";

export const metadata: Metadata = {
  title: "AgroTwin AI — Sustainable Fertilizer Optimizer",
  description: "Evidence-grounded digital twin for continuous farm nutrient monitoring and fertilizer optimization.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-bg-light text-ink-primary font-sans antialiased">
        <Nav />
        {children}
      </body>
    </html>
  );
}
