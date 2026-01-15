import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import "@livekit/components-styles";
import { ThemeProvider } from "@/components/theme-provider";

const inter = Inter({
  subsets: ["latin"],
  variable: "--font-inter",
});

export const metadata: Metadata = {
  title: "Voara AI Voice Agent",
  description: "Real-time voice AI customer service powered by Gemini Live API",
  keywords: ["voice AI", "customer service", "Gemini", "LiveKit", "RAG"],
  authors: [{ name: "Voara AI" }],
  openGraph: {
    title: "Voara AI Voice Agent",
    description: "Real-time voice AI customer service powered by Gemini Live API",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className={`${inter.variable} font-sans antialiased`}>
        <ThemeProvider
          attribute="class"
          defaultTheme="dark"
          enableSystem
          disableTransitionOnChange
        >
          {children}
        </ThemeProvider>
      </body>
    </html>
  );
}
