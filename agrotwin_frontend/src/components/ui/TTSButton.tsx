"use client";

import React, { useState, useEffect } from "react";
import { Volume2, VolumeX, Loader2 } from "lucide-react";
import { speak, stopSpeech, VoiceState } from "@/lib/voice";
import { useLanguage } from "@/contexts/LanguageContext";

export default function TTSButton({ textToRead }: { textToRead: string }) {
  const { language, t } = useLanguage();
  const [state, setState] = useState<VoiceState>("idle");
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    return () => {
      stopSpeech();
    };
  }, []);

  if (!mounted) return null;

  const handleToggle = () => {
    if (state === "playing") {
      stopSpeech();
      setState("idle");
    } else {
      setState("playing"); // optimistic
      speak({
        text: textToRead,
        lang: language,
        onStateChange: setState,
        onError: (err) => {
          console.error("TTS Error:", err);
          alert(err);
        }
      });
    }
  };

  return (
    <button
      onClick={handleToggle}
      className={`inline-flex items-center gap-2 min-h-11 border border-border text-sm font-semibold px-5 py-2 rounded-lg transition-colors ${
        state === "playing" 
          ? "bg-primary text-white border-primary hover:bg-primary-hover" 
          : "bg-surface text-foreground hover:bg-background"
      }`}
      aria-label={state === "playing" ? "Stop reading" : "Listen to report"}
    >
      {state === "playing" ? (
        <>
          <VolumeX className="w-4 h-4" aria-hidden="true" />
          <span>Stop</span>
        </>
      ) : (
        <>
          <Volume2 className="w-4 h-4" aria-hidden="true" />
          <span>{t("report.listen") || "Listen"}</span>
        </>
      )}
    </button>
  );
}
