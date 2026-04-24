import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "Voice Robot - AI Voice Assistant",
  description: "Asisten AI suara yang bisa berbicara dalam Bahasa Indonesia dan Inggris. Gunakan mikrofon atau ketik pesan untuk berinteraksi dengan Voice Robot.",
  keywords: ["Voice Robot", "AI", "Voice Assistant", "TTS", "ASR", "Indonesia", "Next.js"],
  authors: [{ name: "Voice Robot Team" }],
  icons: {
    icon: "https://z-cdn.chatglm.cn/z-ai/static/logo.svg",
  },
  openGraph: {
    title: "Voice Robot - AI Voice Assistant",
    description: "Asisten AI suara interaktif dengan dukungan Bahasa Indonesia",
    type: "website",
  },
  twitter: {
    card: "summary_large_image",
    title: "Voice Robot - AI Voice Assistant",
    description: "Asisten AI suara interaktif dengan dukungan Bahasa Indonesia",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning className="dark">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased bg-background text-foreground`}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
