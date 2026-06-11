import React from "react";
import Breadcrumb from "@/components/Breadcrumb";

export default function LibraryLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top navigation bar */}
      <Breadcrumb />

      {/* Main view */}
      <main className="flex-1 relative overflow-hidden">
        {children}
      </main>
    </div>
  );
}
