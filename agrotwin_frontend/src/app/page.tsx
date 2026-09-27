"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    router.replace("/dashboard");
  }, [router]);

  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="inline-block animate-spin w-8 h-8 border-4 border-agri-primary border-t-transparent rounded-full mb-3"></div>
        <p className="text-sm text-ink-secondary">Redirecting to Dashboard...</p>
      </div>
    </div>
  );
}
