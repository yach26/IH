// agrotwin_frontend/src/lib/voice.ts

export type VoiceState = "idle" | "playing" | "paused" | "error";

interface SpeakOptions {
  text: string;
  lang: string;
  onStateChange?: (state: VoiceState) => void;
  onError?: (err: string) => void;
}

let currentUtterance: SpeechSynthesisUtterance | null = null;
let currentAudio: HTMLAudioElement | null = null;

// Ensure voices are loaded
let voicesLoaded = false;
if (typeof window !== "undefined" && window.speechSynthesis) {
  window.speechSynthesis.onvoiceschanged = () => {
    voicesLoaded = true;
  };
}

export function stopSpeech() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.cancel();
  }
  if (currentAudio) {
    currentAudio.pause();
    currentAudio.currentTime = 0;
    currentAudio = null;
  }
  currentUtterance = null;
}

export function pauseSpeech() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.pause();
  }
  if (currentAudio) {
    currentAudio.pause();
  }
}

export function resumeSpeech() {
  if (typeof window !== "undefined" && window.speechSynthesis) {
    window.speechSynthesis.resume();
  }
  if (currentAudio) {
    currentAudio.play().catch(() => {});
  }
}

export async function speak({ text, lang, onStateChange, onError }: SpeakOptions) {
  stopSpeech();
  
  if (!text) return;
  
  onStateChange?.("playing");
  
  // Try Web Speech API first
  if (typeof window !== "undefined" && window.speechSynthesis) {
    const voices = window.speechSynthesis.getVoices();
    // Try to find matching language (e.g., 'mr-IN', 'hi-IN')
    let voice = voices.find(v => v.lang.startsWith(lang));
    
    // Fallback: if marathi is not found, hindi can often read devanagari reasonably well
    if (!voice && lang.startsWith("mr")) {
        voice = voices.find(v => v.lang.startsWith("hi"));
    }

    if (voice) {
      // Chunk text into sentences to bypass browser limits
      // Match on standard punctuation or devanagari danda
      const sentences = text.match(/[^.!?।]+[.!?।]+/g) || [text];
      
      let i = 0;
      const playNext = () => {
        if (i >= sentences.length) {
            onStateChange?.("idle");
            return;
        }
        
        const utterance = new SpeechSynthesisUtterance(sentences[i].trim());
        utterance.voice = voice;
        utterance.lang = voice.lang;
        utterance.rate = 0.9; // Slightly slower for better comprehension
        
        utterance.onend = () => {
            i++;
            playNext();
        };
        
        utterance.onerror = (e) => {
            console.error("SpeechSynthesis error:", e);
            if (i === 0) {
              // Only fallback to backend if the first chunk failed
               fallbackToBackendTTS(text, lang, onStateChange, onError);
            } else {
               onError?.("Playback interrupted");
               onStateChange?.("error");
            }
        };
        
        currentUtterance = utterance;
        window.speechSynthesis.speak(utterance);
      };
      
      playNext();
      return;
    }
  }
  
  // Fallback to Backend TTS if Web Speech API isn't available or lacks voice
  fallbackToBackendTTS(text, lang, onStateChange, onError);
}

async function fallbackToBackendTTS(text: string, lang: string, onStateChange?: (state: VoiceState) => void, onError?: (err: string) => void) {
  try {
    const baseLang = lang.split("-")[0]; // e.g., mr-IN -> mr
    const url = `/api/backend/tts?text=${encodeURIComponent(text)}&lang=${encodeURIComponent(baseLang)}`;
    
    const res = await fetch(url, { method: 'POST' });
    if (!res.ok) {
        throw new Error("Backend TTS failed");
    }
    
    const blob = await res.blob();
    const audioUrl = URL.createObjectURL(blob);
    
    currentAudio = new Audio(audioUrl);
    
    currentAudio.onended = () => {
        onStateChange?.("idle");
        URL.revokeObjectURL(audioUrl);
    };
    
    currentAudio.onerror = () => {
        onError?.("Audio playback failed");
        onStateChange?.("error");
        URL.revokeObjectURL(audioUrl);
    };
    
    await currentAudio.play();
  } catch (err) {
    console.error(err);
    onError?.("Voice synthesis not available");
    onStateChange?.("error");
  }
}
