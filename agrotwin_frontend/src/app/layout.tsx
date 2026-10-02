import type { Metadata } from "next";
import { Geist, Geist_Mono, Merriweather, Noto_Sans } from "next/font/google";
import "./globals.css";
import TopNavigation from "@/components/layout/TopNavigation";
import PageTransition from "@/components/layout/PageTransition";
import Footer from "@/components/layout/Footer";
import { LanguageProvider } from "@/contexts/LanguageContext";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

// Government-document typography: a serious serif for headings, a clean
// sans (with Devanagari support for Marathi/Hindi) for body text.
const merriweather = Merriweather({
  variable: "--font-heading",
  subsets: ["latin"],
  weight: ["700", "900"],
});

const notoSans = Noto_Sans({
  variable: "--font-body",
  subsets: ["latin", "devanagari"],
  weight: ["400", "500", "600", "700"],
});

export const metadata: Metadata = {
  title: "Kisan Saathi | Living Digital Twin",
  description: "Evidence-grounded farm digital twin for continuous nutrient monitoring and sustainable fertilizer optimization.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className={`${geistSans.variable} ${geistMono.variable} ${merriweather.variable} ${notoSans.variable} scroll-smooth`}>
      <body suppressHydrationWarning className="min-h-screen flex flex-col bg-background text-foreground font-sans">
        <LanguageProvider>
          <TopNavigation />
          <main className="flex-1 flex flex-col">
            <PageTransition>
              {children}
            </PageTransition>
          </main>
          <Footer />
        </LanguageProvider>
      </body>
    </html>
  );
}
