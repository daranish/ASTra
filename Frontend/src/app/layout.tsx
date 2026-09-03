import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "ASTra — AI-Powered Codebase Analyzer",
  description:
    "Point ASTra at a GitHub repo, ask questions in plain English, get cited answers grounded in the actual source code. Built on AST-based code parsing and retrieval-augmented generation.",
  keywords: ["code analysis", "AI", "codebase", "chatbot", "RAG", "AST"],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link
          rel="preconnect"
          href="https://fonts.gstatic.com"
          crossOrigin="anonymous"
        />
      </head>
      <body className="antialiased">{children}</body>
    </html>
  );
}
