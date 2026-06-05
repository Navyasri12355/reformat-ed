import { useCallback, useEffect, useRef, useState } from "react";
import { apiClient } from "../../../api/client";

interface TTSOptions {
  format?: string;
  onWordHighlight?: (wordIndex: number) => void;
  onEnd?: () => void;
  rateOverride?: number;
  pitchOverride?: number;
}

/**
 * Per-profile browser-voice modulation. Mirrors the backend's VOICE_PROFILES so
 * the Web Speech fallback sounds the same as the Coqui path:
 *  • dyslexia → slow & clear   • ADHD → bright & faster   • ASD → calm & steady
 */
const BROWSER_VOICE: Record<string, { rate: number; pitch: number }> = {
  dyslexia_audio: { rate: 0.8, pitch: 1.0 },
  adhd_gamified: { rate: 1.08, pitch: 1.12 },
  asd_structured: { rate: 0.92, pitch: 0.98 },
  blended: { rate: 0.95, pitch: 1.04 },
};

/**
 * Voice hook with per-neurodivergent-profile modulation. Tries server-side
 * Coqui TTS first (richer, profile-tuned audio); transparently falls back to
 * the Web Speech API with the same rate/pitch (and word-by-word highlighting)
 * when Coqui isn't available.
 */
export function useTTS({ format = "asd_structured", onWordHighlight, onEnd, rateOverride, pitchOverride }: TTSOptions = {}) {
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const objectUrlRef = useRef<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [engine, setEngine] = useState<"coqui" | "browser">("browser");
  const supported =
    typeof window !== "undefined" && ("speechSynthesis" in window || "Audio" in window);

  const cleanupAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
    if (objectUrlRef.current) {
      URL.revokeObjectURL(objectUrlRef.current);
      objectUrlRef.current = null;
    }
  }, []);

  const stop = useCallback(() => {
    if ("speechSynthesis" in window) window.speechSynthesis.cancel();
    cleanupAudio();
    setIsPlaying(false);
    setIsPaused(false);
  }, [cleanupAudio]);

  const speakBrowser = useCallback(
    (text: string) => {
      if (!("speechSynthesis" in window)) return;
      window.speechSynthesis.cancel();
      const u = new SpeechSynthesisUtterance(text);
      const v = BROWSER_VOICE[format] ?? BROWSER_VOICE.asd_structured;
      u.rate = rateOverride !== undefined && rateOverride !== null ? rateOverride : v.rate;
      u.pitch = pitchOverride !== undefined && pitchOverride !== null ? pitchOverride : v.pitch;
      u.volume = 1.0;
      if (onWordHighlight) {
        u.onboundary = (event) => {
          if (event.name === "word") {
            const idx = text.substring(0, event.charIndex).split(/\s+/).filter(Boolean).length;
            onWordHighlight(idx);
          }
        };
      }
      u.onend = () => {
        setIsPlaying(false);
        setIsPaused(false);
        onEnd?.();
      };
      u.onerror = () => setIsPlaying(false);
      setEngine("browser");
      window.speechSynthesis.speak(u);
      setIsPlaying(true);
      setIsPaused(false);
    },
    [format, onWordHighlight, onEnd, rateOverride, pitchOverride],
  );

  const speak = useCallback(
    async (text: string) => {
      stop();
      if (rateOverride !== undefined || pitchOverride !== undefined) {
        speakBrowser(text);
        return;
      }
      // Try server-side Coqui synthesis first.
      try {
        const res = await apiClient.post(
          "/tts/audio",
          { text, format },
          { responseType: "arraybuffer" },
        );
        const blob = new Blob([res.data], { type: "audio/wav" });
        const url = URL.createObjectURL(blob);
        objectUrlRef.current = url;
        const audio = new Audio(url);
        audioRef.current = audio;
        audio.onended = () => {
          setIsPlaying(false);
          setIsPaused(false);
          onEnd?.();
        };
        setEngine("coqui");
        await audio.play();
        setIsPlaying(true);
        setIsPaused(false);
      } catch {
        // 503 (Coqui not installed) / network / autoplay → browser voice.
        speakBrowser(text);
      }
    },
    [format, stop, onEnd, speakBrowser, rateOverride, pitchOverride],
  );

  const pause = useCallback(() => {
    if (engine === "coqui" && audioRef.current) audioRef.current.pause();
    else if ("speechSynthesis" in window) window.speechSynthesis.pause();
    setIsPlaying(false);
    setIsPaused(true);
  }, [engine]);

  const resume = useCallback(() => {
    if (engine === "coqui" && audioRef.current) void audioRef.current.play();
    else if ("speechSynthesis" in window) window.speechSynthesis.resume();
    setIsPlaying(true);
    setIsPaused(false);
  }, [engine]);

  useEffect(() => () => stop(), [stop]);

  return { speak, pause, resume, stop, isPlaying, isPaused, supported, engine };
}
