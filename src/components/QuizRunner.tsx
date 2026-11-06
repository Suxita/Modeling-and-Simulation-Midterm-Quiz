"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import type { Question } from "@/lib/data";
import { useProgress } from "@/lib/useProgress";
import RichText from "./RichText";

const LETTERS = ["ა", "ბ", "გ", "დ"];

type Filter = "all" | "unanswered" | "wrong";

type Props = {
  title: string;
  kicker: string;
  questions: Question[];
  storageKey: string;
  backHref: string;
  backLabel: string;
  /** practice mode: show filters + shuffle, label each question with its variant */
  practice?: boolean;
};

function mulberry32(seed: number) {
  let a = seed >>> 0;
  return () => {
    a = (a + 0x6d2b79f5) >>> 0;
    let t = a;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function shuffled<T>(items: T[], seed: number): T[] {
  const rnd = mulberry32(seed);
  const out = items.slice();
  for (let i = out.length - 1; i > 0; i--) {
    const j = Math.floor(rnd() * (i + 1));
    [out[i], out[j]] = [out[j], out[i]];
  }
  return out;
}

export default function QuizRunner({
  title,
  kicker,
  questions,
  storageKey,
  backHref,
  backLabel,
  practice = false,
}: Props) {
  const { answers, ready, answer, reset } = useProgress(storageKey);

  const byId = useMemo(() => new Map(questions.map((q) => [q.id, q])), [questions]);
  const baseIds = useMemo(() => questions.map((q) => q.id), [questions]);

  const [filter, setFilter] = useState<Filter>("all");
  const [seed, setSeed] = useState<number | null>(null);
  const [queue, setQueue] = useState<string[]>(baseIds);
  const [pos, setPos] = useState(0);

  // Jump to the first unanswered question once saved progress is loaded.
  useEffect(() => {
    if (!ready) return;
    const first = queue.findIndex((id) => answers[id] === undefined);
    setPos(first === -1 ? 0 : first);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [ready]);

  const applyView = useCallback(
    (nextFilter: Filter, nextSeed: number | null) => {
      const order = nextSeed === null ? baseIds : shuffled(baseIds, nextSeed);
      const next = order.filter((id) => {
        const q = byId.get(id)!;
        const a = answers[id];
        if (nextFilter === "unanswered") return a === undefined;
        if (nextFilter === "wrong") return a !== undefined && a !== q.correct;
        return true;
      });
      setFilter(nextFilter);
      setSeed(nextSeed);
      setQueue(next);
      setPos(0);
    },
    [answers, baseIds, byId]
  );

  const total = questions.length;
  const answeredCount = questions.filter((q) => answers[q.id] !== undefined).length;
  const correctCount = questions.filter((q) => answers[q.id] === q.correct).length;
  const wrongQuestions = questions.filter(
    (q) => answers[q.id] !== undefined && answers[q.id] !== q.correct
  );
  const finished = answeredCount === total;

  const current = queue.length ? byId.get(queue[Math.min(pos, queue.length - 1)]) : undefined;
  const chosen = current ? answers[current.id] : undefined;
  const answered = chosen !== undefined;

  const go = useCallback(
    (p: number) => setPos(Math.max(0, Math.min(queue.length - 1, p))),
    [queue.length]
  );

  const pick = useCallback(
    (i: number) => {
      if (!current || answers[current.id] !== undefined) return;
      answer(current.id, i);
    },
    [answer, answers, current]
  );

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.metaKey || e.ctrlKey || e.altKey) return;
      if (e.key === "ArrowRight") go(pos + 1);
      else if (e.key === "ArrowLeft") go(pos - 1);
      else if (["1", "2", "3", "4"].includes(e.key)) pick(Number(e.key) - 1);
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [go, pick, pos]);

  const jumpToQuestion = (id: string) => {
    // make sure the question is in the current queue; otherwise switch to the full list
    let idx = queue.indexOf(id);
    if (idx === -1) {
      const order = seed === null ? baseIds : shuffled(baseIds, seed);
      setFilter("all");
      setQueue(order);
      idx = order.indexOf(id);
    }
    setPos(idx);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const onReset = () => {
    if (window.confirm("Reset all progress for this quiz? This cannot be undone.")) {
      reset();
      setFilter("all");
      setSeed(null);
      setQueue(baseIds);
      setPos(0);
    }
  };

  return (
    <div className="page">
      <div className="crumbs">
        <Link href={backHref}>← {backLabel}</Link>
      </div>

      <header className="quiz-head">
        <p className="kicker">{kicker}</p>
        <h1 className="title">{title}</h1>
        <div className="scoreline" aria-live="polite">
          <span>
            Answered <strong>{answeredCount}</strong> / {total}
          </span>
          <span className="sep">·</span>
          <span>
            Correct <strong>{correctCount}</strong>
          </span>
          <span className="sep">·</span>
          <span>
            Wrong <strong>{answeredCount - correctCount}</strong>
          </span>
        </div>
      </header>

      {practice && (
        <div className="toolbar" role="group" aria-label="Question filters">
          <div className="seg">
            {(["all", "unanswered", "wrong"] as Filter[]).map((f) => (
              <button
                key={f}
                type="button"
                className={"seg-btn" + (filter === f ? " on" : "")}
                aria-pressed={filter === f}
                onClick={() => applyView(f, seed)}
              >
                {f === "all" ? "All" : f === "unanswered" ? "Unanswered" : "Wrong"}
              </button>
            ))}
          </div>
          <button
            type="button"
            className={"seg-btn solo" + (seed !== null ? " on" : "")}
            aria-pressed={seed !== null}
            onClick={() => applyView(filter, seed === null ? Date.now() % 2147483647 : null)}
          >
            Shuffle order
          </button>
        </div>
      )}

      {finished && (
        <section className="results" aria-label="Results">
          <p className="kicker">Completed</p>
          <p className="big-score">
            {correctCount}
            <span> / {total}</span>
          </p>
          {wrongQuestions.length > 0 ? (
            <>
              <p className="results-note">Review the questions answered incorrectly:</p>
              <div className="chips">
                {wrongQuestions.map((q) => (
                  <button
                    key={q.id}
                    type="button"
                    className="chip hatch"
                    onClick={() => jumpToQuestion(q.id)}
                    title={`Variant ${q.variant}, question ${q.n}`}
                  >
                    {practice ? `V${q.variant}·${q.n}` : q.n}
                  </button>
                ))}
              </div>
            </>
          ) : (
            <p className="results-note">Every answer correct.</p>
          )}
        </section>
      )}

      {queue.length > 0 && (
        <nav className="navgrid" aria-label="Question navigator">
          {queue.map((id, i) => {
            const q = byId.get(id)!;
            const a = answers[id];
            const state = a === undefined ? "" : a === q.correct ? " ok" : " bad hatch";
            return (
              <button
                key={id}
                type="button"
                className={"nav-cell" + state + (i === pos ? " cur" : "")}
                onClick={() => go(i)}
                aria-label={`Question ${i + 1}${
                  a === undefined ? ", unanswered" : a === q.correct ? ", correct" : ", wrong"
                }`}
                aria-current={i === pos ? "true" : undefined}
              >
                {i + 1}
              </button>
            );
          })}
        </nav>
      )}

      {!ready ? (
        <p className="empty">Loading…</p>
      ) : !current ? (
        <p className="empty">
          {filter === "wrong"
            ? "No wrong answers — nothing to review."
            : filter === "unanswered"
            ? "Every question has been answered."
            : "No questions."}
        </p>
      ) : (
        <article className="card" key={current.id}>
          <div className="card-meta">
            <span>
              Question {Math.min(pos, queue.length - 1) + 1} of {queue.length}
            </span>
            {practice && (
              <span>
                Variant {current.variant} · No. {current.n}
              </span>
            )}
          </div>

          <h2 className="prompt">
            <RichText text={current.prompt} />
          </h2>

          <ul className="options">
            {current.options.map((opt, i) => {
              const isChosen = chosen === i;
              const isCorrect = current.correct === i;
              let cls = "opt";
              let tag = "";
              if (answered) {
                if (isCorrect) {
                  cls += " correct";
                  tag = isChosen ? "✓ Correct" : "✓ Correct answer";
                } else if (isChosen) {
                  cls += " wrong";
                  tag = "✕ Your answer";
                }
              }
              return (
                <li key={i}>
                  <button
                    type="button"
                    className={cls}
                    aria-disabled={answered}
                    onClick={() => pick(i)}
                  >
                    <span className="letter">{LETTERS[i]}</span>
                    <span className="opt-text">
                      <RichText text={opt} />
                    </span>
                    {tag && <span className="tag">{tag}</span>}
                  </button>
                </li>
              );
            })}
          </ul>

          <div className="pager">
            <button
              type="button"
              className="btn"
              style={{ visibility: pos > 0 ? "visible" : "hidden" }}
              onClick={() => go(pos - 1)}
            >
              ← Previous
            </button>
            <button
              type="button"
              className="btn solid"
              style={{ visibility: pos < queue.length - 1 ? "visible" : "hidden" }}
              onClick={() => go(pos + 1)}
            >
              Next →
            </button>
          </div>
        </article>
      )}

      <footer className="quiz-foot">
        <button type="button" className="link-btn" onClick={onReset}>
          Reset progress
        </button>
        <span className="hint">Keys: ← → navigate · 1–4 choose</span>
      </footer>
    </div>
  );
}
