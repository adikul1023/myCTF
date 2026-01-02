import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Investigation Portal",
  description: "Digital Forensics and Incident Response Training Platform",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body>
        {children}
      </body>
    </html>
  );
}
