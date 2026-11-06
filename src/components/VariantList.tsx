"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { ROMAN, variantKey, variants } from "@/lib/data";
import { readAnswers, type Answers } from "@/lib/useProgress";

export default function VariantList() {
  const [progress, setProgress] = useState<Record<number, Answers> | null>(null);

  useEffect(() => {
    const next: Record<number, Answers> = {};
    for (const v of variants) next[v.id] = readAnswers(variantKey(v.id));
    setProgress(next);
  }, []);

  return (
    <ol className="vlist">
      {variants.map((v) => {
        const answers = progress?.[v.id] ?? {};
        const total = v.questions.length;
        const answered = v.questions.filter((q) => answers[q.id] !== undefined).length;
        const correct = v.questions.filter((q) => answers[q.id] === q.correct).length;

        let status = "Not started";
        let action = "Start";
        if (progress && answered > 0 && answered < total) {
          status = `In progress, ${answered} of ${total} answered`;
          action = "Continue";
        } else if (progress && answered === total) {
          status = `Completed — ${correct} / ${total} correct`;
          action = "Review";
        }

        return (
          <li key={v.id}>
            <Link href={`/variants/${v.id}`} className="vrow">
              <span className="vnum">{ROMAN[v.id - 1]}</span>
              <span className="vbody">
                <span className="vtitle">{v.title}</span>
                <span className="vstatus">{progress ? status : " "}</span>
                <span className="vbar" aria-hidden="true">
                  {v.questions.map((q) => {
                    const a = answers[q.id];
                    const cls = a === undefined ? "" : a === q.correct ? " ok" : " bad hatch";
                    return <i key={q.id} className={"seg-cell" + cls} />;
                  })}
                </span>
              </span>
              <span className="vaction">{action} →</span>
            </Link>
          </li>
        );
      })}
    </ol>
  );
}
