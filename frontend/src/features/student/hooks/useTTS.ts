import { useCallback, useEffect, useRef, useState } from "react";

interface TTSOptions {
  onWordHighlight?: (wordIndex: number) => void;
  onEnd?: () => void;
}

/** Thin wrapper around the Web Speech API with word-boundary highlighting. */
export function useTTS({ onWordHighlight, onEnd }: TTSOptions = {}) {
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const supported = typeof window !== "undefined" && "speechSynthesis" in window;

  const speak = useCallback(
    (text: string) => {
      if (!supported) return;
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.85;
      utterance.pitch = 1.0;
      utterance.volume = 1.0;

      const voices = window.speechSynthesis.getVoices();
      const preferred = voices.find(
        (v) => v.lang.startsWith("en") && (v.name.includes("Google") || v.name.includes("Alex")),
      );
      if (preferred) utterance.voice = preferred;

      if (onWordHighlight) {
        utterance.onboundary = (event) => {
          if (event.name === "word") {
            const preceding = text.substring(0, event.charIndex);
            const wordIndex = preceding.split(/\s+/).filter(Boolean).length;
            onWordHighlight(wordIndex);
          }
        };
      }
      utterance.onend = () => {
        setIsPlaying(false);
        setIsPaused(false);
        onEnd?.();
      };
      utterance.onerror = () => setIsPlaying(false);

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
      setIsPlaying(true);
      setIsPaused(false);
    },
    [supported, onWordHighlight, onEnd],
  );

  const pause = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.pause();
    setIsPlaying(false);
    setIsPaused(true);
  }, [supported]);

  const resume = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.resume();
    setIsPlaying(true);
    setIsPaused(false);
  }, [supported]);

  const stop = useCallback(() => {
    if (!supported) return;
    window.speechSynthesis.cancel();
    setIsPlaying(false);
    setIsPaused(false);
  }, [supported]);

  // Stop any speech if the component using this hook unmounts.
  useEffect(() => () => stop(), [stop]);

  return { speak, pause, resume, stop, isPlaying, isPaused, supported };
}
