import { notFound } from "next/navigation";
import QuizRunner from "@/components/QuizRunner";
import { ROMAN, variantKey, variants } from "@/lib/data";

export function generateStaticParams() {
  return variants.map((v) => ({ id: String(v.id) }));
}

export const dynamicParams = false;

export default async function VariantPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = await params;
  const variant = variants.find((v) => String(v.id) === id);
  if (!variant) notFound();

  return (
    <QuizRunner
      title={variant.title}
      kicker={`Exam variant ${ROMAN[variant.id - 1]}`}
      questions={variant.questions}
      storageKey={variantKey(variant.id)}
      backHref="/variants"
      backLabel="All variants"
    />
  );
}
