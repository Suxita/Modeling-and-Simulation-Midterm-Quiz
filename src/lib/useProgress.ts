"use client";

import { useCallback, useEffect, useState } from "react";

/** question id -> index of the option the user picked (locked once chosen) */
export type Answers = Record<string, number>;

export function readAnswers(key: string): Answers {
  try {
    const raw = window.localStorage.getItem(key);
    if (!raw) return {};
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? (parsed as Answers) : {};
  } catch {
    return {};
  }
}

function writeAnswers(key: string, value: Answers) {
  try {
    window.localStorage.setItem(key, JSON.stringify(value));
  } catch {
    /* storage unavailable (private mode, quota) – progress just won't persist */
  }
}

export function useProgress(key: string) {
  const [answers, setAnswers] = useState<Answers>({});
  const [ready, setReady] = useState(false);

  useEffect(() => {
    setAnswers(readAnswers(key));
    setReady(true);
  }, [key]);

  const answer = useCallback(
    (id: string, choice: number) => {
      setAnswers((prev) => {
        if (prev[id] !== undefined) return prev; // answers are final
        const next = { ...prev, [id]: choice };
        writeAnswers(key, next);
        return next;
      });
    },
    [key]
  );

  const reset = useCallback(() => {
    setAnswers({});
    writeAnswers(key, {});
  }, [key]);

  return { answers, ready, answer, reset };
}
