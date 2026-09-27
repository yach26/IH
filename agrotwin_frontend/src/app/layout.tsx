import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import TopNavigation from "@/components/layout/TopNavigation";
import PageTransition from "@/components/layout/PageTransition";
import { LanguageProvider } from "@/contexts/LanguageContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AgroTwin AI | Living Digital Twin",
  description: "Evidence-grounded farm digital twin for continuous nutrient monitoring and sustainable fertilizer optimization.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} scroll-smooth`}>
      <body suppressHydrationWarning className="min-h-screen flex flex-col bg-background text-foreground font-sans">
        <LanguageProvider>
          <TopNavigation />
          <main className="flex-1 flex flex-col">
            <PageTransition>
              {children}
            </PageTransition>
          </main>
        </LanguageProvider>
      </body>
    </html>
  );
}
