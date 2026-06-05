import { useCallback, useEffect, useRef } from "react";
import { sessionsApi } from "../../../api";

interface TrackOptions {
  sessionId: string;
  atomId: string;
  transformedAtomId: string;
}

/** Records passive behavioural signals for the currently-rendered atom. */
export function useSessionTracker({ sessionId, atomId, transformedAtomId }: TrackOptions) {
  const atomStartRef = useRef<number>(Date.now());
  const retryCountRef = useRef<number>(0);
  const completedRef = useRef<boolean>(false);

  const trackEvent = useCallback(
    async (eventType: string, extra: Record<string, unknown> = {}) => {
      const elapsed = Date.now() - atomStartRef.current;
      try {
        await sessionsApi.event(sessionId, {
          atom_id: atomId,
          transformed_atom_id: transformedAtomId,
          event_type: eventType,
          time_on_atom_ms: elapsed,
          retry_count: retryCountRef.current,
          payload: extra,
        });
      } catch {
        // Fire-and-forget — analytics must never block the learning UX.
      }
    },
    [sessionId, atomId, transformedAtomId],
  );

  useEffect(() => {
    atomStartRef.current = Date.now();
    retryCountRef.current = 0;
    completedRef.current = false;
    void trackEvent("atom_start");
    return () => {
      const elapsed = Date.now() - atomStartRef.current;
      // Only count an exit if the student spent real time and didn't complete.
      if (!completedRef.current && elapsed > 2000) {
        void trackEvent("exit_mid_atom");
      }
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [atomId]);

  const markComplete = useCallback(() => {
    completedRef.current = true;
    void trackEvent("atom_complete");
  }, [trackEvent]);

  const markRetry = useCallback(() => {
    retryCountRef.current += 1;
    void trackEvent("atom_retry");
  }, [trackEvent]);

  const markSkip = useCallback(() => void trackEvent("atom_skip"), [trackEvent]);
  const markAudioPlay = useCallback(() => void trackEvent("audio_play"), [trackEvent]);

  return { markComplete, markRetry, markSkip, markAudioPlay };
}
