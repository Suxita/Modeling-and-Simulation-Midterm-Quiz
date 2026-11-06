import raw from "@/data/questions.json";

export type Question = {
  id: string;
  n: number;
  variant: number;
  prompt: string;
  options: string[];
  correct: number;
};

export type Variant = {
  id: number;
  title: string;
  questions: Question[];
};

export const course: string = raw.course;

export const variants: Variant[] = raw.variants.map((v) => ({
  id: v.id,
  title: v.title,
  questions: v.questions.map((q) => ({ ...q, variant: v.id })),
}));

export const allQuestions: Question[] = variants.flatMap((v) => v.questions);

export const ROMAN = ["I", "II", "III", "IV", "V", "VI", "VII", "VIII"];

export const variantKey = (id: number) => `quiz:variant:${id}`;
export const PRACTICE_KEY = "quiz:practice";
