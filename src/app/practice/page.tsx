import QuizRunner from "@/components/QuizRunner";
import { PRACTICE_KEY, allQuestions } from "@/lib/data";

export default function PracticePage() {
  return (
    <QuizRunner
      title="All Questions"
      kicker={`Mode II · ${allQuestions.length} questions from every variant`}
      questions={allQuestions}
      storageKey={PRACTICE_KEY}
      backHref="/"
      backLabel="Home"
      practice
    />
  );
}
