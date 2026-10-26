import type { Metadata } from "next";
import { DM_Sans, Playfair_Display } from "next/font/google";
import "./globals.css";
import { Concierge } from "@/components/concierge";
const dmSans = DM_Sans({ variable: "--font-dm-sans", subsets: ["latin"] });
const playfair = Playfair_Display({ variable: "--font-playfair", subsets: ["latin"] });
export const metadata: Metadata = { title: "TixBee | Make room for wonder", description: "Thoughtful ticketing for India's museums, heritage landmarks, and cultural escapes." };
export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) { return <html lang="en" className={`${dmSans.variable} ${playfair.variable}`}><body>{children}<Concierge /></body></html>; }
